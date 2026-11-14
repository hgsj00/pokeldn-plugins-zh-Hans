"""Coverage report for the translation kit (what is translated, reviewed, or still English).

    python tools/status.py --kit translation-kit --reference reference/strings.en.toml
"""
import argparse
import json
import string
import sys
from collections import Counter
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent / "pylib"))
    import tomllib

KINDS = ("strings", "messages", "templates", "terms", "help")


def fields(text: str) -> set[str]:
    return {name for _, name, _, _ in string.Formatter().parse(text) if name is not None}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kit", type=Path, default=Path("translation-kit"))
    parser.add_argument("--reference", type=Path, default=Path("reference/strings.en.toml"))
    args = parser.parse_args(argv)

    english = tomllib.loads(args.reference.read_text(encoding="utf-8")) if args.reference.is_file() else {}
    total_bad = 0
    for kind in KINDS:
        path = args.kit / f"{kind}.jsonl"
        if not path.is_file():
            print(f"{kind}: missing kit file")
            continue
        records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        counts = Counter(record.get("status", "?") for record in records)
        ready = sum(counts[s] for s in ("translated", "reviewed", "approved", "empty", "skip"))
        print(f"{kind:10} {len(records):5} entries | ready {ready:5} | " +
              " ".join(f"{key}={value}" for key, value in sorted(counts.items())))
        if kind == "strings" and english:
            keys = {record["key"] for record in records}
            missing = sorted(english.keys() - keys)
            extra = sorted(keys - english.keys())
            print(f"{'':10} vs reference: missing {len(missing)}, unknown {len(extra)}")
            if missing:
                print("           e.g.", missing[:5])
            total_bad += len(missing)
        for record in records:
            if record.get("status") in ("translated", "reviewed", "approved") and record.get("zh_Hans"):
                if kind in ("strings", "templates") and fields(record["zh_Hans"]) != fields(record["en"]):
                    print(f"  placeholder mismatch: {record['key']}")
                    total_bad += 1
    return 1 if total_bad else 0


if __name__ == "__main__":
    sys.exit(main())
