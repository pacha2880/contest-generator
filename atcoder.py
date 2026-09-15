import json
import os
import re
import sys
import time

import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CONTESTS_URL = "https://kenkoooo.com/atcoder/resources/contests.json"
CONTEST_PROBLEM_URL = "https://kenkoooo.com/atcoder/resources/contest-problem.json"
SUBMISSIONS_URL = "https://kenkoooo.com/atcoder/atcoder-api/v3/user/submissions"

# Unofficial, undocumented endpoint that powers vjudge.net's own status page
# (confirmed 2026-09-14 by inspecting the request the page itself makes).
# probNum for AtCoder problems already matches kenkoooo's problem_id format
# (e.g. "abc415_b"), so no translation is needed between the two sources.
VJUDGE_STATUS_URL = "https://vjudge.net/status/data"
VJUDGE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "X-Requested-With": "XMLHttpRequest",
}

ABC_RE = re.compile(r"^abc(\d+)$")


def load_config(path="config.json"):
    with open(path) as f:
        return json.load(f)


def fetch_contests():
    print("Fetching AtCoder contest list...", end="", flush=True)
    r = requests.get(CONTESTS_URL, timeout=30)
    r.raise_for_status()
    contests = r.json()
    print(f" {len(contests)} contests loaded")
    return contests


def fetch_contest_problems():
    print("Fetching contest-problem map...", end="", flush=True)
    r = requests.get(CONTEST_PROBLEM_URL, timeout=30)
    r.raise_for_status()
    mapping = {}
    for row in r.json():
        mapping.setdefault(row["contest_id"], []).append(row["problem_id"])
    print(f" {len(mapping)} contests mapped")
    return mapping


def fetch_user_ac(user):
    print(f"  [{user}] fetching submissions...", end="", flush=True)
    solved = set()
    from_second = 0
    total = 0
    while True:
        try:
            r = requests.get(
                SUBMISSIONS_URL,
                params={"user": user, "from_second": from_second},
                timeout=30,
            )
            r.raise_for_status()
            batch = r.json()
        except Exception as e:
            print(f" request failed: {e}")
            break
        if not batch:
            break
        for sub in batch:
            total += 1
            if sub.get("result") == "AC":
                solved.add(sub["problem_id"])
        if len(batch) < 500:
            break
        from_second = batch[-1]["epoch_second"] + 1
        time.sleep(0.3)
    print(f" {len(solved)} accepted ({total} submissions)")
    return solved


def fetch_user_vjudge_ac(vjudge_user, page_size=100):
    """Accepted AtCoder problems submitted through vjudge.net's mirror, which
    doesn't show up in kenkoooo's own submissions API. Recognized by probNum
    (== kenkoooo's problem_id) with status "Accepted", filtered server-side
    to OJId=AtCoder. recordsTotal/recordsFiltered in the response are dummy
    sentinel values, not real counts, so pagination stops on a short page."""
    print(f"  [{vjudge_user}] (vjudge) fetching submissions...", end="", flush=True)
    solved = set()
    start = 0
    total = 0
    while True:
        try:
            r = requests.get(
                VJUDGE_STATUS_URL,
                params={"draw": 1, "start": start, "length": page_size,
                        "un": vjudge_user, "OJId": "AtCoder"},
                headers=VJUDGE_HEADERS,
                timeout=20,
            )
            r.raise_for_status()
            rows = r.json().get("data", [])
        except Exception as e:
            print(f" request failed: {e}")
            break
        if not rows:
            break
        for row in rows:
            total += 1
            if row.get("status") == "Accepted":
                solved.add(row["probNum"])
        if len(rows) < page_size:
            break
        start += page_size
        time.sleep(0.3)
    print(f" {len(solved)} accepted ({total} submissions)")
    return solved


def fetch_group_solved(users):
    """`users` is a list of {"atcoder": handle, "vjudge": handle_or_None}.
    Unions each member's AtCoder-native submissions with their vjudge mirror
    submissions (when they have a vjudge handle on file)."""
    solved = set()
    for user in users:
        solved |= fetch_user_ac(user["atcoder"])
        vjudge_user = user.get("vjudge")
        if vjudge_user:
            solved |= fetch_user_vjudge_ac(vjudge_user)
    return solved


def find_recommended_abc(users, count, lookback):
    contests = fetch_contests()
    abc_contests = []
    for c in contests:
        m = ABC_RE.match(c["id"])
        if m:
            abc_contests.append((int(m.group(1)), c))
    abc_contests.sort(key=lambda x: x[0], reverse=True)
    abc_contests = abc_contests[:lookback]

    problem_map = fetch_contest_problems()

    print("\n=== Fetching user submissions ===")
    solved = fetch_group_solved(users)
    print(f"  Total unique accepted problems across all users: {len(solved)}\n")

    recommended = []
    for _, c in abc_contests:
        problems = problem_map.get(c["id"], [])
        if not problems:
            continue
        if any(p in solved for p in problems):
            continue
        recommended.append(c)
        if len(recommended) >= count:
            break
    return recommended


def build_link(contest_id):
    return f"https://atcoder.jp/contests/{contest_id}"


def main():
    cfg = load_config()
    ac_cfg = cfg.get("atcoder", {})
    users = ac_cfg.get("users", [])
    count = ac_cfg.get("count", 5)
    lookback = ac_cfg.get("lookback", 50)
    output_path = ac_cfg.get("output_links", "outputs/atcoder_links.txt")

    if not users:
        print("No hay usuarios configurados en config.json['atcoder']['users'].")
        return

    user_labels = [
        f"{u['atcoder']}+vjudge:{u['vjudge']}" if u.get("vjudge") else u["atcoder"]
        for u in users
    ]
    print(f"Users ({len(users)}): {', '.join(user_labels)}")
    print(f"Looking back {lookback} most recent ABCs, recommending up to {count}.\n")

    recommended = find_recommended_abc(users, count, lookback)

    print(f"=== Recommended ABCs ({len(recommended)}/{count}) ===")
    links = []
    for c in recommended:
        link = build_link(c["id"])
        links.append(link)
        print(f"  {c['id']}  |  {c['title']}  |  {link}")

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for link in links:
            f.write(link + "\n")

    print(f"\nSaved {len(links)} links to {output_path}")


if __name__ == "__main__":
    main()
