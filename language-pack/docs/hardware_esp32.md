---
title: ESP32 无线通信
parent: Hardware and setup
nav_order: 1
---

# ESP32 无线通信

通过 USB 串口连接的 ESP32 开发板就是射频模块。它运行 `firmware/esp32/`，承载 LDN 的厂商 Action 帧与以太网帧；通告加密、LDN 认证、IP 与 Pia 都留在主机上，[便携信标](#portable-beacon) 除外。`pokeldn.ldn.esp32_wlan` 为 LDN 库提供一个由开发板支撑的工厂，因此 `ldn.scan`、`ldn.connect` 和 `ldn.create_network` 无需改动即可运行，主机也不需要 Wi-Fi 驱动。

## 支持的开发板

| 芯片 | 主机连接方式 | 合并镜像 |
|---|---|---|
| 经典 ESP32（ESP32-D0WD、WROOM-32E） | 通过 USB 串口桥的 UART0 | `pokeldn-radio.bin` |
| ESP32-S3 | 原生 USB Serial/JTAG | `pokeldn-radio-s3.bin` |
| ESP32-C3 | 原生 USB Serial/JTAG | `pokeldn-radio-c3.bin` |
| ESP32-C6 | 原生 USB Serial/JTAG | `pokeldn-radio-c6.bin` |
| 经典 ESP32、ESP32-C6 | 蓝牙低功耗（iOS 应用），以及如上所述的 USB | `pokeldn-radio-ble.bin`、`pokeldn-radio-ble-c6.bin` |

所有目标都使用 2.4 GHz；不支持 ESP32-S2。若 S3、C3 或 C6 同时具备独立的 UART 与原生 USB 接口，必须使用原生接口（S3 GPIO19/20，C3 GPIO18/19）；通过 UART 接口时固件从不应答。当没有固件通过 USB 串口桥应答时，桌面应用会从 ROM 引导加载程序读取芯片（esptool `detect_chip`），并提示 S3、C3 或 C6 插错了接口。`303a:1001` 由多个芯片共用；烧录时用 esptool 检测芯片。

| 开发板 | 天线 | BOOT | 用户 LED | CPU、任务核心 | 空闲可用堆 | 原生 USB 上的 BENCH，macOS |
|---|---|---|---|---|---|---|
| XIAO ESP32C3 rev 0.4 | 随附外置天线，必需 | GPIO9 | 无（仅充电指示灯） | 160 MHz，核心 0 | 152656 | 880.1 KB/s |
| XIAO ESP32C6 rev 0.2（C6FH4，4 MB） | 陶瓷天线，由固件选择 | GPIO9 | 黄色，GPIO15，低电平点亮 | 160 MHz，核心 0 | 255196 | 824.6 KB/s |
| XIAO ESP32S3 rev 0.2（8 MB flash，8 MB PSRAM） | 随附外置天线，必需 | GPIO0 | 黄色，GPIO21，低电平点亮 | 240 MHz，核心 1 | 212416 | 883 KB/s |

BENCH 不会丢数据；主机的波特率设置不改变 USB 速度。较大的 S3 开发板（N8R2、N16R8）带板载天线。开发板指南：[XIAO ESP32C3](https://wiki.seeedstudio.com/XIAO_ESP32C3_Getting_Started/)、[XIAO ESP32C6](https://wiki.seeedstudio.com/xiao_esp32c6_getting_started/)。

XIAO ESP32C6 在 GPIO3 为低电平时为射频开关供电；GPIO14 为低电平则选择陶瓷天线。C6 固件在 Wi-Fi 启动前把这两个引脚都拉低；在 ESP32-C6-DevKitC-1 上这些引脚只引到排针，因此同一份镜像适用于所有 C6 开发板。C6 的站点模式被限制在 11b/g/n。其接收头中没有 `sig_mode`、`mcs` 或 `cwb`：固件从 `cur_bb_format` 推导 `sig_mode`，从 `he_siga1` 推导 HT MCS，其速率字节是 OFDM 帧的 L-SIG 速率码。

各开发板完成的交换见[按开发板统计的交换](#trades-by-board)。

### 复位后的 USB 链路（C6、S3）

打开端口会让 C6 或 S3 复位。在 ESP-IDF 默认的 `CONFIG_ESP_SYSTEM_BBPLL_RECALIB=y` 下，启动过程会停掉为 USB Serial/JTAG 提供时钟的 BBPLL（`recalib_bbpll()`，`esp_system/port/soc/esp32c6/clk.c`），链路可能一直错乱，直到拔掉开发板（SOF 帧号冻结，`USB_SERIAL_JTAG_INT_RAW` 为 `0000b5b2`，而正常时是 `0000b50a`）。C6 与 S3 的构建把它设为 `n`（在 v5.2+ 引导加载程序下允许；每个合并镜像都自带引导加载程序）：900 次 C6 打开与 300 次 S3 打开全部应答。C3 没有该选项，也没有此故障。

C6 与 S3 的构建带有 USB 看门狗（`usbwatch.c`）：SOF 帧号停滞 2 s 就重启芯片，下一次 HELLO 以 LOG 行携带 USB 与时钟寄存器。它在收到第一个 SOF 帧或从线缆读到第一个主机字节时启用，并且在蓝牙主机连接期间绝不重启：接在充电器上的开发板收不到 SOF 帧，而在固件 1.7.0 及之前，蓝牙主机的字节会启用它，因此接在充电器上的 C6 在 iPhone 应用下每 2 到 3 s 重启一次。以 `POKELDN_USB_BEACON=1` 构建时，两种镜像还会每秒把这些寄存器作为厂商 Action 帧广播到 `03:55:53:42:57:00`（布局见 `usbwatch.c`），USB 失效期间由 `esp32_sniff.py --mac 03:55:53:42:57:00` 保留。

## 角色

| 角色 | 开发板做什么 |
|---|---|
| 空闲 | 在单一信道上混杂模式监听；每个带任天堂 LDN 前缀 `7f 00 22 aa` 的 Action 帧都送往主机 |
| 站点 | 用主机推导出的 CCMP 密钥，按 BSSID 加入游戏机的网络 |
| 接入点 | 在主机 BSSID 上建立隐藏 SSID 的 WPA2 网络，密钥以同样方式派生 |

游戏机的网络没有四次握手：两端都从通告的服务器随机数推导 CCMP 密钥。固件替换 ESP-IDF 私有 `struct wpa_funcs` 表中的四个条目（`esp_wifi_driver.h`）。其布局是该 v6.1 blob 的 ABI；固件拒绝针对其他版本构建。

| 条目 | 替代实现 |
|---|---|
| `wpa_sta_connect` | 在原有回调外层安装 Switch 站点模式的 RSN 元素（CCMP、PSK、capabilities `0x000c`） |
| `wpa_sta_rx_eapol` | 丢弃 EAPOL；看到关联响应后通过 `esp_wifi_set_sta_key_internal` 装入密钥，再由 `esp_wifi_auth_done_internal` 打开端口 |
| `wpa_ap_join` | 添加站点并发送关联响应（`esp_send_assoc_resp`），不带 EAPOL-Key 消息 1（`AP_START` 标志位 0 保留原有加入流程）；主循环安装成对密钥（`esp_wifi_set_ap_key_internal(CCMP, mac, 0, key)`）并打开端口（`esp_wifi_wpa_ptk_init_done_internal(mac)`），顺序与 hostapd 的 `PTKINITDONE` 相同（`wpa_auth.c:2290-2332`）；组密钥在 `WIFI_EVENT_AP_START` 时以索引 1 装入 |

陷阱：绝不要等 `WIFI_EVENT_AP_STACONNECTED` 来安装密钥。只有 `esp_wifi_wpa_ptk_init_done_internal` 会发布该事件，因此在没有四次握手的情况下它永远不会到来，游戏机的第一个加密帧会被丢弃。

## 接入点的帧

softAP 的信标、探测响应与关联响应在闭源的 `libnet80211.a` 中构建（v6.1 `ieee80211_output.o` 偏移），此处将其与 `vendor/LDN` 的接入点所发送的内容作对比：

| 字段 | Switch 的形式 | ESP32 softAP | 可设置 |
|---|---|---|---|
| 隐藏 SSID 元素 | 32 个零字节 | 长度 0（`ieee80211_beacon_construct` 0xc4） | 否 |
| Supported Rates | `82 84 8B 96 0C 12 18 24` | `8B 96 82 84 0C 18 30 60` | 否；同样的十二个速率与基本位，9 与 18 在 Extended 中 |
| Extended Rates | `30 48 60 6C` | `6C 12 24 48` | 否 |
| capability，信标 | `0x0511` | `0x0431`（短前导常量，`ieee80211_getcapinfo` 0x7b） | 否 |
| HT 元素 | 无 | 在 11b/g/n 中存在 | 已移除：固件设为 11b/g |
| RSN capabilities | `0x000c` | hostapd 自己的 | 已设置：`wpa_ap_get_wpa_ie` 返回 Switch 的元素 |
| WMM | 无 | 在 11g 中存在 | 仅在 11b-only 时移除 |

隐藏的 softAP 只应答定向探测请求。不带已配置 SSID 的关联请求会被丢弃（0x9c6）。`esp_wifi_80211_tx` 拒绝关联响应（`ieee80211_raw_frame_sanity_check` 0xf9），而 blob 自身发送的信标无法停止。

## 串口协议

一个帧由 `COBS(type | payload | crc32-le(type | payload))` 加上 `0x00` 构成；CRC 为 CRC-32/ISO-HDLC（`zlib.crc32`）。经典 ESP32 以 115200 波特率启动；`BAUD` 切换两端，开发板在复位前保持该速率。在 S3 上，`BAUD` 会被确认，但不改变 USB 传输速率。`0x00` 之前的任何内容（包括 ROM 的启动文本）都无法通过校验并被丢弃。

| 类型 | 方向 | 载荷 |
|---|---|---|
| `0x01` HELLO | 主机 | 无；由 CREDIT 0 应答，随后是 INFO。主机先发送一个 `0x00` 以结束任何不完整的帧 |
| `0x02` BAUD | 主机 | u32 波特率；以旧速率返回 RESULT，UART 排空后切换（最多 3 s）；`open_serial` 以新速率重试第一个 HELLO |
| `0x03` CHANNEL | 主机 | u8 信道；仅空闲时有效 |
| `0x04` STA_JOIN | 主机 | u8 信道、6 字节 BSSID、32 字节 SSID（LDN SSID 的十六进制文本）、16 字节密钥、6 字节站点 MAC（零表示随机）；可选：u8 固定数据速率（AP_START 的第 3..5 位表）、u8 以 0.25 dBm 为单位的最大发射功率（`esp_wifi_set_max_tx_power`，8 到 84，驱动将其上限设为 61）、u8 标志：1 每帧前发 RTS，2 重试前不发 RTS（`esp_wifi_internal_set_rts`） |
| `0x05` STOP | 主机 | 无；返回空闲，清除密钥 |
| `0x06` AP_START | 主机 | u8 信道、6 字节 BSSID、32 字节 SSID、16 字节密钥、u8 最大站点数、u8 标志：1 使用原有的关联与四次握手，2 站点不使用 QoS，4 不复制每个站点数据帧的 40 字节，第 3..5 位为固定数据速率，`0x40` 每 1000 TU 发送一个信标，`0x80` 不进行混杂接收；可选第二个标志字节：1 关闭驱动的噪声底检查，2 其间隔为 250，4 在每个 40 字节副本头部记录接收时间，8 重试上限为 7 和 4，`0x10` 对其站点正常数据帧以外的每一帧启用 RX_CENSUS；随后可选一个以 0.25 dBm 为单位的最大发射功率 |
| `0x07` AP_KICK | 主机 | 6 字节 MAC、u16 原因；解除认证 |
| `0x08` ETH_TX | 主机 | 一个以太网帧，由驱动用站点密钥或组密钥加密。驱动队列满时每 1 ms 重试，最多 100 ms；发往已离开站点的帧以 `0x3015` 失败。站点的以太网源地址必须是 LINK 中的 MAC，否则该帧永远不会被确认 |
| `0x09` RAW_TX | 主机 | 不带 FCS 的 802.11 帧（`esp_wifi_80211_tx`）；通告 |
| `0x0A` SNIFF | 主机 | u8 信道、6 字节 MAC；发往或来自该地址的每个管理与数据帧，以及该信道上每个 Action 帧（一段 LDN 通告会为游戏机即将迁移到的网络设定密钥），完整地作为 RX_SNIFF 发送；MAC ff:ff:ff:ff:ff:ff 会把该信道上每一帧作为 RX_CENSUS 发送 |
| `0x0B` STATUS | 主机 | 无；由 STATUS 应答 |
| `0x0C` BENCH | 主机 | u32 字节数、u16 消息大小（8 到 1600）；返回 RESULT，随后以 UART 能承受的最快速度发送 BENCH 消息 |
| `0x0D` LED | 主机 | u8 图案、u8 峰值亮度、u16 周期 ms（0：图案的默认值）、u16 持续时间 ms（0：直到下一次 LED）；RESULT |
| `0x0E` DISPLAY | 主机 | 一条屏幕命令（[屏幕](#the-screen)）；无屏幕时 RESULT `0x105` |
| `0x0F` ALIVE | 主机 | 无，无回复；启用[主机看门狗](#the-host-watchdog)；仅发送给固件 1.4.0 及之后版本 |
| `0x10` BEACON | 主机 | u8 操作码：0 WRITE 向暂存缓冲区写入 u32 偏移与字节，1 COMMIT u16 长度（校验并保存暂存的镜像），2 ERASE，3 START，4 QUERY（由 BEACON 应答）；其余返回 RESULT。固件 1.8.0 及之后（[便携信标](#portable-beacon)） |
| `0x81` INFO | 开发板 | u8 协议版本（1）、6 字节站点 MAC、6 字节 AP MAC、u8 芯片修订、文本 |
| `0x82` RESULT | 开发板 | u8 命令、i32 `esp_err_t` |
| `0x83` LOG | 开发板 | 文本 |
| `0x84` RX_MGMT | 开发板 | u8 信道、i8 RSSI、不带 FCS 的帧：LDN Action 帧；托管期间还包括发往开发板 BSSID 的管理帧、发往它的数据帧前 40 字节，以及站点的无 DS 广播帧整体 |
| `0x85` RX_ETH | 开发板 | 驱动解密后的一个以太网帧 |
| `0x86` LINK | 开发板 | u8 是否已连接、u16 原因、6 字节 MAC；原因 `0xFFFF` 表示 15 s 内无关联，`0xFFFE` 表示密钥被拒绝 |
| `0x87` STA_JOINED | 开发板 | 6 字节 MAC、u8 AID、i8 密钥安装结果、u8 端口是否打开 |
| `0x88` STA_LEFT | 开发板 | 6 字节 MAC、u16 原因 |
| `0x89` STATUS | 开发板 | 文本计数器（见下文）；托管期间每 2 s 主动发送一次，主机写跟踪记录时每 5 s 轮询一次 |
| `0x8A` BENCH | 开发板 | u32 序号与载荷字节；最后一帧携带序号 `0xFFFFFFFF` 以及开发板花费的 u32 微秒数 |
| `0x8B` CREDIT | 开发板 | 自上次 HELLO 以来读取并处理的主机字节数，从分隔符之后的字节开始计数；在 HELLO 时、每 1024 字节、线路空闲时以及空闲期间每 100 ms 发送，优先于任何排队消息 |
| `0x8C` RX_SNIFF | 开发板 | u8 信道、i8 RSSI、u8 `sig_mode`（0 传统，1 HT）、u8 传统速率码（`wifi_phy_rate_t`）、u8 HT MCS（第 7 位表示 40 MHz）、不带 FCS 的帧；还包括该信道上每个 10 字节 ACK |
| `0x8D` TX_DONE | 开发板 | 驱动对某一帧（站点或接入点）的 TX-done：u32 开发板时间 µs、u32 完成该帧的 ETH_TX 之后经过的 µs（若无则为全 1）、u8 是否被对端射频确认、u8 接口、u16 长度、该帧的前 24 字节（其 802.11 头） |
| `0x8E` BUTTON | 开发板 | 一次 BOOT 按下，30 ms 去抖：u32 开发板时间 µs、u16 自启动以来的按下次数；主机打印 `BOOT button, mark N`，跟踪记录会保留它 |
| `0x8F` RX_CENSUS | 开发板 | 接收到的每一帧，包括 FCS 失败与控制帧：u32 接收时间 µs、i8 RSSI、i8 噪声底、u8 `rx_state`（0 表示正常）、u8 分组类型（0 管理、1 控制、2 数据、3 其他）、u8 `sig_mode`、u8 速率码、u8 MCS（第 7 位表示 40 MHz）、u16 `sig_len`（含 FCS）、该帧的前 16 字节 |
| `0x90` BEACON | 开发板 | u8 是否已保存镜像、u8 是否正在运行、u8 分片数、u16 镜像长度、u32 镜像 CRC-32（整个镜像的 `zlib.crc32`） |

`rx_state` 98 表示双流 HT（MCS 8 到 15），单流的 ESP32 永远无法解码；65 表示任何其他调制方式下的损坏帧。

| STATUS 计数器 | 统计内容 |
|---|---|
| `tx_acked`、`tx_unacked` | 驱动的 TX-done 结果 |
| `tx_eth`、`tx_eth_failed`、`tx_eth_retried` | 已发送的 ETH_TX、失败的 ETH_TX，以及发现驱动队列已满的调用 |
| `tx_queued_max_us`、`_total_us`、`_n`、`_pending` | 从 ETH_TX 到 TX-done，基于匹配的 TX_DONE |
| `wire_dropped`、`wire_rx_bad` | 丢弃的开发板到主机消息；COBS 或 CRC 失败的主机命令 |
| `uart_fifo_ovf`、`uart_buffer_full`、`uart_overflow` | 128 字节硬件 FIFO 与 16 KB 环形缓冲区的溢出及其总和 |
| `uart_frame_err`、`uart_events_full` | 帧错误、校验错误与 break 事件；UART 事件队列满时的滴答（计数器可能偏低） |
| `read_max_us`、`write_max_us`、`handler_max_us`、`handler_max_type` | 最长的主机链路读取轮次（含 20 ms 超时）、写等待，以及命令及其类型 |
| `heap_min`、`queue_max`、`refused_heap`、`refused_queue` | 最小空闲堆、最深的发送队列、因堆下限与队列满而被拒绝的消息 |
| `tx_eth_max_us`、`tx_eth_total_us`、`tx_eth_slow` | `esp_wifi_internal_tx` 中的 ETH_TX，含重试：最长、总和、超过 5 ms 的次数 |

EtherType `0x88B7` 的帧是 LDN 认证；`esp32_wlan` 把它们转换为 LDN 库的 `CustomFrameEvent`。其他所有以太网帧都进入 L2 端口，由 `POKELDN_L2=tap|userspace` 选择：

| 端口 | 位置 | 启动器的套接字 |
|---|---|---|
| `userspace_ip` 栈 | 默认，所有平台 | `userspace_ip.udp_socket` 与 `packet_socket` |
| 以接口名命名的内核 TAP | Linux，仅 `POKELDN_L2=tap` | 内核套接字，`SO_BINDTODEVICE` 与 `AF_PACKET` 不变 |
| `MemoryPort` | 测试 | 无 |

创建 TAP 需要 `CAP_NET_ADMIN`。

### 主机看门狗

主机每秒向固件 1.4.0 及之后版本发送 ALIVE（`esp32.ALIVE_EVERY`）。HELLO 之后的第一个 ALIVE 会启用看门狗；HELLO 会将其关闭，因此从不发送 ALIVE 的主机永远不会被监视。启用后，处于非空闲状态的开发板若 5 s（`HOST_SILENT_US`）内没有读到主机命令，就会执行 STOP 的清理流程：接入点停止发送信标，其站点被断开，站点模式则断开连接。随后它丢弃所有发往主机的消息且不计数，直到主机再次发送命令；否则每条排队消息都要付出一次 500 ms 写入、一个 `wire_dropped` 以及 LED 上持续 `flash3` 的代价。若在火红交换房间期间杀掉主机，游戏机会显示 2318-0006，之后 JOIN 搜索也列不出任何主机。

### 待机

从固件 1.10.0 起，处于空闲状态且 30 s（`STANDBY_AFTER_US`）内未读到主机消息的开发板会调用 `esp_wifi_stop`。空闲时接收器本来是不间断运行的，处于混杂模式且关闭省电。任何类型的第一个主机消息都会在处理前触发 `esp_wifi_start`：在经典 ESP32 上，静默 36 s 后的第一个 HELLO 耗时 8.2 ms，而唤醒状态下为 1.6 ms；随后射频在 3 s 的普查中每个信道听到 81 到 315 个帧。运行中的主机每秒发送 ALIVE，因此开发板在主机运行期间从不休眠；已保存的信标与正在托管的网络属于非空闲状态，会保持运行。CPU 时钟不变。LED 以峰值 12、8 s 的呼吸代替峰值 50、4 s。待机电流尚未测量。

## 便携信标

从固件 1.8.0 起，开发板在 NVS 中保存一个 LDN 通告周期，并在没有主机的情况下发送它。若已保存镜像，且上电后 3 s 内没有主机命令，它就会启动镜像中的接入点，重放最多四条屏幕命令，并每隔 `interval_ms`（100）发送一次通告，每隔 `dwell_ms`（500）切换到下一个分片。HELLO、CHANNEL、SNIFF、STA_JOIN、STOP 和 AP_START 会结束它；被看门狗判定为已消失的主机会让它继续运行。`pokeldn.ldn.portable` 依据 `ldn.create_network` 会创建的网络来构建镜像；`bin/swsh_gift_host.py --save-to-board` 保存一份剑／盾神秘礼物（[剑／盾神秘礼物](swsh_gift.md)）。

开发板像主机那样构建每个帧（`firmware/esp32/main/advert.c`，PSA SHA-256、AES-CTR 与 AES-GCM）：存储的头部、分片的载荷，以及一个在每次启动时从随机值开始、每个分片递增 1 的 nonce，与主机上 `set_application_data` 提升它的方式相同。`tests/test_esp32_beacon.py` 编译 `advert.c`，并对协议 1 与 3 逐字节比较其帧与 LDN 库的帧。

| 偏移 | 大小 | 字段（小端） |
|---|---|---|
| 0 | 4 | `PKSA` |
| 4 | 1 | 布局，1 |
| 5 | 1 | 类型，1（一个通告周期） |
| 6 | 2 | 镜像长度，含 CRC |
| 8 | 1 | 信道 |
| 9 | 6 | BSSID |
| 15 | 32 | SSID，如 AP_START 所接收 |
| 47 | 16 | 数据密钥 |
| 63 | 1 | 最大站点数 |
| 64 | 16 | 通告密钥 |
| 80 | 40 | 通告头：网络 ID、版本、格式、u16 BE 大小、u32 BE nonce |
| 120 | 2 | `interval_ms`，20 到 1000 |
| 122 | 2 | `dwell_ms`，至少为 `interval_ms` |
| 124 | 1 | 分片数，1 到 8 |
| 125 | 1 | 屏幕命令数，0 到 4 |
| 126 | 2 | 零 |
| 128 | | 每个分片：u16 长度与通告明文；每条屏幕命令：u16 长度与一个 DISPLAY 载荷 |
| 末尾 | 4 | 之前所有内容的 `zlib.crc32` |

镜像中保存的是为其唯一网络派生的通告密钥与数据密钥，绝不包含 `prod.keys`。一个镜像最多 12288 字节。一台运行固件 1.9.1 的 XIAO ESP32S3 在上电后独立运行，向一台零售版剑成功派送了一只剑的神秘礼物宝可梦。从固件 1.9.1 起，存储的镜像在开发板应答第一条命令之前就从 NVS 读取；1.9.0 对端口打开后立即发送的 BEACON QUERY 回答“未存储”。留在电脑 USB 上且未打开任何应用的开发板，会像接在充电器上一样启动信标。

### 主机镜像

从固件 1.9.0 起，类型 2 的镜像让开发板自行应答每台游戏机的加入请求，并执行 `bin/frlg_mg_host.py` 所执行的会话，因此火红或叶绿仅凭开发板就能收到神秘礼物。`bin/frlg_mg_host.py --save-to-board`（应用中的“保留在开发板上”）会保存一份；`pokeldn.frlg.gift.portable` 通过构造启动器会运行的主机应用，并保留该主机在游戏机加入之前计算出的内容来构建它。一张神秘卡片、神秘新闻、印章拉力赛的一枚印章、一位访客训练家与一段神秘事件脚本占 2 到 4 KB；缓冲区脚本以及存档备份或恢复在电脑上读取其应答，因此会被拒绝。

类型 2 没有分片（第 124 字节为 0），且只有 AES-GCM 头。屏幕命令之后直到 CRC 是若干记录，每条为 u8 标签、u16 长度与字节（`firmware/esp32/main/gift.h`）：

| 标签 | 记录 | 写入者 |
|---|---|---|
| 1 | LDN：截至并包含主机的 48 字节站点条目的通告明文、认证头的网络 ID（小端）、用于解密认证密钥的 16 字节密钥、32 字节挑战密钥、u64 挑战值、u64 设备 ID、版本、平台 | `pokeldn.ldn.portable.ldn_record` |
| 2 | Pia：会话密钥 `AES(game key, SSID)`、u32 网络 ID、主机的 IPv4 地址、玩家 ID 与名称 | `portable.pia_record` |
| 16、17 | 游戏机 LinkPlayer 块之前与之后的应用数据 | `pokeldn.frlg.gift.portable` |
| 18 | 主机的 200 字节 LinkPlayer 块与 RFU 父 ID | |
| 19 | `MysteryGiftTiming` 的八个字段、标志（1 原生 nonce，2 先发加入响应，4 信任 Pia）、u32 协议滴答 µs | |
| 20 | 游戏家族（0 火红／叶绿，1 绿宝石）、预期的游戏机（0 任意） | |
| 21 | 编译为字节码的服务器脚本：每个 `SVR_LOAD_*` 变成一个槽位 | |
| 22 | 一份载荷：u8 标识、u16 大小（0 表示 1024 字节缓冲区）、字节；每条不同的消息一份 | |
| 23 | 一份提供的卡带：游戏代码（四个零表示任意）、卡片标志 ID、图标、印章字段、每个槽位一份载荷 | |

认证密钥为 `AES-ECB-decrypt(K, SHA-256(client random)[:16])`，其中 `K` 是 `KeyDerivation._derive_key` 针对来源 `f1e7018419a84f711da714c2cf919c9c` 的第三步，一个为 LDN 协议 3 派生的密钥。除最后一条外，每条屏幕命令都在启动时播放；最后一条是派送场景，在完成派送的会话之后播放，然后再播放启动的那些。

该引擎是纯 C 实现，逐行移植了每层一个 Python 模块：

| 文件 | 移植自 |
|---|---|
| `gift_ldn.c` | `ldn.APNetwork` 的认证与挑战应答、站点入座时的通告、`userspace_ip` 的 ARP 与 IPv4/UDP、`host_app.py` 的运行循环 |
| `gift_pia.c` | `crypto.PiaCrypto`、`reliable.parse_messages`、`pia_connect` 的 Net、Session 与 RTT 编解码器、`host_pia.HostPeerProtocol` |
| `gift_link.c` | `reliable.HostReliableSession`、`ni.py`、`rfu_leader.RFULeader`、`host_session.HostSession` |
| `gift_mg.c` | `host_mystery_gift.HostMysteryGiftEngine`、`block.BlockSender` 与 `RecvBlock`、`mg_link`、服务器脚本 |
| `gift_zstd.c` | zstd 1.5.7 的解码器（`vendor/zstd`） |

信标任务负责运行它：驱动的帧与关联通过队列到达它，它按自己返回的截止时间运行定时器，并每隔 `interval_ms` 重建通告，每次变化时 nonce 递增一次。站点的广播（首先是它发给主机的 ARP）以组密钥加密且不带 DS 位，接入点会丢弃它们：引擎从混杂模式回调中整体取走这些帧并自行解密，在 LDN 库的 nonce 与 AAD 上使用带 8 字节 MIC 的 AES-CCM，无论是否带 QoS（[站点的广播](ldn.md#a-stations-broadcasts)）。零售版 ESP32-S3 会在已安装的组密钥下把它们以已解密形式交给上层，保留 Protected 位、CCMP 头与 MIC（一个火红 ARP 为 76 字节）；从固件 1.9.1 起，若报文正文在 CCMP 头之后以 SNAP 头开始，就被视为明文，正如主机的 `accept_decrypted_ccmp` 所做的那样。固件 1.9.0 会丢弃它们，游戏机在认证后以通信错误退出。游戏机压缩了它的大部分数据报（在一次神秘卡片会话中为 1363 个中的 1056 个）；解码器上下文为 38,464 字节，外加 1 KB 字面量缓冲区。主机压缩的数据报以一个原始块的 zstd 帧发出。引擎状态约 41 KB，启动时与解码器一同从堆中取得。

开发板一次只接待一台游戏机，并以状态 1 拒绝另一台的认证。若某台游戏机的游戏代码没有任何卡带记录指定，或其游戏数据被脚本拒绝，它会被断开，且在游戏数据请求之后不发送任何内容。已入座的游戏机静默 60 s，或在 RFU 关闭后 30 s 仍处于入座状态，都会被断开。当该游戏机离开后，在它确认关闭并经过 2 s 稳定期，开发板会在同一网络与密钥上接待下一台。

`tests/test_esp32_gift.py` 编译引擎与 zstd，并在模拟开发板上针对代替游戏机的 `bin/frlg_mg_client.py` 运行它；该客户端像零售版火红那样用 ARP 解析主机，并以自己的 Session 类型 6 打开 Reliable 流；它的广播由 LDN 库加密且不带 DS 位到达开发板。一张神秘卡片、已持有的卡片、被拒绝的替换、一枚印章以及神秘新闻，每一种都以 `MysteryGiftServer` 为该游戏机发送的消息逐字节结束；第二台游戏机在第一台之后得到接待；镜像不提供的卡带会被拒绝。一台运行固件 1.9.1 的 XIAO ESP32S3 在无主机供电的情况下，向一台零售版法语火红派送了一张神秘卡片，并向持有该卡片的游戏机再次提供了它。

## 串口上限

经典 ESP32 的 UART 在 921600 波特率下从开发板到主机可承载 92.16 KB/s；Pia 载荷是密文，无法压缩。托管中的开发板还会为每个站点数据帧发送一份 48 字节的 RX_MGMT 副本，除非设置了 AP 标志 4（`POKELDN_ESP32_AP_FLAGS=4`）；附近每个 LDN 网络每秒大约增加十条通告。

发送队列容纳 384 条消息，并在空闲堆低于 64 KB 时拒绝消息；在游戏机以线路速率发送时，堆下限会先于队列填满而拒绝 RX_ETH。

### 波特率

`POKELDN_ESP32_BAUD` 设置 `open_serial` 切换到的速率，默认为 921600；上限由 USB 桥决定。在 macOS 上 ELEGOO 开发板的 CP2102 上，1500000 可无丢失地承载 149.1 KB/s，而 2000000 与 3000000 从不应答 HELLO。`tools/ldn/esp32_bench.py --port PORT --bauds LIST` 以每种速率流式发送 BENCH。

### 主机到开发板的命令丢失与 CREDIT

在游戏机的洪流下，开发板可能在处理器之前丢失主机命令。固件的各项对策，均与其缺席时作对比测量：

| 原因 | 固件的做法 |
|---|---|
| UART 中断在核心 0 上，与 Wi-Fi 任务同核 | 由读取任务在核心 1 上安装驱动 |
| 阻塞的 ETH_TX 让 16 KB 环形缓冲区与 128 字节 FIFO 溢出 | CREDIT 流控 |
| FIFO 在 120 字节时排空，1500000 下距满仅 53 µs | 阈值 32（`uart_set_rx_full_threshold`），640 µs |
| `uart_read_bytes`（IDF 6.1 `uart.c:1738`）对每个环形缓冲项都要等其超时 | 先等一个字节，再用 `uart_get_buffered_data_len` |
| `uart_write_bytes` 在 TX 环形缓冲区满时忙等，饿死读取者 | 写入者休眠直到帧能放下（`uart_get_tx_buffer_free_size`） |
| `UART_DATA` 事件填满承载溢出事件的 64 项队列 | 一个位于读取者之上的任务每 tick 排空它；`uart_events_full` |

一旦开发板发送了 CREDIT，主机的写入线程就把已写入但未上报的字节控制在 8 KB 以内（`esp32.FLOW_WINDOW`）；启动器的 trio 循环只负责排队，超过 512 个排队帧的 ETH_TX 与 RAW_TX 会被丢弃（`Radio.tx_dropped`）。窗口关闭期间若计数连续 0.3 s 未变，说明有字节丢失，主机会重新打开窗口（`Radio.flow_resyncs`）。绝不要仅因静默就重新同步：繁忙的读取者会阻塞最多 0.7 s，此时重新同步会让 16 KB 在途，对上 16 KB 的环形缓冲区。开发板每 1024 字节发放一次 credit（`wire.c` `CREDIT_STEP`），因此主机把 CREDIT 与已写入字节加上线路上的那个帧相对应。没有 CREDIT 的开发板会被无节流地写入。开发板会记录超过 50 ms 的命令（`slow command`）与超过 100 ms 的读取轮次（`reader held`）。

HELLO 会重启两个计数，因此主机会暂缓发送它直到没有在途内容，并保持窗口关闭直到收到开发板的 CREDIT 0（`tests/test_esp32.py::test_a_hello_mid_session_does_not_open_the_window`）。`tools/ldn/esp32_cmd_loss.py TRACE` 会对跟踪记录做核对：写入的 ETH_TX 对照 `tx_eth + tx_eth_failed`，自 HELLO 以来写入的字节对照最后一个 CREDIT。

### 发送时序

ETH_TX 在驱动中约花 0.1 ms，等待 TX-done 的中位数约为 1 ms。在洪流下，TX_DONE 到达主机最多迟 0.6 s。陷阱：嗅探开发板自身的线路会在一阵突发中积压，因此要按对端的确认来给送达计时；接入点的洪流以 1 Mbit/s 广播，每秒超过约 90 帧就会占满空口。

## 停顿与接收丢失

在火红交换中以开发板作为接入点时，一个帧通常约 1 ms 完成；偶尔会有一个游戏机尚未确认的帧停顿 100 到 260 ms，而其后的帧成串完成，同时开发板既听不到游戏机的数据也听不到它的 ACK。信道决定停顿：在与繁忙接入点共享的信道上，大多数交换都出现停顿，而在信道 11 上则没有。`config/host.local.toml` 接受 `[host] channel`；游戏机加入 1、6 或 11 信道上的主机。240 MHz 的 CPU 与固定速率（AP 标志第 3..5 位：1 到 7 分别对应 1、11、6、12、24、36、54 Mbit/s）都不能消除停顿。`tools/ldn/esp32_hold.py CAPTURE TRACE` 把每次等待拆分成阶段，`tools/ldn/esp32_hold_air.py` 列出嗅探器看到的内容，`tools/ldn/esp32_rx_copies.py` 把游戏机的重试与开发板的接收丢失对应起来。

### 两块开发板上的接收丢失

作为接入点时，开发板会丢失站点 OFDM 首传帧的 1% 到 22%；1 Mbit/s 的 DSSS 几乎从不丢失。`tools/ldn/esp32_pair_bench.py AP STA --flood 0 --burst N --send R` 会统计这些丢失。丢失集中在紧随开发板自身发送之后的帧上，例如其 6 Mbit/s CTS 之后 60 µs 的数据帧。在安静信道上更低（3 到 9 上为 0.8% 到 2.3%），在每个站点帧前都发 RTS（STA_JOIN 标志 1）以及站点满功率时也更低。

改变信标间隔、混杂接收、噪声底检查、接收缓冲区、CPU 时钟、IRAM 优化、接入点功率，或把 ESP-IDF 从 v6.1 换成 v5.5.5，都没有改变结果。大多数丢失在接入点不留下任何痕迹，甚至连 FCS 失败都没有。

站点在每次重试前都发 RTS（`lmacConfMib` +42，阈值在 +22；`esp_wifi_internal_get_rts`/`_set_rts`）。`lmacRetryTxFrame` 按 `lmacConfMib` 的上限重发（短帧 +21，长帧 +20，默认为 32；`esp_wifi_internal_set_retry_counter`）。ACK 与 CTS 速率表位于 `0x3ff73400`..`0x3ff7341c`。

## 用户态协议栈

`pokeldn.ldn.userspace_ip` 在主机进程内承载 IPv4、UDP 与 ARP。协议栈以接口名注册（加入方为 `ldnclient`，接入点为 `ldn-tap`）；对内核接口，`userspace_ip.lookup(name)` 返回 None，每个启动器正是以此选择路径。地址与邻居来自 LDN 库的 `add_address` 与 `add_neighbor` 以及收到的帧；没有邻居的单播目的地会先发 ARP 请求并丢弃该数据报；`.255` 走广播。超过 1472 字节的数据报会被分片，分片会被重组（5 s）。`udp_socket(port)` 与 `packet_socket()` 分别代替已绑定的 UDP 套接字与 `AF_PACKET` 套接字，各自由一个套接字对支撑，每个排队数据报占一个字节，因此 `select` 与 `trio.lowlevel.wait_readable` 在每个平台上都能工作。

陷阱：开发板的帧通过启动器自身 trio 循环中的 trio 任务到达协议栈。绝不要在该循环内的 `select` 中阻塞；应在 `trio.move_on_after` 下用 `trio.lowlevel.wait_readable` 等待。

## 开发板的 LED 与按键

LED 在经典 ESP32 上为 GPIO2，在 S3 上为反相的 GPIO21，在 C6 上为反相的 GPIO15；C3 固件不碰 LED 引脚。BOOT 在经典 ESP32 与 S3 上为 GPIO0，在 C3 与 C6 上为 GPIO9；每次按下都会发送 BUTTON（`0x8E`）、闪烁 LED 并唤醒屏幕。在 ELEGOO ESP-32 Type-C 开发板（CP2102、ESP32-D0WD-V3、无品牌 PCB 天线模块）上，红色 LED 是电源轨，蓝色 LED 是 GPIO2。GPIO2 与 GPIO0 是 strapping 引脚；固件只在启动之后驱动 GPIO2。

LED 以 LEDC PWM（13 位，5 kHz）每 10 ms 更新一次，gamma 2.2，交叉淡入淡出 150 ms。

| 图案 | id | 默认周期 | 形态 |
|---|---|---|---|
| auto | 0 | | 当前模式的外观，见下文 |
| off、on | 1、2 | | |
| breathe | 3 | 3000 ms | 升余弦 |
| blink | 4 | 1000 ms | 周期的一半时间亮 |
| flash3 | 5 | 1000 ms | 在周期前 60 % 内闪三次 |
| ramp-up、ramp-down、pulse | 6、7、8 | 1000、1000、1200 ms | 一次 |

自动外观：启动时一次脉冲，空闲时 4 s 的暗呼吸，[待机](#standby)时 8 s 的更暗呼吸，加入时 250 ms 闪烁，托管且无站点时更亮的 1.5 s 呼吸，已连接时保持微亮，嗅探时熄灭。

此外每个帧都会让 LED 闪烁。加入失败、密钥被拒、开发板到主机的消息被丢弃或主机命令丢失，都会播放 1.5 s 的 flash3。一次完成的交换或神秘礼物会渐亮到最亮（`pokeldn.ldn.show_done`）。`tools/ldn/esp32_led.py --port PORT PATTERN` 设置外观；`--demo` 逐一展示。

## 屏幕

I2C 上的 SSD1306 128x64 OLED 是可选的（SSD1315 与 SSD1309 模块也可用）。固件先探测 0x3C，再探测 0x3D，有屏幕时以 400 kHz 每 50 ms 绘制一帧。

| 目标 | SDA | SCL | 开发板引脚 |
|---|---|---|---|
| ESP32 | GPIO21 | GPIO22 | DevKit V1 D21、D22 |
| ESP32-S3 | GPIO8 | GPIO9 | |
| ESP32-C3 | GPIO6 | GPIO7 | XIAO D4、D5 |
| ESP32-C3 | GPIO5 | GPIO6 | 0.42 英寸 OLED 板自带的 72x40 屏，第二次探测 |
| ESP32-C6 | GPIO22 | GPIO23 | XIAO D4、D5 |

常见的四针模块自带稳压器与上拉电阻；其地址电阻选择 0x3C（丝印 0x78）或 0x3D（0x7A）。固件设置段重映射（`A1`）、反向 COM 扫描（`C8`）与替代 COM 引脚（`DA 12`）。ESP32-C3 0.42 英寸 OLED 板的 72x40 面板显示帧的第 30..101 列与第 24..63 行。

每个面板都运行相同的场景（`scene.c`）、相同的时序与相同的音效提示；只有布局数值不同。一个函数依据 `view_t` 绘制每个场景，该结构保存面板尺寸与各部分的位置。72x40 的视图更紧凑：一行 12 个字符的标题与半尺寸的精灵图。彩色面板（`panel_spi.c`）以整数倍缩放绘制 128x64 帧，亮点颜色为 `#47AEFA`，背景为 `#0B0B0D`（`screen.h` 的 `SCREEN_LIT_RGB`、`SCREEN_DARK_RGB`），与应用镜像使用的两种颜色相同。`tools/ldn/screen_preview.py OUT.gif [--panel 72x40]` 可离线渲染一段脚本化会话；`tests/test_screen_render.py` 在两种视图上逐帧、逐提示地校验应用的镜像（`pokeldn.app.screen_render`）与固件代码一致。

一个球在 900 ms 内左右左摇晃三次，如同正在被捕捉：搜索时每 3 s 一次，空闲场景中每 4 s 一次，以及收到的球落地时在打开前一次。

没有主机命令时，屏幕显示射频模块的状态：空闲、正在加入或正在托管，以及已连接，并显示各方向的帧计数。当射频模块活动或有动画播放时，以及最后一次 DISPLAY、HELLO 或 BOOT 按下之后的 60 s 内，屏幕保持全亮；随后它以对比度 1、预充电 `22`（`81 01 D9 22`）变暗，600 s 后关闭（`AE`）。更低的预充电会闪烁。彩色面板的背光以 LEDC PWM 5 kHz 运行：95 % 亮、12 % 变暗、0 关闭。空闲场景每 60 s 移动 2 像素以防烧屏。`tests/test_esp32_screen.py` 校验这些时序。

DISPLAY（`0x0E`）携带一个操作码：

| op | 布局 |
|---|---|
| `0` SHOW | u8 显示、u16 保持秒数（0：直到下一次显示）、标题、NUL、行、NUL；每段文本最多 21 个 ASCII 字符 |
| `1` SPRITE | u8 槽位（0 我方，1 对方，2 礼物）、u8 宽度 <= 64、u8 高度 <= 64、每行 `(width + 7) / 8` 字节、MSB 在前；宽度 0 清空该槽位 |
| `2` LOBBY | u8 星级（0..7，0：无）、u8 已加入、u8 座位（1..3，至少为已加入）、标题、NUL、名称、NUL、连接密码、NUL；启动大厅显示 |
| `3` JOINED | u8 已加入，最多为大厅的座位数；没有大厅显示时拒绝 |

| 显示 | id | 绘制内容 |
|---|---|---|
| auto | 0 | 射频模块的状态 |
| trade | 1 | 槽位 0 显示“提供中”与那一行文字 |
| traded | 2 | 槽位 0 随球离开（2.1 s），数据包往返直到保持时间，一个球落入（0.6 s）、摇晃（0.4 s）并打开（0.6 s），然后槽位 1 显示“已收到”10 s |
| gift | 3 | 一张放着槽位 2 的神秘卡片 |
| gifted | 4 | 卡片离开，然后显示“已派送！” |
| arrived | 5 | 仍在等待的 traded 显示此刻把它的球带入 |
| lobby | LOBBY | 槽位 0、标题、名称、星级、“已加入／座位”与密码 |

一个显示会等待正在播放的 traded 或 gifted 显示；当射频模块回到空闲时，显示结束。

`pokeldn.app.screen` 是启动器一侧：`offer`、`received`、`arrived`、`gift`、`delivered`、`lobby` 与 `joined` 立即返回，并在一个线程上按顺序执行。托管的团体战会显示大厅。每个启动器都在交换的最后一步调用 `received`，其保持时间为下表中的时间减去 2.5 s，这样球与游戏机的球同时打开：

| 标题 | 起自 | 游戏机上收到宝可梦 | 动画后的第一条消息 |
|---|---|---|---|
| 火红／叶绿 | START_TRADE | 22.7 s | READY_FINISH_TRADE（[火红连接](frlg_link.md)） |
| Let's Go | 步骤 `0e` | 15.3 s | 类型 4 载荷（[Let's Go 会话](lgpe_session.md#the-trade-animation)） |
| 剑／盾 | 最后一个 syncCommand 40 | 15.0 s | 无（[剑交换](swsh_trade.md#the-trade-animation)） |
| 晶灿钻石／明亮珍珠 | `tradeState` 5 | 18.6 s | 无（[BDSP 交换](bdsp_trade.md#the-completed-trade)） |
| 传说 阿尔宙斯 | `01 0e` | 28.5 s | 盒子消息 `00 02`（[传说 阿尔宙斯](pla.md#the-completed-trade)） |
| 朱／紫 | `8001010e` | 19.8 s | 无（[朱／紫](sv.md#the-trade)） |
| 传说 Z-A | 第四步 | 26.2 s | 下一个 `01 01` 预览（[传说 Z-A](za.md#a-trade-with-a-retail-console)） |

这些时间由人工标记（最多迟 2 s）。启动器在动画之后的那条消息处调用 `arrived`。精灵图使用 PokeAPI 的火红／叶绿版本，直到第 386 号物种，之后使用默认图；裁切、缩放至最大 64（卡片上为 40），并阈值化为 1 位，内部线条保持深色。`tools/ldn/esp32_screen.py --port PORT` 在开发板上播放一次交换与一次礼物；`tools/ldn/screen_preview.py OUT.gif` 离线渲染一段脚本化会话。

### 音效

`scene_sound()` 为每一帧开始的提示音命名；带扬声器的开发板会播放它，其他开发板忽略它。一个提示音会打断上一个。`sfx.c` 在开发板上合成每个音效：固定占空比的方波与噪声，原创序列。`tools/ldn/screen_preview.py --sounds DIR` 把每个提示音与整段会话写成 WAV 文件。

| 提示音 | 时机，显示开始后的毫秒数 | 声音 |
|---|---|---|
| linked | 一台游戏机入座（射频模块首次计入一帧的那一帧） | 两个上行音 |
| recall | traded，700 | 一个下滑音 |
| send | traded，1100；gifted，0 | 一个上滑音 |
| data | traded，从 2600 到 300 每 1000 一次，直到对方的到来 | 一声短促的哔声 |
| arrive | 对方的到来 | 一个下滑音 |
| wobble | 到来后 600 | 三声咔哒 |
| open | 到来后 1000 | 一声咔哒与一个上行音 |
| received | 到来后 1600 | 一段五音铃声 |
| delivered | gifted，900 | 一段三音铃声 |

### E32R40T 开发板

E32R40T（以 4.0 英寸 ESP32-32E 显示屏出售）是一块经典 ESP32，带一块 SPI 上的 480x320 ST7796S 面板。它的固件是单独的构建：在 `idf.py` 的环境中设置 `POKELDN_DISPLAY=E32R40T`；发布版本以 `pokeldn-radio-e32r40t.bin` 提供。

| 信号 | GPIO |
|---|---|
| CS、DC、SCK、MOSI | 15、2、14、13 |
| 背光，高电平点亮 | 27 |
| RGB LED，低电平点亮：红、绿、蓝 | 22、16、17 |

面板以 3 倍（384x192）在 40 MHz SPI 下显示 128x64 帧。GPIO2 是面板的 DC，因此开发板的 LED 是 GPIO17 上的蓝色那个。

### szpi 开发板

LCKFB szpi ESP32-S3 开发板（立创·实战派，小智的 `lichuang-dev` 开发板）是一块 ESP32-S3-WROOM-1 N16R8，带 2.0 英寸 320x240 ST7789 面板、驱动扬声器的 ES8311 编解码器、ES7210 麦克风 ADC、摄像头与 FT6336 触摸控制器。其固件是在 esp32s3 目标上设置 `POKELDN_DISPLAY=SZPI`；发布版本以 `pokeldn-radio-szpi.bin` 提供。麦克风、摄像头与触摸未被使用。引脚取自 xiaozhi-esp32 的开发板文件。

| 部件 | 引脚 |
|---|---|
| I2C，由扩展器与编解码器共用 | SDA GPIO1、SCL GPIO2 |
| 0x19 处的 PCA9557 扩展器 | 位 0 LCD CS（低：选中）、位 1 放大器（高：开）、位 2 摄像头断电（高：关） |
| SPI3 上的 ST7789，模式 2 | MOSI 40、SCLK 41、DC 39；MADCTL `60`，反色开启 |
| 背光，低电平点亮 | GPIO42 |
| 0x18 处的 ES8311，I2S | MCLK 38、BCLK 14、WS 13、DOUT 45 |
| BOOT | GPIO0 |
| WS2812 RGB LED | GPIO48 |

面板以 2 倍（256x128）显示 128x64 帧。开发板的 LED 是 WS2812，PWM LED 驱动无法驱动它；此构建没有 LED。编解码器以 16 kHz、16 位运行，MCLK 为来自 ESP32-S3 的 256 fs，作为 I2S 格式的从设备，0 dB；放大器在提示音播放时打开，在最后一个提示音之后 600 ms 关闭。

- 绝不要用恒定电平驱动背光：其升压转换器需要开关信号，否则一直黑屏。
- SPI 模式 0 会让面板全黑；它需要模式 2。

## 构建与烧录

固件版本（`firmware/esp32/version.txt`，`major.minor.patch`，所有目标共用）在 INFO 中以 `version=...` 报告；无版本号的构建显示 `version unknown`，只要其串口协议匹配就能工作。协议号是独立的，仅在线上协议约定变化时改变。

ESP-IDF v6.1（标签 `v6.1`，提交 `fff9895c82d744c7237be8847347bdd1b07c6643`）可构建全部四个目标。用 `install.sh esp32,esp32s3,esp32c3,esp32c6` 安装其工具，然后激活 IDF 环境（`. scripts/esp_env.sh`）。

    cd firmware/esp32
    idf.py set-target esp32   # esp32s3, esp32c3 or esp32c6 for those chips
    idf.py build
    idf.py -p <port> flash

控制台输出已关闭；在经典 ESP32 上，固件自行指定 UART0 的 GPIO1 与 GPIO3（`uart_set_pin`）。桌面应用用 esptool 检测芯片，并在写入前于芯片对应的 flash 偏移（ESP32 为 `0x1000`，其他为 `0x0`）校验合并镜像的引导加载程序：当镜像以填充开头时，esptool 5.4.0 的 `write_flash` 可能跳过芯片检查。绝不要根据 USB 桥的 ID 选择固件。
esptool 依据端口的 USB ID 选择复位方式，而 esp-pylib 1.1.5 拒绝对 `android://board` 这类 URL 端口做该查询；在没有 ID 时，它会给 ESP32-S3、C3 或 C6 使用经典的 DTR/RTS 复位，芯片永远不会进入 ROM 加载程序，日志显示 `Failed to get VID/PID`。Android 应用用开发板自身的 USB ID 回答该查询（`pokeldn/app/android.py`）。在 ID 已知时，Linux 或 Android 上的 CP210x 开发板会得到通过端口的 `fileno()` 上的 `ioctl` 同时写 DTR 与 RTS 的复位；Android 端口没有文件描述符，改为在一个 CDC 的 `SET_CONTROL_LINE_STATE` 中同时发送两条线。
[桌面构建](gui.md) 涵盖全部四个镜像的打包。

### stub 烧录器无法启动的开发板

有些经典 ESP32 开发板会响应 ROM 加载程序，但永远不启动 esptool 的 stub（`Failed to start stub flasher`）；其中一块把 eFuse 块 0 读成全零（`MAC: 00:00:00:00:00:00`，修订 v0.0）。它的 ROM 还会丢弃到 460800 的波特率切换，并在某些写入中途停止。出现该错误时，`gui.board.flash` 会重新连接，并以连接波特率用 `--no-stub` 写入，最多 `ROM_ATTEMPTS`（4）次连接：777 KB 的镜像约需 80 s。其他任何失败都会结束安装。

### 蓝牙

以 `POKELDN_BLE=1` 构建的固件还会通过蓝牙低功耗承载主机链路，供无法打开 USB 串口设备的 iOS 应用使用；此时开发板只需要 USB 供电。

    POKELDN_BLE=1 idf.py -B BUILD_DIR \
        -D SDKCONFIG=BUILD_DIR/sdkconfig \
        -D SDKCONFIG_DEFAULTS="sdkconfig.defaults;sdkconfig.defaults.ble" build

开发板只广播自己的名称 `POKELDN-RADIO`；iOS 应用扫描时不带服务过滤器。服务为 `7a1e0101-5d2c-4c3e-9f4b-504f4b454c44`：主机把 COBS 流写到 `...0102`（无响应写入），开发板在 `...0103` 上通知。当某个中心设备订阅了 `...0103` 时，线路就走那里，线缆静默。分帧、CRC 与 CREDIT 不变。HELLO 文本以 `link=ble` 结尾，开发板页面将其显示为蓝牙无线固件。`POKELDN_RADIO=esp32:ble`（或 `esp32:ble:NAME`）可从任意启动器打开它（`pokeldn/ldn/esp32_ble.py`，bleak）。

BLE 构建使用仅 BLE 的控制器、10 个静态 Wi-Fi 接收缓冲区与一个 10 KB 接收缓冲区，并释放经典蓝牙内存：双模控制器会让空闲堆低于线路要求的 64 KB 下限。通过 BLE 时开发板不发送 TX_DONE，并把排队的帧合并为一个通知。它请求 15 ms 间隔（中心设备订阅后再次请求；STATUS 中的 `ble_itvl_us`）、2M PHY、247 字节 MTU 与数据长度扩展；在 30 ms 下火红房间会慢得难以忍受。

经典 ESP32（蓝牙 4.2，无 2M PHY）测得 28.1 KB/s，能完成火红主机交换，但对火红加入方来说太慢（2318-0013）。XIAO ESP32C6 测得 33.6 KB/s，能完成火红加入方交换。每个射频构建都采用 ESP-IDF 的 single-app-large 分区表（0x10000 处一个 1500 KB 的 factory 应用；nvs 仍在 0x9000，phy_init 在 0xf000）；C6 BLE 镜像（0xfd000 字节）在其中留下 488 KB。

在 macOS 上，若负责的应用没有蓝牙授权，bleak 会在该进程中中止（SIGABRT）；以 `open -n -a Terminal FILE.command` 启动的脚本则在 Terminal 的授权下运行。

### USB 主机链路

S3、C3 与 C6 通过 USB Serial/JTAG 使用相同的 COBS、CRC 与 CREDIT 协议，环形缓冲区为 16 KB。写入者每 20 ms 重试一次被拒绝的 `usb_serial_jtag_write_bytes`，500 ms 后计入一条丢弃消息。接收中断在 RX 环形缓冲区满时丢弃一个 64 字节的数据包且不作任何计数（`usb_serial_jtag.c:144`）；CREDIT 防止环形缓冲区被填满。此路径上 UART 计数器保持为零，`POKELDN_ESP32_BAUD` 只改变经典 ESP32 的速率。在 USB 目标上，读取者以优先级 21 运行，高于写入者（20）：若读取者低于写入者，在满速流下写入者会饿死读取者。

主机设置 1 s 写入超时；写入失败或写入不足会以开发板丢失结束会话。HELLO 之后，1 s 内没有有效帧会排入一次 STATUS 探测，3 s 静默则以 USB 错误结束会话，并请用户重新插拔开发板。

一次两小时、无游戏机的主机到开发板浸泡测试（只有一个波特率值；原生 USB 会忽略它）：

```sh
./.venv/bin/python tools/ldn/esp32_bench.py --port COM5 --bauds 921600 \
    --soak 7200 --size 1400 --rate 460000
```

它每 5 s 打印帧数、字节数、credit 与 STATUS，并在 USB 失败或帧数不符时以非零码退出。它既不重现游戏机的确认，也不重现其 Wi-Fi 负载。

## 运行

`POKELDN_RADIO=esp32:<port>` 把每个启动器的 `ldn` 调用都放到开发板上。`esp32:auto` 采用唯一存在的 USB 串口，并在有多个时拒绝选择，因为打开端口可能让对应的开发板复位。端口在每个进程中只打开一次，DTR 与 RTS 均释放；macOS 上的 CP2102 开发板无论怎样都会在打开时复位。不复位的开发板会保留先前的 `BAUD`，因此主机会依次在 115200、`POKELDN_ESP32_BAUD`、921600 与 1500000 下尝试 HELLO，然后切换到请求的速率。
在 Windows 上 COM 端口以独占方式打开（`PermissionError(13, 'Access is denied.')`），因此启动器在重试前会关闭静默开发板的端口，而运行中拔掉开发板会以 `[esp32] The board disconnected from USB` 结束。使用 CP2102 时，仅拉高 RTS 就会把 EN 拉低，开发板保持静默。处于 ROM 下载模式的开发板从不应答 HELLO。

在开发板上，启动器跳过所有 nl80211 步骤（`--phy auto` 解析为 `esp32`），不需要 root，也不注入信标；加入方的 `--mac` 会成为开发板站点模式的地址。在 5 GHz 上托管游戏机的网络无法被访问。

`POKELDN_ESP32_TRACE=FILE` 追加每条串口消息，每条一行：Unix 时间、`>`（主机）或 `<`（开发板）、类型与十六进制载荷。

`tools/ldn/esp32_first_contact.py` 用于检查新开发板（`--flash` 写入构建，随后 HELLO、STATUS、一次统计各信道 LDN Action 帧的空闲扫描，带 `--keys` 时还会做解密扫描）；`tools/ldn/esp32_sniff.py` 把第二块开发板用作嗅探器；`tests/test_esp32.py` 在两块模拟开发板上运行 LDN 主机与站点（`pokeldn.ldn.esp32_sim`）。CH9102 或 CH343 桥枚举为 CDC ACM（`/dev/ttyACM0`、`/dev/cu.usbmodem*`）。

### 无法解码 OFDM 的开发板

游戏机的通告是 HT MCS 3（[发现](ldn.md#discovery)），因此无法解调 OFDM 的开发板听不到任何通告：`esp32_first_contact.py` 在每个信道上统计到的 LDN Action 帧都是 0，而关联与 ping 在 DSSS 下仍然正常。放在繁忙接入点旁的 `tools/ldn/esp32_census.py` 可区分两者：正常开发板会列出 `OFDM` 与 `HT` 好帧，而无法解码的那块只列出 `DSSS`，OFDM 帧以 `rx_state` 65 失败。一块通用 ESP32-WROOM-32 DevKit（ESP32-D0WD-V3 修订 3.1，CP2102）就是聋的；同款芯片的 WROOM-32E 开发板则正常（[issue 1](https://github.com/Decryptu/pokeldn/issues/1)）。

## 按开发板统计的交换

ELEGOO 开发板（ESP32-D0WD-V3 修订 3.1，CP2102，921600 波特率）在每一部作品中都能与零售版 Switch 2 游戏机交换，站点与接入点两种角色皆可，并能派送火红与剑的神秘礼物。XIAO ESP32C3、ESP32C6（陶瓷天线）与 ESP32S3 在两种角色下都能完成火红交换与剑的主机交换，C6 还能完成朱的主机交换；Windows 上的 ESP32-S3 能完成火红加入方交换（[PR 2](https://github.com/Decryptu/pokeldn/pull/2)）。[Android 应用](../examples/android/README.md) 在把 Python 线程绑定到一个性能核心后，通过 XIAO ESP32C6 以每秒 51.1 个父槽位托管火红。

加入开发板接入点的火红游戏机接受其长度为零的隐藏 SSID、速率顺序、capability `0x0431` 与 WMM 元素，并发送一个关联请求：listen interval 10、SSID 为 32 个十六进制字符、速率 `02 04 0b 16 0c 12 18 24` 与 `30 48 60 6c`、功率能力 `00 14`、RSN capabilities `0x0000`、一个 WMM 信息元素、厂商元素 `00 22 aa 10 01 02`。它的首批广播需要固件转发（[站点的广播](ldn.md#a-stations-broadcasts)）。

### 加入

`STA_JOIN` 只做一次关联尝试：在该信道与 BSSID 上快速扫描，然后开放认证与关联；`LINK` 在 0.23 到 0.34 s 后建立。零售版剑的网络可能在通告仍能被听到时让一次尝试失败（`LINK` 断开，原因为 `0xc9` 或 `0x2`），而新的尝试随后就能关联，因此主机会最多发送三次 `STA_JOIN`（`pokeldn.ldn.esp32_wlan.JOIN_ATTEMPTS`）。尝试为何失败尚不清楚。最后一次被拒的尝试之后，主机会发送 `STOP`：此后扫描发出的 `CHANNEL` 会一直被拒绝，直到开发板回到空闲。

### 发射功率

`POKELDN_ESP32_TX_POWER` 以 dBm 为单位限制开发板的发射功率（2 到 20）；主机以 0.25 dBm 为单位把它作为 `STA_JOIN` 与 `AP_START` 的功率字节发送，桌面应用的设置页中“发射功率”一项也会设置它。从固件 1.9.3 起，站点的功率上限在关联之前设置；更早的镜像在 `LINK` 建立后才设置。爱好者论坛报告 ESP32-C3 Super Mini 开发板只有 8.5 dBm 时才能与接入点关联，这是这些开发板的天线缺陷；在 ESP32-C3 0.42 英寸 OLED 板上该效应尚未测量。

未选择功率时（设置、自动），由主机选择（`pokeldn.ldn.esp32_wlan.board_tx_power`）：

| 开发板 | 功率 |
|---|---|
| HELLO 应答中写明 `esp32c3` | 两种角色都用 8.5 dBm；Super Mini 与 XIAO ESP32C3 报告相同的芯片与 USB ID，因此所有 C3 都采用该值 |
| 其他任何情况 | 驱动的最大值；在 `JOIN_ATTEMPTS` 次加入被拒后，再以 8.5 dBm 发送一次 `STA_JOIN`，若关联成功则在本次运行余下时间保持 |

在设置中选“完整”（20 dBm）会在 C3 上恢复最大值。

### 射频测试

桌面应用开发板页面中的“测试射频”（`pokeldn.ldn.esp32_radio_test`）在无需运行游戏机、也无需第二块开发板的情况下检查开发板的两个方向：

| 阶段 | 开发板做什么 | 玩家读到什么 |
|---|---|---|
| 听，约 20 s | 在信道 1、6 和 11 上：3 s 空闲，此时 LDN 通告以 `RX_MGMT` 到达主机；然后 3 s 普查（`SNIFF` 到 `ff:ff:ff:ff:ff:ff`） | 每个信道的 Switch 发射机与 Wi-Fi 信标及其最佳 RSSI、帧数与损坏计数、噪声底中位数 |
| 被听到，60 s | 以交换所用的功率建立一个隐藏接入点（`AP_START`），并由它通过 `RAW_TX` 每 100 ms 发送一个开放的 `POKELDN-TEST` 信标 | 手机的 Wi-Fi 列表是否在开发板附近显示 `POKELDN-TEST` |

在本地游玩菜单中等待并托管的游戏机会作为其信道上的一个 Switch 出现。听到 Wi-Fi 但听不到 Switch，问题指向游戏机；什么都听不到，问题指向开发板的接收器。手机在开发板旁始终列不出 `POKELDN-TEST`，问题指向其发射器。Mac 的扫描只有在信标带有运行中的时间戳与 TIM 元素时才列出它，并在某些扫描中漏掉；只含 SSID、速率与信道的信标从未被列出。结果写入开发板页面的日志，“复制开发板详情”会包含该日志。

## 未解决

- XIAO ESP32C3 是否能在自动的 8.5 dBm 下完成交换尚未测量；它是在驱动的最大值下完成交换的（[发射功率](#transmit-power)）。
- softAP 会协商 WMM，而 Switch 主机不会；有无该协商交换都能完成（`POKELDN_ESP32_AP_FLAGS=2`、`AP_FLAG_NO_QOS`，清除站点的 QoS 标志）。
- 接入点接收路径中究竟是什么导致错过站点的 OFDM 首传帧，尚不清楚（[两块开发板上的接收丢失](#receive-misses-on-two-boards)）。
- ESP32-WROOM-32E 模块是否比 ELEGOO 开发板的无品牌模块丢帧更少尚未测量。有用户报告称较旧的 ESP32-WROOM-32 交换不可靠；一块 WROOM-32 DevKit 完全无法解码 OFDM（[无法解码 OFDM 的开发板](#a-board-that-decodes-no-ofdm)）。
- 一台加入开发板接入点的朱游戏机可能确认公告却不发送端口 2 加入（[朱／紫](sv.md#unresolved)）。
- szpi 构建尚未在开发板上测量：它已构建，其场景与音效可离线运行。开发板的 USB-C 是连到 ESP32-S3 自身的 USB（S3 构建使用的那条链路）还是桥接芯片，其公开文件中没有说明。
- E32R40T 构建的 PWM 背光及其两种新颜色尚未在该开发板上测量。
