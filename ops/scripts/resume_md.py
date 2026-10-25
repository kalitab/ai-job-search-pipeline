#!/usr/bin/env python3
"""Resume Markdown: normalise to the house format, or lint it.

  python3 ops/scripts/resume_md.py normalise <in.md> [out.md]   # rewrite (in place if no out)
  python3 ops/scripts/resume_md.py lint <file.md> [...]          # exit 1 on any defect

The house format (see ops/skills/resume-tailoring/SKILL.md, "Output format") is
plain GitHub Markdown that both renderers handle: the repo PDF export
(pandoc + resume.css) and the dashboard's in-browser PDF. It forbids the
constructs that broke the 21 Oct Persistent drafts: pipe tables, escaped pipes,
angle-bracket autolinks; and also italics, blockquotes, raw HTML, symbol bullets.

normalise changes layout only, never words. The same rules are mirrored in the
dashboard's sanitiseMd() — change both together.
"""
import re
import sys

URL_RE = re.compile(r"<(https?://[^>\s]+)>")
TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")
TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")
NUM_LABEL = re.compile(r"^(\d+)\)\s+\*\*(.+?)\*\*\s*$")
SYMBOL_BULLET = re.compile(r"^(\*\*)?[•▪◦●■]\s*(\*\*)?\s*")


def normalise(md: str) -> str:
    out = []
    for raw in md.split("\n"):
        ln = raw.rstrip()
        # pipe tables -> one bullet per non-empty cell, row by row
        if "|" in ln and TABLE_SEP.match(ln):
            continue
        if TABLE_ROW.match(ln):
            for cell in ln.strip().strip("|").split("|"):
                cell = cell.strip()
                if cell:
                    out.append("- " + cell)
            continue
        # blockquote lines -> plain lines
        if ln.lstrip().startswith(">"):
            ln = ln.lstrip()[1:].strip()
            if not ln:
                continue
        # symbol bullets (•, ▪, with or without bold wrapper) -> "- "
        if SYMBOL_BULLET.match(ln):
            ln = "- " + SYMBOL_BULLET.sub("", ln)
        ln = re.sub(r"^\s*[*+]\s+", "- ", ln)       # "* item" / "+ item" bullets -> "- "
        # "1)  **Label**" -> "**1) Label**" (a bold label line both renderers handle)
        m = NUM_LABEL.match(ln)
        if m:
            ln = f"**{m.group(1)}) {m.group(2).strip()}**"
        ln = re.sub(r"\\$", "", ln)                # pandoc hard line break "text\\" -> "text"
        ln = ln.replace("\\|", "|")
        ln = URL_RE.sub(lambda m: f"[{m.group(1)}]({m.group(1)})", ln)
        # italics -> plain (keep bold)
        ln = re.sub(r"(?<![*\w])\*(?!\*)([^*\n]+?)\*(?!\*)", r"\1", ln)
        ln = re.sub(r"(?<![\w_])_(?!_)([^_\n]+?)_(?![\w_])", r"\1", ln)
        ln = re.sub(r"</?(em|i)>", "", ln)
        out.append(ln)
    text = "\n".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
    # a list item directly after a paragraph needs a blank line for pandoc
    text = re.sub(r"(\n(?!- )[^\n]+)\n(- )", r"\1\n\n\2", text)
    return text


CHECKS = [
    ("pipe table row or separator", re.compile(r"^\s*\|.*\|\s*$|^\s*\|?-{3,}")),
    ("escaped pipe \\|", re.compile(r"\\\|")),
    ("angle-bracket autolink <http…>", re.compile(r"<https?://")),
    ("raw HTML tag", re.compile(r"<(?!!--|https?:)[a-zA-Z/][^>]*>")),
    ("blockquote", re.compile(r"^\s*>")),
    ("trailing backslash (hard line break)", re.compile(r"\\$")),
    ("symbol bullet (•/▪)", re.compile(r"[•▪◦●■]")),
    ("italics", re.compile(r"(?<![*\w])\*(?!\*)[^*\n]+?\*(?!\*)|(?<![\w_])_(?!_)[^_\n]+?_(?![\w_])")),
    ("heading deeper than ###", re.compile(r"^####")),
    ("role line not \"Title | Company | Month YYYY – Month YYYY|Present\"",
     re.compile(r"^### (?![^|\n]+ \| [^|\n]+ \| [A-Z][a-z]+ \d{4} – (?:[A-Z][a-z]+ \d{4}|Present)$)")),
]


def lint(path: str) -> list:
    problems = []
    for i, ln in enumerate(open(path, encoding="utf-8").read().split("\n"), 1):
        if ln.lstrip().startswith("<!--"):
            continue
        for name, rx in CHECKS:
            if rx.search(ln):
                problems.append(f"{path}:{i}: {name}: {ln.strip()[:90]}")
    return problems


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] not in ("normalise", "lint"):
        sys.exit(__doc__)
    if sys.argv[1] == "normalise":
        src = sys.argv[2]
        dst = sys.argv[3] if len(sys.argv) > 3 else src
        res = normalise(open(src, encoding="utf-8").read())
        open(dst, "w", encoding="utf-8").write(res)
        print(f"normalised {src} -> {dst}")
    else:
        allp = [p for f in sys.argv[2:] for p in lint(f)]
        print("\n".join(allp) if allp else "lint: clean")
        sys.exit(1 if allp else 0)
