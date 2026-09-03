"""
generate_contest.py
Genera UN problema por dificultad (800-2000), sin repetir los de results.txt
ni solved.txt, sin problemas en ruso, y escribe contest.txt en orden aleatorio
sin mostrar la dificultad.
"""

import json
import random
import re
import sys
import time

import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CF_API     = "https://codeforces.com/api"
RESULTS    = "results.txt"
SOLVED     = "solved.txt"
OUTPUT     = "contest.txt"
DIFFICULTIES = [800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000]


# ── helpers ───────────────────────────────────────────────────────────────────

def is_russian(name: str) -> bool:
    return any("Ѐ" <= ch <= "ӿ" for ch in name)


def load_banned() -> set:
    banned = set()

    # From solved.txt
    try:
        with open(SOLVED, encoding="utf-8") as f:
            for line in f:
                v = line.strip()
                if v:
                    banned.add(v)
    except FileNotFoundError:
        pass

    # From results.txt  (parse URLs like /contest/2217/problem/D)
    url_re = re.compile(r"/contest/(\d+)/problem/([A-Z0-9]+)", re.I)
    try:
        with open(RESULTS, encoding="utf-8") as f:
            for line in f:
                m = url_re.search(line)
                if m:
                    banned.add(m.group(1) + m.group(2))
    except FileNotFoundError:
        pass

    return banned


def get_user_solved(users: list) -> set:
    solved = set()
    for user in users:
        print(f"  [{user}] fetching...", end="", flush=True)
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
                print(f" {count} accepted")
            else:
                print(f" error: {data.get('comment', '?')}")
        except Exception as ex:
            print(f" failed: {ex}")
        time.sleep(0.3)
    return solved


def fetch_problemset():
    print("Fetching problemset...", end="", flush=True)
    r = requests.get(f"{CF_API}/problemset.problems", timeout=30)
    data = r.json()
    if data["status"] != "OK":
        raise RuntimeError(data.get("comment"))
    problems = data["result"]["problems"]
    stats = {
        f"{s['contestId']}{s['index']}": s["solvedCount"]
        for s in data["result"]["problemStatistics"]
        if "contestId" in s
    }
    print(f" {len(problems)} problems")
    return problems, stats


def find_one(problems, stats, rating, user_solved, banned):
    candidates = []
    for p in problems:
        if p.get("rating") != rating or "contestId" not in p:
            continue
        key = f"{p['contestId']}{p['index']}"
        if key in user_solved or key in banned:
            continue
        if is_russian(p["name"]):
            continue
        candidates.append({
            "key":        key,
            "url":        f"https://codeforces.com/contest/{p['contestId']}/problem/{p['index']}",
            "name":       p["name"],
            "rating":     rating,
            "contestId":  p["contestId"],
            "solvedCount": stats.get(key, 0),
        })
    # Most recent first
    candidates.sort(key=lambda x: x["contestId"], reverse=True)
    return candidates[0] if candidates else None


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    with open("config.json") as f:
        cfg = json.load(f)
    users = cfg.get("users", [])

    print("=== Loading banned problems ===")
    banned = load_banned()
    print(f"  {len(banned)} problems banned (results.txt + solved.txt)\n")

    print("=== Fetching user solved problems ===")
    user_solved = get_user_solved(users)
    print(f"  {len(user_solved)} unique accepted\n")

    print("=== Fetching problemset ===")
    problems, stats = fetch_problemset()
    print()

    print("=== Selecting problems ===")
    selected = []
    for diff in DIFFICULTIES:
        prob = find_one(problems, stats, diff, user_solved, banned)
        if prob:
            selected.append(prob)
            print(f"  {diff:4d}: {prob['name']}  ({prob['url']})")
        else:
            print(f"  {diff:4d}: NO PROBLEM FOUND")

    # Shuffle — no difficulty info in output
    random.shuffle(selected)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        for prob in selected:
            f.write(f"{prob['url']}  |  {prob['name']}\n")

    # Add to solved.txt so they don't appear again
    with open(SOLVED, "a", encoding="utf-8") as f:
        for prob in selected:
            f.write(prob["key"] + "\n")

    print(f"\n{len(selected)} problems written to {OUTPUT} (shuffled, no ratings).")
    print(f"Keys saved to {SOLVED}.")


if __name__ == "__main__":
    main()
