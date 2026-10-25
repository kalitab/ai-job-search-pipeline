---
name: resume-tailoring
description: Tailor the candidate's resume and cover letter to one job — analyse the job description, edit conservatively from the master resume, render an A4 PDF, then hand to the independent release check. Use for "tailor my resume for this job" or step 8 of the job scan.
---

# Resume tailoring

Produces, for one job: `resume.md`, `cover-letter.md`, a change log and gaps list, and checked PDFs.
Release is gated by a separate skill, **resume-release-check** (`ops/skills/resume-release-check/SKILL.md`),
run by a reviewer that did not write the draft.

## Policy

The current master resume is the only factual source of truth. The job description is a relevance guide,
never evidence of what the candidate has done. Tailoring changes emphasis, order within sections, concision
and wording, never facts. Every contact detail, employer, title, date, credential, metric and the real scope
of each achievement survives unchanged. Missing evidence is reported as a gap, never filled. Nothing is
presented as checked until the release check passes, and a check that could not be run is reported as
NOT VERIFIED, never as passed.

## Inputs and where they live

| Input | Location |
|---|---|
| Master resume (current version) | repo `master/resume-v<N>.md` (highest N), same text as the dashboard's `config/master-resume` |
| Job | dashboard `jobs/<id>`: title, company, city, exp, `jd` (may be null), summary, why[] |
| Existing quick draft (optional) | dashboard `jobs/<id>.tailored`, made by the Tailor now button; a starting proposal only |
| Candidate name for file names | `config/setup.md` |
| Output folder | repo `jobs/YYYY-MM-<company-slug>-<role-slug>/` |
| Tools | `ops/scripts/resume_md.py` (normalise / lint), `ops/scripts/export_pdf.sh` (Markdown → PDF), `ops/scripts/check_pdf.py` (PDF checks) |

If the job description is null, say so in the change log and tailor from the title, summary and match notes
only; the gaps list must then include "full job description not available".

## Workflow

| Stage | Who | Output |
|---|---|---|
| 1. Read the sources | you | master text, job description, format rules below |
| 2. Analyse the job (A) | you | tailoring plan (internal) |
| 3. Tailor content (B) | you | `resume.md`, `cover-letter.md`, change log |
| 4. Render | you | PDFs via `ops/scripts/export_pdf.sh` |
| 5. Content audit (C) | **fresh reviewer** using resume-release-check | audit report |
| 6. Format QA (D) | **fresh reviewer** using resume-release-check | PASS/FAIL report |
| 7. Fix and re-check | you, then the reviewer again | — |
| 8. Release | you | files committed, card marked checked |

### Stage A — Analyse the job (no editing yet)

1. Extract: job title, core responsibilities, mandatory and preferred qualifications, domain skills,
   leadership expectations, recurring keywords.
2. Rank the criteria by importance to this employer.
3. Map each to evidence in the master and classify: **Directly supported** (the resume says so),
   **Partially supported** (adjacent work; say how), **Unsupported**. A shared word is not a match.
4. Write the plan: what to lead with, which existing bullets support it, where they go, and the gaps.
   Unsupported criteria go to the gaps list only.

### Stage B — Tailor the content

Edit as a conservative resume editor.

**Allowed**
- Move the most relevant existing bullets to the top of each role; move sub-groups within a role; reorder the
  expertise list; lead the profile with the strongest match.
- Condense less relevant bullets; merge repetitive ones; condense roles older than ten years.
- Use the job description's terms only where they accurately describe experience the resume shows.
- Fix clear typos and grammar (record each fix in the change log).

**Not allowed**
- New or changed employers, titles, dates, metrics, values, team sizes, countries, budgets, savings,
  certifications, tools, projects or responsibilities.
- Changing scope or certainty: assisted → led, contributed → owned, exposure → expertise, mentored →
  managed, team result → individual result.
- Dropping a role, a qualification or any substantive content from the last ten years.
- Keyword stuffing, or a sentence that only echoes the job description.

**Shortening a bullet:** only if it keeps the achievement, the candidate's role and the scale. Cut repetition
and background explanation before results, specifics or ownership.

Example —
- Master: "Mentored a trained a team of 5 junior analysts"
- Good: "Mentored and trained a team of 5 junior analysts" (typo fixed, logged)
- Wrong: "Led a team of 5" — turns mentoring into line management; the release check fails it.

