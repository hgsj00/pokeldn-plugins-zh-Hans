"""Offline checks for a pokeldn language pack (no pokeldn runtime needed).

    python tools/validate_pack.py language-pack --reference reference/strings.en.toml
    python tools/validate_pack.py repos/pokeldn-plugins-zhTW/language-pack \
        --reference pokeldn-plugins-zh-Hans/reference/strings.en.toml --traditional

Mirrors the rules pokeldn applies at install time (pokeldn/app/i18n.py) plus key coverage
against the English template. Exits 1 on any error; warnings do not fail the run.
"""
import argparse
import json
import re
import string
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:                                  # Python 3.10
    for candidate in (Path(__file__).resolve().parent / "pylib",
                      Path(__file__).resolve().parents[2] / "tools" / "pylib"):
        if (candidate / "tomllib.py").is_file():
            sys.path.insert(0, str(candidate))
            break
    import tomllib


RESOURCES = ("messages", "templates", "terms", "help")


def load(path: Path):
    return tomllib.loads(path.read_text(encoding="utf-8"))


def fields(text: str) -> set[str]:
    return {name for _, name, _, _ in string.Formatter().parse(text) if name is not None}


def check_format(value: str, errors: list, where: str) -> None:
    """The rules of pokeldn.app.i18n._table(formatted=True)."""
    try:
        for _, field, spec, _ in string.Formatter().parse(value):
            if field is None:
                continue
            if not field.isidentifier():
                errors.append(f"{where}: placeholder {field!r} must be a plain name")
            elif "{" in spec or "}" in spec:
                errors.append(f"{where}: placeholder {field!r} has nested braces")
            elif re.search(r"\d{4}", spec):
                errors.append(f"{where}: placeholder {field!r} width/precision above 999")
    except ValueError as error:
        errors.append(f"{where}: invalid format string: {error}")


def check_templates(table: dict, errors: list) -> None:
    for source, target in table.items():
        if len(source) > 2048:
            errors.append(f"templates: source longer than 2048 characters: {source[:40]}...")
        for side, text in (("source", source), ("target", target)):
            check_format(text, errors, f"templates {side}")
            names, previous = [], False
            try:
                for literal, name, spec, conversion in string.Formatter().parse(text):
                    if name is not None:
                        if not name.isidentifier() or spec or conversion:
                            errors.append(f"templates {side}: use plain named fields: {text[:40]}...")
                        if previous and not literal:
                            errors.append(f"templates {side}: fields need literal text between them: {text[:40]}...")
                        names.append(name)
                    previous = name is not None
            except ValueError as error:
                errors.append(f"templates {side}: invalid template: {error}")
                continue
        if not 1 <= len(fields(source)) <= 8:
            errors.append(f"templates: need 1 to 8 named fields: {source[:40]}...")
        if fields(source) != fields(target):
            errors.append(f"templates: fields differ from English: {source[:40]}... "
                          f"{sorted(fields(source))} != {sorted(fields(target))}")


