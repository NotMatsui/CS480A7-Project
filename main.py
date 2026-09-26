import calendar
import json
import os
import sys
import time
from collections import Counter
import datetime

import requests

OWNER = "zephyrproject-rtos"
REPO = "zephyr"
PR = 103195

SINCE = "2021-09-20"
TO = "2026-09-20"

BASE = f"https://api.github.com/repos/{OWNER}/{REPO}"

gh = requests.Session()
gh.headers["Accept"] = "application/vnd.github+json"
gh.headers["User-Agent"] = "cs480a7-project5"
gh.headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"

def get(path, **params):
    r = gh.get(BASE + path, params=params)
    print(
        f"   [{r.headers['x-ratelimit-remaining']} of {r.headers['x-ratelimit-limit']} left]"
    )
    return r.json()

OUT = "zephyr_prs.csv"
LOG = "mine.log"


def log(msg):
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")


def wait_if_low():
    core = gh.get("https://api.github.com/rate_limit").json()["resources"]["core"]
    if core["remaining"] < 50:
        nap = core["reset"] - time.time() + 5
        log(f"only {core['remaining']} requests left, sleeping {nap / 60:.0f} min")
        time.sleep(max(nap, 0))


def search(query):
    url = "https://api.github.com/search/issues"
    params = {"q": query, "per_page": 100}
    items, total = [], None

    while url:
        r = gh.get(url, params=params)
        body = r.json()

        if "items" not in body:  # search rate limit, wait and retry the same url
            reset = int(r.headers.get("x-ratelimit-reset", time.time() + 60))
            nap = max(reset - time.time() + 2, 2)
            log(f"search limit hit, sleeping {nap:.0f}s")
            time.sleep(nap)
            continue

        if total is None:
            total = body["total_count"]
            if total >= 1000:
                log(
                    f"WARNING {total} results, search only returns 1000. Window too big."
                )

        items += body["items"]
        if "next" not in r.links:
            break
        url = r.links["next"]["url"]
        params = None
    return items


def find_pr_numbers():
    # half months, because a whole month of zephyr PRs gets close to the 1000 cap
    numbers = []
    for YEAR in range(datetime.datetime.strptime(SINCE, "%Y-%m-%d").year, datetime.datetime.strptime(TO, "%Y-%m-%d").year):
        for month in range(1, 13):
            last_day = calendar.monthrange(YEAR, month)[1]
            for first, last in ((1, 15), (16, last_day)):
                window = f"{YEAR}-{month:02d}-{first:02d}..{YEAR}-{month:02d}-{last:02d}"
                found = search(f"repo:{OWNER}/{REPO} is:pr created:{window}")
                numbers += [item["number"] for item in found]
                log(f"{window}: +{len(found)}  (total {len(numbers)})")
    return numbers


def step9():
    already_done = set()
    if os.path.exists(OUT):
        for line in open(OUT):
            already_done.add(json.loads(line)["number"])
    log(f"starting - {len(already_done)} PRs already saved, skipping those")

    numbers_file = f"pr_numbers.json"
    if os.path.exists(numbers_file):
        numbers = json.load(open(numbers_file))
        log(f"reusing cached list of {len(numbers)} PR numbers")
    else:
        numbers = find_pr_numbers()
        json.dump(numbers, open(numbers_file, "w"))
        log(f"{len(numbers)} PRs to fetch for {SINCE} to {TO}, list cached")

    saved = 0
    for i, number in enumerate(numbers):
        if number in already_done:
            continue
        if i % 20 == 0:
            wait_if_low()

        pr = get(f"/pulls/{number}")
        comments = get(f"/issues/{number}/comments", per_page=100)
        reviews = get(f"/pulls/{number}/reviews", per_page=100)
        review_comments = get(f"/pulls/{number}/comments", per_page=100)
        commits = get(f"/pulls/{number}/commits", per_page=100)

        record = {
            "number": number,
            "created_at": pr["created_at"],
            "merged_at": pr["merged_at"],
            "closed_at": pr["closed_at"],
            "author": (pr["user"] or {}).get("login"),
            "additions": pr["additions"],
            "deletions": pr["deletions"],
            "changed_files": pr["changed_files"],
            "comments": [
                {
                    "author": (c["user"] or {}).get("login"),
                    "type": (c["user"] or {}).get("type"),
                    "at": c["created_at"],
                }
                for c in comments
            ],
            "reviews": [
                {
                    "author": (r["user"] or {}).get("login"),
                    "type": (r["user"] or {}).get("type"),
                    "state": r["state"],
                    "at": r["submitted_at"],
                    "body": r["body"],
                }
                for r in reviews
            ],
            "review_comments": [
                {
                    "author": (c["user"] or {}).get("login"),
                    "type": (c["user"] or {}).get("type"),
                    "at": c["created_at"],
                    "body": c["body"],
                }
                for c in review_comments
            ],
            "commits": [
                {
                    "sha": c["sha"],
                    "author": (c["author"] or {}).get("login"),
                    "type": (c["author"] or {}).get("type"),
                    "at": c["commit"]["committer"]["date"],
                }
                for c in commits
            ],
            
        }

        with open(OUT, "a") as f:
            f.write(json.dumps(record) + "\n")

        saved += 1
        log(f"PR {number}  ({len(already_done) + saved} of {len(numbers)})")

    log(f"FINISHED - {len(already_done) + saved} PRs in {OUT}")

if __name__ == "__main__":
    step9()