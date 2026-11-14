---
title: 神秘礼物文件
---
# 神秘礼物文件

`.pokegift` 文件保存一份完整的《火红／叶绿》或《剑／盾》神秘礼物配信，或一份 FRLG ARM 主机载荷，以及它的目标游戏与原生记录。

## 电脑版 App

同一个构建器同时服务于两款游戏（`pokeldn/app/gift_builder.py`；表单位于 `pokeldn/frlg/gift/builder.py`、`pokeldn/swsh/gift_builder.py`）。

| 模式 | 发送内容 |
|---|---|
| 使用预设 | 内置的礼物；FRLG 的神秘卡片、神秘新闻与主机代码以标志参数传给启动器 |
| 官方活动 | 真实的《剑／盾》活动卡片（[官方活动卡片](swsh_gift.md#official-event-cards)），像自建礼物一样编译 |
| 自行创建 | 表单内容，在按下“开始”时编译为 `session/gifts/<tool>.pokegift`，并以 `--gift-file` 传入 |
| 打开文件 | 他人分享的 `.pokegift`，或《剑／盾》的 `.wc8` |

FRLG 的游戏强化是常驻钩子（[`install-resident`](frlg_rom.md#install-resident)），以一条链的形式运行（[多个钩子同时使用](frlg_rom.md#several-hooks-at-once)），大小在 1024 字节以内；各项设置会变成 `--resident-param` 标志参数。

| 强化 | 设置 | 参数 |
|---|---|---|
| 加速游戏（`turbo-lite`） | 速度 x1 至 x4；大地图、对战或两者；始终开启，或在按住 R、B 或 Select 时开启；文字更快 | `field` 与 `battle` = 速度 - 1，x3 起为 `budget=228`，`hold`，`extra=4` |
| 穿墙 | R、B 或 Select | `hold` |
| 异色倒计时 | 减速按键；慢 x2、x4 或 x8 | `slow`，`slow_frames` 取 1、3 或 7 |
| 异色传说的宝可梦（`shiny-press`） | 超梦；急冻鸟、闪电鸟或火焰鸟 | `offset` 取 1 或 2 |
| 关闭野生宝可梦遭遇、在画面上显示队首宝可梦的个体值、宝可梦跟随 | 无 | |

不提供 L：只有 R 键的帮助系统开关带有钩子可以挂起的标志。稍后保存强化会把该组强化写入 `filler_B20`（`save-write --resident`）并安装；超过 876 字节的一组，以及跟随功能，始终通过存档完成。妈妈恢复强化会让与妈妈的对话在任何一次开机后安装已保存的那一组。再次发送强化会替换正在运行的那一组。

读取存档会提供训练家 ID（TID）与里 ID（SID）、训练家详情与游戏时间，以及最后一次保存的同行宝可梦的性格、个体值与努力值，且不会更动存档（[读取存档](frlg_rom.md#reading-the-save)）。

`.wc3` 与 `.wc8` 文件按二进制读取，即使它们以 `{` 开头。当表单能够表达某个预设时，自定义会把它复制到表单中：所有《剑／盾》预设，以及仅由无条件表单步骤构成的 FRLG 卡片。

FRLG 表单可构建神秘卡片、神秘新闻或主机代码。

| 部分 | 内容 |
|---|---|
| 卡片 | 标题、副标题、四行文本、图标种类、卡片 ID 1000 至 1019、可再次领取、可分享 |
| 由谁交付 | 任意宝可梦中心的配送员、玩家家中的妈妈，或真新镇南部的男子 |
| 步骤 | 宝可梦（种类、等级、携带道具、四个招式）、道具与数量、蛋、野生宝可梦对战、讯息 |
| 新闻 | 标题、最多十行、新闻 ID |
| 主机代码 | ARM 源码或预构建的 `.bin`、为其构建的卡带、预期应答、回传的字节 |

每个步骤都是独立的交付阶段：同行宝可梦或包包已满时便停在该步骤，重试会给出剩余内容。另一位人物通过 `initramscript` 绑定持有这些步骤，这会隐藏卡片，并在被替换前每次都给出这些步骤。种类使用内部编号（`pokeldn/frlg/save/species_names.py`）。

主机代码需要 `arm-none-eabi-as`（位于 PATH、Homebrew 或 Arm 的 Windows 文件夹），或预构建的 `.bin`：

| 系统 | 命令 |
|---|---|
| macOS | `brew install arm-none-eabi-binutils` |
| Fedora | `sudo dnf install arm-none-eabi-binutils-cs` |
| Debian、Ubuntu 及其衍生版 | `sudo apt install binutils-arm-none-eabi` |
| Windows | `winget install Arm.ArmGnuToolchain` |

离线检查会在模拟主机上运行代码（`pokeldn/frlg/rom/custom_code.py`），开始与保存也会如此，遇到出错或始终不返回 1 的代码会予以拒绝。

《剑／盾》表单可构建一只宝可梦（超极巨化可选）、一颗蛋、最多六个道具、服装（[服装](swsh_gift.md#clothing)，每种性别六件）、对战点数或金钱，并按照[零售版《剑》领取的记录](swsh_gift.md#a-card-delivered-to-a-retail-console)的形式排布。

保存礼物文件会写入一个包含所有卡带变体的 `.pokegift`，无需开发板或密钥。主机的游戏代码会挑选变体；文件中没有的卡带会在发送前被拒绝。

## 命令行

两个礼物启动器都接受 `--gift-file FILE`；在《剑／盾》上 `--record` 是别名。`--export-gift FILE` 会保存所选礼物，并在使用无线通信前退出。

```bash
./.venv/bin/python bin/frlg_mg_host.py --gift celebi --export-gift celebi.pokegift
./.venv/bin/python bin/frlg_mg_host.py --news berry --export-gift news.pokegift
./.venv/bin/python bin/swsh_gift_host.py --species 25 --level 25 --export-gift pikachu.pokegift
./.venv/bin/python -m pokeldn.gifts inspect celebi.pokegift
```

FRLG 礼物文件会一并定义卡片标志 ID、脚本、问卷与拒绝讯息。使用它时，`--flag-id`、`--questionnaire` 和 `--hunt-*` 等载荷覆盖项会被拒绝；无线通信、训练家与卡带选择选项仍然有效。

### 主机代码

内置载荷会连同其回应设置一起导出：

```bash
./.venv/bin/python bin/frlg_mg_host.py --buffer-script save-dump --dump-size 64 \
  --export-gift save-dump.pokegift
```

原始 ARM 代码需指定明确的卡带目标来打包：

```bash
arm-none-eabi-as -march=armv4t -mcpu=arm7tdmi -o payload.o payload.s
arm-none-eabi-objcopy -O binary -j .text payload.o payload.bin
./.venv/bin/python -m pokeldn.gifts import --game frlg --code payload.bin \
  --build BPRF --name "Custom payload" --expect 66 -o custom.pokegift
```

最小的 `payload.s` 会把 66 写入回应参数，并在一次调用内完成：

```asm
.syntax unified
.arm
.text
.global _start
_start:
    mov r3, #66
    str r3, [r0]
    mov r0, #1
    bx lr
```

代码是位置无关的 ARMv4T、按字对齐、最多 1024 字节，每帧调用一次，调用时 `r0 = &param`、`r1 = gSaveBlock2Ptr`、`r2 = gSaveBlock1Ptr`，直到它返回 1（[主机代码](frlg_rom.md)）。不使用 `--expect` 时接受任何应答；字节缓冲区应答需要 `--dump-size N`。

接收方可在 FRLG 神秘礼物工具中打开该文件，或传入 `--gift-file`；`--dump-file PATH` 选择回传的转储内容保存到哪里。打包只检查结构与大小：在实际运行前，请先用 `buffer_script.emulate_repeating` 离线运行新的载荷。

### 原生格式

转换器可导入 WC8、FRLG `.wc3` 以及 `pokemon-gen3-mysterygift-tool` 的卡片与脚本配对；`.wc3` 与 `.wc8` 也可以直接打开。

不含绝对地址的 FRLG 脚本（仅有相对于 `setvaddress` 的 `vgoto`／`vmessage` [scrcmd.c:171]，道具通过 `callstd`）适用于其布局下的所有卡带。含有 `goto`、`call`、`message`、`callnative` 或其他绝对指针的脚本需要 `--build`，直接打开时会被拒绝。

```bash
./.venv/bin/python -m pokeldn.gifts import --game swsh --record event.wc8 -o event.pokegift
./.venv/bin/python -m pokeldn.gifts import --game frlg --wc3 "FL - Item AuroraTicket (FRE).wc3" -o aurora.pokegift
./.venv/bin/python -m pokeldn.gifts import --game frlg --card WonderCard.bin \
  --script Script.bin --name "Event gift" -o event.pokegift
./.venv/bin/python -m pokeldn.gifts export celebi.pokegift --build BPRF --out-dir native-gift
./.venv/bin/python -m pokeldn.gifts export celebi.pokegift --wc3 --build BPRJ --out-dir native-gift
./.venv/bin/python bin/frlg_mg_host.py --gift celebi --console-build BPRJ --export-gift celebi.wc3
```

保存到 `.wc3` 或 `.wc8` 路径会写入原生文件。一个 `.wc3` 只容纳一个卡带；不同变体需要 `--build`。其元数据除图标外均为零，图标则重复卡片中的图标。每个被接受的国际版图库文件都能以完全相同的卡片、脚本与图标字节往返转换。

一个国际版 `.wc3` 为 1420 字节（`0x58C`）：

| 偏移 | 大小 | 内容 |
| --- | --- | --- |
| `0x000` | 336 | 卡片的 CRC16、2 个填充字节、332 字节的 `struct WonderCard` |
| `0x150` | 80 | 存档侧的卡片元数据；不读取 |
| `0x1A0` | 1004 | CRC16、2 个填充字节、`struct RamScriptData`（magic 51、地图组、地图编号、对象 ID、995 字节的脚本）、1 个填充字节 |

图库文件的脚本 CRC 覆盖 1000 字节；游戏自身覆盖 999 字节 [script.c:488]；导入时两者都接受。`--icon N`（App 中的卡片图标）设置 `iconSpecies`（卡片偏移 2），取值 0 至 411；取 0 则不绘制图标 [mystery_gift_show_card.c:466]。

日文 `.wc3` 文件为 1252 字节（`0x4E4`）：卡片结构为 164 字节，其 CRC 封装为 168 字节，元数据从 `0x0A8` 开始，1004 字节的 RAM 脚本结构从 `0x0F8` 开始。日文文件适用于 `BPRJ` 与 `BPGJ`，国际版文件则适用于十个拉丁语系卡带。超出 1000 至 1019 的标志 ID 会被拒绝 [mystery_gift.c:241]。

原生配对（卡片加 1004 字节脚本）无法承载印章、来访训练家、神秘事件脚本、问卷关卡或神秘新闻；导出时会拒绝。导入会检查两个 CRC。

## 版本 2

该文件为 UTF-8 JSON，包含五个必需字段：

| 字段 | 值 |
| --- | --- |
| `format` | `pokeldn.gift` |
| `version` | 整数 `2` |
| `game` | `frlg` 或 `swsh` |
| `name` | 非空的显示名称，最多 180 个字符 |
| `variants` | 将目标代码映射到原生数据与选项的对象 |

每个变体都有 `data` 与 `options` 对象。`data` 中的每个组件都有 `hex`（以十六进制编码的原生字节）与 `sha256`（其小写 SHA-256 摘要）。导出时会排序字段。

| 游戏 | 变体键 | 数据组件 | 选项 |
| --- | --- | --- | --- |
| FRLG 礼物 | 支持的卡带代码 | `card`、`ram_script`、`stamp`、`activation_script`、`install_activation_script`、`trainer`、`news`、`mevent` | `questionnaire`、`denied_message` |
| FRLG 主机代码 | 支持的卡带代码 | `buffer_code`、`buffer_lead_1`.. | 见下方的回应设置 |
| 《剑／盾》 | `swsh` | `wc8` | 无 |

FRLG 卡片变体共享标志 ID 与礼物类型；新闻与主机代码单独存在。主机代码变体有一个 `buffer_code`，以及最多八个在它之前运行的 `buffer_lead_N`，编号不得有空缺。回应设置：`buffer_expect`（u32 或 `trainer-id`）、`buffer_dump_size`（1 至 1024）、`buffer_dump_blocks`（最多 32）、`buffer_dump_address`、`buffer_dump_addresses`（每个块一个）、`buffer_decode`。

读取器接受版本 1 文件（卡片、新闻、WC8）；导出的文件为版本 2，新增了主机代码。版本 1 的读取器会拒绝版本 2 文件。

读取器会拒绝未知的版本、字段与代码、重复字段、错误的哈希、超过 256 KiB 的文件、错误的原生大小以及错误的组合；FRLG 还会检查卡片字段、训练家校验和与神秘事件终止。哈希只能发现损坏，不做任何身份验证。

## 实现

`pokeldn.gifts` 负责信封、校验分发、读取器、写入器与转换器。各游戏专用的编解码器位于 `pokeldn.frlg.gift.file` 与 `pokeldn.swsh.gift_file`。FRLG 适配器构建 `MysteryGiftDistribution`，并包含其卡带选择与拒绝路径；《剑／盾》适配器则为 WC8 广播构建器提供输入。
