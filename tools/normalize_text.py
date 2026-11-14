"""Normalise punctuation in every translation the kit holds.

    python tools/normalize_text.py --kit translation-kit [--check]

Mainland UI style: “ ” for quotes, … for ellipsis, and no 「」/『』/⋯. Idempotent; run it
after merging batches so different reviewers cannot leave mixed punctuation.
"""
import argparse
import json
import sys
from pathlib import Path

KINDS = ("strings", "messages", "templates", "terms", "help")
TABLE = str.maketrans({
    "「": "“", "」": "”", "『": "‘", "』": "’", "⋯": "…",
})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kit", type=Path, default=Path("translation-kit"))
    parser.add_argument("--check", action="store_true", help="report occurrences without writing")
    args = parser.parse_args(argv)

    changed_total = 0
    for kind in KINDS:
        path = args.kit / f"{kind}.jsonl"
        if not path.is_file():
            continue
        records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        changed = 0
        for record in records:
            value = record.get("zh_Hans") or ""
            normalised = value.translate(TABLE)
            if normalised != value:
                changed += 1
                if not args.check:
                    record["zh_Hans"] = normalised
        if changed:
            print(f"{kind}: {changed} value(s) normalised")
        changed_total += changed
        if not args.check:
            path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")
    if not changed_total:
        print("already normalised")
    return 1 if args.check and changed_total else 0


if __name__ == "__main__":
    sys.exit(main())
