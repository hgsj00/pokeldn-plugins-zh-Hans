---
title: 代码签名政策
nav_order: 12
---

# 代码签名政策

免费代码签名由 [SignPath.io](https://about.signpath.io) 提供，证书由 [SignPath Foundation](https://signpath.org) 签发

桌面应用的 Windows 版本，即 [Releases](https://github.com/Decryptu/pokeldn/releases) 页面上的 `pokeldn-windows-x64.zip`，会为本仓库源码构建的以下二进制文件附加 Authenticode 签名：`pokeldn.exe`、PKHeX 辅助程序 `pokeldn-pkhex.exe` 以及 Unicorn 库 `unicorn.dll`。GitHub Actions 从本仓库的 `v*` 标签构建它们（[release.yml](https://github.com/Decryptu/pokeldn/blob/main/.github/workflows/release.yml)）；SignPath 只对那次构建产出的文件签名，不对在别处构建的文件签名。构件配置见 [.github/signpath/artifact-configuration.xml](https://github.com/Decryptu/pokeldn/blob/main/.github/signpath/artifact-configuration.xml)。原样打包的第三方文件保留其各自发布者的签名，或没有签名。

## 团队角色

| 角色 | 成员 |
|---|---|
| 提交者与审核者 | [Decryptu](https://github.com/Decryptu) |
| 批准者 | [Decryptu](https://github.com/Decryptu) |

每个发行版的签名请求都需人工批准。其他人的贡献只能以拉取请求的形式进入仓库，并由提交者审核。

## 隐私政策

除非用户或安装、运行本程序的人明确要求，本程序不会向其他联网系统传输任何信息。它会发起以下请求：

| 时机 | 发往 | 发送内容 |
|---|---|---|
| 启动时，当“设置”中的“更新”处于开启状态（默认） | GitHub API，以及每个已安装插件的更新地址 | 请求最新版本；不包含任何关于玩家或其所玩游戏的信息 |
| 玩家下载射频固件或活动团体战数据 | GitHub | 一个下载请求 |
| 玩家使用交换（在线）或 GTS | 公共 Nostr 中继（[在线交换](online.md)） | 加密的交换事件，包括所提供交换的宝可梦 |
| 玩家安装或更新插件，或浏览插件源 | 该插件或源的地址 | 一个下载请求 |

发往 GitHub 的请求适用 GitHub 的隐私声明。每个中继则适用该中继运营方自己的政策。本应用不发送分析数据，也不发送崩溃报告。