def traditional_map(path: Path) -> dict[str, str]:
    """Traditional character -> its usual simplified form, from OpenCC's TSCharacters."""
    table = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        source, _, target = line.partition("\t")
        target = target.split(" ")[0] if target else ""
        if len(source) == 1 and target and target != source:
            table[source] = target
    return table


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pack", type=Path, help="folder holding plugin.toml")
    parser.add_argument("--reference", type=Path, help="English strings.en.toml to compare keys against")
    parser.add_argument("--traditional", nargs="?", const=Path("repos/OpenCC/data/dictionary/TSCharacters.txt"),
                        type=Path, help="report leftover Traditional characters using this OpenCC table")
    parser.add_argument("--json", action="store_true", help="print a JSON report")
    args = parser.parse_args(argv)

    errors, warnings, report = [], [], {}
    pack: Path = args.pack.resolve()
    meta_path = pack / "plugin.toml"
    if not meta_path.is_file():
        print(f"{pack}: no plugin.toml")
        return 1
    try:
        meta = load(meta_path)
    except Exception as error:                                # noqa: BLE001 - report anything
        print(f"plugin.toml does not parse: {error}")
        return 1

    for key in ("id", "name", "version", "api", "locale"):
        if key not in meta:
            errors.append(f"plugin.toml: missing {key}")
    if not re.fullmatch(r"[a-z0-9._-]+", str(meta.get("id", ""))):
        errors.append("plugin.toml: id must be lowercase letters, digits, dots, dashes or underscores")
    if not re.fullmatch(r"[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*", str(meta.get("locale", ""))):
        errors.append("plugin.toml: locale must be a BCP 47 tag such as zh-Hans")

    tables = {}
    for kind in ("strings",) + RESOURCES:
        name = meta.get(kind)
        if not name:
            if kind == "strings":
                errors.append("plugin.toml: missing strings")
            continue
        path = pack / name
        if not path.is_file():
            errors.append(f"plugin.toml: {kind} names a missing file: {name}")
            continue
        try:
            tables[kind] = load(path)
        except Exception as error:                            # noqa: BLE001
            errors.append(f"{name} does not parse: {error}")
            continue
        bad = [key for key, value in tables[kind].items() if not isinstance(value, str)]
        if bad:
            errors.append(f"{name}: {len(bad)} non-text value(s), e.g. {bad[0]}")
        report[kind] = len(tables[kind])

    strings = tables.get("strings", {})
    for key, value in strings.items():
        check_format(value, errors, f"strings[{key}]")

    if "templates" in tables:
        check_templates(tables["templates"], errors)
    if "terms" in tables:
        terms = tables["terms"]
        if len(terms) > 10000:
            errors.append("terms: more than 10000 entries")
        for key in terms:
            if not key or len(key) > 200:
                errors.append(f"terms: key must be 1 to 200 characters: {key[:40]!r}")

    documents = str(meta.get("documents", ""))
    if documents:
        if not re.fullmatch(r"[A-Za-z0-9._-]+", documents):
            errors.append("plugin.toml: documents must name one folder beside plugin.toml")
        else:
            folder = pack / documents
            if not folder.is_dir():
                errors.append(f"documents: folder not found: {documents}")
            else:
                pages = sorted(folder.glob("*.md"))
                report["documents"] = len(pages)
                for page in pages:
                    head = page.read_text(encoding="utf-8")[:2000]
                    if not head.lstrip().startswith("---") or "title:" not in head.split("---", 2)[1]:
                        warnings.append(f"documents: {page.name} has no front-matter title; the sidebar keeps "
                                        f"the English title")

    if args.reference:
        english = load(args.reference)
        missing = sorted(english.keys() - strings.keys())
        unknown = sorted(strings.keys() - english.keys())
        placeholder = sorted(k for k in english.keys() & strings.keys()
                             if fields(english[k]) != fields(strings[k]))
        report.update({"missing": len(missing), "unknown": len(unknown), "placeholder_diffs": len(placeholder)})
        if missing:
            errors.append(f"strings: missing {len(missing)} key(s), e.g. {missing[:5]}")
        if unknown:
            warnings.append(f"strings: {len(unknown)} key(s) not in this English template, e.g. {unknown[:5]}")
        if placeholder:
            errors.append(f"strings: {len(placeholder)} placeholder difference(s), e.g. {placeholder[:5]}")
        untranslated = sorted(k for k in english.keys() & strings.keys() if strings[k] == english[k])
        report["identical_to_english"] = len(untranslated)
        if untranslated:
            warnings.append(f"strings: {len(untranslated)} value(s) identical to English "
                            f"(expected for names/abbreviations), e.g. {untranslated[:5]}")

    if args.traditional:
        if not args.traditional.is_file():
            warnings.append(f"traditional table not found: {args.traditional}")
        else:
            table = traditional_map(args.traditional)
            leftovers = {}
            for kind in ("strings",) + RESOURCES:
                for key, value in tables.get(kind, {}).items():
                    found = sorted({char for char in value if char in table})
                    if found:
                        leftovers.setdefault(kind, []).append((key, "".join(found)))
            report["traditional"] = {kind: len(items) for kind, items in leftovers.items()}
            if leftovers:
                sample = leftovers.get("strings", [])[:5]
                warnings.append(f"leftover Traditional characters in {sum(len(v) for v in leftovers.values())} "
                                f"value(s), e.g. {sample}")

    result = {"pack": str(pack), "counts": report, "errors": errors, "warnings": warnings}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"pack: {pack}")
        for kind, count in report.items():
            if isinstance(count, int):
                print(f"  {kind}: {count}")
        for warning in warnings:
            print(f"  warning: {warning}")
        for error in errors:
            print(f"  ERROR: {error}")
        print("OK" if not errors else f"{len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
