"""
network_handler.py: Library dedicated to Network Handling tasks including downloading files

Primarily based around the DownloadObject class, which provides a simple
object for libraries to query download progress and status
"""

import time
import requests
import threading
import logging
import enum
import hashlib
import atexit

from typing import Union
from pathlib import Path

from ..constants import Constants

from . import utilities

SESSION = requests.Session()

settings = Constants()

# GitHub 加速镜像候选列表，"" 表示直连 GitHub
GITHUB_MIRRORS = [
    ("", "直连 (GitHub)"),
    ("https://gh-proxy.com", "gh-proxy"),
    ("https://ghproxy.net", "ghproxy.net"),
    ("https://ghfast.top", "ghfast"),
]

# 多线程分段下载配置
MULTITHREAD_ENABLED = True
MULTITHREAD_DEFAULT_THREADS = 6  # 直连时使用的并发线程数
MULTITHREAD_PROXY_THREADS = 2    # 镜像代理时使用的并发线程数（避免 429 限流）
MULTITHREAD_MIN_SIZE = 50 * 1024 * 1024  # 小于 50MB 不分段
MULTITHREAD_CHUNK_SIZE = 4 * 1024 * 1024  # 单线程读取块大小

_fastest_mirror_cache: dict = {"url": None, "timestamp": 0}


def _extract_underlying_github_url(url: str) -> str:
    """
    识别已被代理前缀包裹的真实 github 链接。

    e.g. https://ghfast.top/https://github.com/a/b/c -> https://github.com/a/b/c
         https://download.simplehac.cn/https://github.com/a/b/c -> https://github.com/a/b/c
    """
    marker = "https://github.com/"
    http_marker = "http://github.com/"
    idx = url.find(marker)
    if idx == -1:
        idx = url.find(http_marker)
        if idx == -1:
            return url
        marker = http_marker
    return url[idx:]


def get_github_candidate_urls(original_url: str, force: bool = False) -> list:
    """
    探测 GitHub 直连及可用加速镜像，返回按可用性与速度排序的候选 URL 列表。
    直连正常可用时优先使用直连（避免第三方代理 429 限制与 Range 不兼容问题）。
    """
    underlying = _extract_underlying_github_url(original_url)
    if not underlying.startswith("https://github.com/"):
        return [original_url]

    results = {}

    def _probe(mirror: str, name: str):
        url = (mirror + "/" + underlying) if mirror else underlying
        try:
            t0 = time.time()
            r = SESSION.head(url, timeout=5, allow_redirects=True, verify=False)
            if r.status_code < 400:
                latency = time.time() - t0
                results[url] = (latency, mirror == "")
            else:
                results[url] = (999999.0, False)
        except Exception:
            results[url] = (999999.0, False)

    threads = [threading.Thread(target=_probe, args=(m, name)) for m, name in GITHUB_MIRRORS]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # 排序策略：直连在响应良好（<= 3.0s）时优先，避免代理镜像并发限流
    def _sort_key(item):
        url, (latency, is_direct) = item
        score = latency
        if is_direct and latency <= 3.0:
            score -= 1.5  # 给予官方直连优先权
        return score

    valid_candidates = [
        url for url, data in sorted(results.items(), key=_sort_key)
        if data[0] < 999999.0
    ]

    # 保底：若所有探测均超时，确保原始直连和镜像在候选列表中
    if not valid_candidates:
        valid_candidates = [underlying]
        for m, _ in GITHUB_MIRRORS:
            if m:
                valid_candidates.append(m + "/" + underlying)
    elif underlying not in valid_candidates:
        valid_candidates.append(underlying)

    logging.info(f"GitHub 下载候选源探测完成 (共 {len(valid_candidates)} 个可用): 首选 -> {valid_candidates[0]}")
    return valid_candidates


def get_fastest_github_url(original_url: str, force=False) -> str:
    """
    返回最适用的 GitHub 下载 URL。
    """
    candidates = get_github_candidate_urls(original_url, force=force)
    return candidates[0] if candidates else original_url

class DownloadStatus(enum.Enum):
    """
    Enum for download status
    """

    INACTIVE:    str = "Inactive"
    DOWNLOADING: str = "Downloading"
    ERROR:       str = "Error"
    COMPLETE:    str = "Complete"


