import json
import os
import re
import sys
import time

import requests

from app import fetch_vjudge_rows
from cancel import StoppedByUser

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CONTESTS_URL = "https://kenkoooo.com/atcoder/resources/contests.json"
CONTEST_PROBLEM_URL = "https://kenkoooo.com/atcoder/resources/contest-problem.json"
SUBMISSIONS_URL = "https://kenkoooo.com/atcoder/atcoder-api/v3/user/submissions"

ABC_RE = re.compile(r"^abc(\d+)$")


def load_config(path="config.json"):
    with open(path) as f:
        return json.load(f)


def fetch_contests(*, on_progress):
    on_progress("Fetching AtCoder contest list...")
    r = requests.get(CONTESTS_URL, timeout=30)
    r.raise_for_status()
    contests = r.json()
    on_progress(f"{len(contests)} contests loaded")
    return contests


def fetch_contest_problems(*, on_progress):
    on_progress("Fetching contest-problem map...")
    r = requests.get(CONTEST_PROBLEM_URL, timeout=30)
    r.raise_for_status()
    mapping = {}
    for row in r.json():
        mapping.setdefault(row["contest_id"], []).append(row["problem_id"])
    on_progress(f"{len(mapping)} contests mapped")
    return mapping


def fetch_user_ac(user, *, on_progress):
    on_progress(f"[{user}] fetching submissions...")
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
            on_progress(f"[{user}] request failed: {e}")
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
    on_progress(f"[{user}] {len(solved)} accepted ({total} submissions)")
    return solved


def fetch_user_vjudge_ac(vjudge_user, *, on_progress, page_size=100):
    """Accepted AtCoder problems submitted through vjudge.net's mirror, which
    doesn't show up in kenkoooo's own submissions API. Recognized by probNum
    (== kenkoooo's problem_id) with status "Accepted", filtered server-side
    to OJId=AtCoder. Pagination/requests-vs-curl fallback lives in
    app.fetch_vjudge_rows, shared with the Codeforces-side vjudge check."""
    rows = fetch_vjudge_rows(vjudge_user, "AtCoder", on_progress=on_progress, page_size=page_size)
    solved = {row["probNum"] for row in rows if row.get("status") == "Accepted"}
    on_progress(f"[{vjudge_user}] {len(solved)} accepted ({len(rows)} submissions)")
    return solved


def fetch_group_solved(users_atcoder, users_vjudge, *, on_progress, should_stop=lambda: False):
    """Two independent handle lists (not required to match in size or to
    correspond 1:1 — a vjudge handle doesn't need a matching AtCoder one and
    vice versa). Unions AtCoder-native submissions from users_atcoder with
    vjudge-mirror submissions from users_vjudge."""
    solved = set()
    for handle in users_atcoder:
        if should_stop():
            on_progress("Detenido por el usuario.")
            raise StoppedByUser()
        solved |= fetch_user_ac(handle, on_progress=on_progress)
    for handle in users_vjudge:
        if should_stop():
            on_progress("Detenido por el usuario.")
            raise StoppedByUser()
        solved |= fetch_user_vjudge_ac(handle, on_progress=on_progress)
    return solved


def find_recommended_abc(users_atcoder, users_vjudge, count, lookback, *, on_progress, problem_letters=None, should_stop=lambda: False):
    """problem_letters: e.g. ["c", "d", "e"] narrows the check from "any
    problem in the contest" to just those letters — a contest is recommended
    if none of THOSE specific problems were solved, even if others were.
    Empty/None means check the whole contest (original behavior). A letter
    that doesn't exist for a given contest (old ABCs use numeric suffixes,
    and some borrow problems from ARC) is reported and skipped for that
    contest; if none of the requested letters exist there, the contest is
    skipped entirely — there's nothing matching the filter to recommend."""
    contests = fetch_contests(on_progress=on_progress)
    abc_contests = []
    for c in contests:
        m = ABC_RE.match(c["id"])
        if m:
            abc_contests.append((int(m.group(1)), c))
    abc_contests.sort(key=lambda x: x[0], reverse=True)
    abc_contests = abc_contests[:lookback]

    problem_map = fetch_contest_problems(on_progress=on_progress)

    on_progress("=== Fetching user submissions ===")
    solved = fetch_group_solved(users_atcoder, users_vjudge, on_progress=on_progress, should_stop=should_stop)
    on_progress(f"Total unique accepted problems across all users: {len(solved)}")

    recommended = []
    for _, c in abc_contests:
        if should_stop():
            on_progress("Detenido por el usuario.")
            raise StoppedByUser()
        problems = problem_map.get(c["id"], [])
        if not problems:
            continue

        if problem_letters:
            target = []
            for letter in problem_letters:
                pid = f"{c['id']}_{letter}"
                if pid in problems:
                    target.append(pid)
                else:
                    on_progress(f"Nota: {c['id']} no tiene problema '{letter.upper()}', se omite para este contest")
            if not target:
                continue
        else:
            target = problems

        if any(p in solved for p in target):
            continue
        recommended.append(c)
        if len(recommended) >= count:
            break
    return recommended


def build_link(contest_id):
    return f"https://atcoder.jp/contests/{contest_id}"


def main(on_progress=print, should_stop=lambda: False):
    """on_progress defaults to print for the console entry point. The GUI
    calls this same function with its own callback instead, sharing the
    exact same logic, output files, and config.json reading."""
    cfg = load_config()
    ac_cfg = cfg.get("atcoder", {})
    users_atcoder = ac_cfg.get("users_atcoder", [])
    users_vjudge = ac_cfg.get("users_vjudge", [])
    count = ac_cfg.get("count", 5)
    lookback = ac_cfg.get("lookback", 50)
    output_path = ac_cfg.get("output_links", "outputs/atcoder_links.txt")
    problem_letters = [p.lower() for p in ac_cfg.get("problems", [])]

    if not users_atcoder and not users_vjudge:
        raise ValueError("config.json['atcoder']['users_atcoder'/'users_vjudge'] is empty")

    on_progress(f"AtCoder users ({len(users_atcoder)}): {', '.join(users_atcoder)}")
    on_progress(f"vjudge users ({len(users_vjudge)}): {', '.join(users_vjudge)}")
    if problem_letters:
        on_progress(f"Filtering to problems: {', '.join(p.upper() for p in problem_letters)}")
        base, ext = os.path.splitext(output_path)
        output_path = f"{base}_{'-'.join(p.upper() for p in problem_letters)}{ext}"
    on_progress(f"Looking back {lookback} most recent ABCs, recommending up to {count}.")

    recommended = find_recommended_abc(
        users_atcoder, users_vjudge, count, lookback,
        on_progress=on_progress, problem_letters=problem_letters, should_stop=should_stop,
    )

    on_progress(f"=== Recommended ABCs ({len(recommended)}/{count}) ===")
    links = []
    for c in recommended:
        link = build_link(c["id"])
        links.append(link)
        on_progress(f"  {c['id']}  |  {c['title']}  |  {link}")

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for link in links:
            f.write(link + "\n")

    on_progress(f"Saved {len(links)} links to {output_path}")


if __name__ == "__main__":
    main()
