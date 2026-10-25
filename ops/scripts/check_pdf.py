#!/usr/bin/env python3
"""Automated part of the format QA (resume-release-check, stage D) for an exported PDF.

  python3 ops/scripts/check_pdf.py <resume.pdf> <resume.md> [--max-pages 3] [--kind resume|cover]

Checks the actual file, not the source: fonts, italics, selectable text, contact
details and link targets, leftover Markdown, blank pages, stranded headings,
section order and that every line of the audited Markdown made it into the PDF.
Prints PASS/FAIL per check; exit 1 if any FAIL. Visual checks (clipping, overlap,
awkward breaks) still need the page images to be looked at — see the skill.
"""
import re
import subprocess
import sys

import pypdf

ALLOWED_FONTS = ("arial", "helvetica", "liberationsans", "arimo",          # Arial family
                 "calibri", "carlito",                                     # Calibri family
                 "timesnewroman", "times", "liberationserif", "tinos",     # Times family
                 "symbol")                                                 # Word bullet glyphs only
ITALIC = re.compile(r"italic|oblique", re.I)


def norm(s):
    s = s.replace("­", "").replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = re.sub(r"[–—]", "-", s)
    return re.sub(r"\s+", "", s).lower()


def used_fonts(reader):
    names = set()
    for page in reader.pages:
        res = page["/Resources"].get_object() if "/Resources" in page else {}
        fonts = res["/Font"].get_object() if "/Font" in res else {}
        c = page.get_contents()
        data = c.get_data() if c is not None else b""
        for ref in set(re.findall(rb"/([A-Za-z0-9_.+-]+)\s+[\d.]+\s+Tf", data)):
            f = fonts.get("/" + ref.decode())
            if f is not None:
                fo = f.get_object()
                fd = fo.get("/FontDescriptor")
                name = fo.get("/BaseFont") or (fd.get_object().get("/FontName") if fd else None) \
                    or fo.get("/Name") or ref.decode()   # Type 3 fonts carry the name on the descriptor
                names.add(str(name).lstrip("/").split("+")[-1])
    return sorted(names)


def md_plain(line):
    line = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line)
    line = re.sub(r"^#+\s*|^\s*-\s+|\*\*", "", line)
    return line.strip()


def main():
    args = sys.argv[1:]
    if len(args) < 2:
        sys.exit(__doc__)
    pdf, md = args[0], args[1]
    max_pages = int(args[args.index("--max-pages") + 1]) if "--max-pages" in args else 3
    kind = args[args.index("--kind") + 1] if "--kind" in args else "resume"
    src = open(md, encoding="utf-8").read()
    src_lines = [l for l in src.split("\n") if l.strip() and not l.startswith("<!--")]
    results = []

    def check(name, ok, detail=""):
        results.append((name, ok, detail))

    reader = pypdf.PdfReader(pdf)
    pages = len(reader.pages)
    check(f"page count ≤ {max_pages}", pages <= max_pages, f"{pages} pages")

    names = used_fonts(reader)   # fonts actually used to draw text (some generators declare all 14 base fonts)
    check("fonts detected", bool(names), "" if names else "no text fonts found — cannot verify fonts")
    bad = [n for n in names if not any(a in n.lower().replace("-", "").replace(" ", "") for a in ALLOWED_FONTS)]
    check("only Arial / Calibri / Times fonts", not bad, ", ".join(names) + (f"  — not allowed: {bad}" if bad else ""))
    ital = [n for n in names if ITALIC.search(n)]
    check("no italic fonts", not ital, ", ".join(ital))

    page_text = [subprocess.run(["pdftotext", "-layout", "-f", str(i), "-l", str(i), pdf, "-"],
                                capture_output=True, text=True).stdout for i in range(1, pages + 1)]
    text = "\n".join(page_text)
    check("text is selectable", len(text.strip()) > 200, f"{len(text)} chars extracted")
    blank = [i + 1 for i, t in enumerate(page_text) if len(t.strip()) < 40]
    check("no blank pages", not blank, f"blank: {blank}" if blank else "")

    flat = norm(text)
    # contact details exactly as in the source
    if kind == "resume":
        email = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", src)
        phone = re.search(r"(?:Mobile|Phone)[^0-9+]*([+0-9][0-9 ]{7,})", src)
        url = re.search(r"https?://(?:www\.)?linkedin\.com/[^\s)\]>]+", src)
        for label, m in (("email", email), ("phone", phone), ("LinkedIn URL", url)):
            if not m:
                check(f"contact: {label} visible in full", False, "not found in the Markdown source")
                continue
            val = m.group(1) if label == "phone" else m.group(0)
            check(f"contact: {label} visible in full", norm(val) in flat, val)
        if url:
            first = page_text[0].split("\n")
            same = any("LinkedIn" in l and url.group(0).rstrip("/") in l for l in first)
            check("contact: LinkedIn URL on the same line as the label", same, "" if same else "URL wrapped onto its own line")
        links = []
        for p in reader.pages:
            for a in p.get("/Annots") or []:
                a = a.get_object()
                if a.get("/A") and a["/A"].get("/URI"):
                    links.append(a["/A"]["/URI"])
        if url:
            check("LinkedIn link goes to the right address", url.group(0) in links, ", ".join(links) or "no links in PDF")
        if email:
            mail = [l for l in links if "@" in l]
            check("email link (if any) is correct", all(email.group(0) in l for l in mail), ", ".join(mail))

    left = [s for s in ("|---", "\\|", "<http", "**", "](", "> ") if s in text]
    check("no leftover Markdown in the PDF", not left, f"found {left}" if left else "")

    # every source line present, in order
    missing, out_of_order, pos = [], [], 0
    for l in src_lines:
        p = md_plain(l)
        if not p:
            continue
        key = norm(p)[:60]
        at = flat.find(key, pos)            # repeated phrases: look ahead of the last match first
        if at < 0:
            if flat.find(key) < 0:
                missing.append(p[:70])
            else:
                out_of_order.append(p[:60])
        else:
            pos = at
    check("every Markdown line appears in the PDF", not missing, "; ".join(missing[:5]))
    check("reading order matches the Markdown", not out_of_order, "; ".join(out_of_order[:5]))

    heads = [md_plain(l) for l in src_lines if re.match(r"^#{2,3} ", l)]
    labels = [md_plain(l) for l in src_lines if re.fullmatch(r"\*\*[^*]+\*\*", l.strip())]
    stranded = []
    for i, t in enumerate(page_text[:-1]):
        lines = [x.strip() for x in t.split("\n") if x.strip()]
        if lines and any(norm(lines[-1]) == norm(h) for h in heads + labels):
            stranded.append(f"p{i+1}: {lines[-1]}")
    check("no heading stranded at a page bottom", not stranded, "; ".join(stranded))

    width = max(len(n) for n, _, _ in results)
    for n, ok, d in results:
        print(f"{'PASS' if ok else 'FAIL'}  {n.ljust(width)}  {d}")
    fails = sum(1 for _, ok, _ in results if not ok)
    print(f"\n{len(results) - fails}/{len(results)} automated checks passed"
          + ("" if not fails else f" — {fails} FAIL"))
    print("NOT VERIFIED by this script: clipping/overlap, awkward breaks, margins — inspect page images.")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
