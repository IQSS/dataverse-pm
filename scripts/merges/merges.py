#!/usr/bin/env python3
"""Figure out who merged each pull request into IQSS/dataverse's develop branch.

Subcommands:
  collect  Read git history and write out/prs.csv (one row per merged PR).
  fetch    Ask the GitHub API who merged each PR and cache the answers in cache/.
  report   Combine the two and write out/merges.csv plus summary tables.

Standard library only. See README.md for details.
"""

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "out"
API_DIR = HERE / "cache"
PRS_CSV = DATA / "prs.csv"
MERGES_CSV = DATA / "merges.csv"

REPO = "IQSS/dataverse"
DEFAULT_GIT_DIR = Path.home() / "github/iqss/dataverse"
DEFAULT_SINCE = "2023-11-05"

# Git author names that are the same person as another name.
ALIASES = {
    "ofahimIQSS": "Omer Fahim",
}

MERGE_RE = re.compile(r"^Merge pull request #(\d+) from ")
SQUASH_RE = re.compile(r"\(#(\d+)\)$")
SEP = "\x1f"


# ---------------------------------------------------------------- collect

def git_log(git_dir, branch, since, merges):
    fmt = SEP.join(["%H", "%ad", "%an", "%cn", "%s"])
    cmd = ["git", "-C", str(git_dir), "log", "--first-parent", branch,
           f"--since={since}", "--date=short", f"--format={fmt}"]
    cmd.append("--merges" if merges else "--no-merges")
    out = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout
    for line in out.splitlines():
        sha, date, author, committer, subject = line.split(SEP, 4)
        yield sha, date, author, committer, subject


def cmd_collect(args):
    rows = []
    for sha, date, author, committer, subject in git_log(args.git_dir, args.branch, args.since, True):
        m = MERGE_RE.match(subject)
        if not m:
            continue
        # For a merge commit made in GitHub's web UI, the author is the person who clicked merge.
        rows.append(dict(pr=int(m.group(1)), date=date, method="merge",
                         git_merger=ALIASES.get(author, author), git_author="",
                         subject=subject, sha=sha))
    for sha, date, author, committer, subject in git_log(args.git_dir, args.branch, args.since, False):
        m = SQUASH_RE.search(subject)
        if not m:
            continue  # a direct push, not a PR
        # For a squash merge, the author is the PR author; git doesn't record the merger.
        rows.append(dict(pr=int(m.group(1)), date=date, method="squash",
                         git_merger="", git_author=author,
                         subject=subject, sha=sha))
    rows.sort(key=lambda r: (r["date"], r["pr"]), reverse=True)
    DATA.mkdir(parents=True, exist_ok=True)
    with PRS_CSV.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    c = Counter(r["method"] for r in rows)
    print(f"Wrote {len(rows)} PRs to {PRS_CSV} ({c['merge']} merge commits, {c['squash']} squash merges)")


# ---------------------------------------------------------------- fetch

def read_prs():
    if not PRS_CSV.exists():
        sys.exit(f"{PRS_CSV} not found. Run 'collect' first.")
    with PRS_CSV.open() as f:
        return list(csv.DictReader(f))


def get_token(args):
    if args.token:
        return args.token
    if os.environ.get("GITHUB_TOKEN"):
        return os.environ["GITHUB_TOKEN"]
    if args.gh:
        if not shutil.which("gh"):
            sys.exit("--gh given but gh is not installed (brew install gh, then gh auth login).")
        return subprocess.run(["gh", "auth", "token"], check=True,
                              capture_output=True, text=True).stdout.strip()
    return None


def api_get(url, token):
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "dataverse-merge-stats",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.load(resp), resp.headers
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        return e.code, body, e.headers


def wait_for_reset(headers, can_wait):
    reset = int(headers.get("X-RateLimit-Reset", "0"))
    secs = max(0, reset - int(time.time())) + 5
    when = datetime.fromtimestamp(reset).strftime("%H:%M:%S")
    if not can_wait:
        print(f"Rate limit reached. It resets at {when} (in {secs // 60} min). "
              f"Run fetch again then, or use --wait.")
        return False
    print(f"Rate limit reached. Sleeping {secs // 60} min until {when}...", flush=True)
    time.sleep(secs)
    return True


