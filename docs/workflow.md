# 简体中文语言包：工作计划与工作流

面向 [Decryptu/pokeldn](https://github.com/Decryptu/pokeldn) 的简体中文（`zh-Hans`）语言包，
形态与 [jimmyorz/pokeldn-plugins-zhTW](https://github.com/jimmyorz/pokeldn-plugins-zhTW) 一致：
一个只含数据、可签名、可经 Sources 安装的 `.pokeplugin`。

- 本仓库 ID：`community-zh-hans`，locale：`zh-Hans`
- 当前基准：pokeldn **0.65.2**（commit `2bee2a1`），Plugins API **1.13**
- 翻译术语基准：PKHeX `zh-Hans` 资源（commit `c758bac`）

---

## 1. 目标与范围

### 1.1 交付物

| 交付物 | 位置 | 说明 |
| --- | --- | --- |
| 语言包源码 | `language-pack/` | `plugin.toml` + 5 个 TOML + `icon.png` |
| 可安装包 | `packages/pokeldn-zh-Hans-<版本>.pokeplugin` | ZIP，含 Ed25519 `plugin.sig` |
| 来源清单 | `pokeldn-source.json` | pokeldn 内 Sources 可订阅 |
| 术语表 | `docs/glossary.md` | 与 PKHeX 简体中文对齐 |
| 翻译工作包 | `translation-kit/` | 交给专用工具的 JSONL 与回写契约 |
| 维护与验证文档 | `docs/maintenance.md`、`docs/validation.md` | 每次发版更新 |
| 对照快照 | `reference/` | 英文基准、上游哈希 |

### 1.2 不在范围内

- 不修改 pokeldn 程序代码；不提交补丁给上游。
- 不翻译固件像素文字、无线通讯原始输出、`[done]` 行、文件名、路径、GTS 原始数据、设置存储值
  （上游设计如此，见 §3.6）。
- 不重新分发 PKHeX 的名称数据库；宝可梦/招式/道具等名称由 pokeldn 在运行时按 `zh-Hans`
  向 PKHeX 查询（见 §3.3）。

---

## 2. 已下载的仓库与基线

| 仓库 | 本地路径 | 版本 / commit | 用途 |
| --- | --- | --- | --- |
| `Decryptu/pokeldn` | `repos/pokeldn` | 0.65.2，`2bee2a1`，2026-11-14 | 目标程序、字符串模板、校验脚本 |
| `kwsch/PKHeX` | `repos/PKHeX` | `c758bac`，2026-11-13 | 简体中文术语与名称库 |
| `jimmyorz/pokeldn-plugins-zhTW` | `repos/pokeldn-plugins-zhTW` | 1.1.18，`cfb4840`，2026-11-14 | 结构参考 + 语义参考（繁中） |
| `BYVoid/OpenCC` | `repos/OpenCC` | `fae2a0a` | 繁→简转换词典（仅辅助，不入包） |

---

## 3. 机制结论（决定工作方式）

### 3.1 语言包是“数据插件”

`pokeldn/plugins.py` 在 `plugin.toml` 含 `locale` 或 `strings` 时按语言包读取：

```toml
id = "community-zh-hans"
name = "简体中文"
version = "1.0.0"
api = "1.13"
author = "…"
description = "简体中文语言包，术语对齐 PKHeX 简体中文。"
locale = "zh-Hans"
strings = "strings.toml"
messages = "messages.toml"
templates = "templates.toml"
terms = "terms.toml"
help = "help.toml"
font_family = "Noto Sans CJK SC"
```

- 资源必须是 `plugin.toml` 同级的单个 TOML 文件名；值必须是字符串。
- `strings` / `templates` 会做格式串校验：只允许具名占位符（`{value0}`、`{name!r}`），
  不允许属性/下标访问，宽度与精度 ≤ 999。
- 装好后在 **Settings → App language** 出现；切换后必须**完全退出并重启**两次
  （一次让包被识别，一次应用语言）。
- 包损坏或 TOML 非法时整体回退英文，因此校验必须前置。

### 3.2 查找链

`pokeldn.app.i18n.t(key, default, **fmt)`：

1. `strings.toml[key]`，缺失则用源码内联英文默认值；
2. 格式化失败（占位符缺失/类型不符）→ 回退英文；
3. 模块文本（`messages`）在显示边界单独走 `i18n.message()`：整句 → `templates` 模板 →
   按句切分 → `terms` 词边界替换；
4. 工具选项说明走 `help.toml`，键为 `工具KEY:--选项`。

### 3.3 PKHeX 名称自动本地化（关键）

`services/pkhex/Program.cs` 的 `DisplayLanguage()` 已把 `zh-Hans` 映射到 PKHeX 的
`zh-Hans`；`gui/localization.py` 的 `DisplayService` 在请求中带 `display_language`。
因此以下内容**不需要**写进语言包，切到简体中文后自动显示简体：

- 宝可梦种类、形态、招式、特性、道具、精灵球、性格、属性
- 遭遇地点、合法性报告、相遇方式、HOME 追踪码相关提示

本包只需覆盖 **pokeldn 自己的界面文字** 与 **模块英文消息**。

### 3.4 语言标签规则

`DisplayLanguage()`：`zh` + 任一 `hant/tw/hk/mo` → `zh-Hant`，否则 `zh-Hans`。
所以 `locale = "zh-Hans"` 是正确且唯一需要的写法；`zh-CN` 也可落为简体，但语义不如
`zh-Hans` 明确。

### 3.5 校验脚本

```bash
# 官方：列出缺失/多余键、占位符差异、help 缺失
python scripts/check_language_pack.py <语言包目录>     # 仅在占位符不一致时 exit 1
python scripts/extract_strings.py --check              # 英文模板是否与源码同步
```

`check_language_pack.py` 会导入 `pokeldn.app.catalog` 与每个工具的 `build_parser()`，
**必须**在装了依赖的 pokeldn 环境（Python 3.13）里跑。本机限制见 §9。

### 3.6 上游明确保留英文的部分

与繁中包相同的边界（详见繁中 `docs/translation.md`）：固件像素文字、无线测试原始输出、
ROM 写入进度标题、`[done]`、文件名/路径/银行摘要/GTS 原始数据/设置存储值、部分底层
诊断与第三方插件文本。翻译时不为这些硬造译文，验证文档里如实记录。

---

## 4. 工作量盘点

### 4.1 需翻译的条目（以 0.65.2 英文模板为准）

| 资源 | 条目 | 英文规模 | 说明 |
| --- | --- | --- | --- |
| `strings.toml` | **1,945** | 65,977 字符 | 含 348 条带占位符；35 条按上游惯例保留英文 |
| `messages.toml` | **1,773** | 约 3.1 万字符 | 键是英文原文，覆盖模块消息/配信/错误 |
| `help.toml` | **2,950 / 2,950** | 约 20 万字符 | 46 个工具的全部选项说明（含预览与诊断项） |
| `terms.toml` | **114** | 444 字符 | 术语级替换（词边界） |
| `templates.toml` | **68** | 1,787 字符 | 带具名字段的动态消息 |

繁中包 1.1.18 对 0.65.2 的键覆盖是 **1,945/1,945，缺失 0、多余 0、占位符差异 0**，
可作为完整性参照。

### 4.2 PKHeX 简体中文名称库（术语来源）

| 资源 | 条目 |
| --- | --- |
| 种类 `text_Species_zh-Hans.txt` | 1,026 |
| 招式 `text_Moves_zh-Hans.txt` | 921 |
| 特性 `text_Abilities_zh-Hans.txt` | 311 |
| 道具 `text_Items_zh-Hans.txt` | 2,595 |
| 性格 `text_Natures_zh-Hans.txt` | 25 |
| 属性 / 形态 / 奖章 / 游戏名 | 19 / 354 / 164 / 47 |
| 程序消息 `MessageStrings_zh-Hans.txt` | 281 行（设置/文件/存档口径） |

### 4.3 繁→简“机械转换”可行性（OpenCC t2s）

| 文件 | 条目 | 转换后变化 | 无需变化 | 转换后残留繁体字 |
| --- | --- | --- | --- | --- |
| strings | 1,945 | 1,606 | 339 | 0（修正后） |
| messages | 1,773 | 1,589 | 184 | 0 |
| help | 879 | 876 | 3 | 0 |
| templates | 68 | 64 | 4 | 0 |
| terms | 114 | 80 | 34 | 0 |

结论：**字形转换可一次性完成**，但台湾用词（程式/資訊/裝置/韌體/埠/群組/就緒…）不会
被 t2s 修正，必须再走一遍“大陆用词 + PKHeX 术语”替换与逐条审校（见 §5）。加入
`tools/vocab.toml` 的约 90 条用词替换后，`strings` 有 1,616 条与繁中原文不同；剩余问题
主要是句式与语境（如“设置精灵”→“设置向导”、“当机”→“崩溃”），需人工逐条确认。

---

## 5. 翻译策略

### 5.1 三层基线

1. **语义基线**：`reference/strings.en.toml` 的英文原文与键（唯一权威）。
2. **参考译文**：繁中包（语义已验证、键齐、术语成熟），用 OpenCC t2s 生成简体种子。
3. **专有名词基线**：种类、招式、特性、道具、精灵球、性格、属性、形态、奖章、游戏名、
   地点与合法性报告，**一律采用 PKHeX `zh-Hans`**；本包不翻译、不复制这些名称，
   由 pokeldn 在 `locale=zh-Hans` 时运行时查询（见 §3.3 与
   `translation-kit/proper-nouns.json`）。
4. **机制词基线**：PKHeX 已收录的（异色、头目、个体值、努力值、奋斗等级、初训家、
   配信、导入/导出…）直接采用；PKHeX 未收录的官方机制词（集友圈、蓝乐活、通信进化、
   太晶团体战、极巨团体战…）按官方简中。

> 采用繁中包作为语义起点时，本包属于其衍生作品，须沿用 **AGPL-3.0-or-later**，并在
> README/CHANGELOG 注明来源与转换方式。

### 5.2 处理顺序

```
英文键 + 繁中值
   ↓ OpenCC（TSPhrases → TSCharacters）
简体种子（字形正确、用词偏台）
   ↓ 术语替换表（docs/glossary.md，最长匹配、词边界保护）
大陆软件用词（文件/程序/信息/设备/固件/网络/默认/支持/用户/界面…）
   ↓ 逐条审校（对照英文，检查语义、变量、标点、空格、长度）
定稿 strings.toml
```

专有名词不进入这条流水线：工具只处理界面文字，遇到名称占位符（`{species}` 等）保持
变量不动；名称本身由 PKHeX 提供。

### 5.3 硬性规则（违反即失败）

- 占位符名称、数量、转换（`!r`）与格式规格（`:02X`）**原样保留**；允许移动位置。
- `{{` / `}}` 表示字面花括号，不得改成单个。
- 中文与英文/数字之间加半角空格（`USB 设备`、`ID 1234`）；全角标点用于中文句读。
- 斜杠任一侧为中文时用全角 `／`；两侧均为英文/数字时用半角 `/`。
- 数值范围与图号用半角连字符 `-`（`0-100`、`图 1-2`），不用 `～`。
- 不翻译：命令、路径、文件名、变量名、`pokeldn` 品牌、GTS/HP/BP/IV/EV 等缩写
  （按上下文保留缩写或首次出现给全称）。
- 不以“机器翻译感”直译；界面文字以简洁为主，按钮不超过原文长度太多。

### 5.4 关键术语（完整表见 `docs/glossary.md`）

| 英文 | 繁中参考 | 简体采用 | 依据 |
| --- | --- | --- | --- |
| Pokémon | 寶可夢 | 宝可梦 | 官方 / PKHeX |
| Shiny | 異色 | 异色 | PKHeX |
| Alpha | 頭目 | 头目 | PKHeX |
| IV / EV / AV / GV | 個體值／努力值／覺醒值／奮鬥等級 | 个体值／努力值／觉醒值／奋斗等级 | PKHeX |
| Ability / Hidden Ability | 特性／隱藏特性 | 特性／隐藏特性 | PKHeX |
| Move / Nature | 招式／性格 | 招式／性格 | PKHeX |
| OT / TID / SID | 初訓家／訓練家 ID／裏 ID | 初训家／训练家 ID／里 ID | PKHeX |
| Trade evolution | 通訊進化 | 通信进化 | 官方简中 |
| Max Raid / Tera Raid | 極巨團體戰／太晶團體戰 | 极巨团体战／太晶团体战 | 官方简中 |
| Dynamax Adventure | 極巨大冒險 | 极巨大冒险 | 官方简中 |
| Union Circle / Blueberry Quests | 集友圈／藍樂活任務 | 集友圈／蓝乐活任务 | 官方简中 |
| Mystery Gift | 神秘禮物 | 神秘礼物 | PKHeX |
| Save / Import / Export | 存檔／匯入／匯出 | 存档／导入／导出 | PKHeX |
| Plugin / Board / Firmware | 外掛／開發板／韌體 | 插件／开发板／固件 | 大陆习惯 + 官方硬件文档 |
| Legal / Illegal | 合法／不合法 | 合法／不合法 | 保留 |

### 5.5 分批方式（避免上下文过载）

按字符串键前缀分 6 批，每批 250–400 条，逐批校验后再合并：

1. `app` + `main` + `command` + `failure`（启动/错误）
2. `catalog` + `games` + `encounter`（工具目录/活动）
3. `settings` + `plugins` + `boards` + `controller`（设置/插件/开发板）
4. `pokemon` + `bank` + `saves` + `gifts` + `event_gifts`（宝可梦/银行/存档/礼物）
5. `raid_seed` + `raid_event` + `raid_partners` + `rewards`（团体战）
6. `gts` + 其余前缀

---

## 6. 目录与文件清单

```
pokeldn-plugins-zh-Hans/
├─ README.md                     # 安装、版本、范围（发布时更新）
├─ CHANGELOG.md                  # 每次发版
├─ LICENSE                       # AGPL-3.0-or-later（随包分发）
├─ .gitattributes / .gitignore
├─ pokeldn-source.json           # Sources 清单（发版时生成）
├─ language-pack/
│  ├─ plugin.toml                # 元数据（id/locale/api/资源名/字体）
│  ├─ strings.toml               # 1,945 条界面键值【核心】
│  ├─ messages.toml              # 1,773 条原文对照
│  ├─ templates.toml             # 68 条动态模板
│  ├─ terms.toml                 # 114 条术语
│  ├─ help.toml                  # 2,950 条工具选项说明
│  └─ icon.png                   # 96×96
├─ reference/
│  ├─ strings.en.toml            # 英文基准快照（SHA-256 入 upstream.json）
│  └─ upstream.json              # 上游版本/commit/哈希/条目数
├─ packages/                     # 已签名 .pokeplugin
├─ translation-kit/              # 交给专用工具的工作包（JSONL + 契约）
│  ├─ README.md                  # 字段、状态机、回写契约
│  ├─ strings.jsonl              # 1,945 条主字符串
│  ├─ messages.jsonl / help.jsonl / terms.jsonl / templates.jsonl
│  └─ proper-nouns.json          # 专有名词的 PKHeX 来源与规则
├─ docs/
│  ├─ workflow.md                # 本文件
│  ├─ glossary.md                # 术语表（EN / TW / CN / 依据）
│  ├─ maintenance.md             # 上游更新流程
│  └─ validation.md              # 每次验证记录
└─ tools/
   ├─ validate_pack.py           # 本地校验（TOML 层，可离线）
   ├─ seed_from_zhtw.py          # 繁中 → 简体种子生成
   ├─ vocab.toml                 # 台湾用词 → 大陆用词
   ├─ export_kit.py              # 生成 translation-kit/
   ├─ build_strings.py           # 工作包回写 → language-pack/*.toml
   └─ translation-kit.md         # 工作包说明模板
```

包内最终只有 9 个文件：`plugin.toml`、5 个 TOML、`LICENSE`、`icon.png`、`plugin.sig`。

---

## 7. 分阶段工作流

每个阶段都给出：输入 → 动作 → 产出 → 验收。标 ★ 的是质量门禁。

### 阶段 0：准备（已完成）

- 输入：三个仓库 + OpenCC
- 动作：浅克隆、锁定 commit、盘点键数、验证工具链
- 产出：`repos/`、`work/inventory.json`、本文件
- 验收：仓库 HEAD 与版本号记录在案；英中键数一致（1,945）

### 阶段 1：脚手架

- 动作：建立目录；写 `plugin.toml`；快照英文基准与上游哈希；本地校验脚本
- 产出：§6 的骨架、`reference/upstream.json`
- 验收：`reference/strings.en.toml` 的 SHA-256 = `93a3349a…0052`；`plugin.toml` 可被 TOML 解析

### 阶段 2：主字符串（最大工作量）

1. `tools/seed_from_zhtw.py` 生成 `work/seed/strings.toml`（t2s，不直接进包）。
2. 用 `docs/glossary.md` 做术语替换（脚本 + 人工复核）。
3. 按 §5.5 六批逐条审校：语义、占位符、标点、空格、长度、上下文。
4. 每批完成后跑 `tools/validate_pack.py`（键覆盖/占位符）。

- 产出：`language-pack/strings.toml`
- 验收 ★：1,945 键齐全；缺失 0 / 多余 0 / 占位符差异 0；无残留繁体字；35 条保留英文项与
  繁中包一致（或不冲突）

### 阶段 3：补充资源

- `terms.toml`：先落术语表，再做词边界回归（避免把“宝可梦”拆开）。
- `templates.toml`：逐条核对 1–8 个具名字段，字面分隔符不得丢失。
- `messages.toml`：按模块分批（配信、错误、GTS、银行、开发板、工具）。
- `help.toml`：优先 7 个内置游戏的常用交换/配信/团体战/集线器选项（约 800–900 条），
  其余诊断项按上游允许回退英文并在 `docs/validation.md` 记录。

- 验收 ★：TOML 全部可解析；模板字段集合与英文完全一致；术语键长 1–200、总数 ≤ 10,000

### 阶段 4：图标、许可与文档

- 96×96 PNG 图标（方形，简体中文视觉标识，不使用任天堂素材）。
- `LICENSE` = AGPL-3.0-or-later；README/CHANGELOG 注明衍生自繁中包与 pokeldn。
- 填写 `docs/glossary.md`、`docs/maintenance.md`。

### 阶段 5：本地校验

```powershell
# 结构 + 键 + 占位符 + 资源格式（离线）
python tools/validate_pack.py language-pack --reference reference/strings.en.toml

# 有完整环境时（Python 3.13 + requirements）：
python repos/pokeldn/scripts/check_language_pack.py language-pack
python repos/pokeldn/scripts/extract_strings.py --check
```

- 验收 ★：本地校验 0 错误；官方脚本 `placeholders differ: 0`、缺失 0、多余 0
- 冒烟：`POKELDN_PLUGINS=<包目录> python gui/main.py` 检查设置页、工具目录、弹窗、
  开发板页、银行页的截断与排版

> 首次本地实测（2026-11-14）已完成：用已安装的 pokeldn 0.63.1 + 隔离 `POKELDN_DATA`
> 启动预览包，界面完整显示简体中文；截图与缺陷记录见 `docs/validation.md`。
> 尚未做 `.pokeplugin` 安装向导、签名包与 0.65.2 复测。

### 阶段 6：打包与签名

```bash
python repos/pokeldn/scripts/pack_plugin.py language-pack \
  -o packages/pokeldn-zh-Hans-1.0.0.pokeplugin --key <私钥>.pem
```

- 验收 ★：9 个文件；签名可验证；包内无 README/docs/私钥；记录指纹与 SHA-256
- 私钥不入库；首次生成后离线备份；后续版本必须同一把钥匙

### 阶段 7：安装验证（隔离数据目录）

```powershell
$env:POKELDN_DATA = "$PWD\work\verify-data"
```

1. 全新目录安装包 → 启用 → 选“简体中文” → 退出 → 重启 → 界面为简体。
2. 覆盖升级：先装旧版再装新版，确认保留启用状态与语言选择。
3. 抽查：`Settings`、`Plugins`、`Games`、宝可梦摘要、配信向导、银行、团体战页面。
4. 记录到 `docs/validation.md`（未跑项如实写“未执行”）。

### 阶段 8：发布

- 更新 `README.md`（版本、日期、对应 pokeldn 版本、下载链接）。
- 更新 `CHANGELOG.md`。
- 生成 `pokeldn-source.json`：`download`、`sha256`、`size`、`icon`。
- 推送 `packages/` 与清单；验证 raw 链接可下载、SHA-256 一致。
- CI：GitHub Actions（ubuntu + Python 3.13，零第三方依赖）跑离线校验、与提交快照的覆盖比对、
  kit 与语言包一致性、包结构与签名验证，作为每次 PR 的门禁。

---

## 8. 质量门禁汇总

| 门禁 | 阈值 | 工具 |
| --- | --- | --- |
| 主字符串键覆盖 | 缺失 0 / 多余 0 | `validate_pack.py`、官方脚本 |
| 占位符一致 | 差异 0（含格式规格） | 同上 |
| 资源 TOML 合法性 | 全部可解析、值为字符串 | `validate_pack.py` |
| 模板字段 | 每条 1–8 个具名、字段集相同 | `validate_pack.py` |
| 残留繁体字 | 0（白名单外） | `validate_pack.py --traditional` |
| 包结构 | 9 文件、签名有效、无敏感文件 | `pack_plugin.py` + 解压核对 |
| UI 冒烟 | 关键页面无截断/串行 | 人工 |
| 上游同步 | 基准 commit 与哈希可追溯 | `reference/upstream.json` |

---

## 9. 本机环境与限制（重要）

| 事项 | 现状 | 影响 / 对策 |
| --- | --- | --- |
| Python | 系统 3.10；DSH 自带 3.12 | pokeldn 要求 3.13；本地只做 TOML 层工作 |
| 依赖安装 | PyPI、raw.githubusercontent 均被阻断（仅 git 协议可用） | 无法 `pip install`；CI 改用零依赖快照校验 |
| pokeldn 运行 | 本机已有安装版（路径略） | 可做界面观感检查，但不能跑源码校验 |
| 兼容层 | `tools/pylib`（`tomllib` 垫片 + 第三方库占位） | **仅工具用**，不参与打包、不进入仓库发布物 |
| 繁简转换 | 无 OpenCC wheel，改用其词典自实现 t2s | 结果已量化（§4.3），足够做种子 |

因此本地流程是“TOML 校验 + 种子生成 + 人工审校”，最终门禁由 CI 的零依赖校验执行；官方脚本在装有 3.13 依赖的环境补充运行。

---

## 10. 风险与对策

| 风险 | 表现 | 对策 |
| --- | --- | --- |
| 台湾用词残留 | “程式/資訊/韌體/埠” | 术语替换表 + `--traditional` 检查 + 分批人工复核 |
| 术语漂移 | 同一英文多种译法 | 单一 `docs/glossary.md` 为准，PR 必须引用条目 |
| 占位符破坏 | 运行时抛错回退英文 | 校验脚本 + 禁止手改变量名 |
| UI 截断 | 按钮/标签过长 | 抽查 + 优先短译；必要时用缩写并在术语表登记 |
| 上游漂移 | 新版本新增键 | `maintenance.md` 增量流程；`upstream.json` 记基线 |
| 签名失控 | 更新被判“他人签名” | 私钥离线备份；指纹写进 README；不自动生成新钥 |
| 授权 | 衍生繁中译文 | 全包 AGPL-3.0-or-later，注明来源；不含 PKHeX 名称库 |

---

## 11. 里程碑与估算

| 阶段 | 内容 | 估算（人日） |
| --- | --- | --- |
| 0 | 准备与盘点 | 0.5（已完成） |
| 1 | 脚手架与工具 | 0.5 |
| 2 | 主字符串 1,945 条 | 3.0 |
| 3 | messages/help/terms/templates | 3.5 |
| 4 | 图标与文档 | 0.5 |
| 5 | 校验与冒烟 | 1.0 |
| 6–7 | 打包、签名、安装验证 | 1.0 |
| 8 | 发布与 CI | 0.5 |
| **合计** | | **≈10.5 人日** |

借助 AI 批量生成与脚本校验，实际日历时间可压缩到 3–5 天；瓶颈在人工抽查与术语一致性。

---

## 12. 已确认的决策（2026-11-14）

| 议题 | 决定 | 落地方式 |
| --- | --- | --- |
| 专有名词 | **全部采用 PKHeX 简体中文**，不自译、不复制名称库 | `translation-kit/proper-nouns.json` 记录来源与规则；运行时由 pokeldn 查询 |
| 其余界面文本 | **先整理留档，交由专用工具完成** | `translation-kit/`（JSONL + 契约）；`tools/build_strings.py` 负责回写组装 |
| 翻译基线 | 英文为语义基准，繁中作参考，机器种子仅作预览 | `strings.jsonl` 同时保留 `en` / `zh_TW` / `seed` |
| 推进节奏 | **翻译已完成（2026-11-14）** | 五类资源全部中文；发布相关（签名/Sources/版本号）待定 |
| 署名 | `pokeldn 社区`（占位，发布前替换） | `language-pack/plugin.toml` 的 `author` |

## 13. 翻译工作包（交给专用工具的接口）

`translation-kit/` 是阶段 2 的实际输入，格式见 `translation-kit/README.md`：

| 文件 | 用途 |
| --- | --- |
| `strings.jsonl` | 1,945 条：`key` / `en` / `zh_TW` / `seed` / `zh_Hans`（待填）/ `placeholders` / `batch` / `status` |
| `messages.jsonl`、`help.jsonl`、`terms.jsonl`、`templates.jsonl` | 补充资源，同样保留英文与繁中参考 |
| `proper-nouns.json` | 各专有名词类别的 PKHeX 源文件、运行时机制、禁止复制的规则 |
| `README.md` | 字段说明、状态机（`translated/reviewed/approved/empty/skip`）与回写契约 |

工具只需填写 `zh_Hans` 与 `status`，然后：

```bash
python tools/build_strings.py --kit translation-kit --out language-pack
python tools/validate_pack.py language-pack --reference reference/strings.en.toml \
  --traditional ../repos/OpenCC/data/dictionary/TSCharacters.txt
```

`build_strings.py` 会拒绝任何占位符差异；默认只收 `translated/reviewed/approved`，
`--allow-seed` 仅用于生成预览包。

> 工具产出仍须人工抽查术语与语气；`reviewed`/`approved` 状态应由复核者设置，
> 不能由生成工具自行升级。

当前工作包状态：

| 资源 | 条目 | 状态 |
| --- | --- | --- |
| strings | 1,945 | 1,944 reviewed + 1 empty |
| messages | 1,773 | 1,772 reviewed + 1 empty |
| templates / terms | 68 / 114 | 全部 reviewed |
| help | 2,950 | 2,234 translated + 716 reviewed |

## 14. 上游更新（每次 pokeldn 发版）

```bash
# 1. 更新代码并枚举新的工具选项
git -C ../repos/pokeldn pull
python -O ../work/help_keys.py                    # 生成 work/help-keys.json

# 2. 同步工作包：新增 todo、改动 stale、删除 removed，并刷新 reference/
python tools/update_upstream.py --pokeldn ../repos/pokeldn \
  --reference reference/strings.en.toml --kit translation-kit \
  --help-keys ../work/help-keys.json --apply

# 3. 翻译新增/改动条目（工作包逐条回写），合并
python tools/merge_reviews.py --kind strings --inputs ../work/review/strings-*.jsonl
python tools/merge_reviews.py --kind help --inputs ../work/help-trans/*.jsonl \
  --unique ../work/help-unique.json

# 4. 统一标点、组装、校验、打包
python tools/normalize_text.py
python tools/status.py
python tools/build_strings.py --kit translation-kit --out language-pack
python tools/validate_pack.py language-pack --reference reference/strings.en.toml \
  --traditional ../repos/OpenCC/data/dictionary/TSCharacters.txt
python ../repos/pokeldn/scripts/pack_plugin.py language-pack -o packages/… --key …
```

只翻译新增/改动条目，不重译未变条目；`status.py` 的 `stale` 数即本次需要复核的量。
