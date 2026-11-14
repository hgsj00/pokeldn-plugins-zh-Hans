# 上游更新流程

本文件说明 pokeldn 发新版后如何同步语言包。结构遵循
[繁中语言包的维护方式](https://github.com/jimmyorz/pokeldn-plugins-zhTW/blob/main/docs/maintenance.md)，
但基准值以本仓库 `reference/upstream.json` 为准。

## 基准与对照

| 文件 | 对照方式 |
| --- | --- |
| `strings.toml` | 与 `reference/strings.en.toml` 的键逐一配对 |
| `messages.toml` | 英文原文 → 中文；部分与主字符串重叠 |
| `help.toml` | `工具 ID:选项` → 说明 |
| `terms.toml` | 完整英文术语 → 中文术语 |
| `templates.toml` | 带具名变量的英文模板 → 中文模板 |

## 更新步骤

1. **核对基准**：确认 `reference/strings.en.toml` 的 SHA-256 与
   `reference/upstream.json` 记录一致；不一致时先查明原因，不得直接覆盖。
2. **取上游差异**：从基准 commit 到最新 `main`，只看变更文件：
   新增/删除/改名的键、原文变化、占位符或格式规格变化、`help` 的选项增删。
3. **增量翻译**：只处理变化条目；沿用 `docs/glossary.md` 的术语。
4. **检查补充资源**：新功能里的模块消息、模板、工具选项是否可译；`messages`/`help` 的键
   是否被上游改掉（键是原文/工具 ID，改名即失效）。
5. **更新基准快照**：重新生成 `reference/strings.en.toml` 与 `reference/help-keys.json`
   （`work/help_keys.py`），否则 CI 仍按旧版比对。
6. **校验**：
   ```bash
   python tools/validate_pack.py language-pack --reference reference/strings.en.toml
   # 有完整环境时
   python scripts/check_language_pack.py language-pack
   ```
7. **更新文档**：README 的版本/日期/对应 pokeldn 版本；`docs/validation.md` 记录本次检查；
   `CHANGELOG.md` 写用户可见变化。
8. **打包签名**（版本号必须递增）：
   ```bash
   python scripts/pack_plugin.py language-pack -o packages/pokeldn-zh-Hans-<版本>.pokeplugin --key <私钥>.pem
   ```
9. **更新清单**：`pokeldn-source.json` 的版本、API、下载 URL、大小、SHA-256、图标 URL。
10. **更新 `reference/upstream.json`**：pokeldn 版本/commit/日期、英文模板哈希、条目数、
   包哈希、语言包版本。

## 版本纪律

- 已发布的 `.pokeplugin` 保留原始字节，不覆盖；修复用新版本号。
- 签名私钥不入库、不上传；打包前确认私钥存在且指纹与 README 记录一致。
- 仅当上游变更影响语言包（字符串、API、资源机制、打包格式）时才发版；
  纯程序修复、测试、文档、AltStore 清单更新不构成发版理由。
