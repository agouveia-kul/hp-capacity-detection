"""Mechanical style check for Alex's prose rules (2026-10-02) on one LaTeX section file.

Checks the prose only (comments, tables, figures, math and LaTeX commands removed):
banned punctuation (em dash, dash as punctuation, semicolon, colon), sentence length (cap 35 words),
median length (target 20-24, below 18 = choppy) and expletive openers.

    python paper/tools/style_check.py paper/sections/03_data_protocol.tex
"""
import re
import statistics
import sys
from pathlib import Path

MACROS = {r"\dataCH{}": "CH dataset", r"\dataCH": "CH dataset", r"\dataGB{}": "GB dataset", r"\dataGB": "GB dataset"}
EXPLETIVES = ("It can be", "It is possible", "It is relevant", "It is important", "It should be noted")


def prose(tex):
    t = re.sub(r"(?<!\\)%.*", "", tex).replace(r"\%", " percent")
    t = re.sub(r"\\begin\{(table\*?|figure\*?|equation\*?|align\*?)\}.*?\\end\{\1\}", "", t, flags=re.S)
    t = re.sub(r"\$[^$]*\$", "X", t)
    t = re.sub(r"\\(label|cite|ref|input|todo|figplaceholder)\{[^}]*\}", "", t)
    t = re.sub(r"\\(section|subsection|subsubsection)\*?\{[^}]*\}", "", t)
    t = re.sub(r"\\num\{([^}]*)\}", r"\1", t)
    for k, v in MACROS.items():
        t = t.replace(k, v)
    return " ".join(t.replace(r"et al.\ ", "et al. ").replace("~", " ").split())


def main(path):
    t = prose(Path(path).read_text(encoding="utf-8"))
    bad = {"em dash": "—", "spaced en dash": " – ", "spaced --": " -- ", "semicolon": ";", "colon": ":"}
    for name, ch in bad.items():
        for m in re.finditer(re.escape(ch), t):
            print(f"BANNED {name}: ...{t[max(0, m.start() - 50):m.start() + 30]}...")
    sents = [x for x in re.split(r"(?<=[.?!])\s+(?=[A-Z$\\])", t) if x.strip()]
    lens = [len(x.split()) for x in sents]
    if not lens:
        print("no prose found")
        return
    print(f"sentences {len(lens)}, median {statistics.median(lens)}, max {max(lens)}, over 35: {sum(n > 35 for n in lens)}, under 15: {sum(n < 15 for n in lens)}")
    for x, n in sorted(zip(sents, lens), key=lambda z: -z[1])[:3]:
        print(f"  {n:2d} | {x[:140]}")
    for w in EXPLETIVES:
        if t.count(w):
            print(f"expletive opener '{w}': {t.count(w)}")


if __name__ == "__main__":
    main(sys.argv[1])