def cmd_fetch(args):
    token = get_token(args)
    print("Using an authenticated token (5000 requests/hour)." if token
          else "Unauthenticated (60 requests/hour). Use --gh or GITHUB_TOKEN for more.")
    API_DIR.mkdir(parents=True, exist_ok=True)

    prs = read_prs()
    if not args.all:
        prs = [p for p in prs if p["method"] == "squash"]
    todo = [p for p in prs if not (API_DIR / f"{p['pr']}.json").exists()]
    print(f"{len(prs) - len(todo)} of {len(prs)} already cached, {len(todo)} to fetch.")
    if args.limit:
        todo = todo[:args.limit]
        print(f"Fetching only {len(todo)} this run (--limit).")

    done = 0
    i = 0
    while i < len(todo):
        p = todo[i]
        status, body, headers = api_get(f"https://api.github.com/repos/{REPO}/pulls/{p['pr']}", token)
        remaining = headers.get("X-RateLimit-Remaining") if headers else None
        if status in (403, 429) and remaining == "0":
            if wait_for_reset(headers, args.wait):
                continue  # retry the same PR
            break
        if status != 200:
            print(f"  #{p['pr']}: HTTP {status}: {str(body)[:200]}")
            i += 1
            continue
        record = {
            "pr": body["number"],
            "title": body["title"],
            "author": (body.get("user") or {}).get("login"),
            "merged_by": (body.get("merged_by") or {}).get("login"),
            "merged_at": body.get("merged_at"),
            "merge_commit_sha": body.get("merge_commit_sha"),
            "base": (body.get("base") or {}).get("ref"),
            "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        (API_DIR / f"{p['pr']}.json").write_text(json.dumps(record, indent=2) + "\n")
        done += 1
        i += 1
        print(f"  #{record['pr']}: merged by {record['merged_by']}  (remaining: {remaining})", flush=True)
        if remaining == "0" and i < len(todo):
            if not wait_for_reset(headers, args.wait):
                break
    print(f"Fetched {done}. {len(todo) - i} left in this run's list.")


# ---------------------------------------------------------------- report

def load_api():
    out = {}
    for f in API_DIR.glob("*.json"):
        r = json.loads(f.read_text())
        out[int(r["pr"])] = r
    return out


def period_of(date, bounds):
    for label, start, end in bounds:
        if start <= date < end:
            return label
    return None


def print_table(title, counter):
    total = sum(counter.values())
    print(f"\n{title} ({total} PRs)")
    for name, n in counter.most_common():
        print(f"  {n:5d}  {n * 100 / total:5.1f}%  {name}")


def learn_logins(prs, api):
    """Map git names to GitHub logins using pairs the API data reveals."""
    seen = defaultdict(Counter)
    for p in prs:
        a = api.get(int(p["pr"]))
        if not a:
            continue
        if p["method"] == "squash" and p["git_author"] and a.get("author"):
            seen[p["git_author"]][a["author"]] += 1
        if p["method"] == "merge" and p["git_merger"] and a.get("merged_by"):
            seen[p["git_merger"]][a["merged_by"]] += 1
    return {name: c.most_common(1)[0][0] for name, c in seen.items()}


def cmd_report(args):
    prs = read_prs()
    api = load_api()
    logins = learn_logins(prs, api)
    rows = []
    mismatches = []
    for p in prs:
        n = int(p["pr"])
        a = api.get(n)
        api_login = a["merged_by"] if a else ""
        if p["method"] == "merge":
            # Use the GitHub login when we've learned it, so each person has one name.
            merger, source = logins.get(p["git_merger"], p["git_merger"]), "git"
            if a and api_login:
                merger, source = api_login, "api"
                mismatches.append((n, p["git_merger"], api_login))
        else:
            if api_login:
                merger, source = api_login, "api"
            else:
                merger, source = "squash merge", "none"
        rows.append(dict(pr=n, date=p["date"], method=p["method"], merger=merger, source=source,
                         pr_author=(a or {}).get("author") or p["git_author"],
                         subject=p["subject"], url=f"https://github.com/{REPO}/pull/{n}"))

    with MERGES_CSV.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {MERGES_CSV}")

    squash = [r for r in rows if r["method"] == "squash"]
    known = sum(1 for r in squash if r["source"] == "api")
    print(f"Squash merges resolved via API: {known} of {len(squash)}")
    if mismatches:
        print(f"Regular merges checked against API: {len(mismatches)} (git name vs GitHub login)")
        pairs = Counter((g, l) for _, g, l in mismatches)
        for (g, l), c in pairs.most_common():
            print(f"  {c:4d}  {g} -> {l}")

    print_table("All PRs", Counter(r["merger"] for r in rows))
    print_table("Squash merges only", Counter(r["merger"] for r in squash))

    today = datetime.now().strftime("%Y-%m-%d")
    bounds = [
        ("Nov 2023 - Oct 2024", "2023-11-05", "2024-11-05"),
        ("Nov 2024 - Oct 2025", "2024-11-05", "2025-11-05"),
        ("Nov 2025 - now", "2025-11-05", "9999"),
    ]
    by_period = defaultdict(Counter)
    for r in rows:
        label = period_of(r["date"], bounds)
        if label:
            by_period[label][r["merger"]] += 1
    for label, _, _ in bounds:
        if by_period[label]:
            print_table(label, by_period[label])
    if args.since:
        print_table(f"Since {args.since}", Counter(r["merger"] for r in rows if r["date"] >= args.since))


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("collect", help="read git history into out/prs.csv")
    c.add_argument("--git-dir", type=Path, default=DEFAULT_GIT_DIR)
    c.add_argument("--branch", default="develop")
    c.add_argument("--since", default=DEFAULT_SINCE)
    c.set_defaults(func=cmd_collect)

    f = sub.add_parser("fetch", help="ask the GitHub API who merged each PR (cached, resumable)")
    f.add_argument("--all", action="store_true", help="fetch regular merges too, not just squash merges")
    f.add_argument("--limit", type=int, help="fetch at most this many PRs this run")
    f.add_argument("--wait", action="store_true", help="sleep through rate-limit resets instead of stopping")
    f.add_argument("--gh", action="store_true", help="authenticate with the token from 'gh auth token'")
    f.add_argument("--token", help="GitHub token (or set GITHUB_TOKEN)")
    f.set_defaults(func=cmd_fetch)

    r = sub.add_parser("report", help="write out/merges.csv and print summary tables")
    r.add_argument("--since", help="also print a table for PRs merged on or after this date (YYYY-MM-DD)")
    r.set_defaults(func=cmd_report)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
