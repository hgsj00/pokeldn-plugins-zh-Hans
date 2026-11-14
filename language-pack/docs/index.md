---
title: 主页
nav_order: 1
---

# pokeldn

pokeldn 是任天堂 Switch 本地无线（LDN）的一种实现，它以 ESP32 开发板作为射频，与零售 Switch 主机上的宝可梦游戏通信：可通过电脑或 Android 手机的 USB 串口连接，也可通过 iPhone 的蓝牙连接。这些页面记录了这些协议，并附有反编译出处、反汇编地址与硬件测量数据。

从[应用设置](gui.md)或[命令行用法](usage.md)开始。

## 目标

七款游戏共用相同的 LDN 与 Pia 层：

| | FRLG | LGPE | SwSh | BDSP | PLA | SV | PLZA |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 交换 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 神秘礼物 | ✓ | ∅ | ✓ | ∅ | ∅ | ∅ | ∅ |
| 配信宝可梦 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 连接对战 | ✓ | ✗ | ✗ | ✗ | ∅ | ✗ | ✗ |
| 主机端执行代码、读写存档 | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |

✓ 可在零售主机上运行 · ✗ 未完成 · ∅ 游戏在本地无线下没有此功能
FRLG 火红／叶绿 · LGPE Let's Go！皮卡丘／伊布 · SwSh 剑／盾 · BDSP 晶灿钻石／明亮珍珠 · PLA 传说 阿尔宙斯 · SV 朱／紫 · PLZA 传说 Z-A

火红与叶绿以 GBA ROM 的形式运行在 Switch 的模拟器内，因此该 ROM 的 GBA 连接协议架在 LDN 与 Pia 之上。其余六款游戏则把自己的代码直接架在 Pia 上：BDSP 为 Unity/IL2CPP，SwSh 与 LGPE 为经 `gflnet3` 使用 protocol buffers 的 C++，PLA、SV 与 PLZA 为静态链接 Pia 的 C++。

## 章节

| 章节 | 内容 |
|---|---|
| [无线层](ldn.md) | LDN 与 Pia：广播、关联、各版本的数据包格式、会话密钥推导。 |
| [逆向 Switch 游戏](switch_re.md) | 阅读零售游戏自身的代码：原地提取 NCA/RomFS、IL2CPP 元数据、C++ RTTI。 |
| [火红与叶绿](frlg.md) | GBA 连接、神秘礼物、代码执行、RNG、卡带。 |
| [晶灿钻石与明亮珍珠](bdsp.md) | Pia 5.27-5.45、联盟交谊厅，以及交换流程。 |
| [剑与盾](swsh.md) | Pia 4、同步框架、交换、极巨团体战、极巨大冒险、神秘礼物。 |
| [Let's Go！皮卡丘与伊布](lgpe.md) | Pia 3、连接密码，以及交换流程。 |
| [传说 阿尔宙斯](pla.md) | Pia 头部版本 11、交换流程、组合记录。 |
| [朱与紫](sv.md) | Pia 头部版本 11、可靠流、交换、太晶团体战、集友圈。 |
| [传说 Z-A](za.md) | Pia 头部版本 16 与二十条交换消息。 |
| [模拟神秘礼物](gift_simulated.md) | 由主机以交换方式送给没有本地神秘礼物功能的游戏的官方配信宝可梦。 |
| [命令行用法](usage.md) | 各游戏的源码设置与命令。 |
| [桌面应用](gui.md) | 设置、Bank、控制器、构建；Android 与 iOS。 |
| [代码组织](architecture.md) | 共享模块、宝可梦的准备与校验。 |
| [硬件与设置](hardware.md) | ESP32 射频、Switch 密钥，以及旧式 Linux Wi-Fi 网卡。 |
| [代码签名政策](code_signing.md) | Windows 版本签名的内容、团队角色，以及隐私政策。 |

## 致谢

本项目基于 [kinnay 的 LDN 库](https://github.com/kinnay/LDN) 与 [NintendoClients wiki](https://github.com/kinnay/NintendoClients/wiki) 构建，并对照 [pret/pokefirered](https://github.com/pret/pokefirered)（火红／叶绿的反编译项目）阅读。
