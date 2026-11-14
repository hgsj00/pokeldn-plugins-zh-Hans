---
title: 命令行用法
---

# 命令行用法

本页列出各游戏作品的命令行入口。请在仓库根目录运行。源码工具需要 Python 3.11+、Switch 的 `prod.keys`（默认 `~/.switch/prod.keys`，或 `--keys PATH`），以及一块已刷好固件的 ESP32 开发板。参见[支持的开发板](hardware_esp32.md#supported-boards)和[构建与刷写](hardware_esp32.md#building-and-flashing)。

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
dotnet build -c Release services/pkhex
export POKELDN_RADIO=esp32:auto
python -m pokeldn --list
python -m pokeldn --radio esp32:auto swsh-host --offer-file offer.pk8
```

交换工具需要 .NET 10 SDK。PyPI 上的 `ldn` 包是另一个库。在 Windows 上请使用 `.venv\Scripts\Activate.ps1` 和 `$env:POKELDN_RADIO = "esp32:auto"`。`esp32:auto` 会选择唯一的 USB 串口；`esp32:PORT` 用于指定某个串口（[无线设置](hardware_esp32.md#running)）。每个入口都接受 `--help`。

## 火红／叶绿

在主机上解锁 Direct Corner，并准备至少两只 `.pk3` 队伍成员。

```bash
./.venv/bin/python bin/frlg_trade_join.py --live -o output.pk3 PARTY1.pk3 PARTY2.pk3   # join the Switch's trade
./.venv/bin/python bin/frlg_trade_host.py -o output.pk3 PARTY1.pk3 PARTY2.pk3          # host a Direct Corner trade
```

主机端送出 `PARTY2.pk3`，并把收到的内容写入 `output.pk3`。默认值来自 `config/host.toml`，然后是 `config/host.local.toml`；参数会覆盖两者（`--print-effective-config`）。在 `Hosting Direct Corner` 之后：Direct Corner → Join Group → pokeldn 的训练家 → 挑选并确认。`--trades N`（1 到 6）会送出 0 到 N-1 号槽位，每次交换用一个；最后一个之后选 CANCEL、YES。

| 参数 | 用途 |
|---|---|
| `--keys PATH` | `prod.keys` 的位置 |
| `--slot N` | 送出的队伍成员，从 0 开始计数 |
| `--capture FILE` | JSONL 诊断抓取 |
| `--config` / `--local-config` / `--no-local-config` | 替换或禁用某一层配置 |
| `--ot NAME`, `--version firered\|leafgreen`, `--id TID[:SID]` | 单次运行的训练家覆盖值（各为 0..65535；LinkPlayer ID 为 `(SID << 16) \| TID`） |
| `--verbose` | 逐包输出；仅在配合 `--replay` 时，会使实时连接卡住 |

[`pokeldn/config.py`](../pokeldn/config.py) 中的 `DEFAULT_TRAINER` 保存其余默认值。协议：[连接协议](frlg_link.md)。

### 联机房间

`--union-room` 会扮演中间的 NPC；主机约 10 秒后连接。一条连接只承载一次交换（`union_room.c:1744`）。`--board-type normal` 会在交换板上登记，`--union-room-chat` 配合 `--chat-message` / `--chat-file` 聊天，`--union-room-battle --battle-fight` 进行对战（两只 30 级或以下的非蛋宝可梦）。

```bash
./.venv/bin/python bin/frlg_trade_host.py --union-room --union-room-keepalive 120 PARTY1.pk3 PARTY2.pk3
```

### 神秘礼物

`bin/frlg_mg_host.py` 在神秘礼物 → 神秘卡片 → 朋友中发送神秘卡片和发放脚本。`--make-artifact` 会把发送的字节写成 `.ram.lst`。目录：[神秘礼物](frlg_gift.md)。

```bash
./.venv/bin/python -u bin/frlg_mg_host.py --gift beast-cutscene --flag-id 1005 --capture mystery-gift.jsonl
```

这只野兽会随最初的伙伴而定（妙蛙种子→水君、杰尼龟→炎帝、小火龙→雷公）。

### 神秘新闻

`--news` 提供神秘礼物 → 神秘新闻 → 朋友。主机只在新闻与已保存的内容不同时才会保留；`--news-id N` 会强制推送一条新的。

```bash
./.venv/bin/python -u bin/frlg_mg_host.py --news berry --news-id 7
```

### 存档备份与还原

“朋友”路径会把 128 KB 的存档复制成 `.sav`（约四分钟），或把存档写回去；未完成的还原会让存档保持原样（[详情](frlg_gift.md#save-backup-and-restore)）。

```bash
./.venv/bin/python -u bin/frlg_mg_host.py --live --save-backup backup.sav --save-resume-dir partial
./.venv/bin/python -u bin/frlg_mg_host.py --live --save-restore backup.sav
```

### 主机存档

`save-dump` 读取运行中的存档；`flash-patch` 改写一个扇区中指定的字节，并更新其校验和与计数器。写入前请先阅读[组装扇区](frlg_rom.md#composing-a-sector-from-a-ram-snapshot)。载荷：[主机上的代码](frlg_rom.md)。

```bash
./.venv/bin/python -u bin/frlg_mg_host.py --buffer-script save-dump --dump-block sav2 --dump-size 64 --dump-file dump.bin
./.venv/bin/python tools/frlg/dump_read.py dump.bin --block sav2
./.venv/bin/python -u bin/frlg_mg_host.py --buffer-script flash-patch --flash-id 0 \
  --flash-patch-offset 0x00 --flash-patch-hex cac9c5bfc6bec8ff --write-unsafe
```

## Let's Go！皮卡丘／Let's Go！伊布

pokeldn 可以创建也可以加入。两者都会送出 232 字节的 PB7（`pokeldn.lgpe.pb7`；`--offer echo` 会返回主机的 PB7）；主机端的 `--first echo` 会回显主机的身份信息。主机端的 `--next-offer` 和加入方重复的 `--offer` 会排队后续交换；`--leave-after S` 会让加入方离开。

```bash
./.venv/bin/python bin/lgpe_host.py --seconds 600 --player-name POKELDN \
  --first echo --our-trainer 41234:12345 --offer offer.pb7
./.venv/bin/python bin/lgpe_join.py --connect --connect-seconds 300 \
  --ack-peer-clock --ack-re-announce \
  --our-trainer 41234:12345 --offer offer.pb7
```

主机上：Communiquer → Communication locale → Échange，连接密码选皮卡丘 ×3，然后在搜索界面等待。模拟主机：`lgpe_host.py --ip-host --our-ip IP`。参见 [Let's Go](lgpe.md)。

## 剑／盾

主机上：YY 通信 → 连接交换 → 本地通信，两条提示都按 A，然后在搜索界面等待。

```bash
# join the console's session and trade: the console's own party snapshot is sent back, rewritten
POKELDN_RADIO=esp32:auto ./.venv/bin/python bin/swsh_connect.py --keys PROD_KEYS \
  --preset trade --offer-slot 1 [--offer-file your.pk8 --offer-file next.pk8 --fresh-pid] \
  --save-offered received.pk8

# or host, and let the console join: its snapshot is taken from this trade
POKELDN_RADIO=esp32:auto ./.venv/bin/python bin/swsh_host.py --keys PROD_KEYS \
  --offer-file your.pk8 --fresh-pid --received received.pk8 --channel 6 --seconds 900
```

`--code 12345678` 会为连接密码搜索创建主机。重复的 `--offer-file` 会每次交换排队一个；第 N 次交换写出的文件带 `-N` 后缀。详情：[交换](swsh_trade.md)。

神秘礼物：神秘礼物 → 接收礼物 → 通过本地无线通信。

```bash
./.venv/bin/python bin/swsh_gift_host.py --species 25 --level 25 \
  --move1 84 --move2 45 --move3 86 --move4 98 --nickname POKELDN --ot POKELDN --seconds 300
./.venv/bin/python bin/swsh_gift_host.py --record card.wc8 --seconds 300
```

`--set FIELD=VALUE` 设置记录的字段（`shiny_type=3`、`held_item=236`），`--ribbon N` 添加一个奖章，`--dump FILE` 无需无线模块即可写出记录。若某个道具 ID 在表中没有对应行，游戏在显示它的背包行时会中止。参见[神秘礼物](swsh_gift.md)。

## 晶灿钻石／明亮珍珠

pokeldn 会以角色身份加入主机的联机房间。主机上：任意宝可梦中心 2 楼，找左侧的接待员，选普通的“是”（第一个选项），然后在联机房间中避开墙壁等待。

```bash
./.venv/bin/python tools/ldn/ldn_scan.py --channels 1,6,11 --dwell 0.8      # see the session
./.venv/bin/python bin/bdsp_connect.py --channels 1,6,11 --count 9 --connect 5 --join 6 \
  --hold 420 --reliable-ack --reliable-sweep 3 --room-walk 15 --room-pattern fixed \
  --room-walk-steps 0 --join-avatar 0 --answer-requests --state 0 --recruiting 0 \
  --answer-talk --can-talk 0 --initiate-talk --initiate-delay 3 \
  --after-approach 0x06:0001000000 --trade-reply --complete-trade \
  --trade-template offer.pb8 --trade-nickname POKELDN --src-var 0x2B7F4C12
```

出现 `Connect failed with status code 1` 时重试（[会话](bdsp_session.md)）。重复的 `--trade-template` 会排队交换，最后一次会再次送出。每次运行都要使用新的 `--src-var`。`--complete-trade` 允许主机保存；不加它时，交换会停在最后一次确认处。角色走进房间后：Y → 通信菜单 → 交换宝可梦。

若要创建主机，请先启动主机端；玩家用同样的方式进入房间，并选择 Y → 通信菜单 → 交换宝可梦：

```bash
./.venv/bin/python bin/bdsp_host.py --offer offer.pb8 --complete-trade --capture host.jsonl
```

`--offer` 是一只合法、且该存档中没有其 PID 的 PB8；重复给出会排队交换。`--password 00000000` 会创建带密码的房间。参见[晶灿钻石／明亮珍珠](bdsp.md)。

## 传说 阿尔宙斯

`bin/pla_host.py` 以主机的连接密码创建主机端；`bin/pla_join.py` 加入主机的搜索，重复的 `--offer` 用于每次交换，并在被移交主机角色时接任主机（[传说 阿尔宙斯](pla.md)）。

```bash
./.venv/bin/python bin/pla_host.py --code 00000000 --channel 6 --seconds 1800 \
  --session-update --sustain --clock --data-exchange --data-exchange-name POKELDN \
  --data-exchange-id 11223344 --game-channel --trade-box --trade-box-record offer.pa8 \
  --offer-out received.pa8
./.venv/bin/python bin/pla_host.py --ip-host --our-ip 172.16.86.128 --code 00000000 ...   # emulated console, no radio
```

主机上：到祝庆村找 Simona，选择交换 → 附近的人，输入同样的八位数密码，送出一只宝可梦并确认。`--offer-out` 会保存每条收到的记录（`-2` 起），`--save-shown DIR` 会保存主机显示的每一条记录；重复的 `--trade-box-record` 会排队交换。`pokeldn.pla.pokemon` 可构建一条记录。

## 朱／紫

pokeldn 可以创建（`bin/sv_host.py`）或加入（`bin/sv_join.py`）。

```bash
./.venv/bin/python bin/sv_host.py --seconds 240 --player-name POKELDN \
  --rtt-probe --net-property --clock --net-stations 4 --scarlet-response \
  --record-delay 0.17 --announce --announce-delay 5.25 \
  --send-at 6.00:0x7c:1:b90101b902b90280800001 \
  --trade-offer offer.hex --offer-after-open 8
```

主机上：X → 宝可入口站 → 连接交换 → 离线 → 无密码 → 搜索。重复的 `--trade-offer` 会排队交换。参见[朱／紫](sv.md)。

太晶团体战：`--raid-seed` 会创建一场（宝可入口站 → 太晶团体战 → 连接密码 4970），`--raid-reward ITEM:QUANTITY` 替换奖励，`--raid-pokemon` 是 pokeldn 的宝可梦，`--raid-event FOLDER` 使用 Project Pokemon 的 [EventsGallery](https://github.com/projectpokemon/EventsGallery) 中的宝可入口站新闻活动，`--raid-players N`（最多 3）等待 N 台主机，`--raid-partner TRAINER` 为空位挑选 NPC 伙伴。`bin/sv_join.py --raid-pokemon FILE` 会加入主机的团体战。参见[太晶团体战](sv_raid.md)。

## 传说 Z-A

主机上：连接交换 → 本地通信 → 用密码 00000000 搜索。

```bash
# host: start it first, then search on the console
POKELDN_RADIO=esp32:auto ./.venv/bin/python -u bin/za_host.py --keys prod.keys --trade-offer offer.bin --capture zh.jsonl
# join
./.venv/bin/python bin/za_join.py --channels 1,6,11 --dwell 0.35 --seconds 900 \
  --hold 450 --quiet-seat 25 --connect-timeout 6 --game --trade-offer offer.bin --offer-delay 4
```

重复的 `--trade-offer` 会排队交换；在主机上按 B 可结束会话。`--offer-out FILE` 会保存主机送出的内容。模拟主机：`--ip-host --our-ip IP --comm-id ffffffffffffffff`（创建）或 `--ip-join --host-ip IP --our-ip IP --comm-id ffffffffffffffff`（加入）。送出文件为 354 字节（9 字节头、344 字节记录、1 个结尾字节）；`pokeldn.gen9.build` 可组装该记录。参见[传说 Z-A](za.md)。

## 诊断

- `tools/ldn/ldn_scan.py` 列出可发现的 LDN 网络；`esp32_sniff.py` 把第二块开发板变成空中嗅探器，监听某个频道上某个 MAC 的流量。
- `POKELDN_ESP32_TRACE=FILE` 记录开发板的串口流量与计数器；每个入口上的 `--capture FILE` 会把协议轨迹写成 JSONL。
- [主机实现](frlg_host.md)：组件布局、协议流程、时序、关闭流程。
