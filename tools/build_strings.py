"""Assemble language-pack TOMLs from a translation kit, rejecting placeholder drift.

    python tools/build_strings.py --kit translation-kit --out language-pack
    python tools/build_strings.py --kit translation-kit --out ../work/preview --allow-seed

Only entries with a usable `zh_Hans` are written:
  * default: status `translated`, `reviewed` or `approved`, and `zh_Hans` non-empty;
  * `--allow-seed`: fall back to `seed` (status `seed`), for preview builds only.

Missing keys are reported, never invented. Any placeholder difference from the English
source is an error and stops the run (same rule as pokeldn's installer).
"""
import argparse
import json
import string
import sys
from pathlib import Path

USABLE = ("translated", "reviewed", "approved")
FILES = ("strings", "messages", "templates", "terms", "help")


def fields(text: str) -> set[str]:
    return {name for _, name, _, _ in string.Formatter().parse(text) if name is not None}


def read_jsonl(path: Path):
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def render(table: dict) -> str:
    return "".join(f"{json.dumps(k, ensure_ascii=False)} = {json.dumps(v, ensure_ascii=False)}\n"
                   for k, v in table.items())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--kit", type=Path, default=Path("translation-kit"))
    parser.add_argument("--out", type=Path, default=Path("language-pack"))
    parser.add_argument("--allow-seed", action="store_true", help="use the machine seed where nothing is translated")
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)

    errors, report = [], {}
    for name in FILES:
        kit = args.kit / f"{name}.jsonl"
        if not kit.is_file():
            print(f"skip {name}: no {kit}")
            continue
        picked, counts = {}, {"total": 0, "usable": 0, "seed": 0, "missing": 0, "skip": 0, "empty": 0}
        for record in read_jsonl(kit):
            key, en = record["key"], record.get("en", record["key"])
            counts["total"] += 1
            status = record.get("status", "")
            if status == "empty":
                picked[key] = ""                    # deliberate empty, e.g. a plural suffix
                counts["usable"] += 1
                counts["empty"] += 1
                continue
            value = record.get("zh_Hans", "") if status in USABLE else ""
            if not value and args.allow_seed and status in ("seed", "translated", "reviewed"):
                value = record.get("seed", "")
                counts["seed"] += value != ""
            if status == "skip":
                counts["skip"] += 1
                value = en                          # deliberately English
            if not value:
                counts["missing"] += 1
                continue
            if name in ("strings", "templates"):
                if fields(value) != fields(en):
                    errors.append(f"{name}[{key}]: placeholders {sorted(fields(value))} != {sorted(fields(en))}")
                    continue
            picked[key] = value
            counts["usable"] += 1
        (args.out / f"{name}.toml").write_text(render(picked), encoding="utf-8")
        report[name] = counts

    for name, counts in report.items():
        print(f"{name}: {counts['usable']}/{counts['total']} written "
              f"(seed {counts['seed']}, empty {counts['empty']}, missing {counts['missing']}, skip {counts['skip']})")
    for error in errors:
        print(f"ERROR: {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
