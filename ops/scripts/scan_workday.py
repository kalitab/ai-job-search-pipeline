#!/usr/bin/env python3
"""Scan Workday careers sites for roles that match your search.

Usage:
  python3 ops/scripts/scan_workday.py companies.json settings.json > workday_hits.json

companies.json  the "Workday feed" rows of config/target-companies.md, as
                [{"company": "Example Corp", "url": "https://example.wd5.myworkdayjobs.com/Careers"}, ...]
settings.json   what to look for (see config/workday-settings.example.json):
                {
                  "search_terms":   ["head of operations", "operations director"],
                  "title_include":  "operations|programme|program",
                  "title_exclude":  "intern|analyst|assistant",
                  "locations":      "India|Gurgaon|Gurugram|Noida|Hyderabad|Pune|Remote"
                }
                title_include, title_exclude and locations are case-insensitive regular expressions.
                Leave title_exclude empty ("") to keep every matching title.

Output: JSON list of {company, title, locations, posted, url, jd} for postings whose title matches
title_include, does not match title_exclude, and whose location matches locations.
Per-company errors are reported as {"company": ..., "error": ...} and never abort the run.
Needs *.myworkdayjobs.com on the session's allowed network domains.
"""
import concurrent.futures as cf
import html
import json
import re
import sys
import urllib.request


def _post(url, body):
    req = urllib.request.Request(url, json.dumps(body).encode(),
                                 {"Content-Type": "application/json", "Accept": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=25))


def _get(url):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=25))


def make_scanner(settings):
    terms = settings.get("search_terms") or []
    include = re.compile(settings.get("title_include") or ".", re.I)
    exclude_src = settings.get("title_exclude") or ""
    exclude = re.compile(exclude_src, re.I) if exclude_src else None
    where = re.compile(settings.get("locations") or ".", re.I)

    def scan(entry):
        name, site_url = entry["company"], entry["url"].rstrip("/")
        m = re.match(r"https://([^.]+)\.(wd\d+)\.myworkdayjobs\.com/(?:[a-z]{2}-[A-Z]{2}/)?([^/?#]+)", site_url)
        if not m:
            return [{"company": name, "error": f"not a Workday site URL: {site_url}"}]
        tenant, wd, site = m.groups()
        base = f"https://{tenant}.{wd}.myworkdayjobs.com/wday/cxs/{tenant}/{site}"
        postings = {}
        try:
            for term in terms:
                for offset in (0, 20):
                    data = _post(base + "/jobs", {"limit": 20, "offset": offset, "searchText": term, "appliedFacets": {}})
                    for j in data.get("jobPostings", []):
                        postings[j.get("externalPath")] = j
                    if len(data.get("jobPostings", [])) < 20:
                        break
        except Exception as e:  # noqa: BLE001
            return [{"company": name, "error": f"{type(e).__name__}: {str(e)[:80]}"}]
        hits = []
        for path, j in postings.items():
            title = j.get("title", "")
            if not include.search(title) or (exclude and exclude.search(title)):
                continue
            locs, jd = j.get("locationsText", ""), None
            try:
                info = _get(base + path).get("jobPostingInfo", {})
                locs = " | ".join([info.get("location", "")] + info.get("additionalLocations", [])) or locs
                jd = re.sub(r"<[^>]+>", " ", html.unescape(info.get("jobDescription", "")))
                jd = re.sub(r"\s+", " ", jd).strip()[:6000]
            except Exception:  # noqa: BLE001
                pass
            if where.search(locs or ""):
                hits.append({"company": name, "title": title, "locations": locs, "posted": j.get("postedOn"),
                             "url": f"https://{tenant}.{wd}.myworkdayjobs.com/{site}{path}", "jd": jd})
        return hits

    return scan


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    companies = json.load(open(sys.argv[1]))
    settings = json.load(open(sys.argv[2]))
    if not settings.get("search_terms"):
        sys.exit("settings.json needs at least one entry in search_terms")
    scan = make_scanner(settings)
    out = []
    with cf.ThreadPoolExecutor(8) as ex:
        for res in ex.map(scan, companies):
            out.extend(res)
    json.dump(out, sys.stdout, ensure_ascii=False, indent=1)