class NetworkUtilities:
    """
    Utilities for network related tasks, primarily used for downloading files
    """

    def __init__(self, url: str = None) -> None:
        self.url: str = url

        if self.url is None:
            if settings.use_simplehacapi == True:
                self.url = "https://next.oclpapi.simplehac.cn/"
            else:
                self.url = "https://dortania.github.io/"

        # 配置SESSION，禁用SSL验证
        SESSION.verify = False
        # 忽略不安全的HTTPS请求警告
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


    def verify_network_connection(self) -> bool:
        """
        Verifies that the network is available

        Returns:
            bool: True if network is available, False otherwise
        """

        try:
            # 禁用SSL验证
            response = requests.head(self.url, timeout=5, allow_redirects=True, verify=False)
            if response.status_code == 404:
                return False
            else:
                return True
        except requests.exceptions.SSLError:
            # SSL错误也认为网络可用（因为只是证书问题，不是网络连接问题）
            logging.warning(f"SSL证书验证失败，但网络连接正常: {self.url}")
            return True
        except Exception as e:
            logging.debug(f"网络检测异常: {self.url} -> 错误: {str(e)}")
            return False

    def validate_link(self) -> bool:
        """
        Check for 404 error

        Returns:
            bool: True if link is valid, False otherwise
        """
        try:
            response = SESSION.head(self.url, timeout=5, allow_redirects=True)
            if response.status_code == 404:
                return False
            else:
                return True
        except (
            requests.exceptions.Timeout,
            requests.exceptions.TooManyRedirects,
            requests.exceptions.ConnectionError,
            requests.exceptions.HTTPError
        ):
            return False


    def get(self, url: str, **kwargs) -> requests.Response:
        """
        Wrapper for requests's get method
        Implement additional error handling

        Parameters:
            url (str): URL to get
            **kwargs: Additional parameters for requests.get

        Returns:
            requests.Response: Response object from requests.get
        """

        result: requests.Response = None

        try:
            # 确保禁用SSL验证
            kwargs['verify'] = False
            kwargs['timeout'] = kwargs.get('timeout', 30)
            result = SESSION.get(url, **kwargs)
        except (
            requests.exceptions.Timeout,
            requests.exceptions.TooManyRedirects,
            requests.exceptions.ConnectionError,
            requests.exceptions.HTTPError
        ) as error:
            logging.warn(f"Error calling requests.get: {error}")
            # Return empty response object
            return requests.Response()
        except requests.exceptions.SSLError as ssl_error:
            logging.warn(f"SSL错误，尝试不使用验证: {ssl_error}")
            # 重试一次，不使用SSL验证
            try:
                kwargs['verify'] = False
                result = SESSION.get(url, **kwargs)
            except Exception as retry_error:
                logging.error(f"重试下载失败: {retry_error}")
                return requests.Response()

        return result

    def post(self, url: str, **kwargs) -> requests.Response:
        """
        Wrapper for requests's post method
        Implement additional error handling

        Parameters:
            url (str): URL to post
            **kwargs: Additional parameters for requests.post

        Returns:
            requests.Response: Response object from requests.post
        """

        result: requests.Response = None

        try:
            result = SESSION.post(url, **kwargs)
        except (
            requests.exceptions.Timeout,
            requests.exceptions.TooManyRedirects,
            requests.exceptions.ConnectionError,
            requests.exceptions.HTTPError
        ) as error:
            logging.warn(f"Error calling requests.post: {error}")
            # Return empty response object
            return requests.Response()

        return result


