---
title: 控制器开发板
parent: Hardware and setup
nav_order: 5
---

# 控制器开发板

控制器开发板是一块 ESP32-S3，Switch 会在其 USB-C 端口上把它识别为有线手柄；或者是一块经典 ESP32，通过蓝牙经典以 Pro Controller 的身份与其配对。主机按下游戏机的按键，并加载由板子按自身时钟播放的宏。固件 `firmware/pad`，主机侧 `pokeldn.pad`，应用页面 [控制器](gui.md#the-controller)，命令行 `tools/switch/pad.py`。

## 哪些开发板

| 芯片 | 手柄形态 | 原因 |
|---|---|---|
| ESP32-S3 | 有线，通过 USB | 其 USB-OTG 模块可以呈现为任意 USB 设备 |
| 经典 ESP32 | 无线 Pro Controller，蓝牙经典；主机接在其 USB 转串口上 | 自身没有 USB 设备功能；它有蓝牙经典，也就是 Pro Controller 的传输方式 |
| ESP32-C3、ESP32-C6 | 无 | USB Serial/JTAG 是固定功能，且它们的蓝牙仅支持 LE |

## USB 一侧

板子会枚举为一个 HORI Pokken 手柄，`0f0d:0092`，包含一个 HID 接口，带一个中断 IN 和一个中断 OUT 端点。Switch 会把该 ID 当作普通 HID 手柄接受，无需 Pro Controller 握手；一台固件为 23.0.1 的零售版 Switch Lite 无需改动任何设置，即可从 HOME 菜单接受它。

输入报告为 8 字节，在主机准备好接收时每毫秒发送一次：

| 偏移 | 大小 | 字段 |
|---|---|---|
| 0 | 2 | 按键，小端序 |
| 2 | 1 | hat：0 为上，顺时针依次到 7 为左上；8 为居中 |
| 3 | 4 | LX、LY、RX、RY；128 为居中，0 为左或上 |
| 7 | 1 | 厂商字节；固件把蓝牙状态放在这里 |

| 位 | 按键 | 位 | 按键 |
|---|---|---|---|
| 0x0001 | Y | 0x0100 | Minus |
| 0x0002 | B | 0x0200 | Plus |
| 0x0004 | A | 0x0400 | 左摇杆按下 |
| 0x0008 | X | 0x0800 | 右摇杆按下 |
| 0x0010 | L | 0x1000 | HOME |
| 0x0020 | R | 0x2000 | Capture |
| 0x0040 | ZL | | |
| 0x0080 | ZR | | |

厂商字节：1 表示已同步，2 表示广播中，3 表示已连接；该步骤失败时为 `0x80 | step`。

## 接线

用一根 USB-C 转 USB-C 线把板子接到游戏机。游戏机既是电源也是 USB 主机；板子从它取电。当主机已完成该设备的配置时，XIAO ESP32S3 的 LED（GPIO21）会亮起。

把 Switch Lite 接到 Mac 的 USB-A 端口，并打开“通过 USB 连接复制到电脑”，它会枚举为 `057e:201d`：一个 MTP 接口、一个只读的“相册”存储、十项只读操作（`0x1001`-`0x100a`）。

## 蓝牙一侧

板子以 `POKELDN-PAD` 广播，包含一个服务 `7a1e0001-5d2c-4c3e-9f4b-504f4b454c44`：

| 特征 | 访问方式 | 内容 |
|---|---|---|
| `...0002` | 写、无响应写 | 8 字节输入报告，原样发送；播放宏期间被忽略 |
| `...0003` | 读 | 状态，见下文 |
| `...0004` | 写 | 命令，见下文 |

状态（小端序）：mounted u8、report writes u32、playing u8、loops done u32、entry index u16、entry count u16、以文本表示的固件版本，然后是 NUL、复位原因 u8（`esp_reset_reason`）、上一次启动到达的阶段 u8，以及自加电以来的启动次数 u16。1.0.0 之前的固件只发送前五个字节。

| 命令 | 载荷 | 作用 |
|---|---|---|
| `0x10` load | count u16、loop start u16、loops u32 | 停止当前宏并设定程序大小；loops 为 0 时一直播放到被停止 |
| `0x11` data | first entry u16，随后是各个条目 | 每个条目是一个报告加一个以毫秒计的 hold u16，共 10 字节 |
| `0x12` play | | 启动程序 |
| `0x13` stop | | 停止它并释放所有按键 |
| `0xB0` download | | 重启芯片进入 ROM 加载器 |

程序可容纳 8192 个条目。循环起点之前的条目播放一次；其余条目重复播放。播放器在 1 kHz 时基上以 `vTaskDelayUntil` 等待，因此各段保持时长会累加而不会漂移。

陷阱：在 macOS 上通过 bleak 发出的无响应写，会在 CoreBluetooth 队列满时丢失，而 bleak 从不读取 `canSendWriteWithoutResponse`（300 个连续报告中只有 67 个到达）。`pokeldn.pad.link` 在每次写报告前等待该标志（每报告 2.4 毫秒，无一丢失），而在该标志不存在或持续一秒为 false 的情况下改用有响应写，每次 60 毫秒。

断开连接会把报告恢复为中立状态，因此消失的主机不会留下被按住的按键；正在播放的宏会继续播放。

## 串口一侧

经典 ESP32 一直留在电脑的 USB 上：UART0 以 921600 波特双向承载帧（`firmware/pad/main/uart_link.c`、`pokeldn/pad/serial_link.py`），且控制台输出已关闭。控制台关闭时，没有任何东西把 UART0 路由到 GPIO1 和 GPIO3，因此固件会自行设置引脚；若没有这一步，板子不会有任何回应。

    A5 5A | length u16 (type and payload) | type u8 | payload | sum of type and payload mod 256

| 类型 | 方向 | 载荷 |
|---|---|---|
| `0x01` | 发往板子 | 8 字节报告；由 `0x81` 应答 |
| `0x02` | 发往板子 | 无；由 `0x82` 携带状态记录应答 |
| `0x03` | 发往板子 | 一条命令，与控制特征上的相同；由 `0x81` 应答 |
| `0x81` | 发往主机 | 结果 i8：0，-1 长度错误，-2 被拒绝 |
| `0x82` | 发往主机 | 状态记录；mounted 表示 Switch 已设置玩家指示灯 |

主机以 DTR 和 RTS 为低电平打开端口。在 macOS 上，DevKit 的 CP2102 仍会在端口打开时重启板子，启动期间发出的请求会丢失；主机会把状态请求重发最多 3 秒。服务会先逐个尝试非 S3 原生 USB 的 USB 串口，然后再扫描蓝牙 LE。请只用一个进程占用该端口：每次重新打开都会重启板子并断开其蓝牙链路。

## 蓝牙经典一侧

`firmware/pad/main/bt_esp32.c` 注册一个 Bluedroid HID 设备：170 字节的 Pro Controller 报告描述符，服务名 “Wireless Gamepad”，厂商 “Nintendo”，子类 0x08，设备类别 0x002508，名称 “Pro Controller”，SSP 无输入也无输出，关闭 modem sleep。它按 ID 应答 0x01 子命令：0x02 设备信息（固件 4.00、类型 0x03、其蓝牙地址）、0x10 SPI 读取、0x03 报告模式、0x04 触发时间、0x21 MCU 配置，其余返回普通 ACK；0x30（玩家指示灯）会把该手柄标记为已被占用。任何 0x30 之前都会先发出一个应答。

0x30 报告在按键或摇杆变化时立即发出，否则每 100 毫秒发出一次，从链路打开的那一刻起就是这样；板子不发，Switch 就不会开始握手。板子在链路打开后等待 1 秒，状态变化后 250 毫秒进入 sniff 模式，在一次发送因拥塞（原因 8）被拒后等待 45 毫秒：这些是 friendmaker 的 Switch Lite 取值（`classic_bt_controller_transport.cpp`、`SWITCH_LITE`）。陷阱：每 15 毫秒发一次 0x30 会拥塞链路，Switch 会在玩家指示灯亮起后 20 秒内断开（HCI 0x13）。

Switch 的握手顺序为：0x02、0x08，在 0x6000 和 0x6050 处 0x10，0x03（0x30），0x04，在 0x6080、0x6098、0x8010、0x603D、0x6020 处 0x10，0x40，0x30（0），0x48，0x21，0x30（玩家 1）。

配对过的板子会在启动时重连其 Switch。刷写合并镜像会覆写 NVS 分区，配对信息也随之丢失：请从“更改握法/顺序”重新配对。

`pro_report.c` 把共享报告映射到 Pro Controller 的字节上（dekuNukem 的 `bluetooth_hid_notes.md`）：摇杆静止时为 0x800，任一方向满偏为 0x700，与它在 0x603D 处返回的出厂校准一致；序列号与用户校准为空白闪存（0xFF）。`tests/test_pad_pro.py` 会在主机上编译它，并检查每个按键位与校准。

## 宏

宏是一个扩展名为 `.pokemacro` 的 JSON 文件（`pokeldn.pad.macro`）：

```json
{
  "format": "pokeldn-macro", "version": 1,
  "name": "Soft reset", "description": "", "author": "", "game": "",
  "press_ms": 100, "gap_ms": 150,
  "setup": [{"press": "HOME"}, {"wait": 1000}],
  "loop": [
    {"press": ["A", "B"], "ms": 500, "after": 2000, "note": "skip the intro"},
    {"repeat": 3, "steps": [{"press": "A"}]},
    {"press": [], "left": [0, 1], "ms": 300},
    {"wait": 5000}
  ],
  "loops": 0
}
```

| 字段 | 含义 |
|---|---|
| `press_ms`、`gap_ms` | 步骤未另行指定时，一个步骤保持其输入多久，以及其后的停顿 |
| `setup` | 只运行一次的步骤 |
| `loop` | 重复 `loops` 次的步骤；为 0 时一直重复到被停止 |
| 按下步骤 | `press`：一个按键名，或同时按住的按键列表（`A B X Y L R ZL ZR PLUS MINUS LSTICK RSTICK HOME CAPTURE UP DOWN LEFT RIGHT UPLEFT UPRIGHT DOWNLEFT DOWNRIGHT`）；`left` 和 `right`：摇杆 `[x, y]`，取值 -1 到 1，向上为正；`ms` 保持时长；`after` 停顿；`note` |
| 等待步骤 | `wait`：毫秒数，期间释放所有按键 |
| 重复步骤 | `repeat`：对 `steps` 重复 1 到 10000 次，最多嵌套 8 层 |

编译器会展开重复、合并持有相同报告的相邻条目，并把超过 65535 毫秒的保持时长拆分。展开后超过 8192 个条目的宏会被拒绝。两个相同按下之间若为 `after: 0`，会合并为一次保持。若文件的 `version` 比读取器的新，会被拒绝。

## 主机一侧

`pokeldn.pad.service` 持有蓝牙链路，并在 `127.0.0.1:47800` 上每行接收一个 JSON 请求：`status`、`connect`、`send`、`tap`、`play`、`stop`、`download`、`scan`、`disconnect`。应用会把它作为自己的子进程启动；若没有在运行，`tools/switch/pad.py` 会在独立进程中启动它。

在 macOS 上，当板子在链路仍打开时断电（从 Switch 上拔下），CoreBluetooth 可能让一次读或写一直挂起而不报错。服务会在时限内应答每个请求（`status` 5 秒，`play` 120 秒，`scan` 20 秒，其余 40 秒，连接也包括在内）。超过时限后，服务会关闭链路，让板子重新广播，并回复一个错误。应用侧客户端会在 150 秒后停止等待。

    ./.venv/bin/python tools/switch/pad.py A
    ./.venv/bin/python tools/switch/pad.py HOME wait:1 'RIGHT*3' A
    ./.venv/bin/python tools/switch/pad.py hold:B:2 stick:L:-1:0:0.5
    ./.venv/bin/python tools/switch/pad.py --play soft_reset.pokemacro
    ./.venv/bin/python tools/switch/pad.py --stop --status

当负责的应用没有声明 `NSBluetoothAlwaysUsageDescription` 时，macOS 会中止打开蓝牙的进程，这种情况会在终端嵌入其他应用时出现。`pad.py --make-app PATH` 会写出一个运行该服务的小应用；用 `open` 打开它一次并允许蓝牙，之后 `pad.py` 的调用和源码检出中的该应用都会使用它。

## 再次刷写

手柄板占用着 USB 端口，因此 esptool 无法将其复位进加载器。download 命令、开发板页面里的安装以及 `pad.py --download` 都通过蓝牙完成这件事；插板子时按住 BOOT 则无需固件即可做到。

| 陷阱 | 固件或主机的应对 |
|---|---|
| `RTC_CNTL_USB_CONF` 会在复位后保留；若停留在 USB-OTG，加载器为 `303a:0009`，esptool 只有一半概率能连上 | 停止 NimBLE 和 TinyUSB，把 PHY 交还 USB Serial/JTAG 并设置 `RTC_CNTL_FORCE_DOWNLOAD_BOOT`；此时加载器为 `303a:1001` |
| 在蓝牙和 USB 都启动时调用 `esp_restart()` 可能挂起 | 不以那种方式调用 |
| 在 macOS 上首次打开新的加载器端口读不到任何内容，且 esptool 会一直占住端口 | `gui/board.py` 等待 8 秒，然后在不复位的情况下连接 |
| 从强制加载器刷写之后，一次 USB 复位会仍停留在加载器 | `--after watchdog-reset` |

`python -m gui.board --kind pad|radio` 可把任一种固件刷到另一种上；`--from-loader` 用于刷写下载命令已放进加载器的板子。

陷阱：在 FreeRTOS 默认的 100 Hz 下，USB 循环的延迟为零个 tick，会让 NimBLE 饿死；固件按 1000 Hz 构建。

## 构建

    . scripts/esp_env.sh
    cd firmware/pad && idf.py -B BUILD_DIR -D SDKCONFIG=SDKCONFIG_PATH build

TinyUSB 来自组件管理器（`espressif/esp_tinyusb` 2.4.0）。发布版会在射频固件镜像旁构建 `pokeldn-pad-s3.bin`。

## 未解决

- Switch 2 是否会与经典 ESP32 固件配对，或会接受 HORI ID，尚无实测；只测过 Switch Lite。
