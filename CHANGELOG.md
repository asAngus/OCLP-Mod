# OCLP-Mod changelog

*Automatically generated from GitHub releases*
*Source: https://github.com/laobamac/OCLP-Mod*
*Last update: 2026-11-13*

---

## 3.1.9-mod1
*Release date: 2026-11-13*

### 解决的核心问题 (Issues Fixed)
1. **修复 GitHub 下载 429 报错及驱动补丁（KDK）中断问题**：
   - **智能测速与源排序优化**：在网络直连 GitHub 良好（延迟 <= 3s）时优先直连官方源，大幅提升大文件吞吐率（实测可达 20~54 MB/s），且避免第三方代理限流与分段不兼容。
   - **动态并发控制**：官方直连启用 6 线程分段并发加速；镜像代理自动降至 2 线程，彻底解决 `ghfast` 等公共镜像并发请求触发 `HTTP 429 Too Many Requests` 导致下载失败的问题。
   - **Range 预检保护**：下载前进行 Range 预检，对不支持 206 状态码或返回 429 的节点自动降级为单流或自动切源。

2. **多源无缝自动容灾回退（Failover）**：
   - 任何单一节点遇到 429 限流、网络超时或连接中断时，自动清理临时分片并平滑无缝切换至下一个健康备用源重试，彻底杜绝下载流程报错中断。

3. **清理失效镜像与更新通道**：
   - 移除已失效的 `download.simplehac.cn`（连接重置）及 `proxy.yaoyaoling.net`（超时死链）。
   - 修复应用更新检查模块（`gui_update.py`）中对失效域名的硬编码依赖，统一由具备自动容灾的下载器接管。

---

## 3.1.4
*Release date: 2026-01-15*

- 添加OCLP-Mod Shim，现在你可以在 **macOS Tahoe** 的 **Spotlight Plus** 中找到并打开 **OCLP-Mod** 了！
- 修正了 **无线网卡补丁** 内错误的“需要下载KDK”设置
- 修正了部分未翻译的字符串

