---
name: job-scan
description: Daily job scan — collect roles from alert emails, job boards and target companies' careers sites, de-duplicate, filter by config/search-criteria.md, add a company rating snapshot, score against the master resume, and update the job dashboard and the GitHub repo. Use for "run the job scan" or the scheduled morning run.
---

# Job scan

Run once a day on a schedule, or on request ("run the job scan"). The goal is a short, trustworthy feed:
only roles that pass the search criteria reach the dashboard. Quality over volume.

## Where things live

| What | Where |
|---|---|
| Your settings (repo, dashboard link, budget, run time) | `config/setup.md` |
| Search criteria | `config/search-criteria.md` — the source of truth; re-read every run |
| Target companies | `config/target-companies.md`, with search-page URLs in `config/search-pages.md` |
| Workday scan settings | `config/workday-settings.json` (copy of the `.example.json`, filled in) |
| Master resume | `master/resume-v<N>.md` — the highest N is current |
| Dashboard | an artifact with a database: collections `jobs`, `applications`, `outreach`, `runs`, document `config/master-resume` |
| Resume skills | `ops/skills/resume-tailoring/SKILL.md` and `ops/skills/resume-release-check/SKILL.md` |
| Helper scripts | `ops/scripts/` |
| Run logs | `ops/runs/YYYY-MM-DD.md` in the repo, plus `runs/<date>` in the dashboard |

## Hard rules

- **Never apply, never send email, never contact anyone.** Collect, filter, research, draft, log.
- **Never invent facts.** No guessed ratings, salaries, emails or experience. Missing = "not available".
- **Never overwrite the candidate's actions.** Pin every dashboard update with `if_version`; on a version
  conflict re-read and merge. Never change `status`, `tailored`, application stages or outreach entries the
  candidate set.
- **Spend cap:** if Apify is used, stop calling paid actors once the run reaches the cap in `config/setup.md`,
  and log it. Company ratings use web search, which costs nothing.
- **Each source runs on its own.** A failing source is logged in the run record and the run carries on.
- **Respect each site's terms.** Use public job listings only. Never sign in to a job site, never read
  profiles of people, never bypass a block.

## Steps

### 0. Load rules and state
1. Read `config/setup.md`. Attach the repo named there with push access and clone it. If GitHub is
   unavailable, carry on without steps 8 and 9's commits and log it.
2. Read `config/search-criteria.md`, `config/target-companies.md`, `config/search-pages.md` and the current
   master resume. These are the rules for this run. Never work from memory of an earlier run.
3. Read the dashboard: all `jobs`, all `outreach`, `config/master-resume`. If the repo's current master is newer
   than the dashboard copy, update `config/master-resume` (version, date, markdown). Build the set of existing
   job keys (see step 2) and the statuses the candidate set.

### 1. Collect
Turn every source into the same candidate record:
`title, company, city, workMode, pay, exp, posted, applyUrl, sources[], jd|null, recruiter|null`.

| # | Source | How |
|---|---|---|
| A | **Alert emails** | If an email connector is attached: search the job-search inbox for job alert emails received since the last run; take title, company, city and link from each. If not: read every file in `alerts/pending/` (see `alerts/README.md`), then `git mv` each processed file to `alerts/processed/`. |
| B | **Job board connector** (e.g. Indeed) | Search each title in "Titles to include" × each preferred and secondary city, in the country set in `config/setup.md`. Fetch the full description only for results that survive the pre-filter below. |
| C | **Job-board actors** (Apify, optional) | Only if `config/setup.md` says Apify is used. Prefer a board's category listing URL over keyword search, which tends to match loosely. Keep postings from the last few days. Log the cost of each call. |
| D | **Target companies: Workday feeds** | Rows with Access `Workday feed ✓`. Write `[{company, url}]` to a temp file and run `python3 ops/scripts/scan_workday.py <companies.json> config/workday-settings.json`. Needs `*.myworkdayjobs.com` allowed. |
| E | **Target companies: search pages** | Rows with Access `Search page ✓`. Open each URL from `config/search-pages.md` with a fetch tool and keep titles that match the criteria. |
| F | **Target companies: career-site index** (Apify, optional) | Rows marked `Not mapped` or `Blocked`, in one call to the `fantastic-jobs/career-site-job-listing-api` actor: `{timeRange:"24h", limit:50, locationSearch:[<country>], titleSearch:[<terms from setup.md>], titleExclusionSearch:[<exclusions from setup.md>], organizationSearch:[<exact company names>], descriptionType:"text"}`, with a charge cap. Use exact company names; prefixes over-match. |

**Pre-filter (cheap, before any description is fetched):** drop titles that are clearly below the level in
the criteria, clearly outside the field, or located only outside the preferred and secondary locations and not
remote or hybrid.

### 2. De-duplicate (across sources and against the dashboard)
- **Key** = normalised company + normalised title + city.
  - Company: lower-case; drop Pvt, Private, Ltd, Limited, Inc, Group, the country name and punctuation.
  - Title: lower-case; drop separators and trailing qualifiers; sort the words ("Head - Operations" =
    "Operations Head").
  - City aliases: treat a city and its common other names as one (e.g. Gurugram = Gurgaon). A multi-city
    posting matches on any shared city.
- Exact key → one card; combine `sources`. Near match (same company and city, titles at least 80% similar) →
  merge and tag "possible duplicate".
- Recruiter postings that don't name the client: key on title + city + experience range + recruiter. The same
  role from two recruiters stays as two cards, tagged "similar role via another recruiter".