class DownloadObject:
    """
    Object for downloading files from the network

    Usage:
        >>> download_object = DownloadObject(url, path)
        >>> download_object.download(display_progress=True)

        >>> if download_object.is_active():
        >>>     print(download_object.get_percent())

        >>> if not download_object.download_complete:
        >>>     print("Download failed")

        >>> print("Download complete"")

    """

    def __init__(self, url: str, path: str, size: str = None) -> None:
        self.url:       str = url
        self.status:    str = DownloadStatus.INACTIVE
        self.size:      str = size
        self.error_msg: str = ""
        self.filename:  str = self._get_filename()

        self.filepath:  Path = Path(path)

        self.total_file_size:      float = 0.0
        self.downloaded_file_size: float = 0.0
        self.start_time:           float = time.time()

        self.error:             bool = False
        self.should_stop:       bool = False
        self.download_complete: bool = False
        self.has_network:       bool = True  # 假设有网络，实际在下载时验证

        self.active_thread: threading.Thread = None

        self.should_checksum: bool = False

        self.checksum = None
        self._checksum_storage: hash = None

        # 注释掉初始的文件大小获取，在下载时再获取
        # if self.has_network:
        #     self._populate_file_size()


    def __del__(self) -> None:
        self.stop()


    def download(self, display_progress: bool = False, spawn_thread: bool = True, verify_checksum: bool = False) -> None:
        """
        Download the file

        Spawns a thread to download the file, so that the main thread can continue
        Note sleep is disabled while the download is active

        Parameters:
            display_progress (bool): Display progress in console
            spawn_thread (bool): Spawn a thread to download the file, otherwise download in the current thread
            verify_checksum (bool): Calculate checksum of downloaded file if True

        """
        self.status = DownloadStatus.DOWNLOADING
        logging.info(f"开始下载: {self.filename}")
        if spawn_thread:
            if self.active_thread:
                logging.error("下载正在进行中")
                return
            self.should_checksum = verify_checksum
            self.active_thread = threading.Thread(target=self._download, args=(display_progress,))
            self.active_thread.start()
            return

        self.should_checksum = verify_checksum
        self._download(display_progress)


    def download_simple(self, verify_checksum: bool = False) -> Union[str, bool]:
        """
        Alternative to download(), mimics  utilities.py's old download_file() function

        Parameters:
            verify_checksum (bool): Return checksum of downloaded file if True

        Returns:
            If verify_checksum is True, returns the checksum of the downloaded file
            Otherwise, returns True if download was successful, False otherwise
        """

        if verify_checksum:
            self.should_checksum = True
            self.checksum = hashlib.sha256()

        self.download(spawn_thread=False)

        if not self.download_complete:
            return False

        return self.checksum.hexdigest() if self.checksum else True


    def _get_filename(self) -> str:
        """
        Get the filename from the URL

        Returns:
            str: Filename
        """

        return Path(self.url).name


    def convert_size(self, size_str):
        units = {'KB': 1024, 'MB': 1024**2, 'GB': 1024**3, 'TB': 1024**4}
        for unit, factor in units.items():
            if unit in size_str:
               return float(size_str.replace(unit, '')) * factor
        return float(size_str)

    def _populate_file_size(self) -> None:
        """
        Get the file size of the file to be downloaded

        If unable to get file size, set to zero
        """

        # 若调用方显式提供了大小（如 convert_size 解析出的字节数），直接采用
        if self.size is not None:
            try:
                self.total_file_size = float(self.size)
                return
            except (ValueError, TypeError):
                pass

        try:
            result = SESSION.head(self.url, allow_redirects=True, timeout=5, verify=False)
            if 'Content-Length' in result.headers:
                self.total_file_size = float(result.headers['Content-Length'])
                return
            # Content-Length 缺失时尝试 Range 请求从 Content-Range 获取大小
            logging.info("HEAD 获取大小失败，尝试 Range 请求获取文件大小")
            raise Exception("Content-Length 头部缺失")
        except Exception as e:
            try:
                r = SESSION.get(
                    self.url, stream=True, timeout=10, allow_redirects=True, verify=False,
                    headers={"Range": "bytes=0-0"}
                )
                cr = r.headers.get("Content-Range")
                if cr and "/" in cr:
                    total = cr.split("/")[-1]
                    if total.isdigit():
                        self.total_file_size = float(total)
                        r.close()
                        return
                r.close()
            except Exception as re:
                logging.error(f"Range 获取文件大小失败: {re}")
            logging.error(f"确定文件大小时出错 {self.url}: {str(e)}")
            logging.error("假设文件大小为0")
            self.total_file_size = 0.0


    def _update_checksum(self, chunk: bytes) -> None:
        """
        Update checksum with new chunk

        Parameters:
            chunk (bytes): Chunk to update checksum with
        """
        self._checksum_storage.update(chunk)


    def _prepare_working_directory(self, path: Path) -> bool:
        """
        Validates working enviroment, including free space and removing existing files

        Parameters:
            path (str): Path to the file

        Returns:
            bool: True if successful, False if not
        """

        try:
            if Path(path).exists():
                logging.info(f"删除现有文件: {path}")
                Path(path).unlink()
                return True

            if not Path(path).parent.exists():
                logging.info(f"创建目录: {Path(path).parent}")
                Path(path).parent.mkdir(parents=True, exist_ok=True)

            available_space = utilities.get_free_space(Path(path).parent)
            if self.total_file_size > available_space:
                msg = f"没有足够的可用空间下载 {self.filename}，需要 {utilities.human_fmt(self.total_file_size)}，现有 {utilities.human_fmt(available_space)}"
                logging.error(msg)
                raise Exception(msg)

        except Exception as e:
            self.error = True
            self.error_msg = str(e)
            self.status = DownloadStatus.ERROR
            logging.error(f"准备工作目录时出错 {path}: {self.error_msg}")
            return False

        logging.info(f"- 目录已准备好: {path}")
        return True


    def _download(self, display_progress: bool = False) -> None:
        """
        Download the file

        Libraries should invoke download() instead of this method

        Parameters:
            display_progress (bool): Display progress in console
        """

        utilities.disable_sleep_while_running()

        try:
            original_url = self.url
            underlying = _extract_underlying_github_url(original_url)
            is_github = underlying.startswith("https://github.com/") or "github.com" in original_url

            if is_github:
                candidate_urls = get_github_candidate_urls(underlying)
            else:
                candidate_urls = [self.url]

            last_error = None
            for candidate_url in candidate_urls:
                if self.should_stop:
                    break

                self.url = candidate_url
                self.downloaded_file_size = 0
                self.start_time = time.time()
                logging.info(f"开始尝试下载: {self.url}")

                if self._prepare_working_directory(self.filepath) is False:
                    last_error = Exception(self.error_msg)
                    break

                self._populate_file_size()

                is_direct = not any(self.url.startswith(m[0]) for m in GITHUB_MIRRORS if m[0])
                num_threads = MULTITHREAD_DEFAULT_THREADS if is_direct else MULTITHREAD_PROXY_THREADS

                use_multithread = (
                    MULTITHREAD_ENABLED
                    and self.total_file_size >= MULTITHREAD_MIN_SIZE
                    and self.should_checksum is False
                )

                success = False
                if use_multithread:
                    success = self._download_multithread(display_progress, num_threads=num_threads)
                    if not success and not self.should_stop:
                        logging.warning(f"多线程分片下载未完成，自动尝试单连接流式下载: {self.url}")
                        self.downloaded_file_size = 0
                        self.start_time = time.time()
                        success = self._download_single_stream(display_progress)
                else:
                    success = self._download_single_stream(display_progress)

                if success and self.download_complete:
                    last_error = None
                    break
                else:
                    err_detail = self.error_msg or "下载不完整或被中断"
                    last_error = Exception(f"源 {self.url} 下载失败: {err_detail}")
                    logging.warning(f"{last_error}，自动切换至下一备用源...")
                    self._cleanup_temp_files()

            if last_error:
                self.error = True
                self.error_msg = str(last_error)
                self.status = DownloadStatus.ERROR
                logging.error(f"所有可用源均下载失败: {self.error_msg}")
            else:
                self.status = DownloadStatus.COMPLETE

        except Exception as e:
            self.error = True
            self.error_msg = str(e)
            self.status = DownloadStatus.ERROR
            logging.error(f"下载过程遇到未处理异常: {self.error_msg}")
        finally:
            utilities.enable_sleep_after_running()

    def _download_single_stream(self, display_progress: bool = False) -> bool:
        """单连接流式下载"""
        try:
            response = SESSION.get(self.url, stream=True, timeout=30, allow_redirects=True, verify=False)
            logging.info(f"单连接流式下载响应状态码: {response.status_code}")

            if response.status_code != 200:
                raise Exception(f"服务器返回错误状态码: {response.status_code}")

            if self.total_file_size == 0.0 and 'Content-Length' in response.headers:
                content_length = response.headers['Content-Length']
                if content_length and content_length.isdigit():
                    self.total_file_size = float(content_length)
                    logging.info(f"从响应头获取到文件大小: {utilities.human_fmt(self.total_file_size)}")

            with open(self.filepath, 'wb') as file:
                atexit.register(self.stop)
                for i, chunk in enumerate(response.iter_content(MULTITHREAD_CHUNK_SIZE)):
                    if self.should_stop:
                        raise Exception("下载已停止")
                    if chunk:
                        file.write(chunk)
                        self.downloaded_file_size += len(chunk)
                        if self.should_checksum:
                            self._update_checksum(chunk)
                        if display_progress and i % 100 == 0:
                            if self.total_file_size == 0.0:
                                print(f"已下载 {utilities.human_fmt(self.downloaded_file_size)} 的 {self.filename}")
                            else:
                                print(f"已下载 {self.get_percent():.2f}% 的 {self.filename} ({utilities.human_fmt(self.get_speed())}/秒) ({self.get_time_remaining():.2f} 秒剩余)")

            self.download_complete = True
            logging.info(f"单连接下载完成: {self.filename}")
            logging.info(f"- 已下载大小: {utilities.human_fmt(self.downloaded_file_size)}")
            logging.info(f"- 经过时间: {(time.time() - self.start_time):.2f} 秒")
            logging.info(f"- 速度: {utilities.human_fmt(self.downloaded_file_size / max(time.time() - self.start_time, 0.001))}/秒")
            logging.info(f"- 位置: {self.filepath}")
            return True

        except Exception as e:
            logging.error(f"单连接流式下载失败: {e}")
            if Path(self.filepath).exists():
                try:
                    Path(self.filepath).unlink()
                except Exception:
                    pass
            self.error_msg = str(e)
            return False

    def _download_multithread(self, display_progress: bool = False, num_threads: int = 6) -> bool:
        """
        多线程 Range 分段下载。
        在正式下载前执行 Range 预检，若服务器返回 429 或不支持 Range 则立即返回 False。
        """
        total = int(self.total_file_size)
        threads_count = min(num_threads, total // MULTITHREAD_CHUNK_SIZE or 1)
        if threads_count < 1:
            threads_count = 1

        logging.info(f"执行多线程 Range 预检: {self.url}")
        try:
            pre_r = SESSION.get(
                self.url,
                stream=True,
                timeout=10,
                allow_redirects=True,
                verify=False,
                headers={"Range": "bytes=0-1023"}
            )
            pre_status = pre_r.status_code
            pre_r.close()
            if pre_status == 429:
                logging.warning(f"该源已触发 429 限流，放弃多线程: {self.url}")
                return False
            if pre_status != 206:
                logging.info(f"服务器返回状态码 {pre_status}，不支持 Range 206，放弃多线程")
                return False
        except Exception as e:
            logging.warning(f"Range 预检异常: {e}")
            return False

        logging.info(f"Range 预检通过，使用 {threads_count} 个连接分片下载: {self.filename}")

        # 预创建文件
        try:
            with open(self.filepath, 'wb') as f:
                f.truncate(total)
        except Exception as e:
            logging.error(f"创建占位文件失败: {e}")
            return False

        part_files = [Path(str(self.filepath) + f".part{i}") for i in range(threads_count)]
        for pf in part_files:
            if pf.exists():
                try:
                    pf.unlink()
                except Exception:
                    pass

        lock = threading.Lock()
        failed_flag = {"value": False, "error": ""}
        ranges = []

        segment = total // threads_count
        for i in range(threads_count):
            start = i * segment
            end = total - 1 if i == threads_count - 1 else (i + 1) * segment - 1
            ranges.append((start, end))

        def _fetch_range(idx: int):
            if failed_flag["value"] or self.should_stop:
                return
            start, end = ranges[idx]
            part_path = part_files[idx]
            expected_bytes = end - start + 1
            written_bytes = 0
            try:
                headers = {"Range": f"bytes={start}-{end}"}
                with SESSION.get(self.url, stream=True, timeout=60, allow_redirects=True, verify=False, headers=headers) as r:
                    if r.status_code == 429:
                        raise Exception("429 Too Many Requests")
                    if r.status_code != 206:
                        raise Exception(f"分片响应状态码非 206: {r.status_code}")

                    with open(part_path, 'wb') as pf:
                        for chunk in r.iter_content(MULTITHREAD_CHUNK_SIZE):
                            if self.should_stop or failed_flag["value"]:
                                return
                            if chunk:
                                pf.write(chunk)
                                written_bytes += len(chunk)
                                with lock:
                                    self.downloaded_file_size += len(chunk)

                if written_bytes != expected_bytes and not self.should_stop and not failed_flag["value"]:
                    raise Exception(f"分片 {idx} 字节数不一致: 预期 {expected_bytes}, 实际 {written_bytes}")

            except Exception as e:
                with lock:
                    if not failed_flag["value"]:
                        failed_flag["value"] = True
                        failed_flag["error"] = str(e)
                        logging.warning(f"分片 {idx} 下载失败: {e}")

        threads = [threading.Thread(target=_fetch_range, args=(i,)) for i in range(threads_count)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        if failed_flag["value"] or self.should_stop:
            self._cleanup_part_files(part_files)
            if Path(self.filepath).exists():
                try:
                    Path(self.filepath).unlink()
                except Exception:
                    pass
            return False

        # 合并分片
        try:
            with open(self.filepath, 'r+b') as out:
                for i, (start, end) in enumerate(ranges):
                    part_path = part_files[i]
                    with open(part_path, 'rb') as pf:
                        out.seek(start)
                        while True:
                            chunk = pf.read(MULTITHREAD_CHUNK_SIZE)
                            if not chunk:
                                break
                            out.write(chunk)
                    part_path.unlink()
        except Exception as e:
            logging.error(f"合并分片文件失败: {e}")
            self._cleanup_part_files(part_files)
            if Path(self.filepath).exists():
                try:
                    Path(self.filepath).unlink()
                except Exception:
                    pass
            return False

        self.download_complete = True
        logging.info(f"多线程下载完成: {self.filename}")
        logging.info("统计信息:")
        logging.info(f"- 已下载大小: {utilities.human_fmt(self.downloaded_file_size)}")
        logging.info(f"- 经过时间: {(time.time() - self.start_time):.2f} 秒")
        logging.info(f"- 速度: {utilities.human_fmt(self.downloaded_file_size / max(time.time() - self.start_time, 0.001))}/秒")
        logging.info(f"- 位置: {self.filepath}")
        return True

    def _cleanup_part_files(self, part_files) -> None:
        for pf in part_files:
            try:
                if pf.exists():
                    pf.unlink()
            except Exception:
                pass

    def _cleanup_temp_files(self) -> None:
        self._cleanup_part_files([Path(str(self.filepath) + f".part{i}") for i in range(16)])
        if Path(self.filepath).exists():
            try:
                Path(self.filepath).unlink()
            except Exception:
                pass


    def get_percent(self) -> float:
        """
        Query the download percent

        Returns:
            float: The download percent, or -1 if unknown
        """

        if self.total_file_size == 0.0:
            return -1
        return self.downloaded_file_size / self.total_file_size * 100


    def get_speed(self) -> float:
        """
        Query the download speed

        Returns:
            float: The download speed in bytes per second
        """

        return self.downloaded_file_size / (time.time() - self.start_time)


    def get_time_remaining(self) -> float:
        """
        Query the time remaining for the download

        Returns:
            float: The time remaining in seconds, or -1 if unknown
        """

        if self.total_file_size == 0.0:
            return -1
        speed = self.get_speed()
        if speed <= 0:
            return -1
        return (self.total_file_size - self.downloaded_file_size) / speed


    def get_file_size(self) -> float:
        """
        Query the file size of the file to be downloaded

        Returns:
            float: The file size in bytes, or 0.0 if unknown
        """

        return self.total_file_size


    def is_active(self) -> bool:
        """
        Query if the download is active

        Returns:
            boolean: True if active, False if completed, failed, stopped, or inactive
        """

        if self.status == DownloadStatus.DOWNLOADING:
            return True
        return False


    def stop(self) -> None:
        """
        Stop the download

        If the download is active, this function will hold the thread until stopped
        """

        self.should_stop = True
        if self.active_thread:
            while self.active_thread.is_alive():
                time.sleep(1)