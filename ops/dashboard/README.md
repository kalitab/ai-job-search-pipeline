# Dashboard

`index.html` is the source of the dashboard. Publish it as a Claude artifact with the `db`, `user`, `sample` and `downloads` capabilities, and put its link in `config/setup.md`.

Its data lives in the artifact's database, not in this repo:

| Collection or document | Holds |
|---|---|
| `jobs` | One card per role, written by the daily scan |
| `applications` | Stage and next step for roles marked applied |
| `outreach` | Recruiter and company contacts |
| `runs` | One record per daily run |
| `config/master-resume` | `{version, updated, markdown}` of the current master resume |

Tabs: **Jobs** (new and shortlisted, with Maybe below), **Applied**, **Skipped**, **Resumes** and **Outreach**.

**Tailor now** drafts a resume and cover letter in the browser. These drafts are marked "not yet checked" until the next scheduled run audits them and archives them to GitHub.

After changing `index.html`, republish it to the same artifact link and commit the change here.
