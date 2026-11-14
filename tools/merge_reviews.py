"""Merge batch review/translation output back into the translation kit.

    python tools/merge_reviews.py --kit translation-kit --kind strings \
        --inputs "../work/review/strings-*.jsonl" --status reviewed
    python tools/merge_reviews.py --kit translation-kit --kind help \
        --inputs "../work/help-trans/*.jsonl" --unique ../work/help-unique.json --status reviewed

Input lines are JSON objects: {"key": ...} or {"en": ...} or {"i": ...}, plus {"zh": ...}.
`i` indexes the file named by --unique (the deduplicated English list). Placeholders must match
the English source; a mismatch is reported and that entry is left untouched.
"""
import argparse
import json
import string
import sys
from pathlib import Path


def fields(text: str) -> set[str]:
    return {name for _, name, _, _ in string.Formatter().parse(text) if name is not None}


def read_lines(paths):
    for path in paths:
        with open(path, encoding="utf-8") as handle:
            for number, line in enumerate(handle, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    yield path, number, json.loads(line)
                except json.JSONDecodeError as error:
                    print(f"skip {path}:{number}: {error}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--kit", type=Path, default=Path("translation-kit"))
    parser.add_argument("--kind", required=True, choices=("strings", "messages", "help", "terms", "templates"))
    parser.add_argument("--inputs", nargs="+", required=True, type=Path)
    parser.add_argument("--unique", type=Path, help="JSON list of deduplicated English texts, for i-indexed input")
    parser.add_argument("--status", default="reviewed")
    args = parser.parse_args(argv)

    unique = json.loads(args.unique.read_text(encoding="utf-8")) if args.unique else []
    translated, errors = {}, []
    for path, number, obj in read_lines(args.inputs):
        zh = obj.get("zh")
        if not isinstance(zh, str) or not zh:
            continue
        if "key" in obj:
            translated[obj["key"]] = zh
        elif "en" in obj:
            translated[obj["en"]] = zh
        elif "i" in obj and 0 <= obj["i"] < len(unique):
            translated[unique[obj["i"]]] = zh
        else:
            print(f"skip {path}:{number}: no key/en/i")

    path = args.kit / f"{args.kind}.jsonl"
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    used = 0
    for record in records:
        source = record.get("en", record["key"])
        zh = translated.get(record["key"]) or translated.get(source)
        if not zh:
            continue
        if args.kind in ("strings", "templates") and fields(zh) != fields(source):
            errors.append(f"{record['key']}: placeholders {sorted(fields(zh))} != {sorted(fields(source))}")
            continue
        record["zh_Hans"] = zh
        record["status"] = args.status
        used += 1
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")
    print(f"{args.kind}: merged {used}/{len(records)} entries from {len(list(args.inputs))} file(s)")
    for error in errors:
        print("ERROR:", error)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
