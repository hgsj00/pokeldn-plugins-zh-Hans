"""Sync the kit with a newer pokeldn checkout, keeping every existing translation.

    python tools/update_upstream.py --pokeldn ../repos/pokeldn \
        --reference reference/strings.en.toml --kit translation-kit --help-keys ../work/help-keys.json --apply

Without --apply it only reports. With --apply it:
  * replaces reference/strings.en.toml with the checkout's template;
  * appends new string keys as `todo`;
  * marks changed English defaults `stale` (the translation is kept for review);
  * marks removed keys `removed`;
  * does the same for help keys when --help-keys is given.

Run `tools/status.py` afterwards, then `tools/build_strings.py` and `validate_pack.py`.
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent / "pylib"))
    import tomllib


def read_kit(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_kit(path: Path, records):
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pokeldn", type=Path, required=True, help="pokeldn checkout")
    parser.add_argument("--reference", type=Path, default=Path("reference/strings.en.toml"))
    parser.add_argument("--kit", type=Path, default=Path("translation-kit"))
    parser.add_argument("--help-keys", type=Path, help="JSON from work/help_keys.py for the new checkout")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    upstream = args.pokeldn / "pokeldn" / "app" / "data" / "strings.en.toml"
    new = tomllib.loads(upstream.read_text(encoding="utf-8"))
    old = tomllib.loads(args.reference.read_text(encoding="utf-8")) if args.reference.is_file() else {}

    added = sorted(new.keys() - old.keys())
    removed = sorted(old.keys() - new.keys())
    changed = sorted(k for k in old.keys() & new.keys() if old[k] != new[k])
    print(f"strings: {len(old)} -> {len(new)} | added {len(added)}, removed {len(removed)}, changed {len(changed)}")
    for label, keys in (("added", added), ("removed", removed), ("changed", changed)):
        for key in keys[:10]:
            print(f"  {label}: {key}")
        if len(keys) > 10:
            print(f"  {label}: ... and {len(keys) - 10} more")

    if not args.apply:
        return 0

    records = {record["key"]: record for record in read_kit(args.kit / "strings.jsonl")}
    for key in added:
        records[key] = {"key": key, "en": new[key], "zh_TW": "", "seed": "", "zh_Hans": "",
                        "placeholders": [], "status": "todo", "notes": "new upstream key", "batch": 6}
    for key in changed:
        records[key]["en"] = new[key]
        if records[key].get("status") in ("translated", "reviewed", "approved"):
            records[key]["status"] = "stale"
            records[key]["notes"] = "English text changed upstream"
    for key in removed:
        records[key]["status"] = "removed"
    order = {key: index for index, key in enumerate(new)}
    ordered = sorted(records.values(), key=lambda r: order.get(r["key"], len(order)))
    write_kit(args.kit / "strings.jsonl", ordered)

    shutil.copyfile(upstream, args.reference)
    print(f"applied: reference updated, kit strings {len(ordered)} entries")

    if args.help_keys:
        new_help = json.loads(args.help_keys.read_text(encoding="utf-8"))["keys"]
        help_path = args.kit / "help.jsonl"
        help_records = {r["key"]: r for r in read_kit(help_path)}
        help_added = sorted(new_help.keys() - help_records.keys())
        help_removed = sorted(help_records.keys() - new_help.keys())
        for key in help_added:
            help_records[key] = {"key": key, "en": new_help[key], "zh_TW": "", "seed": "",
                                 "zh_Hans": "", "status": "todo", "notes": "new upstream option"}
        for key in help_removed:
            help_records[key]["status"] = "removed"
        for key in new_help.keys() & help_records.keys():
            help_records[key]["en"] = new_help[key]
        write_kit(help_path, [help_records[k] for k in sorted(help_records)])
        print(f"applied help: added {len(help_added)}, removed {len(help_removed)}, total {len(help_records)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