[Full Release](https://github.com/laobamac/OCLP-Mod/releases/tag/3.1.4)

---


## 3.1.3
*Release date: 2026-01-01*

- 修复了单独安装无线网卡补丁并重启后错误地显示“需要卸载补丁以继续”的问题
- 修改为使用UTC偏移量判断地区

[Full Release](https://github.com/laobamac/OCLP-Mod/releases/tag/3.1.3)

---

## 3.1.2
*Release date: 2025-12-28*

- Updated **OpenCore** to `1.0.6`
- Fixed the issue where the `populate_pci_path` method failed to obtain the correct PCI path on certain platforms (especially C612), causing crashes
- Added `OMAPIv1` and `OMAPIv2` mainland China nodes. If necessary, they can be switched under **Settings → App**
- Automatically detects the current region (Mainland China / Hong Kong, Macao, Taiwan / Overseas) to select the default API node. **Mainland China** defaults to **OMAPIv1**, others directly connect to Github
- 修复`populate_pci_path`方法在部分平台（尤其是C612）上无法获取正确PCI路径导致崩溃的问题
- 增加了`OMAPIv1`和`OMAPIv2`大陆节点，必要情况下可以在 **设置->App** 下更换。
- 自动检测当前地区（中国大陆/港澳台/海外）来选择默认API节点。**中国大陆**默认**OMAPIv1**，其余直连Github

[Full Release](https://github.com/laobamac/OCLP-Mod/releases/tag/3.1.2)

---

## 3.1.1
*Release date: 2025-12-25*

- 在macOS 26上运行时支持 `Solarium 液态玻璃`外观 。
- 在无网络状态下自动删除网络所需的补丁。如果没有网络连接，则允许先安装无线补丁。
- 提高kdk_handler和metallib_handler的稳定性。
- 改进API选择策略。

[Full Release](https://github.com/laobamac/OCLP-Mod/releases/tag/3.1.1)

---

## 3.1.0
*Release date: 2025-12-24*

- 支持在`macOS Tahoe`安装博通无线网卡/英特尔无线网卡的补丁，**无需禁用AMFI**，只需要正常加载**AMFIPass.kext**即可！（无法进入系统请添加启动参数`-lilubetaall`或者`-amfipassbeta`）
- Support the installation of Broadcom wireless network card/Intel wireless network card patches in `macOS Tahoe`, **no need to disable AMFI**, just load **AMFIPass.kext** normally! ( If you can't enter the system, please add the startup parameter `-lilubetaall` or `-amfipassbeta`)

[Full Release](https://github.com/laobamac/OCLP-Mod/releases/tag/3.1.0)

---

## 2.6.9
*Release date: 2025-11-29*

- Automatically modify `SpotlightPlus.plist` to switch the App style when installing/uninstalling the relevant patches of `old launchpad`<br>

[Full Release](https://github.com/laobamac/OCLP-Mod/releases/tag/2.6.9)

---

## 2.6.8
*Release date: 2025-11-29*

- Reconstruct gui_kdk_dl and gui_ml_dl,fix speed detection. #53<br>
- Brand-new KDK and Metallib download manager UI<br>
- Fix wrong file size detection.<br>
- Fix some Liquid Glass UI styles on Tahoe,Improve code style.<br>
- Switch to OMAPIv1.<br>

[Full Release](https://github.com/laobamac/OCLP-Mod/releases/tag/2.6.8)

---

## 2.6.7
*Release date: 2025-11-23*

- 使用位于中国大陆的新OMAPI，修复KDK/ML下载对象，修复DMG下载对象。下载速度将达到50MB/s~100MB/s
- HDA补丁不再需要AMFIPass.kext。
- 将OpenCore同步到1.0.6。

[Full Release](https://github.com/laobamac/OCLP-Mod/releases/tag/2.6.7)

---

## 2.6.4
*Release date: 2025-05-12*

- 更新 **BrcmPatchRAM** 至 `2.7.0`
- 添加对 `EHCI` 总线 (USB1.1) 下 USB 摄像头的补丁支持

[Full Release](https://github.com/laobamac/OCLP-Mod/releases/tag/2.6.4)

---

## 2.6.2
*Release date: 2025-04-09*

- 增加了对 **Intel AX211 (CNVi)** 无线网卡的支持
- 将进度条动画缩短以减少GPU占用，防止低性能机器在加载过程死机

[Full Release](https://github.com/laobamac/OCLP-Mod/releases/tag/2.6.2)

---

## 2.6.0
*Release date: 2025-04-04*

- 修复了搭载T1安全芯片的Mac在 **macOS Sequoia 15.4 +** 中无法使用钥匙串等安全性工具的问题

[Full Release](https://github.com/laobamac/OCLP-Mod/releases/tag/2.6.0)

---

## 2.5.5
*Release date: 2025-04-02*

- 修复了未安装KDK时无法拉起Metallib下载任务的问题
- 修复了在 **macOS Sequoia** 上Intel 4代前核显小部件白屏的问题
- 修复了启用 **OpenCore Vaulted** 后无法正确生成EFI的问题
- 更新 **OpenCore** 到`1.0.4`
- 更新 **WhateverGreen** 到`1.6.9`

[Full Release](https://github.com/laobamac/OCLP-Mod/releases/tag/2.5.5)

---

## 2.5.4
*Release date: 2025-03-31*

- 修复了在**macOS Sequoia 15.1 +**`Non-Metal`显卡在Hello页面黑屏的问题
- 修复了在**macOS Sequoia**中4代Intel之前的旧核显无法正确加载的问题
- 修复了在**macOS Sequoia 15.4**中搭载T1安全芯片的Mac无法使用指纹解锁的问题
- 修复了**macOS Sequoia 15.4**中`Non-Metal`显卡状态栏不透明的问题

[Full Release](https://github.com/laobamac/OCLP-Mod/releases/tag/2.5.4)

---

## 2.5.3
*Release date: 2025-02-22*

- 移除了App自动安装程序（OCLP-Mod-GUI.app），后续只编译Pkg安装包
- 修复部分补丁集无法识别已安装信息的问题

[Full Release](https://github.com/laobamac/OCLP-Mod/releases/tag/2.5.3)

---

## 2.5.2
*Release date: 2025-02-02*

- 修复了macOS Sonoma上错误的补丁报告

[Full Release](https://github.com/laobamac/OCLP-Mod/releases/tag/2.5.2)

---

## 2.5.1
*Release date: 2025-01-01*

- 增加 **AMD GCN** 显卡安装补丁时的启动参数检测
- 增加 **NVIDIA** 显卡安装补丁时的参数检测

[Full Release](https://github.com/laobamac/OCLP-Mod/releases/tag/2.5.1)

---

## 2.5.0
*Release date: 2024-12-29*

- 鉴于国内站点大多付费分享镜像且为低速网盘，SimpleHac发布于[SimpleHac资源社](https://www.simplehac.cn)和PCBETA的镜像有时不方便登录使用，故添加直链复制、在线下载功能。
- 刻录DMG未完工，假期继续
- 2.4.5 +版本可点击“在线更新”到2.5.0

[Full Release](https://github.com/laobamac/OCLP-Mod/releases/tag/2.5.0)

---

## 2.4.8
*Release date: 2024-12-15*

- 支持 **NVIDIA** 显卡在 **macOS Sequoia 15.2** 的 **WebDrivers** 补丁，支持使用 **红杉日出** 动态壁纸！
- 解决了iCloud同步问题
- 在macOS Sequoia 15.2/Safari 18.2上解析了在缺失AVX2的Mac上的JavaScriptCore

[Full Release](https://github.com/laobamac/OCLP-Mod/releases/tag/2.4.8)

---

## 2.4.7
*Release date: 2024-12-12*

- 修复T1安全芯片的Mac在macOS Sequoia 15.2的 **ApplePay** 失效
- 修复T1安全芯片的Mac在macOS Sequoia 15.2的 **TouchID** 失效
- 修复T1安全芯片的Mac在macOS Sequoia 15.2的 **iCloud** 失效
- 支持在macOS Sonoma/Sequoia上的non-metal显卡使用台前调度缩放
- 支持在macOS Sequoia上的non-metal显卡使用iCloud加载相册
- 支持在macOS Sequoia 15.1.1 + 上的non-metal显卡使用屏幕共享，随行，截图，录屏等功能
- 支持在macOS Sequoia 15.1.1 + 上的non-metal显卡加载半透明菜单栏和天气app
- 支持在macOS Sonoma/Sequoia上的non-metal显卡使用外置屏幕时缩放大小
- 添加了需要avx2补丁的处理器在macOS Sequoia 15.2的支持
- 修复了BCM43502C在macOS Sequoia锁死7M的问题

[Full Release](https://github.com/laobamac/OCLP-Mod/releases/tag/2.4.7)

---

## 2.4.6
*Release date: 2024-12-05*

- 正式支持Atheros网卡在Sequoia的WiFi驱动，教程可见 [远景论坛-使用OCLP-Mod在Sequoia上驱动AR9285等高通网卡](https://bbs.pcbeta.com/viewthread-2024928-1-1.html)
- 修复了需要安装Metallib的显卡补丁时无限循环 ，来自@P.S.KEEN
- 更新api节点，原来的api节点多次被举报，目前已被Cloudflare拉入黑名单，导致2.4.5以前的OCLP-Mod无法安装需要网络连接（如下载KDK）的补丁。我不清楚某些人出于什么心理，但我相信这是最后一次，且是无意之举！

[Full Release](https://github.com/laobamac/OCLP-Mod/releases/tag/2.4.6)

---

## 2.4.5
*Release date: 2024-12-04*

- 修复根修补期间的metallib_install_handle句柄。
- 修复KDK_down_handle错误的尾缀名（*.dmg）。

[Full Release](https://github.com/laobamac/OCLP-Mod/releases/tag/2.4.5)

---

## 2.4.4
*Release date: 2024-12-03*

- 更新至 OpenCore 1.0.3
- 添加对AR9485/AR8111/AR9285在Sequoia的支持
- 修复SN的生成
- 启用Github Action，以后可在Actions获取最新编译版本（开发测试！生产环境不要使用！）
- 将Lilu更新到1.7.0，WEG更新到1.6.9，修复OpenCore的更新程序，以便它可以在1.0.3+上使用

[Full Release](https://github.com/laobamac/OCLP-Mod/releases/tag/2.4.4)

---

## 2.4.3
*Release date: 2024-12-01*

# OCLP-Mod 2.4.3
* Add support to run Application directly！Don't need to install .pkg any more！🎉
* Fix patches on AMD_GCN 7000,these GPUs can be used on Seqouia 15.2+ now!
* Reuse the OpenCore 1.0.2，fix the SLC folder，for #3
⚠️Warning：Since 2.4.3，many application strings have been changed，so the Auto-Update of 2.4.2 and below perhaps will fail.You need download it from RELEASEs and install it manually！
* 支持直接运行应用程序（.app）！不再需要pkg安装了！🎉
* 修复AMD_GCN 7000上的补丁，这些GPU现在可以在Seqouia 15.2+上使用！
* 重复使用OpenCore 1.0.2，修复SLC文件夹，解决 #3
⚠️警告：自2.4.3以来，许多应用程序字符串已被更改，因此2.4.2及以下版本的自动更新可能会失败。您需要手动从RELEASES下载并安装！

[Full Release](https://github.com/laobamac/OCLP-Mod/releases/tag/2.4.3)

---

## 2.4.2
*Release date: 2024-11-25*

- 更新至OpenCore 1.0.3
- 修复了payload.dmg挂载失败导致无法生成OpenCore的问题

[Full Release](https://github.com/laobamac/OCLP-Mod/releases/tag/2.4.2)

---

## 2.4.1
*Release date: 2024-11-24*

- 修复手动下载KDK，Metallib版本不对应的问题
- 允许复制下载加速链接自行使用其他工具下载

[Full Release](https://github.com/laobamac/OCLP-Mod/releases/tag/2.4.1)

---

## 2.4.0
*Release date: 2024-11-24*

- 更新Kext以更好的支持Sequoia
- `Lilu.kext -> 1.6.9`
- `WhateverGreen.kext -> 1.6.7`
- `WhateverGreen (Navi Patch).kext -> 1.6.7-Navi`
- `AirPortBrcmFixup.kext -> 2.1.9`
- `NVMeFix.kext -> 1.1.1`
- `AppleALC.kext -> 1.6.3`
- `RestrictEvents.kext -> 1.1.4`
- `FeatureUnlock.kext -> 1.1.7`
- `DebugEnhancer.kext -> 1.1.0`
- `CPUFriend.kext -> 1.2.9`
- `BlueToolFixup (BrcmPatchRAM).kext -> 2.6.9`
- `CSLVFixup.kext -> 2.6.1`
- `AutoPkgInstaller.kext -> 1.0.4`
- `CryptexFixup.kext -> 1.0.4`
- 添加自动更新，使用SimpleHac的`OCLP-API`，国内可满速
- 汉化剩余字符串
- 修改`checkNetwork`方法，修改`downloadObj`实现国内加速
- 添加对AR9485，AR9565等网卡的支持（仅环境补丁）

[Full Release](https://github.com/laobamac/OCLP-Mod/releases/tag/2.4.0)

---

## 2.3.2
*Release date: 2024-11-17*

- 修复了在Macintosh上无法生成OpenCore的问题 #2 @kingtosh
- 更新OpenCore至1.0.2，Lilu 1.6.9以更好的支持Sequoia
- 优化EFI -> ESP安装逻辑，并添加安装引导UI

[Full Release](https://github.com/laobamac/OCLP-Mod/releases/tag/2.3.2)

---

## 2.3.0
*Release date: 2024-11-13*

- 修复macOS 15.2 的non-metal显卡补丁
- 修复macOS 15.2 的工具挂载失败
- 支持在应用程序启动之间从GUI保存设置。请注意，这仅适用于模型上的设置，更改Mac型号会重置设置。
- 默认禁用FeatureUnlock和mediaanalysisd（实时文本）以保持稳定性。如果需要任一功能，可以在设置中重新启用。
- 解决macOS 15.1（24B2083）苹果安装程序显示为下载选项。在15.1上解决WhatsApp崩溃问题。
- 在构建OpenCore错误时添加额外的错误处理，防止损坏的EFI被安装到磁盘上

[Full Release](https://github.com/laobamac/OCLP-Mod/releases/tag/2.3.0)

---

## 2.1.3
*Release date: 2024-10-04*

* 修改OTA后第一次启动自动Patch的弹窗
* 添加KDK，Metallib加速自选下载（Patch提示下载也有加速，不用担心）

[Full Release](https://github.com/laobamac/OCLP-Mod/releases/tag/2.1.3)

---

## 2.1.2
*Release date: 2024-10-03*

- Updated to OCLP 2.0.2
- Blocked updates.

[Full Release](https://github.com/laobamac/OCLP-Mod/releases/tag/2.1.2)

---

## 2.1.1
*Release date: 2024-10-01*

- Add KDK/MetalLib files accelerated download url.
- Thanks llkk/moeyy/ghproxy and others.
- Please use .pkg to install!!! .app file maybe make errors.

[Full Release](https://github.com/laobamac/OCLP-Mod/releases/tag/2.1.1)

---

## 2.1.0
*Release date: 2024-10-01*

- 1.Add IntelWireless and BCM Wireless Card patch back.
- 2.Sinicize almost all strings.
More see here [ChangeLog](https://github.com/dortania/OpenCore-Legacy-Patcher/blob/main/CHANGELOG.md)
- ⚠️Please use .pkg to install OCLP-Mod！！！Open .app directly maybe make error.

[Full Release](https://github.com/laobamac/OCLP-Mod/releases/tag/2.1.0)

---

