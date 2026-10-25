# Target companies

Every daily run reads this table and scans each company through its **Access** column, then keeps only roles that pass `search-criteria.md`. Delete a row to stop scanning it; add a row to start.

Ask your AI assistant to find and test each company's careers source when you add it, and to fill in the Access column with what worked.

| # | Company | Cities | Type | Careers source | Access |
| --- | --- | --- | --- | --- | --- |
| 1 | <Company name> | <cities> | <listed / multinational / private> | <careers page or Workday URL> | <one of the values below> |

## Access values

| Access | What the scan does |
| --- | --- |
| `Workday feed ✓` | Reads the company's Workday job feed with `ops/scripts/scan_workday.py`. Careers source is the `https://<company>.wd<n>.myworkdayjobs.com/<site>` URL. |
| `Search page ✓` | Opens the careers search page listed in `search-pages.md` and keeps matching titles. |
| `Not mapped` | Looked up through the career-site index (Apify, optional) and job-board searches by company name. |
| `Blocked` | The site refuses automated reading. Same fallback as Not mapped. |
