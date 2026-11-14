"""Export a translation kit for an external tool (one JSONL record per string).

    python tools/export_kit.py --english reference/strings.en.toml \
        --zhtw ../repos/pokeldn-plugins-zhTW/language-pack \
        --seed ../work/seed --out translation-kit

The kit keeps every input a translation tool needs, and never decides wording itself:
  * `strings.jsonl`  — key, English, zh-TW reference, machine seed, placeholders, batch, status
  * `messages.jsonl`, `help.jsonl`, `terms.jsonl`, `templates.jsonl`
  * `proper-nouns.json` — where each proper-noun category comes from (PKHeX zh-Hans), and why
    the pack must not copy those lists
  * `README.md` — schema, statuses and the write-back contract

A tool fills `zh_Hans` and sets `status`; `tools/build_strings.py` assembles the pack and
rejects anything with a placeholder difference.
"""
import argparse
import json
import re
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    for candidate in (Path(__file__).resolve().parent / "pylib",
                      Path(__file__).resolve().parents[2] / "tools" / "pylib"):
        if (candidate / "tomllib.py").is_file():
            sys.path.insert(0, str(candidate))
            break
    import tomllib

# The six review batches of docs/workflow.md §5.5.
BATCHES = {
    1: ("app", "main", "command", "failure"),
    2: ("catalog", "games", "encounter"),
    3: ("settings", "plugins", "boards", "board", "controller"),
    4: ("pokemon", "bank", "saves", "gifts", "event_gifts", "received"),
    5: ("raid_seed", "raid_event", "raid_partners", "rewards"),
}
PLACEHOLDER = re.compile(r"\{[^{}]*\}")


def load(path: Path):
    return tomllib.loads(path.read_text(encoding="utf-8"))


def batch_of(key: str) -> int:
    prefix = key.split(".", 1)[0]
    for number, prefixes in BATCHES.items():
        if prefix in prefixes:
            return number
    return 6


def placeholders(text: str) -> list[str]:
    return PLACEHOLDER.findall(text)


def records(english: dict, zhtw: dict, seed: dict, *, with_batch: bool):
    for key, en in english.items():
        reference = zhtw.get(key, "")
        if key in zhtw and reference == "" and en:
            status, notes = "empty", "繁中参考有意留空（例如复数后缀），简中也应留空"
        else:
            status, notes = ("seed" if key in seed else "todo"), ""
        record = {
            "key": key,
            "en": en,
            "zh_TW": reference,
            "seed": seed.get(key, ""),
            "zh_Hans": "",
            "placeholders": placeholders(en),
            "status": status,
            "notes": notes,
        }
        if with_batch:
            record["batch"] = batch_of(key)
        yield record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--english", type=Path, default=Path("reference/strings.en.toml"))
    parser.add_argument("--zhtw", type=Path, required=True, help="zh-TW language-pack folder")
    parser.add_argument("--seed", type=Path, required=True, help="folder from tools/seed_from_zhtw.py")
    parser.add_argument("--help-keys", type=Path,
                        help="JSON from work/help_keys.py holding every tool option's English help")
    parser.add_argument("--out", type=Path, default=Path("translation-kit"))
    args = parser.parse_args(argv)

    english = load(args.english)
    args.out.mkdir(parents=True, exist_ok=True)

    strings = list(records(english, load(args.zhtw / "strings.toml"),
                           load(args.seed / "strings.toml"), with_batch=True))
    (args.out / "strings.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in strings), encoding="utf-8")

    for name in ("messages", "help", "terms", "templates"):
        source = load(args.zhtw / f"{name}.toml")
        seed = load(args.seed / f"{name}.toml") if (args.seed / f"{name}.toml").is_file() else {}
        if name == "help" and args.help_keys:
            upstream = json.loads(args.help_keys.read_text(encoding="utf-8"))["keys"]
            entries = []
            for key, english in upstream.items():
                reference = source.get(key, "")
                entries.append({"key": key, "en": english, "zh_TW": reference,
                                "seed": seed.get(key, ""), "zh_Hans": "",
                                "status": "empty" if key in source and reference == "" else
                                          ("seed" if key in seed else "todo"),
                                "notes": "繁中参考未覆盖，需从英文翻译" if key not in source else ""})
        else:
            entries = [{"key": key, "en": key, "zh_TW": value, "seed": seed.get(key, ""),
                        "zh_Hans": "", "status": "empty" if value == "" else ("seed" if key in seed else "todo"),
                        "notes": "繁中参考有意留空" if value == "" else ""}
                       for key, value in source.items()]
        (args.out / f"{name}.jsonl").write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in entries), encoding="utf-8")

    proper = {
        "policy": "专有名词一律采用 PKHeX 的简体中文；本语言包不复制、不改写这些名称。",
        "runtime": "pokeldn 在 locale=zh-Hans 时由 services/pkhex 向 PKHeX 查询名称，"
                   "按 gui/localization.py 的 DisplayService 显示；合法性报告同样如此。",
        "sources": {
            "species": "PKHeX.Core/Resources/text/other/zh-Hans/text_Species_zh-Hans.txt",
            "moves": "PKHeX.Core/Resources/text/other/zh-Hans/text_Moves_zh-Hans.txt",
            "abilities": "PKHeX.Core/Resources/text/other/zh-Hans/text_Abilities_zh-Hans.txt",
            "natures": "PKHeX.Core/Resources/text/other/zh-Hans/text_Natures_zh-Hans.txt",
            "types": "PKHeX.Core/Resources/text/other/zh-Hans/text_Types_zh-Hans.txt",
            "forms": "PKHeX.Core/Resources/text/other/zh-Hans/text_Forms_zh-Hans.txt",
            "ribbons": "PKHeX.Core/Resources/text/other/zh-Hans/text_Ribbons_zh-Hans.txt",
            "games": "PKHeX.Core/Resources/text/other/zh-Hans/text_Games_zh-Hans.txt",
            "items": "PKHeX.Core/Resources/text/items/text_Items_zh-Hans.txt",
            "balls": "PKHeX 由道具名派生（精灵球为道具编号），无需单独表",
            "locations": "PKHeX.Core/Resources/text/locations/gen*/text_*_zh-Hans.txt",
            "program_messages": "PKHeX.Core/Resources/text/program/MessageStrings_zh-Hans.txt",
        },
        "rules": [
            "不得把上述文件复制进本仓库或 .pokeplugin。",
            "不得为名称自造译名；界面里出现名称时交给 PKHeX 查询。",
            "术语表只收录机制词（异色、头目、个体值等），名称类不收录。",
        ],
        "pkhex_commit": "c758bac1082878eb2e439be1cd3b5cdfc26b5e04",
    }
    (args.out / "proper-nouns.json").write_text(
        json.dumps(proper, ensure_ascii=False, indent=2), encoding="utf-8")

    readme = Path(__file__).with_name("translation-kit.md")
    (args.out / "README.md").write_text(readme.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"{args.out}: strings {len(strings)}, batches 1-6, "
          f"resources messages/help/terms/templates exported")
    return 0


if __name__ == "__main__":
    sys.exit(main())
