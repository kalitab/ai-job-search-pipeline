# Master resume

Your master resume is the only source of facts for every tailored version. Save each approved version as its own file: `resume-v1.md`, then `resume-v2.md` and so on. The highest number is current. Exports (PDF, Word) go in `exports/`.

Write it in plain GitHub Markdown, in exactly this shape. The PDF export and the dashboard both depend on it.

```
# FIRSTNAME LASTNAME

Current Title

Mobile: +00 00000 00000 | Email: name@example.com | LinkedIn: [https://www.linkedin.com/in/your-profile/](https://www.linkedin.com/in/your-profile/)

## EXECUTIVE PROFILE

One paragraph about who you are and what you are best at.

## CORE EXPERTISE

- One area per line
- Another area

## PROFESSIONAL EXPERIENCE

### Title | Company | Month YYYY – Present

**1) A group of related work, if you use groups**

- What you did and the result
- Another achievement

### Earlier Title | Earlier Company | Month YYYY – Month YYYY

- What you did and the result

## EDUCATION

- Degree, Institution, Year
```

Rules:
- `## ` for sections, `### ` for each role, `**Label**` alone on a line for a sub-group, `- ` for every bullet.
- Role lines are `Title | Company | Month YYYY – Month YYYY`, in title case.
- No tables, italics, blockquotes, HTML, emoji or symbol bullets.
- Check it with `python3 ops/scripts/resume_md.py lint master/resume-v1.md`.
