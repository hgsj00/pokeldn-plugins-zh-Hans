---
title: 适配器
parent: Hardware and setup
nav_order: 3
---

# Wi-Fi 适配器

Linux 主机可以以 root 身份直接驱动一块支持 AP 的 Wi-Fi 网卡，取代 [ESP32 射频](hardware_esp32.md)。该方案属于旧式做法。

| 症状 | 原因 |
|---|---|
| AP 启动时出现虚拟机管理程序式的 USB 断开 | USB 模式切换（见下文） |
| 主机静默无输出 | 未设置 `accept_decrypted_ccmp` |
| `dmesg` 中出现 `failed to get tx report from firmware` | 主机自身的拆除动作 |

## 通过 ldnrs 使用 Windows USB Wi-Fi

Windows 可以通过 [ldnrs 0.0.3](https://github.com/unlimitedcoder2/ldnrs/releases/tag/0.0.3) 使用外置 USB Wi-Fi 适配器。请单独安装 ldnrs，完成其适配器向导，并让它的守护进程保持运行。在 pokeldn 中打开 **插件**，然后在 **射频** 下选择 **USB Wi-Fi（Windows，ldnrs）**。Switch 密钥仍来自 pokeldn 的设置。

ldnrs 向导会把适配器绑定到 WinUSB，并下载它所需的 Linux 驱动固件；在设备管理器中恢复原始驱动之前，该适配器不再提供 Windows Wi-Fi。兼容性取决于 ldnrs；下文 Linux 网卡的结果并不能说明 Windows 上的情况。

在 PowerShell 中，先选择后端，再运行任意游戏惯用的启动器：

```powershell
$env:POKELDN_RADIO = 'ldnrs:'
python bin/swsh_gift_host.py --keys C:\Switch\prod.keys --species 25 --level 25
```

空参数会选择本地管道 `\\.\pipe\ldnd`；冒号之后可以跟另一个管道名。守护进程通过该管道接收密钥。它掌控射频、LDN 关联与加密；pokeldn 则通过其现有的用户态 IPv4 栈承载以太网帧。扫描、加入、主持和广播更新都使用 [守护进程协议 7](https://github.com/unlimitedcoder2/ldnrs/blob/0.0.3/docs/daemon-protocol.md)。守护进程缺失、适配器未就绪或协议版本不同都会以错误告终。

关联在守护进程中允许 70 秒，在启动器中至少 90 秒：上游的 [RTL8822BU 测量](https://github.com/unlimitedcoder2/ldnrs/blob/0.0.3/clients/python/ldnd/compat.py) 把两次驱动重配置各计为约 14.5 秒。游戏握手在关联之后开始。一个守护进程同一时间只承载一个会话。会话结束时 pokeldn 会关闭其原始通道与网络；它会让外部守护进程继续运行。抓包会保留游戏的 UDP 流量；ESP32 计数器与捆绑库的 Wi-Fi 管理钩子则不适用。

离线测试会用 ldnrs 0.0.3 的 Python 客户端给出的向量比对扫描、加入与主持请求，并与脚本化的守护进程交换 UDP。Windows 适配器搭配零售版主机的情况尚未在此后端上测试。

## 已测试网卡

| 型号 | 类型 | 驱动 | 在已测试主机上的结果 |
|---|---|---|---|
| TP-Link Archer T3U（`2357:012d`） | 外置 USB | `rtw88_8822bu` | 可靠；参考适配器 |
| ALFA AWUS036ACHM | 外置 USB | `mt76x0u` | 可靠 |
| Realtek RTL8821CE | 内置 PCIe | `rtw88_8821ce` | 可靠 |
| AMD RZ616 | 内置 M.2 | `mt7921e` | 速度约为一半，有时在退出前死锁 |
| MT7601U | 外置 USB | `mt7601u` | 原版驱动没有 AP 模式；需要固定版本的 `mt7601u-ap` DKMS 模块（[树莓派主机](hardware_raspberry_pi.md)） |
| Intel AX200 | 内置 M.2 | `iwlwifi` | 失败：无法分配 IP |
| Atheros AR9271 | 外置 USB | `ath9k_htc` | 失败：通常无法分配 IP |

## 主机模式

`--skip-encryption` 会跳过 LDN 的 Python CCMP 步骤，让 mac80211 或硬件只应用一次 CCMP；流量在空中仍保持加密。Archer T3U（`config/host.toml` 中的 `skip_encryption = true`）和 ALFA AWUS036ACHM 都需要它。

`--accept-decrypted-ccmp` 面向这样的监听模式驱动：它们在硬件解密后的明文周围保留 CCMP 头与 MIC，Archer T3U 的 `rtw88_8822bu` 便是如此；它会在把明文转发给 `ldn-tap` 之前剥掉 MIC。ALFA 请保持关闭，因为它交付的是标准帧。

| 适配器 | 主机配置 |
|---|---|
| TP-Link Archer T3U | 仓库跟踪的 `config/host.toml` 配置档；不加任何 Wi-Fi 标志 |
| ALFA AWUS036ACHM | `--phy phyN --skip-encryption --no-accept-decrypted-ccmp` |

`phy = "auto"` 只会解析单个 `rtw88_8822bu` USB `2357:012d` 设备，若没有或有多个则失败。显式的 `--phy phyN` 始终优先；请仅在一次性调试时使用，因为每次重新枚举后编号都会改变。启动时会打印检测到的配置档、发送与接收模式，以及标志与已验证配置档不一致时的警告。

## TP-Link Archer T3U

`rtw88_8822bu` 自内核 6.11 起进入主线，并列出该 USB id。确认内核已将其绑定：

```bash
modinfo rtw88_8822bu | grep -i 2357
lsusb | grep -i 2357
iw dev
```

### 让 NetworkManager 不要接管适配器本身

NetworkManager 会占用适配器热插拔产生的接口（`wlx...`）并启动一次后台扫描；信道切换会在接口出现后不久让射频停止工作（实测 11 秒）：

```text
rtw88_8822bu 3-1:1.0: write register 0x81c failed with -71
usb 3-1: USB disconnect, device number 2
```

将适配器与 LDN 接口排除在外：

```text
# /etc/NetworkManager/conf.d/zz-ldn-unmanaged.conf
[keyfile]
unmanaged-devices=interface-name:ldnclient;interface-name:ldn;interface-name:ldn-mon;interface-name:ldn-tap;interface-name:wlx*;interface-name:wlan*
```

该文件必须排在最后（`zz-`）：某些发行版会附带一个更靠后的文件，其中设置 `unmanaged-devices=none`。重新加载 NetworkManager；`nmcli device status` 必须把该适配器显示为 `unmanaged`，`NetworkManager --print-config | grep unmanaged` 则必须显示该列表。若其中没有 `ldnclient`，NetworkManager 会抢占加入操作创建的接口，把 wpa_supplicant 指向它，加入便以 `[Errno 114] Match already configured` 失败。

### 禁用驱动的 USB 3 模式切换

`rtw88_usb` 默认为 `switch_usb_mode=Y`，这会在驱动加载后把适配器重新枚举为 USB 3 模式。直通该设备的虚拟机管理程序会看到一次断开，LDN 接口随之消失，主机在主持初期就崩溃（实测约 1 秒），且之前没有任何驱动错误：

```text
RuntimeError: 802.11 beacon injector stopped: [Errno 100] Network is down
```

该参数自身的说明指出，USB 3 模式可能干扰 2.4 GHz，也就是 LDN 使用的频段。

```text
# /etc/modprobe.d/rtw88-ldn.conf
options rtw88_usb switch_usb_mode=N
options rtw88_core disable_lps_deep=Y
```

之后重新插拔适配器：在断电之前它会一直停留在 USB 3 模式。此后它只会挂载一次，且为高速模式（开关开启时会枚举两次，先高速、后 SuperSpeed）：

```bash
cat /sys/bus/usb/devices/*/speed     # 480, not 5000
cat /sys/bus/usb/devices/*/version   # 2.10, not 3.00
```

### 运行前先将适配器接口关闭

处于 up 状态的受管接口会占住射频的信道。`transport.free_radio()` 会将其关闭；直接运行 `tools/ldn/ldn_scan.py` 则不会：

```text
OSError: [Errno 16] Device or resource busy
```

```bash
sudo ip link set wlxXXXXXXXXXXXX down
```

若有终止脚本把基础接口重新启用，下一次启动就会以该错误失败。任何为了让内核 `iw scan` 而启用接口的操作，都必须在交接前再次将其关闭。

### 验证

`./scripts/preflight_pi.sh` 可在任意 Linux 主机上运行。
