---
title: 桌面版构建
---
# 桌面版构建

桌面版 App 是 pokeldn 在 macOS、Windows 与 Linux 上的界面。发行版内置 PKHeX 与适用于 ESP32、ESP32-S3、ESP32-C3 和 ESP32-C6 的无线通信固件；`prod.keys` 需由用户自行提供。

1. “设置”：选择 `prod.keys`。
2. “开发板”页面：选择 USB 开发板并安装无线通信固件。安装时会选用该芯片的内置镜像；从文件选择的镜像会先与芯片核对。S3、C3 与 C6 通过原生 USB Serial/JTAG 连接；S2 芯片会被拒绝。
3. 选择游戏与工具，准备好宝可梦或文件，按主机的操作步骤执行，然后按下“开始”。接收到的宝可梦会存入“设置”里选定的文件夹，可用“输出”旁的按钮打开。

每个交换工具中“用于交换的宝可梦”都可以留空：此时按下“开始”会让 PKHeX 为该游戏随机创建一个合法宝可梦，初训家为你的训练家（`command.prepare`），每次运行都会重新创建。

神秘礼物类工具共用同一个构建器（预设、自行创建、`.pokegift`，以及《剑／盾》的 `.wc8`）。没有开发板时，保存礼物文件的导出格式为 `.pokegift`、`.wc3` 或 `.wc8`（[神秘礼物文件](gifts.md#desktop-app)）。

## 首次启动

macOS 保留系统自带的窗口按钮；Windows 与 Linux 则在 App 标题栏中绘制这些按钮，拖动标题栏可移动窗口，双击可最大化。

| 系统 | 步骤 |
|---|---|
| macOS | 未签名：先打开一次，关闭警告，再到“系统设置”→“隐私与安全性”→“仍要打开” |
| Windows | 解压 zip 并运行 `pokeldn.exe`，`_internal` 需与其同目录；SmartScreen：选择“更多信息”→“仍要运行”。没有 COM 端口：[Windows USB 驱动](#windows-usb-drivers) |
| Linux | 需要 GTK 3 与 libsecret；执行 `sudo usermod -aG dialout $USER`（Arch 上为 `uucp`），然后重新登录。参见 [Linux 串口](#linux-serial-ports) |

没有可用的 `prod.keys` 时，App 会打开一个请求选择密钥的欢迎页面；按 Esc 或选择“稍后”即可关闭。在电脑上选好密钥后，第二步会监视 USB 端口，并提示开发板还需要做什么：接入开发板、从“开发板”页面安装固件，或无需任何操作。手机端则在各自的页面中完成开发板设置。

密钥文件可用，指的是它包含无线通信密钥派生所读取的每一项（`ldn.KEYS_NEEDED`）：`aes_kek_generation_source`、`aes_key_generation_source`、`master_key_00`（LDN 协议 1）与 `master_key_12`（协议 3）。缺少的项会在“设置”、“游戏”页面的检查清单以及“开始”处指明。`ldn.load_keys` 会跳过不是 16 或 32 字节密钥的行，例如注释。

### 设置文件损坏

`settings.json` 会在启动时读取（`pokeldn.app.settings.load`）。若文件不是 JSON，或有字段的值类型不正确，会先将其复制为同目录下的 `settings.json.bad`，再替换任何内容；只有无法读取的字段会恢复为默认值。随后 App 会显示哪些字段被重置，以及旧文件所在的位置。

## Android 环境要求

[Android App](../examples/android/README.md) 就是这套界面在手机上的版本。“开发板”页面会在插入、拔出、关闭 USB 提示以及从“设置”返回时重新读取 USB 状态。原生 USB 开发板（`303a:1001`）在插入时会自动打开 App。

| 检测到的状态 | 提示 |
|---|---|
| 没有兼容的 USB 设备 | 检查数据线；显示手机的 USB 主机或 OTG 设置（OnePlus 有 OTG 开关） |
| 缺少或未授予 USB 权限 | 说明 Android 的提示；提供重试 |
| 开发板握手失败 | 检查开发板与固件；显示错误 |
| 开发板有响应 | 显示开发板与固件；继续 |
| 开发板断开，或从“设置”返回 | 刷新并在就绪后继续 |

经典款 ESP32 只能通过 CP210x 桥接芯片使用（`10c4:ea60`，`UsbStream.java`）；CH34x 与 FTDI 会被明确标为不支持。PKHeX 在手机上运行。保存与“打开文件夹”（一个 zip）都使用 Android 的文件选择器。

## iOS 设置

[iOS App](../examples/ios/README.md) 是这套界面在 iPhone 或 iPad 上的版本（通过 AltStore 或 SideStore 安装）。它通过蓝牙连接开发板：请在桌面版的“开发板”页面安装蓝牙无线通信固件（ESP32-C6 用 `pokeldn-radio-ble-c6.bin`，经典款 ESP32 用 `pokeldn-radio-ble.bin`）；USB 只用于供电。手机占用开发板期间，开发板会忽略 USB：若要改在其他地方使用，请先关闭 iOS App。App 文件位于“文件”→“我的 iPhone”→“pokeldn”。

## 窗口尺寸

页面的各个面板按各自分到的宽度布局，随窗口变化实时测量（`gui/theme.py` 的 `Panes`）。与其他面板并排时，选项栏的宽度不会低于 440 点。

| 留给各面板的宽度 | 布局 |
|---|---|
| 侧边面板全宽再加 440 | 并排显示 |
| 侧边面板 88% 再加 440 | 并排显示，侧边面板收窄 |
| 最后一个面板 88% 再加 440（三面板页面） | 前两个放入切换器，最后一个与其并排 |
| 更窄 | 一次只显示一个面板，用切换器切换 |

从并排状态收窄窗口时，选项栏会移到前面。在宽窗口中，选项栏限宽 720 点并居中，输入框按可用宽度每行尽量多放几个；“设置”与“插件”限宽 760。调整尺寸后打开的页面，会以当前宽度允许的布局启动。

桌面窗口最窄可缩到 380 点。宽度低于 760 时，会实时切换为下文的手机布局，再次加宽则切回；桌面窗口始终保留位于内容上方的标题栏行。

## 手机

宽度低于 760 点时，页面会放在底部标签栏中，面板通过切换器逐个显示（游戏、选项、连接阶段）。Android 与 iOS 没有“控制”与“更新”页面。带文字和按钮的卡片（`gui/theme.py` 的 `text_row`）会把按钮放在文字下方，银行的排序与筛选菜单各占一行；布局取决于宽度的视图，会在窗口跨越 760 时通过 `relayout()` 重新渲染。

## “游戏”页面

游戏的列表按活动各列一行：交换、神秘礼物，然后是各种团体战与集友圈。运行该行的方式以按钮形式显示在其选项上方，每个选项占一行：

| 选项 | 按钮 | 显示于 |
|---|---|---|
| pokeldn | 创建（你的主机加入）、加入（你的主机创建） | 通过开发板或局域网的交换、团体战、极巨大冒险 |
| 连接 | 开发板、Wi-Fi（不需开发板）、在线 | 交换；Wi-Fi 仅限《剑／盾》 |
| 模式 | 蓝乐活任务、野生宝可梦 | 集友圈 |

每种组合对应一个目录工具（`pokeldn/app/catalog.py` 中 `Tool` 的 `activity` 与 `variant`），因此一次运行、其保存的字段以及 `python -m pokeldn TOOL` 都沿用该工具的键。只有单一取值的选项不会显示：在线交换没有主机相关的选项。更改一个选择时，该行其他选择会保持上次的取值。插件工具也以同样的方式加入某一行（[工具所在的行](plugins.md#a-tools-row-112)）。

## App 语言

“设置”→“App 语言”会列出英文以及已安装的语言包（[语言包](plugins.md#language-packs-15)）；更改后需重启才会生效，缺失的文本会回退为英文。训练家语言是另一项设置。内置的 Noto Sans CJK SC 字体覆盖中文、日文与韩文（`gui/assets/fonts/LICENSE`）。它自带的 ‘ ’ “ ” · … 是全角，因此会在它之前优先使用 Noto Sans Punctuation——同一字体中这六个符号的拉丁宽度字形（`scripts/gen_punctuation_font.py`）；语言包自己的 `font_family` 仍然排在最前。

## 你的训练家

“设置”→“你的训练家”是 App 创建的每只宝可梦的初训家：名称、性别、语言，以及按游戏显示方式给出的两组 ID 对。记录中保存 16 位 TID 与 16 位 SID，二者是一个 32 位 ID 的两半。

| 游戏 | 显示的 ID | 里 ID | 保存的 id |
|---|---|---|---|
| 火红、叶绿 | TID，0 到 65535 | SID，0 到 65535 | `SID << 16 \| TID` |
| Let's Go、剑／盾、晶灿钻石／明亮珍珠、传说 阿尔宙斯、朱／紫、传说 Z-A | id mod 10^6 | id div 10^6，0 到 4294 | `secret * 10^6 + ID` |

`Settings.ids` 会按游戏进行换算。每个连接主机的工具都会把这个训练家作为其玩家呈现（`tests/test_gui_catalog.py`）。《火红／叶绿》的名称会被截到第三代游戏的 7 个字符；无法编码的名称会变为 `POKELDN`（`Settings.name`）。《传说 Z-A》只有在性别、ID 与名称都一致时，才会把接收到的宝可梦视为玩家自己的（[接收记录](za.md#what-the-trade-writes-into-a-received-record)）；《传说 阿尔宙斯》的记录会带上性别（[记录](pla.md#the-games-reader-and-the-pre-handler-phase)）。

宝可梦文件会保留其原有的初训家，除非交换请求卡片中的“设我为它的初训家”开关已打开：此时 PKHeX 的 `check` 会带上 `trainer` 字段，写入这个训练家的名称、ID 与性别（`Retrain`）。异色与否由 PID 与这些 ID 共同决定。从第七世代起，会调整 PID 的高半部分，以保持方块异色、星星异色或普通闪光；若遭遇决定了 PID（第三世代的性格、特性与性别，《剑／盾》的地图上遭遇或团体战种子），则 PID 保持不变，卡片会说明闪光有所变化。只能与自身初训家一同合法的宝可梦（例如初训家固定的活动宝可梦）会被拒绝，并给出 PKHeX 的原因。

来自其他游戏的宝可梦文件（`.pk4` 到 `.pk7`、`.pb7`，以及 PKHeX 能读取的任何作品格式，`pokeldn.pokemon.FOREIGN`）会按[银行](#importing)转移宝可梦的方式进入交换请求对应的游戏：PKHeX 的 `convert` 会去掉其携带道具与第三／四世代的秘传招式，再让它经过 HOME 的转换（`Converted`）。游戏没有的种类或形态会被拒绝，并给出原因。

### 读取你的训练家

“读取我的数据”会用某次运行从主机读到的最新训练家，填入某一行的 ID 与里 ID，以及名称、性别与语言。Switch 游戏从不显示里 ID；该值由连接本身携带。

| 行 | 训练家的判定依据 |
|---|---|
| 火红、叶绿 | 主机的 LinkPlayer，`trainerId` = `SID << 16 \| TID`；在所有交换、神秘礼物与联盟交谊厅连接阶段中，两种角色都适用 |
| Switch | 在 Let's Go、晶灿钻石／明亮珍珠、传说 阿尔宙斯、朱／紫或传说 Z-A 的交换中，两种角色都取主机的会话数据（[这是谁的存档](gift_simulated.md#whose-save-it-is)）；在剑／盾以及任何作品中，则取主机交换出的、由其存档捕捉的宝可梦（handler 为 0、游戏版本一致、不是蛋） |

启动器会为每位训练家打印一次 `[trainer] {json}`（`pokeldn.console_trainer`）；App 会按行、并按游戏保存最新的一条到 `settings.json` 的 `found_trainers`，并在隐私日志的遮盖规则下记录它。Switch 这一行为所有 Switch 作品服务，因此会采用最后一次交换到的那一条。若什么都没找到，“读取我的数据”会提示先进行一次交换。

### 为每个游戏设置训练家

为每个游戏使用不同的训练家，可以让每个作品拥有各自的名称、性别、语言、ID 与里 ID，并逐个游戏编辑；ID 按该游戏的显示方式给出。从未编辑过的游戏会沿用共用的训练家。以两个版本发售的游戏会分别列出每个版本（《火红》与《叶绿》、《剑》与《盾》，以及其他作品），因此同一游戏的两个存档可以各自保留训练家；从未编辑过的版本会沿用该游戏的训练家。两个版本存在差异时，该游戏的工具会在“创建”与“加入”旁显示“你的游戏”，运行时会使用所选版本的训练家。`settings.json` 用 `per_game_trainer` 保存开关，用 `game_trainers` 保存各项值（游戏或版本键对应有差异的字段），用 `played` 保存每个游戏选定的版本。`Settings.own(game)` 是某个游戏看到的训练家；`Settings.ids`、`Settings.name`、`Settings.trainer` 以及启动参数 `{ot}`、`{tid}`、`{sid}`、`{language}`、`{gender}` 都通过它读取（`tests/test_gui_catalog.py`）。在某个游戏上按“读取我的数据”，会取从该游戏读到的最新训练家。“设置”会打开在最后编辑过的游戏上。

`settings.json` 位于数据文件夹中，与 App 分离，因此更新不会改动它：Windows 上为 `%APPDATA%\pokeldn`，macOS 上为 `~/Library/Application Support/pokeldn`，Linux 上为 `~/.local/share/pokeldn`。手机 App 会把它保存在各自的私有存储中，卸载时会被清除。

## Windows USB 驱动

经典款 ESP32 的 USB 转串口桥接芯片需要驱动，Windows 才会给出 COM 端口（设备管理器问题代码 28）。使用原生 USB 的 S3、C3 与 C6 无需驱动。

| 桥接芯片 | USB ID | 驱动 |
|---|---|---|
| CP210x | `10c4:ea60` | [CP210x VCP 驱动](https://www.silabs.com/developer-tools/usb-to-uart-bridge-vcp-drivers)：右键点击 `silabser.inf`，选择“安装”，然后重新插入 |
| CH340 | `1a86:7523` | [CH341SER.EXE](https://www.wch-ic.com/downloads/CH341SER_EXE.html)：选择“安装”，然后重新插入 |

没有 COM 端口时，“开发板”页面会每 2 秒轮询 `Win32_PnPEntity`（`ConfigManagerErrorCode <> 0`），并指出已知的桥接芯片（`gui/board.py` 的 `bridges_without_driver`）。

## Linux 串口

端口需要 `dialout` 组权限（Arch 上为 `uucp`）；遇到 `EACCES` 时，“开发板”页面会指出该组。

| 服务 | 开发板 | 影响 |
|---|---|---|
| brltty 6.4（Ubuntu 22.04） | CH340 | 会抢占该设备，导致没有 `/dev/ttyUSB*`（[LP 1990357](https://bugs.launchpad.net/bugs/1990357)）；解决：`sudo apt remove brltty` |
| brltty 6.6（Ubuntu 24.04） | CH340 | 只在经过 `1a40:0101` 集线器时抢占（[LP 1958224](https://bugs.launchpad.net/bugs/1958224)） |
| ModemManager 1.23 | 全部 | 没有针对 `10c4`、`1a86`、`303a` 的忽略规则 |

没有端口时，“开发板”页面会读取 `/sys/bus/usb/devices`，并指出没有 tty 的桥接芯片（`gui/board.py` 的 `bridges_without_port`）。

## 本机存储

“设置”→“存储”会显示可回收的空间；“清除本机文件”会在确认后于后台删除这些内容，期间会暂停连接阶段与烧录。请先保存问题反馈所需的任何内容。

| 删除 | 保留 |
|---|---|
| `session/`（连接记录、跟踪记录、临时交换请求）、`logs/`、`pokemon/` 中未使用的已生成或已导入交换请求、空文件夹 | 不到一分钟的交换请求，或被保存的设置与队列引用的交换请求；已接收文件、银行、存档、密钥、固件、设置；符号链接；检查之后被改动的文件 |

## 备份与还原

“设置”→“存储”→“备份”会写出一个 zip（`pokeldn.app.backup`），其中包含 `pokeldn-backup.json` 与以下文件夹；“还原”会读回其中一个。

| zip 中的文件夹 | 来源 |
|---|---|
| `settings/settings.json` | 数据文件夹中的 `settings.json` |
| `pokemon/` | 已生成与已导入的交换请求 |
| `received/` | 在“设置”中选择的“已接收”文件夹 |
| `bank/`、`saves/`、`gts/`、`macros/` | 银行、存档、GTS 与宏文件夹 |

`.keys` 文件永远不会写入备份，也不会从备份中还原；插件及其数据同样不在备份中。还原时会先把当前文件备份到数据文件夹的 `backups/`（只保留最新的三份），然后逐个覆盖同名文件；备份中没有的文件会保留。设置会写入 `settings.restore.json`，下次启动时会在读取设置之前将其放到位置。若某个成员位于这些文件夹之外、是符号链接、路径中含有 `..` 或格式未知，整个还原会在写入任何内容之前被拒绝；若某个成员的数据与其 CRC 不符，还原会中止，已经写入的内容会保留。

## 你的存档

《火红／叶绿》神秘礼物工具的“你的存档”标签页可以备份或还原主机的存档（[存档备份与还原](frlg_gift.md#save-backup-and-restore)）。存档位于 `Documents/pokeldn/Saves`（`pokeldn.app.saves`；若设置了 `POKELDN_DATA`，则位于其中），每个存档各有一个 `.sav` 与一个 `.json`。

| 操作 | 结果 |
|---|---|
| 从 Switch 备份 | 写出 `backup-<run>.sav`；中断的备份会留在 `Saves/.partial` 中，下次会从中继续 |
| 将存档写入 Switch | 传入 `--save-restore`；未选择存档前“开始”会被阻止 |
| `+` 或拖入 `.sav` | 复制进来；会去掉 16 字节的模拟器尾部，大小不是 128 KB 的会被拒绝 |
| 重命名、导出、删除 | “删除”会在本机删除两个文件 |
| 查看与编辑 | PKHeX 会读取训练家、同行队伍与盒子 |

若没有完整的存档副本，或同行队伍中有不合法的宝可梦，还原会被阻止，直到开启“仍要还原”。编辑器可以修改训练家名称、性别、金钱、游戏币以及同行队伍；“保存为新存档”会通过 PKHeX 写入，重新计算扇区校验和，并作为新条目保存。

## 宝可梦银行

“银行”页面会保存每一只接收到的宝可梦，并能把它交换进 HOME 会将其转移到的任何游戏。记录以各自游戏的格式保存在 `Documents/pokeldn/Bank`（`pokeldn.app.bank`；若设置了 `POKELDN_DATA`，则位于其中），并附带一个 `.json`。

| 步骤 | 结果 |
|---|---|
| 一次交换完成 | 每个接收到的文件按其字节只存入银行一次 |
| 宝可梦存入银行 | `.json` 会保存种类、摘要、判定结果、来源、SHA-256、随机的 63 位追踪码与 `home_tracker` |
| 目标游戏 | 辅助程序的 `destinations` 会尝试全部七个游戏 |
| 选定目标游戏 | `move` 会将其转换并加入该工具的队列，同时带上 `"bank": id` |
| 第 N 次交换完成 | `[done] trade N complete` 会将其移出银行 |
| 运行失败 | 它会留在银行与队列中 |

转移会使用 PKHeX 的 HOME 转换（通过 `PKH` 调用 `EntityConverter.ConvertToType`）以及目标游戏的合法性检查。App 的训练家会成为 handler（`IHandlerUpdate`、`PB8.UpdateHandler`）；无效的招式会被替换为 PKHeX 建议的招式组合；PID、加密常数、初训家与 ID 都会保留，运行时不会带 `--fresh-pid`。

| 拒绝 | 来源 |
|---|---|
| 无法转回《火红／叶绿》 | `EntityConverter.IsConvertibleToFormat` |
| 无法转入《Let's Go！皮卡丘／伊布》 | HOME 只从中取出 |
| 蛋；携带道具或秘传招式的《火红／叶绿》宝可梦 | HOME 的《火红／叶绿》筛选 |
| 没有该种类或形态 | 目标游戏的宝可梦数据表 |
| 《传说 Z-A》记录转出 | PKHeX.Core 26.10.18 没有对应路径 |

盒子会列出银行中的每只宝可梦，并支持按摘要（可按显示内容与英文名搜索：种类、昵称、性格、特性、精灵球）及其游戏名称搜索，还提供排序（最新、最早、图鉴编号、名称）与筛选（异色、等待交换、不合法）；排序、筛选与图鉴筛选会保存在 `settings.json` 的 `bank_view` 中。“选择”可以选中多只宝可梦（长按也会进入选择状态），用于一次导出到文件夹、移出交换队列或删除。选中多只时，侧边栏会列出每个游戏能接收其中多少只，并按盒子中的顺序把这些宝可梦加入所选交换工具的队列，直到占满其空位（一个队列可容纳六只）。图像的裁剪结果会连同其 SHA-256 保存在图像缓存的 `index.json` 中，因此打开盒子时无需重新解码此前已显示过的 PNG。

宝可梦面板中的“复制”会把同一条记录再存入银行一份，拥有自己的 id 与 HOME 追踪码（`bank.duplicate`）；一次交换或一次删除只会取走其中一份，另一份保留。

宝可梦面板会根据辅助程序的 `check`（`battle`）显示其对战配置：个体值、努力值与能力值按 Showdown 的顺序排列，并给出英文的 Showdown 配置，供“复制为 Showdown 配置”使用。努力值一列在《Let's Go！皮卡丘／伊布》中是觉醒值（`IAwakened`），在《传说 阿尔宙斯》中是按游戏显示方式给出的奋斗值（存储值加上个体值的 `GanbaruExtensions.GetBias`），在其他游戏中则是努力值。

图鉴会列出银行所涉七个游戏拥有的所有种类（即辅助程序 `species` 的并集），并对已拥有的每一种显示银行中的数量、图像与异色标记；筛选可以显示已收集、尚未收集或尚无异色个体的种类。点击已收集的种类，会在盒子中以该种类为条件搜索。

“编辑”只允许游戏允许的内容：昵称、往上调整等级、招式、携带道具。辅助程序的 `check` 会拒绝使合法宝可梦变为不合法的编辑。已加入队列的宝可梦不可编辑。`tests/test_bank.py` 通过真实的辅助程序覆盖了招式、拒绝、编辑与导入。

### 不合法的宝可梦

“设置”→“高级”→“允许不合法的宝可梦”（`Settings.allow_illegal`，默认关闭）会在每次向辅助程序发出的请求中附带 `allow_illegal`；运行时会以 `POKELDN_ALLOW_ILLEGAL` 继承该设置。构建器仍会先尝试每一种遭遇。若没有合法结果，辅助程序的 `Forged` 会取一条遭遇记录，并按你的要求写入种类、形态、等级、异色、昵称、性格、性别、特性、个体值、招式、道具与精灵球；该记录会被标记为“不合法”。此时特性与精灵球列表会提供游戏中的每一个取值。第三世代的记录会在 PID 中保存性格与性别，PID 会反复重掷直到二者相符，并且只使用该种类可用的特性。

该设置也会解除对不合法文件、银行编辑、游戏间转移与交换的拒绝。游戏没有的种类或形态仍会被拒绝。GTS 只接受合法的宝可梦，因为上架项目会送达其他玩家，而不合法的宝可梦可能在对方游戏绘制它时导致崩溃。

“设置”→“高级”→“将不合法的宝可梦导入银行”（`Settings.bank_illegal`，默认关闭）只会在辅助程序的 `import` 请求中附带 `bank_illegal`。这样导入时会保留 PKHeX 标记的记录（原格式或经过 HOME 转换后），银行会将其标记为“不合法”。将其移出银行或用于交换，仍需遵循“允许不合法的宝可梦”。

### HOME 追踪码设置

对于被转移到其他游戏的宝可梦，以及经由 HOME 送来的礼物，PKHeX 会标记缺失的追踪码（`TransferTrackerMissing`）。HOME 3.1.0 及以后会拒绝不是它签发的追踪码（错误 10015）。“设置”→“高级”→“HOME 追踪码”（`Settings.home_tracker`）会随每次辅助程序请求发送，并以 `POKELDN_HOME_TRACKER` 传给运行。

| 设置 | 写入的追踪码 | 合法性 | 警告 |
|---|---|---|---|
| `empty`（默认） | 无 | 带追踪码时合法即可通过 | PKHeX 会标记缺失的 HOME 追踪码 |
| `made` | 随机的 63 位（与银行相同） | 不改变 | 无法存入 HOME |

在 `empty` 下，辅助程序会在一份带有追踪码、并应用了 HOME 改动的副本上判定记录（`ValidWithTracker`），因为 PKHeX 会以追踪码作为跨 HOME 游戏进化与 Z-A 特性重新对齐的前提条件。礼物会遵循该设置（`MendGift`）；自行生成的追踪码会同时带上 HOME 的改动（`HomeSeen`：在《朱／紫》中以身高表示体型值，在 Z-A 中为身高、体重与头目证章）。《剑／盾》的神秘礼物卡片从不携带追踪码（[Pokemon HOME](swsh_gift.md#pokemon-home)）。

### 导入

按加号按钮或拖入文件，可以导入 PKSM 银行、游戏存档（`SaveUtil.TryGetSaveFile`；3DS 的存档是名为 `main` 的文件）或任何 PKHeX 格式的单条记录（`FileUtil.TryGetPKM`）。存档会先给出同行队伍再给出盒子中的位置；PKSM 银行会按顺序给出其盒子中的位置。

| PKSM 银行（`.bnk`） | 结构（PKSM `common/source/BankFile.cpp`） |
|---|---|
| 头部 | `PKSMBANK`、u32 版本号、u32 盒子数量（版本 1 中没有，按长度读取） |
| 条目 | u32 世代标记，然后是解密后以 `0xFF` 填充的记录；版本 1 与 2 中为 264 字节，版本 3 中为 0x150 |
| 位置 | 每个盒子 30 个，最多 500 个盒子 |
| 标记（PKSM-Core `Generation.hpp`） | 0 第四世代，1 第五世代，2 第六世代，3 第七世代，4 Let's Go，5 第八世代（PK8），6 第三世代，7 第一世代，8 第二世代；`0xFFFFFFFF` 为空 |

第一、二世代的条目是只含一只宝可梦、并同时带有两个名称的列表：第一世代为 59 或 69 字节，第二世代为 63 或 73 字节；当其最后一个字节为 `0x50` 或 0 时，取日文长度（PKSM `3ds/source/Bank.cpp` 的 `Bank::pkm`）。版本高于 3 的会被拒绝。盒子名称保存在银行旁的 PKSM `.json` 中，不会被读取。

| 记录 | 保留方式 |
|---|---|
| 银行中某个游戏的格式 | 合法时原样保留 |
| 其他任何格式 | 去掉携带道具、遗忘第三／四世代秘传招式；若合法，则转移到第一个能接收它的游戏：火红／叶绿、朱／紫、剑／盾、晶灿钻石／明亮珍珠、传说 阿尔宙斯、传说 Z-A |

不合法的记录、校验和错误、其他游戏的蛋以及无法到达的种类都会被拒绝。`Bank/.imported` 会保存每条已导入记录的 SHA-256，因此重新导入同一存档时只会带入有改动的记录。

### 尚待确认

- HOME 是否接受自行生成的追踪码，或跨游戏转移的宝可梦上的空追踪码。
- HOME 针对《火红／叶绿》的规则是否超出蛋、携带道具与秘传招式的范围。
- HOME 的 Switch 版《火红／叶绿》来源图标由哪个字段承载；PKHeX 会按伙伴公园的来历转换 `.pk3`。

## GTS

“GTS”页面会列出公开的上架项目，可按种类筛选；“你的”下则是玩家自己的项目。“仅异色”只保留提供异色宝可梦的项目；“银行可回应”只保留那些能由银行中合法且未入队的宝可梦回应的项目。上架项目可按最新优先、结束日期、图鉴编号或等级排序。若提供、求取或选中要寄存的宝可梦是异色的，会带有闪光特效。“寄存”会取走一只合法且未入队的银行宝可梦，在上架期间保存在 `Documents/pokeldn/GTS`，并可求取最多三个种类（每个都可以要求异色），且只设一个等级范围。App 只要在运行，就会回应其他玩家的请求（[GTS](online.md#the-gts)）。

## 开发板与固件

“开发板”页面会列出每一块已插入的开发板，以及它的固件、版本，并显示“已是最新”或“有可用更新”。固件卡片（`gui.board.FIRMWARES`）会在确认后安装无线通信固件或控制器固件；“从文件安装”可以选用 pokeldn 的 `.bin`。

| 开发板 | 查找方式 | 版本来源 |
|---|---|---|
| 无线通信 | 串口 | HELLO 回复 |
| 控制器，经典款 ESP32 | 串口 | 状态帧 |
| 控制器，ESP32-S3 | USB ID `0f0d:0092` | 蓝牙状态 |
| 无 | 串口，无应答 | 无 |

所安装的版本取自 ESP-IDF 应用描述符的 `version`（魔术字 `0xABCD5432`，在合并镜像中位于 `0x10020`）。运行控制器固件的 S3 会通过蓝牙收到下载命令；App 会等待加载器端口 20 秒，并用 `--from-loader` 烧录。

被设置为[便携式信标](hardware_esp32.md#portable-beacon)的开发板会显示“已保存礼物”，旁边是“移除”。

### 开发板信息

无论“开发板”页面是否选中了开发板，“复制开发板信息”都会把信息复制为纯文本，并保存为数据文件夹中的 `logs/board-report-DATE.txt`（`gui/board_report.py`）。复制会打开所选端口，因此开发板可能会重启；在运行期间，它只会列出端口。

| 部分 | 包含内容 |
|---|---|
| 这台电脑 | App 版本、打包版或源码版、系统、Python、pyserial 与 esptool 版本 |
| USB 串口 | pyserial 列出的每个端口，及其 USB ID、序列号、位置与 `hwid` |
| 驱动 | Windows 上没有驱动的桥接芯片、Linux 上没有 tty 的桥接芯片、USB 上的控制器开发板 |
| 打开端口 | 打开时的错误及 `errno`/`winerror`，或前 2 秒读到的字节 |
| pokeldn 固件 | HELLO 与 STATUS，或无人应答的原因 |
| ESP32 引导程序 | esptool 给出的芯片、描述、特性、晶振、MAC 与 USB-Serial/JTAG 模式 |
| 活动记录 | 该页面最近 80 行 |

## 控制器

“控制”页面通过控制器固件（[控制器开发板](hardware_pad.md)）按下 Switch 的按键，并播放宏。ESP32-S3 插在 Switch 上，通过蓝牙低功耗连接；经典款 ESP32 则留在电脑的 USB 上，并要在“更改握法／顺序”中配对。重新安装固件会清除配对。连接断开时，页面会持续搜索，直到开发板响应或按下“停止搜索”。

| 部分 | 作用 |
|---|---|
| 屏幕上的控制器 | 按住按键；摇杆支持八个方向，居中按下为 L3/R3 |
| 键盘 | 方向键对应十字键，X 为 A，Z 为 B，S 为 X，A 为 Y，Q 为 L，W 为 R，1 为 ZL，2 为 ZR，Enter 为 +，Backspace 为 -，H 为 HOME，C 为截图 |
| 录制到宏 | 每次按下都会成为一个步骤，包含按住时长与停顿 |
| 宏编辑器 | 按键、摇杆、等待、嵌套重复；包含“运行一次”与“循环”部分 |
| 在开发板上播放 | 开发板按自己的时钟播放宏 |

宏是 `Documents/pokeldn/Macros` 中的 `.pokemacro` 文件（[控制器开发板：宏](hardware_pad.md#macros)）。该页面会与 `127.0.0.1:47800` 上的 `pokeldn.pad.service` 通信。在 macOS 26 上，以 App 包主可执行文件身份签名的进程无法发现蓝牙设备，因此打包版 App 会从 `Contents/Helpers/pokeldn-bluetooth` 运行该服务——这是一份仅做裸签名的副本，其 `_internal` 链接到 `../Frameworks`。

## 开发板的屏幕

“设置”→“显示开发板屏幕”会把开发板 128x64 像素的屏幕绘制在“连接阶段”面板顶部，无论开发板是否接了屏幕（[屏幕](hardware_esp32.md#the-screen)）。App 会为一次运行设置 `POKELDN_SCREEN_MIRROR=1`；随后运行会打印它发出的每条 DISPLAY 命令，并每秒打印一次来自 STATUS 的开发板模式、已就座站点、数据帧与 BOOT 按下次数：

    [screen] reset
    [screen] cmd HEX
    [screen] radio MODE STATIONS RX TX PRESSES

`pokeldn.app.screen_render` 会通过固件 `scene.c` 与 `screen.c` 的 Python 副本重放这些内容；`tests/test_screen_render.py` 会用编译后的 C 代码校验每一帧。该面板按固件 50 毫秒的帧率绘制，会随开发板一起变暗，并在闲置十分钟后关闭。

## 宝可梦图像

图像按需来自 [PokeAPI](https://github.com/PokeAPI/sprites)，并缓存到 `sprites/` 中。“设置”→“宝可梦图像”可以关闭下载并清除缓存。缺少图像时会显示占位图；缺少异色图像时会回退为普通形态。

道具、精灵球与奖章选择器会显示同一代码库中的图标（`sprites/items/`、`sprites/ribbons/generation-ix/`——其中以相同文件名保存了第八世代的每一个文件——以及供《火红／叶绿》记录使用的 `sprites/ribbons/generation-iii/`），并缓存到 `sprites/items/`、`sprites/ribbons/` 与 `sprites/ribbons-g3/`。PokeAPI 没有证章图标。辅助程序会按英文名称命名每个文件（`IconName`：“Poké Ball” 为 `poke-ball`；第三世代的道具使用其后来的名称；《传说 阿尔宙斯》独有的精灵球加 `la` 前缀）。每个图标缓存后，对应行就会显示它；若打开列表时图标缺失，会按列表顺序逐个下载，间隔 0.05 秒，每个缓存用一个线程（`SpriteCache.prefetch`），并且每下载 24 个就重绘一次。网络故障会结束该次运行；下次打开列表时会继续。PokeAPI 中没有的名称（招式学习器、多数《传说 Z-A》道具）不会显示图标。

## 奖章

折起的“奖章”位于已创建或已加载的宝可梦下方，会列出辅助程序 `ribbons` 命令返回的内容：记录所属格式中的每一枚奖章（`RibbonInfo.GetRibbonInfo`），在单独加入当前记录时能被 PKHeX 合法性分析接受的，取它能接受的最高次数。第三世代的华丽大赛奖章是一个次数，从普通（1）到大师（4）。遭遇本身附带的奖章，例如活动赠送的经典奖章，无法取下。证章来自野生遭遇的随机结果，因此不会列出；PK3 上的第四世代回忆次数同样不会列出，因为没有任何第三世代游戏会写入它。开启“允许不合法的宝可梦”后，所有奖章都会列出，不合法的以红色显示。

点击一次会发送带 `ribbons` `{property: count}` 的 `check`，并把结果保存为新文件；PKHeX 拒绝的结果会被丢弃，除非开启了“允许不合法的宝可梦”。列表取决于记录本身：用默认值创建的 100 级《朱》皮卡丘会列出最佳好友奖章、努力奖章、大师级奖章与帕底亚冠军奖章；《传说 Z-A》创建的记录则一枚也不列出。重新创建会从没有奖章开始。

## 团体战活动

《朱／紫》太晶团体战（创建）的团体战活动卡片会用 [EventsGallery](https://github.com/projectpokemon/EventsGallery) 中的数据开放团体战（[活动团体战](sv_raid.md#event-raids)），并将其复制到 `EventsGallery/`（`pokeldn.app.events_gallery`）。“下载”会从 `codeload.github.com` 获取涉及 `Released/Gen 9/SV/Raid Events` 的最新提交，并保留每个活动最新的数据表；“检查更新”会比较该提交。复制只有完整之后才会替换旧内容；Windows 会以 `\\?\` 打开长路径。

选定一个活动后，团体战卡片会被限制在该活动的版本、进度与结晶范围内（`raid_event.constrain`），“寻找团体战”也会被限制在其结晶、头目与奖励表中（[寻找种子](sv_raid.md#finding-a-seed)、[体型证章](sv_raid.md#size-marks)）。只能捕捉一次的头目会提供“允许再次捕捉”（`--raid-catch-normal`）。折叠该卡片会恢复为标准团体战（“关闭：活动”）；副本中缺少的活动会显示“缺失：活动”，运行时会被拒绝。

## 开团团体战的奖励

“奖励”卡片提供模板（培养道具、薄荷、对战道具、树果、进化道具、太晶碎块、秘传调味料、宝物、精灵球），并共用一个 1 到 999 的数量；开始编辑会切换为自定义奖励，最多 45 行。“团体战自带奖励”会清除这些覆盖设置（[开团](sv_raid.md#hosting)；`gui/views/rewards.py`）。

## 团体战 NPC 队友

“团体战 NPC 队友”卡片会补上主机留空的位置（[队友](sv_raid.md#partners)；`gui/views/raid_partners.py`）；若不做选择，开团方会像主机一样自行抽选。队友的进度通过 `--raid-partner-progress` 传入；每张卡片会显示训练家、宝可梦（等级为我方宝可梦的五分之四）、太晶属性、特性与招式，受青睐的队友会带有蓝色或银色条带（[受青睐的队友](sv_raid.md#favoured-partners)）。每次点击会按位置顺序传入 `--raid-partner`；当前阶段没有的选择会被丢弃。

## 集友圈

《朱／紫》的集友圈工具会用四位数的连接密码加入主机的集友圈（[集友圈](sv_union_circle.md)）；该字段初始为空。

- 蓝乐活任务：解锁尚未获得的点心大叔传说的宝可梦，或给予 BP（1 到 9,999,999）；点心大叔相关的运行会绘制一条显示完成次数的[进度](#progress)条。
- 野生宝可梦：生成卡片（`gui/views/encounter.py`）可设置种类、异色、形态、等级、太晶属性、性格、性别、特性、道具、证章、大小与个体值；“仅限合法遭遇”（默认开启）会将其限制为 PKHeX 接受的范围，并列出有效地点。它会传入 `--spawn` 与 `--spawn-*`。

`[panel]` 卡片（[状态卡片](plugins.md#status-cards-18)）会在运行期间显示在工具选项的上方。`--verbose-circle` 会记录每条集友圈消息。

## 神秘礼物 - 模拟

该工具在 Let's Go、晶灿钻石／明亮珍珠、传说 阿尔宙斯、朱／紫与传说 Z-A 上的卡片会列出 PKHeX 活动表中的配信宝可梦（[模拟神秘礼物](gift_simulated.md#the-gifts)；`gui/views/event_gifts.py`），最新在前，可搜索。点击一次会为“设置”中的训练家加入一份新副本；一次连接阶段最多可交换六份礼物。副本会保留创建它时所用的训练家。

若某份礼物指定的领取者语言没有任何存档达到，会显示为不合法图块（[卡片触达的存档](gift_simulated.md#saves-a-card-reached)）。“为领取者重建”（默认开启）会为此类礼物按主机的存档重新生成（[为领取者重建](gift_simulated.md#made-for-the-receiving-player)）；若队列中没有符合条件的礼物，该开关会被禁用，也不会传入 `--for-receiver`。HOME 礼物会用琥珀色描边，并遵循 [HOME 追踪码设置](#the-home-tracker-setting)（[交换提供的副本](gift_simulated.md#the-copy-a-trade-offers)）。

## 隐私日志

“设置”→“在日志中隐藏个人信息”（默认开启）会对显示与复制的日志进行遮盖（`pokeldn/app/redact.py`）：

| 遮盖内容 | 显示为 |
|---|---|
| 路径中的主文件夹 | `~` |
| iOS App 容器 | `<app>` |
| MAC 的设备部分 | `**:**:**` |
| `ot_name`、`ht_name`、`OT`、`nickname`、`trainer`、`player`、`name` 之后的带引号值（`POKELDN`、`PKLDN` 除外） | `***` |
| `TID`、`SID`、`trainer_id` 之后的值 | `***` |
| 出现过的训练家名称，以及“设置”中的名称，按整词匹配 | `***` |

连接记录（`captures/`）不会被遮盖。链路本地地址会保留。

## 弹窗

运行、子进程与 App 都可以在任何页面上打开弹窗（`pokeldn.popup`，插件 API 1.2）。

| 类型 | 回调 |
|---|---|
| `acknowledge(title, text)` | `on_ack` |
| `confirm(title, text, agree, disagree)` | `on_agree`、`on_disagree`、`on_dismiss` |
| `choose(title, text, options)`（1.7，2 到 8 个选项） | `on_choice(index)`、`on_dismiss` |

选项：`id`（重新打开已在显示的 id 会替换它并丢弃其回调）与 `tone`（`info`、`warning`、`error`）。打开时会返回 id；除非设置了 `set_dispatcher(dispatch)`，回调会在应答线程上运行。`cancel(id)` 会关闭一个弹窗。32 个未应答的弹窗会引发 `RuntimeError`。没有 App 时（`available()` 为 false），弹窗会变成一行 `[pop-up]` 输出。

`runner.Process(..., popups=app.popups)` 会设置 `POKELDN_POPUPS=1`；子进程在 stdout 写出 `[popup]` 与 JSON，并从 stdin 读取 `[popup] {"id", "n", "answer"}`（`pokeldn.app.runner.child`）；`n` 会让对已被替换弹窗的迟到应答不产生任何效果。`pokeldn.app.popups.Manager` 负责保存，`gui.popups.Dialogs` 负责绘制。App 自身的弹窗会报告更新失败、插件被禁用，以及用“设置”中的训练家发送领取者礼物（[交换](gift_simulated.md#the-trade)）。

## 运行状态

运行等待时，“连接阶段”面板会显示“等待主机连接”与已用时间；若无主机响应达 60 秒，会询问主机是否停在操作步骤指定的画面。“主机已连接”会在加入成功后出现。开发板的后端会在无线通信首次创建或扫描时打印一次 `[link] waiting`，之后在每次站点或连接变化时打印 `[link] joined` 与 `[link] left`（`pokeldn.ldn.show_link`，仅在 App 启动的运行中；插件提供的无线通信不会打印这些内容）。

### 运行失败时

`pokeldn.app.failure` 会读取该次运行的输出行，指出一个原因，并给出可修复它的页面：

| 原因 | 匹配内容 | 按钮 |
|---|---|---|
| 开发板断开 | `[esp32] The board's USB connection failed`、`the board left USB` | 开发板 |
| 端口被占用 | `Resource busy`、`Access is denied`、errno 13 | 开发板 |
| 固件不匹配 | `board speaks protocol N, host speaks M` | 开发板 |
| 开发板无响应 | HELLO 无回复、端口的设备消失 | 开发板 |
| 缺少密钥 | `prod.keys has no NAME`（`ldn.MissingKey`） | 设置 |
| 加入失败 | `the board could not join` | |
| 没有主机 | 出现 `[link] waiting` 且从未出现 `[link] joined`，未完成交换 | |
| 其他任何情况 | 回溯信息与非零退出码 | 复制日志 |

第一条匹配的行会决定原因。玩家主动停止的运行，或已完成一次交换的运行，不会报告任何内容。神秘礼物信标（`Tool.joins` 为 false）从不会被归咎于主机。

### 自动重试失败的交换

开启“设置”中的“自动重试失败的交换”后，若一次交换运行以可重试的原因结束（开发板断开、加入失败、没有主机），会在 15 秒后用尚未交换的队列宝可梦重新开始，最多连续三次；完成过一次交换的运行会重置计数。“不重试”会取消等待；按下“开始”或改选其他工具也会取消。

## 设置搜索

“设置”顶部的输入框只会显示标题或说明中包含所输入文字的卡片（不区分大小写），并各自归在所属分区标题下。搜索也会覆盖处于隐藏状态的高级设置。游戏工具的“所有选项”标签页有自己的一套选项搜索。

## 键盘快捷键

macOS 上为 Cmd，其他平台为 Ctrl：

| 按键 | 操作 |
|---|---|
| 1 到 6 | 游戏、开发板、银行、GTS、控制、文档 |
| , | 设置 |
| Enter | “连接阶段”面板的“开始”，可按下时为“停止并开始” |
| . | 停止 |

## 放大文字

“设置”→“放大文字”会把所有文字放大 15 %（`gui/theme.py` 的 `text_scale`），在启动时读取。最浅的文字颜色 `#98989D` 在其最浅的底色上仍保持 4.8:1 的对比度。

## 进度

一次运行会打印 `[progress] DONE TOTAL UNIT TITLE`（`pokeldn.progress.show`，API 1.7；`UNIT` 为 `bytes` 或 `items`）来绘制进度条，显示已处理量、30 秒速率与剩余时间，每个标题每秒最多四行。`[save]` 行会绘制同样的进度条。

## 更新

启动时 App 会请求 `api.github.com/repos/Decryptu/pokeldn/releases/latest`（超时 5 秒）。若某个 `vX.Y.Z` 标签高于 `pokeldn.__version__`，会增加一个“更新”条目，提供“立即更新”或“下载”。

“立即更新”（`pokeldn.app.update`）会把平台归档与 `SHA256SUMS` 下载到 `update/`，校验和不符时拒绝，然后解包（`ditto -x -k`、`tarfile` 的 `data` 过滤器、`zipfile`），并启动 `pokeldn --apply-update NEW TARGET PID VERSION`（`gui/updating.py`）。该辅助程序会等待旧 App 退出（在 Windows 上还要等其进程退出），将其重命名为 `.<name>.old`，复制新版本并打开；任何失败都会还原旧 App。新 App 会读取一次 `update/outcome.json`。校验和只能发现损坏，并不能验证发行版的身份。

| 情况 | 行为 |
|---|---|
| 预发布、草稿、异常标签 | 不提供 |
| 没有网络 | “立即检查”会显示 GitHub 没有回应 |
| 在“设置”中关闭更新 | 启动时不发出请求 |
| 没有归档或 `SHA256SUMS`、从源码检出运行、App Translocation、文件夹不可写（macOS、Linux） | 仅提供下载 |
| Windows，`C:\Program Files` | “立即更新”需经 UAC（`ShellExecuteExW` 的 `runas`） |
| Windows，另一驱动器的根目录（`D:\pokeldn`） | “立即更新”无需 UAC：替换只会在 App 旁新增文件夹，而卷的根目录允许普通用户这样做。0.34.0 之前的发行版会用文件探测根目录，因此在那里要求 UAC，标准用户更新时会停在“Windows 没有授予 pokeldn 修改 D:\ 的权限”；从这样的发行版升级时，需要手动下载一次下一个版本 |
| Windows，映射驱动器或 `subst` 驱动器 | 会保留盘符；辅助程序用两种写法都能找到旧 App 的进程；需要 UAC 时，辅助程序拿到的是该盘符所指的文件夹，因为提权后的进程看不到用户会话映射的盘符 |
| App 文件夹中存在打包版不会附带的条目（桌面上散放着 `pokeldn.exe` 与 `_internal`） | 仅提供下载；辅助程序会拒绝来自旧 App 的同一文件夹，因为替换会把该文件夹重命名并整个删除 |
| 有连接阶段、烧录或清理正在进行 | 会要求先完成 |

`scripts/check_update.py ARCHIVE FOLDER` 会针对 127.0.0.1 测试打包版 App 的更新；`POKELDN_UPDATE_URL` 可以替换该端点（`tests/test_app_update.py`）。macOS 在 `/Applications` 中是否会请求 App 管理权限，尚未实测。

## 复制交换

交换的复制按钮会把同一只宝可梦插入为下一项交换。已创建的宝可梦会按相同的选择重新创建，因此副本拥有自己的 PID；《晶灿钻石／明亮珍珠》会拒绝存档中已存在该 PID 的交换请求。来自文件的宝可梦会逐字节复制。

## 文件拖放

| 目标 | 接受 |
|---|---|
| 交换中的宝可梦 | 宝可梦文件或 Showdown `.txt`；多余的文件会填入后续交换 |
| 添加交换 | 每个文件一项交换 |
| 礼物卡片 | `.pokegift`、`.wc8`、`.wc3` |
| 开发板固件卡片 | pokeldn 的 `.bin` |
| 任意路径输入框 | 该文件，或其所在文件夹 |

Flet 1.0.2 的客户端不支持拖放；`scripts/build_client.py` 会用 `gui/flet_drop`（[desktop_drop](https://pub.dev/packages/desktop_drop)）把 Flet 客户端构建到 `gui/client/<platform>`，使用 `python -m flet_cli.cli --version --json` 所报的 Flutter 版本，macOS 部署目标为 12.0。没有它时，`gui/main.py` 会运行 Flet 自带的客户端，不支持拖放。

## “文档”页面

“文档”页面会显示 App 使用指南以及本站所有可导航的页面；搜索按小节匹配，要求包含每个词，标题匹配优先（`gui/views/docs.py`）。

## 未发售作品

比 Switch 发售更早的作品，只有在从源码检出运行时才会出现在“游戏”“银行”与“文档”中（`pokeldn/app/preview.py`）。`POKELDN_PREVIEW=1` 可在任何情况下显示它，`0` 则隐藏。它的文档页面会设置 `nav_exclude` 与 `search_exclude`。

## 从源码运行

安装 Python 3.13 与 .NET 10 SDK：

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r gui/requirements.txt
dotnet build -c Release services/pkhex -warnaserror
python scripts/build_client.py    # optional: file drops; needs Flutter
python gui/main.py
```

Raspberry Pi OS 会把 piwheels 添加为软件包索引，而 piwheels 的 `flet_web-1.0.2-py3-none-any.whl`（25 KB）缺少 PyPI 的 wheel（27 MB）中所带的 `flet_web/web` 客户端；此时 App 会报 `RuntimeError: Web root path not found`。请只从 PyPI 安装该软件包：`python -m pip install --force-reinstall --no-cache-dir --index-url https://pypi.org/simple flet-web==1.0.2`。没有 Linux arm64 的发行版；Raspberry Pi 需要从源码运行 App。

源码检出中没有固件镜像。“开发板”页面上的“下载固件”会从最新的发行版连同 `SHA256SUMS` 获取所有镜像，并且只有在全部匹配时才写入。

## 构建桌面版 App

在已激活 ESP-IDF v6.1 的情况下，把每个镜像构建到 `gui/firmware`，然后打包：

```sh
mkdir -p gui/firmware
OUT="$PWD/gui/firmware"
cd firmware/esp32
for t in esp32:radio esp32s3:radio-s3 esp32c3:radio-c3 esp32c6:radio-c6; do
  chip=${t%%:*}; name=${t#*:}
  idf.py -B build/$chip -D SDKCONFIG="$PWD/build/$chip/sdkconfig" set-target $chip
  idf.py -B build/$chip -D SDKCONFIG="$PWD/build/$chip/sdkconfig" build
  idf.py -B build/$chip merge-bin -o "$OUT/pokeldn-$name.bin"
done
export POKELDN_BLE=1   # Bluetooth images for the iOS app (hardware_esp32.md, Bluetooth)
DEF="sdkconfig.defaults;sdkconfig.defaults.ble"
for t in esp32:ble esp32c6:ble-c6; do
  chip=${t%%:*}; name=${t#*:}
  idf.py -B build/$name -D SDKCONFIG="$PWD/build/$name/sdkconfig" -D SDKCONFIG_DEFAULTS="$DEF" set-target $chip
  idf.py -B build/$name -D SDKCONFIG="$PWD/build/$name/sdkconfig" -D SDKCONFIG_DEFAULTS="$DEF" build
  idf.py -B build/$name merge-bin -o "$OUT/pokeldn-radio-$name.bin"
done
unset POKELDN_BLE
for t in esp32:E32R40T esp32s3:SZPI; do   # the colour screen boards (hardware_esp32.md, The screen)
  chip=${t%%:*}; name=$(echo ${t#*:} | tr A-Z a-z)
  POKELDN_DISPLAY=${t#*:} idf.py -B build/$name -D SDKCONFIG="$PWD/build/$name/sdkconfig" set-target $chip
  POKELDN_DISPLAY=${t#*:} idf.py -B build/$name -D SDKCONFIG="$PWD/build/$name/sdkconfig" build
  idf.py -B build/$name merge-bin -o "$OUT/pokeldn-radio-$name.bin"
done
cd ../pad
idf.py -B build -D SDKCONFIG="$PWD/build/sdkconfig" set-target esp32s3
idf.py -B build -D SDKCONFIG="$PWD/build/sdkconfig" build
idf.py -B build merge-bin -o "$OUT/pokeldn-pad-s3.bin"
cd ../..
python scripts/build_client.py
python scripts/build_unicorn.py   # needs CMake
python scripts/pack_app.py
```

冻结版 App 的检查会确认每个镜像、`flet_drop` 客户端与 Unicorn 都已打包。版本号是 `pokeldn.__version__`，会随 `.github/release-notes.md` 一起提升，后者的第一行必须是 `# pokeldn X.Y.Z`（`tests/test_release.py`）。`v*` 标签会发布九个文件与 `SHA256SUMS`；只有带连字符的标签才是预发布。

这些 App 是单文件夹的 PyInstaller 构建（`pokeldn.app`；在其他平台上则是含 `_internal` 的 `pokeldn` 文件夹）：在 M4 上，“游戏”页面在 0.7 秒内打开，一次运行在 0.08 秒内启动。`scripts/pack_app.py` 在 Flet 的 `--onefile` 之后传入 `--onedir`，并设置 `LSBackgroundOnly`，使只有查看器拥有 Dock 图标。

| 部分 | 大小 | 保持小巧的方式 |
|---|---|---|
| Flet 查看器 | 31 MB（macOS 上 xz 压缩后 9.4 MB） | 不含可选扩展、单一架构、`--split-debug-info` |
| Unicorn | 3 MB | 仅保留 ARM 与 ARM64 引擎 |
| PKHeX 辅助程序 | 16 MB | 完全裁剪 |
| Python | 8 MB | 排除 web、图像、测试与语法模块；macOS 上执行 `strip -x` |

打包陷阱：

- 裁剪会禁用反射式 JSON；`JsonSerializerIsReflectionEnabledByDefault` 可恢复它。`DynamicDependency` 会保留 PKHeX.Core 的第三世代活动表。
- macOS 查看器的归档是 xz 压缩、命名为 `flet-macos.tar.gz`；`gui/flet_client.py` 会通过压缩探测打开它，并删除标记为 `pokeldn-drop` 的过期 `~/.flet/client` 文件夹。
- 永远不要对可执行文件或 PKHeX 辅助程序执行 strip：二者在 Mach-O 映像之后都附带一个归档。
- `scripts/pack_flet.py` 会保留查看器的授权项；没有 `com.apple.security.files.user-selected.read-write` 时，选择 `prod.keys` 会引发 `ENTITLEMENT_NOT_FOUND`。
- 在 Linux 上，`pokeldn/app/paths.py` 会恢复用户的 `LD_LIBRARY_PATH`（内置的 `libstdc++` 会破坏 Fedora 的 EGL），并设置 `FLET_LINUX_DISTRO`。
- Unicorn 在控制流保护下会以 `0xC0000409` 中止（[unicorn#2281](https://github.com/unicorn-engine/unicorn/issues/2281)）；打包脚本会清除 `pokeldn.exe` 中的 `GUARD_CF`（`0xC160` 改为 `0x8160`）。永远不要在冻结版检查中启用 `faulthandler`。
- 在 Windows 上，`pokeldn.exe` 是 GUI 子系统（子系统 2），不会打开控制台窗口。与其同目录的 `pokeldn-run.exe` 是同一文件、子系统为 3：每次运行、烧录与辅助程序都以管道和 `CREATE_NO_WINDOW` 启动它，因此它的日志能到达 App，而关闭 stdin 即可停止它。

### App 图标

`gui/AppIcon.icon` 是一个 Icon Composer 文稿，也是 macOS 与 iOS 图标的唯一来源。`actool`（Xcode 26）会把它编译为 `Assets.car` 与 `AppIcon.icns`；`scripts/pack_app.py` 会在设置 `CFBundleIconName` 的情况下把二者放入 `pokeldn.app` 与 Flet 查看器。macOS 26 会从目录中绘制分层图标；macOS 12 到 15 会绘制其扁平版本，这些版本对齐 Apple 的图标网格（图块占据 128 像素中的 102 像素）。Windows 使用 `gui/assets/icon.ico`，Linux 使用 `gui/assets/icon.png`，二者都是满版：两个平台都不会为图标留内边距。