**Length:** at most three A4 pages in the house style (10.5pt Arial, 18mm margins); two is better when it
costs nothing. To shorten, in this order: merge repeated bullets; condense roles older than ten years to one or
two lines each; set the expertise list on one line separated by " · " and merge Education and Recognition;
tighten wordy phrasing and bullets that wrap onto a line of one or two words; shorten the profile. Never cut
recent substantive content to make it fit. Log every merge and every dropped detail in the change log.

**Cover letter:** under 250 words, addressed to this company and role, in the candidate's voice, no flattery,
only experience in the master, and no gap presented as a strength. Same format rules.

**Change log** (goes in `notes.md`): one line per substantive change (what moved or changed, and the master
line it comes from), every typo fix, the gaps list, and "job description not available" if so.

### Output format (both renderers depend on it)

Plain GitHub Markdown, exactly this shape:

```
# FIRSTNAME LASTNAME

Current Title

Mobile: +00 00000 00000 | Email: name@example.com | LinkedIn: [https://www.linkedin.com/in/your-profile/](https://www.linkedin.com/in/your-profile/)

## EXECUTIVE PROFILE

One paragraph.

## CORE EXPERTISE

- One item per line

## PROFESSIONAL EXPERIENCE

### Title | Company | Month YYYY – Present

**1) Sub-group label**

- Bullet
```

- Contact line copied from the master character for character; LinkedIn written as `[url](url)` so the full
  address is visible and clickable.
- `## ` sections, `### ` role lines, `**Label**` alone on a line for sub-groups, `- ` for every bullet.
- Role lines exactly as in the master: `### Title | Company | Month YYYY – Month YYYY` (or `– Present`), in
  title case, never all capitals. Titles, employers and months are facts: copy them, never shorten or reword.
- **Never:** tables, `\|`, `<https://…>` links, italics (`*x*`, `_x_`), blockquotes (`>`), raw HTML, symbol
  bullets (• ▪), emoji, headings below `###`.
- Run `python3 ops/scripts/resume_md.py lint <file>` — it must say `lint: clean`.
  `python3 ops/scripts/resume_md.py normalise <file>` repairs layout without touching words.

Typography is fixed by `ops/scripts/resume.css`: Arial (Calibri or Times New Roman are the only alternatives),
no italics, bold for headings and labels, A4 with 18mm margins, 10.5pt body, 9.5pt contact line (so the full
LinkedIn URL fits on one line), single column, underlined links, no colour, icons, tables or text boxes. The
dashboard's in-browser PDF follows the same rules.

### Stage 4 — Render

```
ops/scripts/export_pdf.sh <folder>/resume.md       <folder>/exports/<Name>_Resume_<Company>.pdf
ops/scripts/export_pdf.sh <folder>/cover-letter.md <folder>/exports/<Name>_CoverLetter_<Company>.pdf
```

The script lints first and refuses non-conforming Markdown. It needs `pandoc` and a headless Chromium.

### Stages 5–7 — Independent release check

Start a **fresh reviewer** (a subagent that has not seen your drafting) with this brief, paths filled in:

> Use the skill at `ops/skills/resume-release-check/SKILL.md`. Original: `master/resume-v<N>.md`.
> Job description: <text or "not available">. Tailored: `<folder>/resume.md` and `cover-letter.md`.
> Change log: `<folder>/notes.md`. PDFs: `<folder>/exports/`. Return both reports and the release decision.

- Any Critical or Major finding → fix the Markdown, re-render, and run the check again with a fresh reviewer.
  Re-run the full content audit if any words changed; format QA only if only layout changed.
- At most two fix rounds. Still failing → do not release: leave the card as a draft, put the open findings in
  `notes.md` and the run message.
- No subagent available → run the check yourself, label the report "self-checked, not independent" and leave
  `validated` false.

### Stage 8 — Release

Only when the release decision is RELEASE:
1. Commit `resume.md`, `cover-letter.md`, `notes.md` (change log, gaps, both reports' summaries, master
   version) and the PDFs: `<company>: tailored resume + cover letter from master v<N> (checked)`.
2. On the dashboard card (pinned with `if_version`), set inside `tailored`: `validated: true`, `validatedAt`,
   `repoPath`; replace `resume_md` / `cover_letter_md` with the released text if fixes changed it. Never touch
   `status` or any field the candidate set.
3. Report in 2–3 lines: what leads now, the gaps, and any check marked NOT VERIFIED.
