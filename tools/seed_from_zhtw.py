"""Build a Simplified-Chinese *seed* from the zh-TW reference pack (review required).

    python tools/seed_from_zhtw.py --source ../repos/pokeldn-plugins-zhTW/language-pack \
        --opencc ../repos/OpenCC/data/dictionary --out ../work/seed

Two passes, exactly as docs/workflow.md §5.2:
  1. OpenCC t2s (TSPhrases longest match, then TSCharacters) for glyph conversion;
  2. tools/vocab.toml for Taiwan wording that t2s leaves alone (程式 -> 程序).

Placeholders (`{...}`) are never touched. The output is a starting point: every entry still
needs a review against reference/strings.en.toml and docs/glossary.md. This script never
writes into language-pack/.
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

PLACEHOLDER = re.compile(r"(\{[^{}]*\})")
FILES = ("strings", "messages", "templates", "terms", "help")


class Convert:
    """OpenCC's tw2s chain: Taiwan phrase/variant tables first, then the glyph tables."""

    CHAIN = ("TWVariantsRevPhrases.txt", "TWPhrasesRev.txt", "TSPhrases.txt")

    def __init__(self, dictionary: Path):
        self.stages = []
        for name in self.CHAIN:
            table = self._load(dictionary / name)
            self.stages.append((table, sorted({len(key) for key in table}, reverse=True)))
        self.chars = self._load(dictionary / "TSCharacters.txt", first_variant=True)

    @staticmethod
    def _load(path, first_variant=False):
        table = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line or line.startswith("#"):
                continue
            source, _, target = line.partition("\t")
            if target:
                # Tables list candidates space-separated ("介面\t界面 接口"); the first is preferred.
                target = target.split(" ")[0]
            table[source] = target
        return table

    @staticmethod
    def _apply(text, table, sizes):
        out, i = [], 0
        while i < len(text):
            for size in sizes:
                if size <= len(text) - i and text[i:i + size] in table:
                    out.append(table[text[i:i + size]])
                    i += size
                    break
            else:
                out.append(text[i])
                i += 1
        return "".join(out)

    def glyphs(self, text):
        for table, sizes in self.stages:
            text = self._apply(text, table, sizes)
        return "".join(self.chars.get(char, char) for char in text)


class Vocabulary:
    def __init__(self, table: dict[str, str]):
        self.table = table
        self.pattern = re.compile("|".join(re.escape(key) for key in sorted(table, key=len, reverse=True)))

    def apply(self, text):
        parts = PLACEHOLDER.split(text)
        return "".join(part if PLACEHOLDER.fullmatch(part) else self.pattern.sub(lambda m: self.table[m[0]], part)
                       for part in parts)


def render(table: dict) -> str:
    lines = ["# 机器生成的简体种子（OpenCC + 术语替换），未经审校，不得直接作为发布包。"]
    lines += [f"{json.dumps(key, ensure_ascii=False)} = {json.dumps(value, ensure_ascii=False)}"
              for key, value in table.items()]
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", type=Path, required=True, help="zh-TW language-pack folder")
    parser.add_argument("--opencc", type=Path, required=True, help="OpenCC data/dictionary folder")
    parser.add_argument("--out", type=Path, required=True, help="output folder for the seed")
    parser.add_argument("--vocab", type=Path, default=Path(__file__).with_name("vocab.toml"))
    args = parser.parse_args(argv)

    glyphs = Convert(args.opencc)
    vocab = Vocabulary(tomllib.loads(args.vocab.read_text(encoding="utf-8")))
    args.out.mkdir(parents=True, exist_ok=True)

    for name in FILES:
        source = args.source / f"{name}.toml"
        if not source.is_file():
            print(f"skip {name}: no {source}")
            continue
        table = tomllib.loads(source.read_text(encoding="utf-8"))
        converted, changed = {}, 0
        for key, value in table.items():
            target = vocab.apply(glyphs.glyphs(value))
            converted[key] = target
            changed += target != value
        (args.out / f"{name}.toml").write_text(render(converted), encoding="utf-8")
        print(f"{name}: {len(converted)} entries, {changed} changed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
