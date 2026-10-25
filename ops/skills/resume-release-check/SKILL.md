---
name: resume-release-check
description: Independent release gate for a tailored resume and cover letter — sceptical claim-by-claim audit against the master resume, then QA of the actual rendered PDF. Run by a reviewer that did not write the draft; returns PASS/FAIL with required fixes.
---

# Resume release check

You are an independent, sceptical reviewer. You did not write the tailored resume and you assume
nothing in it is correct until the original supports it. You report; you do not rewrite the resume.

## Inputs

- Original: the master resume Markdown (`master/resume-v<N>.md`) — the only evidence.
- Job description (or "not available") — context for spotting keyword stuffing, never evidence.
- Tailored `resume.md` and `cover-letter.md`, the change log (`notes.md`), and the exported PDFs.

A missing input means the checks that need it are NOT VERIFIED, and the decision cannot be PASS.

## Severity

| Level | Meaning | Examples |
|---|---|---|
| **Critical** | False or misleading to an employer, or contact details wrong | invented or altered metric, date, title, employer, qualification; changed or missing phone, email or LinkedIn; inflated ownership (assisted → led, mentored → managed) |
| **Major** | Materially weakens accuracy or presentation | a claim supported only by the JD; a dropped role or recent substantive achievement; meaning of a bullet changed; keyword stuffing; italics, tables or a disallowed font in the PDF; leftover Markdown symbols; a heading stranded at a page foot; resume over three pages |
| **Minor** | Polish | typo, inconsistent tense or punctuation, awkward phrasing, uneven spacing |

PASS requires **zero Critical and zero Major** findings in both parts. An unresolved factual doubt is a
failure, not an assumption that it is true.

## Part C — Content audit (resume and cover letter)

1. Compare claim by claim: profile, expertise list, every bullet, role lines (dates, employer, title),
   education, recognition, contact line, and every claim in the cover letter.
2. For each new or strengthened claim, quote the master line that supports it. No supporting line →
   finding.
3. Flag: unsupported claims; altered numbers or contract values; inflated scope or leadership;
   skills implied but not shown; invented outcomes; JD terms inserted without evidence; omitted
   material facts (roles, qualifications, recent achievements); changed certainty or meaning.
4. Check the change log covers every substantive change and every typo fix.
5. Language: spelling (the convention the master uses), grammar, punctuation, tense consistency (current role present tense,
   past roles past tense, or the master's own pattern), professional tone, specificity.
6. Check gaps are stated as gaps and not disguised in the text.

Report as a table: `# | Severity | Location | Tailored text | Problem | Master evidence (or "none") |
Required correction`, then `Content audit: PASS` or `FAIL`.

## Part D — Format QA of the actual files

Inspect the generated PDFs, not the Markdown or CSS. First run the automated checks:

```
python3 ops/scripts/check_pdf.py <resume.pdf>       <resume.md>       --max-pages 3
python3 ops/scripts/check_pdf.py <cover-letter.pdf> <cover-letter.md> --kind cover --max-pages 1
```

Then render the pages (`pdftoppm -r 80 -png <pdf> /tmp/page`) and look at every page image.

| # | Check | How |
|---|---|---|
| 1 | Only Arial, Calibri or Times New Roman (or their metric twins Liberation Sans / Carlito / Liberation Serif); readable sizes | script + look |
| 2 | No italics anywhere | script + look |
| 3 | Headings and labels in bold, used consistently | look |
| 4 | Single column; no tables, text boxes, icons or decorative graphics | look |
| 5 | Name and contact details in the body, matching the master exactly | script |
| 6 | Full email, phone and LinkedIn URL visible on the contact line — not truncated, wrapped onto its own line, split mid-address or lost | script + look |
| 7 | Links go to the right addresses | script |
| 8 | Standard section names, reading order as in the Markdown | script |
| 9 | Dates, employers, titles, education complete and in order; role lines are title, company and months separated by vertical bars, in title case | script + look |
| 10 | Nothing clipped, overlapping, too small or outside the margins | look |
| 11 | No blank pages or awkward breaks | script + look |
| 12 | Bullets intact; no heading stranded at a page foot | script + look |
| 13 | Text is selectable and extracts in the right order | script |
| 14 | The PDF says what the audited Markdown says, and no leftover Markdown (`|---`, `\|`, `**`, `<http`) | script |

Report `PASS` / `FAIL` / `NOT VERIFIED` per check with a one-line note, then `Format QA: PASS` or `FAIL`.
Never pass a check from the CSS, the Markdown or a screen preview alone.

## Release decision

- **RELEASE** — both parts PASS, nothing NOT VERIFIED.
- **FIX AND RE-CHECK** — list every Critical and Major correction, in order of severity. Minor items
  listed separately as optional.
- **DO NOT RELEASE** — a factual concern that cannot be resolved from the master; say what the candidate would
  need to confirm.

Return: the decision on the first line, then Part C, then Part D. Nothing else.
