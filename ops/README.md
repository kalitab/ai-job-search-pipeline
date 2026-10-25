# Ops

| Path | What |
|---|---|
| `skills/job-scan/SKILL.md` | The daily job scan. Step 8 calls the two resume skills. |
| `skills/resume-tailoring/SKILL.md` | Tailor the resume and cover letter to one job: job analysis, conservative editing, house Markdown format, PDF export, release. |
| `skills/resume-release-check/SKILL.md` | Independent release gate: claim-by-claim content audit and QA of the rendered PDF, run by a reviewer that did not write the draft. |
| `scripts/resume_md.py` | `normalise` (fixes layout, never words) and `lint` (fails on tables, `\|`, `<http…>` links, italics, blockquotes, HTML, symbol bullets). |
| `scripts/export_pdf.sh` | Markdown → lint → HTML → A4 PDF. Needs `pandoc` and a headless Chromium (set `CHROME` to its path). |
| `scripts/resume.css` | Print style: Arial, no italics, A4, 18mm margins, single column. |
| `scripts/resume.lua` | pandoc filter: wraps the page, marks the contact line and bold label lines, drops italics. |
| `scripts/check_pdf.py` | Automated PDF checks: fonts used, italics, contact details and link targets, leftover Markdown, every line present and in order, blank pages, stranded headings. |
| `scripts/scan_workday.py` | Workday careers-site scanner, driven by `config/workday-settings.json`. |
| `runs/` | One Markdown log per daily run. |
| `dashboard/index.html` | Source of the dashboard artifact. |

The dashboard's in-browser PDF follows the same format rules as the export script; its `sanitiseMd()` mirrors `resume_md.py normalise`. Change both together.
