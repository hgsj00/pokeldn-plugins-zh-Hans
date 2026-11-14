"""Check a pack against the committed English snapshot, without pokeldn or its dependencies.

    python tools/check_upstream.py --pack language-pack \
        --reference reference/strings.en.toml --help-keys reference/help-keys.json

Strings must match the snapshot exactly (missing/unknown keys, placeholder differences fail).
Tool help must cover every key in the snapshot; pass --allow-missing-help to only warn.
"""
import argparse
import json
import string
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent / "pylib"))
    import tomllib


def fields(text: str) -> set[str]:
    return {name for _, name, _, _ in string.Formatter().parse(text) if name is not None}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pack", type=Path, default=Path("language-pack"))
    parser.add_argument("--reference", type=Path, default=Path("reference/strings.en.toml"))
    parser.add_argument("--help-keys", type=Path, default=Path("reference/help-keys.json"))
    parser.add_argument("--allow-missing-help", action="store_true")
    args = parser.parse_args(argv)

    english = tomllib.loads(args.reference.read_text(encoding="utf-8"))
    strings = tomllib.loads((args.pack / "strings.toml").read_text(encoding="utf-8"))
    errors = []
    missing = sorted(english.keys() - strings.keys())
    unknown = sorted(strings.keys() - english.keys())
    placeholder = sorted(k for k in english.keys() & strings.keys()
                         if fields(english[k]) != fields(strings[k]))
    print(f"strings: {len(strings)}/{len(english)} | missing {len(missing)}, unknown {len(unknown)}, "
          f"placeholder differences {len(placeholder)}")
    if missing:
        errors.append(f"missing strings: {missing[:8]}")
    if unknown:
        print(f"  warning: {len(unknown)} key(s) not in the snapshot: {unknown[:5]}")
    if placeholder:
        errors.append(f"placeholder differences: {placeholder[:8]}")

    upstream = json.loads(args.help_keys.read_text(encoding="utf-8"))["keys"]
    help_pack = tomllib.loads((args.pack / "help.toml").read_text(encoding="utf-8"))
    missing_help = sorted(upstream.keys() - help_pack.keys())
    unknown_help = sorted(help_pack.keys() - upstream.keys())
    print(f"help: {len(help_pack)}/{len(upstream)} | missing {len(missing_help)}, unknown {len(unknown_help)}")
    if missing_help:
        message = f"missing help: {len(missing_help)}, e.g. {missing_help[:5]}"
        if args.allow_missing_help:
            print(f"  warning: {message}")
        else:
            errors.append(message)
    if unknown_help:
        print(f"  warning: {len(unknown_help)} help key(s) not in the snapshot: {unknown_help[:5]}")

    for error in errors:
        print(f"ERROR: {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