- The fullest record supplies the description: full job description > structured fields > alert email. Fill gaps
  from the others and keep every apply link.
- Against the dashboard: an existing key updates that card (add the source, refresh "still open") and is never
  added again. A key the candidate marked skipped or applied stays hidden. Reposted after 30 days or more → a
  new card tagged "reposted".

### 3. Fill missing descriptions
For records without a description, look for the same role on the company's careers source or the job board
connector. Not found → `jd: null`; the card says "description not available".

### 4. Filter by the search criteria
Apply every rule in `config/search-criteria.md` as written today: titles, locations, pay floor (undisclosed pay
stays in), sectors and exclusions. Excluded roles are counted in the run log, not written as cards.

### 5. Company check
- For a company with no snapshot on an existing card, look up its employee rating. No paid tools.
  Prefer a search connector that can read whole pages (e.g. Parallel Search); otherwise the built-in web search
  and fetch. Use one fixed random `session_id` for all Parallel calls in a run.
  1. **AmbitionBox first** for employers in India: search `"<company>" AmbitionBox reviews`, take the overview
     page whose company name **exactly** matches the employer (ignore look-alikes and location sub-pages), and
     read the overall rating, review count, work-life balance, culture, career growth and headcount.
  2. **Glassdoor** when AmbitionBox has no exact match or fewer than 20 reviews, or first for employers outside
     India: the `/Reviews/<Company>-Reviews-E<id>.htm` page for the exact employer.
  3. Write `snapshot{source, rating, reviews, wlb, culture, growth, headcount, url}` with numbers read from the
     page only. Neither found → `snapshot: null`, tag "no rating profile found". Page could not be read →
     `snapshot: null`, tag "rating not checked", and log it. Never drop a card for this.
  4. Skip the lookup for recruiter postings with an unnamed client.
- Apply the company gate from the criteria. A rating below the flag level gets a red-flag tag. An unnamed
  recruiter client goes to Maybe, tagged "client unnamed — ask recruiter".

### 6. Score and write cards
- Fit 0–100 using the weights in the criteria, judged against the **current master resume**. Cut-offs from the
  criteria decide `section: "main"`, `"maybe"` or dropped (counted in the log).
- Card fields (dashboard `jobs/<id>`, id = `<source>-<stable id>`, e.g. `wd-<company>-<req>`):
  `title, company, city, workMode, pay, exp, posted (YYYY-MM-DD), sources[], applyUrls[], fit, section,
  status: "new", summary (1–2 plain sentences), why[] (2–3 specific matches to the resume), gaps[] (honest),
  snapshot|null, tags[], jd|null`.
- The scan only ever writes `status: "new"` on new cards. The candidate moves them to shortlisted, applied or
  skipped.
- Write in batches of 50 or fewer. New cards need no `if_version`; updates use the one read in step 0.

### 7. Recruiter contacts → Outreach
- From recruiter postings, record the **named consultant** and firm, with the posting URL as the source.
- Email only if the firm itself publishes it on a posting or its team page. Never guess from name patterns.
- Write to `outreach/<firm-id>` → `contacts[]` entries `{name, role, email|null, emailSource|null, sourceUrl,
  foundOn}`. Merge; don't duplicate.

### 8. Tailor, check and archive drafts
For every job with a `tailored` draft that is not yet `validated` (drafts made with the dashboard's
**Tailor now** button are quick, unchecked proposals), follow `ops/skills/resume-tailoring/SKILL.md`. That skill
owns the tailoring rules, the Markdown format, the PDF export and release, and its stages 5–6 hand the draft to an
independent reviewer running `ops/skills/resume-release-check/SKILL.md`. In short, per job:
1. Folder `jobs/YYYY-MM-<company-slug>-<role-slug>/`; start from the card's draft, re-tailor where it breaks
   the skill's rules, and run `python3 ops/scripts/resume_md.py lint` until clean.
2. Export both PDFs, then run the release check with a fresh reviewer; fix and re-check, two rounds at most.
3. PASS → commit (`<company>: tailored resume + cover letter from master vN (checked)`), push, and set
   `tailored.validated`, `validatedAt`, `repoPath` on the card. Not PASS → leave `validated` false, write the
   open findings to the folder's `notes.md`, and mention it in the run message.

### 9. Run log and message
- Dashboard `runs/<YYYY-MM-DD>` and repo `ops/runs/YYYY-MM-DD.md`: one-line summary; per source a count,
  "failed: reason" or "skipped: reason"; scanned, kept, merged, excluded by criteria, dropped for low fit, companies
  looked up; cost in USD. Commit the repo file (`run: YYYY-MM-DD`).
- Once a week, add a digest: new roles this week, outreach follow-ups due, applications with no movement for
  10+ days.
- Final message, 3–6 lines: counts by source, the top new roles (title, company, fit), drafts checked (released,
  or still draft and why), anything that failed, cost. No recap of the steps.

## Known quirks
- Workday feeds return global postings; location filtering happens in `scan_workday.py`.
- Rating searches return look-alike companies and location sub-pages; use the exact employer's own page.
- Built-in fetch tools can ask for per-site approval, which nobody answers in an unattended run. A search
  connector that reads pages avoids that.
- Some careers sites refuse automated reading. Mark them `Blocked`; the career-site index or job-board search by
  company name covers them.
- Some Apify actors start paid runs whenever their connector connects, even if no tool is called. Disconnect an
  actor you have stopped using; leaving it unused is not enough.
