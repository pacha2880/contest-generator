import json
import os
import sys
import time
import requests
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CF_API = "https://codeforces.com/api"
PAST_FILE = "solved.txt"


def load_config(path="config.json"):
    with open(path) as f:
        return json.load(f)


def get_user_solved(users, *, on_progress):
    solved = set()
    for user in users:
        on_progress(f"[{user}] fetching submissions...")
        try:
            r = requests.get(
                f"{CF_API}/user.status",
                params={"handle": user, "from": 1, "count": 10000},
                timeout=20,
            )
            data = r.json()
            if data["status"] == "OK":
                count = 0
                for sub in data["result"]:
                    if sub.get("verdict") == "OK" and "contestId" in sub["problem"]:
                        p = sub["problem"]
                        solved.add(f"{p['contestId']}{p['index']}")
                        count += 1
                on_progress(f"[{user}] {count} accepted")
            else:
                on_progress(f"[{user}] API error: {data.get('comment', '?')}")
        except Exception as e:
            on_progress(f"[{user}] request failed: {e}")
        time.sleep(0.3)
    return solved


def fetch_problemset(*, on_progress):
    on_progress("Fetching full problemset from Codeforces API...")
    r = requests.get(f"{CF_API}/problemset.problems", timeout=30)
    data = r.json()
    if data["status"] != "OK":
        raise RuntimeError(f"Problemset API error: {data.get('comment')}")
    problems = data["result"]["problems"]
    stats = {
        f"{s['contestId']}{s['index']}": s["solvedCount"]
        for s in data["result"]["problemStatistics"]
        if "contestId" in s
    }
    on_progress(f"{len(problems)} problems loaded")
    return problems, stats


def load_past(path=PAST_FILE):
    past = set()
    try:
        with open(path) as f:
            for line in f:
                v = line.strip()
                if v:
                    past.add(v)
    except FileNotFoundError:
        pass
    return past


def save_past(keys, path=PAST_FILE):
    with open(path, "a") as f:
        for k in keys:
            f.write(k + "\n")


def find_unsolved(problems, stats, rating, user_solved, past, count):
    candidates = []
    for p in problems:
        if p.get("rating") != rating or "contestId" not in p:
            continue
        key = f"{p['contestId']}{p['index']}"
        if key in user_solved or key in past:
            continue
        candidates.append({
            "key": key,
            "contestId": p["contestId"],
            "index": p["index"],
            "name": p["name"],
            "solvedCount": stats.get(key, 0),
            "url": f"https://codeforces.com/contest/{p['contestId']}/problem/{p['index']}",
        })
    candidates.sort(key=lambda x: x["contestId"], reverse=True)
    return candidates[:count]


def main():
    cfg = load_config()
    cf_cfg = cfg.get("codeforces", {})
    users = cf_cfg.get("users", [])
    diff_list = cf_cfg.get("difficulties", [])
    output_path = cf_cfg.get("output_links", "results.txt")

    if not users:
        raise ValueError("config.json['codeforces']['users'] is empty")

    if not diff_list:
        raise ValueError("config.json['codeforces']['difficulties'] is empty")

    diff_count = Counter(int(d) for d in diff_list)

    print(f"\nUsers ({len(users)}): {', '.join(users)}")
    print("Problems needed per difficulty:")
    for r, c in sorted(diff_count.items(), reverse=True):
        print(f"  {r}: {c}")
    print()

    print("=== Step 1: Collecting solved problems ===")
    user_solved = get_user_solved(users, on_progress=print)
    print(f"  Total unique accepted problems across all users: {len(user_solved)}\n")

    print("=== Step 2: Fetching problemset ===")
    problems, stats = fetch_problemset(on_progress=print)
    print()

    past = load_past()
    print(f"Previously recommended (skipped): {len(past)}\n")

    print("=== Results ===\n")
    newly_recommended = []
    result_lines = []

    for rating in sorted(diff_count.keys(), reverse=True):
        needed = diff_count[rating]
        found = find_unsolved(problems, stats, rating, user_solved, past, needed)

        print(f"[{rating}] {len(found)}/{needed} problems:")
        result_lines.append(f"[{rating}] {len(found)}/{needed} problems:")
        for p in found:
            line = f"  [{rating}] {p['url']}  |  {p['name']}  (solved by {p['solvedCount']} on CF)"
            print(line)
            result_lines.append(line)
            newly_recommended.append(p["key"])

        if len(found) < needed:
            note = f"  (only {len(found)} unsolved problems available at this rating)"
            print(note)
            result_lines.append(note)
        print()
        result_lines.append("")

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(result_lines))

    save_past(newly_recommended)
    print(f"Saved {len(newly_recommended)} problems to {PAST_FILE}.")
    print(f"Full results saved to {output_path}")


if __name__ == "__main__":
    main()
