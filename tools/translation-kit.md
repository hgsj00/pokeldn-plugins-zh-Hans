# 翻译工作包（translation kit）

本目录是**给专用翻译工具/流程的输入与回写格式**。语言包的最终文本不在这里定稿，
工具产出后由 `tools/build_strings.py` 组装并校验。

## 文件

| 文件 | 内容 | 条数 |
| --- | --- | --- |
| `strings.jsonl` | 主界面字符串：键、英文、繁中参考、机器种子、占位符、批次、状态 | 1,945 |
| `messages.jsonl` | 模块原文 → 繁中参考（键即英文原文） | 1,773 |
| `help.jsonl` | `工具:--选项` → 英文说明 + 繁中参考 | 2,950（879 有参考，2,071 仅英文） |
| `terms.jsonl` | 术语（英文 → 繁中参考） | 114 |
| `templates.jsonl` | 动态模板（英文模板 → 繁中参考） | 68 |
| `proper-nouns.json` | 专有名词的 PKHeX 来源与“不得复制”规则 | — |

## strings.jsonl 字段

| 字段 | 说明 |
| --- | --- |
| `key` | 翻译键（不可改） |
| `en` | 英文原文（语义基准） |
| `zh_TW` | 繁中参考译文（语义参考，非简体用词依据） |
| `seed` | OpenCC + 术语替换生成的简体种子（**未审校**） |
| `zh_Hans` | **工具填写**：最终简体译文 |
| `placeholders` | 英文原文里的占位符原文（如 `{value0}`、`{value2:.0%}`），必须原样保留 |
| `batch` | 审校批次 1–6（见 `docs/workflow.md` §5.5） |
| `status` | `todo` / `seed` / `translated` / `reviewed` / `approved` / `skip` |
| `notes` | 工具或审校者的备注（可选） |

`messages/help/terms/templates` 的字段为 `key`（英文原文）、`zh_TW`、`seed`、`zh_Hans`、
`status`、`notes`。

## 回写契约

1. 只写 `zh_Hans`、`status`、`notes`，不动 `key`、`en`、`placeholders`。
2. `zh_Hans` 中的占位符必须与 `en` 完全一致（名称、数量、`:格式`、`!转换`、`{{`/`}}`）。
   允许移动位置，不允许改名、删除或新增。
3. 中文标点、空格、斜杠规则见 `docs/glossary.md` §6。
4. 专有名词（种类/招式/道具/特性/性格/属性/形态/奖章/游戏名/地点）**不要翻译**，
   也不要写进译文；界面显示时由 pokeldn 向 PKHeX 查询（`proper-nouns.json`）。
5. 状态语义：
   - `translated`：工具产出，待人工复核；
   - `reviewed`：人工复核过语义与术语；
   - `approved`：可发布；
   - `empty`：有意输出空字符串（例如 `plugins.plural_suffix` 的英文复数 `s`），
     简中应留空；
   - `skip`：有意保留英文（品牌、缩写、命令等），需在 `notes` 说明。
6. 工具可分批回写（同一文件用最后一行覆盖前一行也可以，按 `key` 去重）。

## 组装

```bash
python tools/build_strings.py --kit translation-kit --out language-pack
python tools/validate_pack.py language-pack --reference reference/strings.en.toml --traditional
```

`build_strings.py` 默认只收 `translated/reviewed/approved` 且 `zh_Hans` 非空的条目；
`--allow-seed` 时用 `seed` 兜底（仅用于预览，不可发布）。占位符不一致会让组装失败并列出键。
