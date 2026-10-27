import json
import os
import re
import subprocess
import sys
import time
import requests
from collections import Counter
from urllib.parse import urlencode

from cancel import StoppedByUser

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CF_API = "https://codeforces.com/api"
PAST_FILE = "solved.txt"

# Unofficial, undocumented endpoint that powers vjudge.net's own status page.
# Shared by atcoder.py (OJId=AtCoder) and gym.py (via fetch_user_vjudge_cf_rows
# below, OJId=CodeForces). Confirmed empirically (2026-10-26, querying with
# OJId=CodeForces) that `probNum` for Codeforces problems is already
# "{contestId}{index}" (ej. "2203B", "1458A") — exactly this project's own
# key format, no translation needed.
VJUDGE_STATUS_URL = "https://vjudge.net/status/data"
VJUDGE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "X-Requested-With": "XMLHttpRequest",
}


def load_config(path="config.json"):
    with open(path) as f:
        return json.load(f)


def get_user_solved(users, *, on_progress, should_stop=lambda: False):
    solved = set()
    for user in users:
        if should_stop():
            on_progress("Detenido por el usuario.")
            raise StoppedByUser()
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


def _vjudge_fetch_page(method, un, oj_id, start, page_size):
    """One page from vjudge's status endpoint via either 'requests' or
    'curl'. Returns (status_code_or_None, raw_body) — never raises, so the
    caller can log/compare both methods' results instead of just catching an
    exception."""
    params = {"draw": 1, "start": start, "length": page_size, "un": un, "OJId": oj_id}
    if method == "requests":
        try:
            r = requests.get(VJUDGE_STATUS_URL, params=params, headers=VJUDGE_HEADERS, timeout=20)
            return r.status_code, r.text
        except Exception as e:
            return None, f"(excepción: {e})"
    url = f"{VJUDGE_STATUS_URL}?{urlencode(params)}"
    try:
        result = subprocess.run(
            ["curl", "-s", "-w", "\n%{http_code}",
             "-A", VJUDGE_HEADERS["User-Agent"],
             "-H", f"X-Requested-With: {VJUDGE_HEADERS['X-Requested-With']}",
             url],
            capture_output=True, encoding="utf-8", errors="replace", timeout=20,
        )
        body, _, code = result.stdout.rpartition("\n")
        return (int(code) if code.strip().isdigit() else None), body
    except Exception as e:
        return None, f"(excepción: {e})"


def fetch_vjudge_rows(vjudge_user, oj_id, *, on_progress, page_size=100):
    """Raw rows from vjudge's status endpoint for one OJ (ej. "CodeForces"/
    "AtCoder" — different callers filter to their own judge). recordsTotal/
    recordsFiltered in the response are dummy sentinel values, not real
    counts, so pagination stops on a short page instead.

    On the first page, tries `requests` first and, if that doesn't return
    200, falls back to `curl` — logging both attempts' status + a body
    snippet either way. Added 2026-10-27 after a 403 from Render that didn't
    reproduce locally with `requests` (confirmed against vjudge, which also
    sits behind Cloudflare like codeforces.com): unlike Codeforces, `requests`
    worked fine locally here, which points at an IP/datacenter-reputation
    block rather than the TLS-fingerprint issue `gym.has_editorial already
    works around with `curl` — this diagnostic is to confirm which one it
    actually is once it runs on Render. Whichever method gets a 200 on the
    first page is reused for the rest of that user's pages."""
    on_progress(f"[{vjudge_user}] (vjudge) fetching submissions...")
    rows_out = []
    start = 0
    method = "requests"
    first_page = True
    while True:
        status, body = _vjudge_fetch_page(method, vjudge_user, oj_id, start, page_size)

        if first_page:
            on_progress(f"[{vjudge_user}] (vjudge, {method}) status={status} body={body[:200]!r}")
            if status != 200:
                other = "curl" if method == "requests" else "requests"
                status2, body2 = _vjudge_fetch_page(other, vjudge_user, oj_id, start, page_size)
                on_progress(f"[{vjudge_user}] (vjudge, {other}) status={status2} body={body2[:200]!r}")
                if status2 == 200:
                    method = other
                    status, body = status2, body2
            first_page = False

        if status != 200:
            on_progress(f"[{vjudge_user}] request failed: HTTP {status}")
            break
        try:
            rows = json.loads(body).get("data", [])
        except Exception as e:
            on_progress(f"[{vjudge_user}] respuesta no es JSON válido: {e}")
            break
        if not rows:
            break
        rows_out.extend(rows)
        if len(rows) < page_size:
            break
        start += page_size
        time.sleep(0.3)
    return rows_out


def fetch_user_vjudge_cf_rows(vjudge_user, *, on_progress, page_size=100):
    """Shared by gym.py, which needs the same rows to detect touched gyms
    (parsing the contest id out of `probNum` itself)."""
    return fetch_vjudge_rows(vjudge_user, "CodeForces", on_progress=on_progress, page_size=page_size)


def fetch_user_vjudge_solved(vjudge_user, *, on_progress):
    rows = fetch_user_vjudge_cf_rows(vjudge_user, on_progress=on_progress)
    solved = {row["probNum"] for row in rows if row.get("status") == "Accepted"}
    on_progress(f"[{vjudge_user}] {len(solved)} accepted ({len(rows)} submissions)")
    return solved


def get_group_solved(users, users_vjudge, *, on_progress, should_stop=lambda: False):
    """Two independent handle lists (not required to match in size or to
    correspond 1:1 — same pattern as atcoder.fetch_group_solved). Unions
    native Codeforces submissions from `users` with vjudge-mirror
    submissions from `users_vjudge`."""
    solved = get_user_solved(users, on_progress=on_progress, should_stop=should_stop)
    for handle in users_vjudge:
        if should_stop():
            on_progress("Detenido por el usuario.")
            raise StoppedByUser()
        solved |= fetch_user_vjudge_solved(handle, on_progress=on_progress)
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


# contest.list has no structured "division" field — Educational and Div.3
# rounds even share the same "type": "ICPC" as everything else. The only
# signal is free-text in the contest name, checked in this priority order
# because "Educational ... (Rated for Div. 2)" and "Div. 1 + Div. 2" both
# also contain a plain "Div. 2" substring that would misclassify them if
# checked last.
ROUND_TYPE_PATTERNS = [
    ("educational", re.compile(r"Educational", re.IGNORECASE)),
    ("div1+div2", re.compile(r"Div\.?\s*1\s*\+\s*Div\.?\s*2", re.IGNORECASE)),
    ("div4", re.compile(r"Div\.?\s*4", re.IGNORECASE)),
    ("div3", re.compile(r"Div\.?\s*3", re.IGNORECASE)),
    ("div2", re.compile(r"Div\.?\s*2", re.IGNORECASE)),
    ("div1", re.compile(r"Div\.?\s*1", re.IGNORECASE)),
]


def classify_round(name):
    for label, pattern in ROUND_TYPE_PATTERNS:
        if pattern.search(name):
            return label
    return "other"


# config.json["codeforces"]["type"] is a single enum value, not a list — div1,
# div3 and div4 are each their own exclusive category, but "div2" is treated
# as the general "normal training round" bucket and also covers the combined
# Div.1+Div.2 rounds and Educational rounds (which are themselves rated for
# Div.2), since in practice someone filtering for Div.2-level problems wants
# all three.
ROUND_TYPE_GROUPS = {
    "div1": {"div1"},
    "div2": {"div2", "div1+div2", "educational"},
    "div3": {"div3"},
    "div4": {"div4"},
}


def fetch_contest_round_types(*, on_progress):
    """Mirrored rounds (ej. "Round N (Div. 1)" / "Round N (Div. 2)") get
    their own contestId each, and problemset.problems already lists each
    contest's problems under its own letters — a problem shared between a
    Div.1 and Div.2 mirror can have a different index in each (confirmed:
    "Lavencia Oranges" is A in the Div.1 listing, C in the Div.2 one), so no
    letter remapping is needed here, just classifying each contestId."""
    on_progress("Fetching Codeforces contest list...")
    r = requests.get(f"{CF_API}/contest.list", params={"gym": False}, timeout=30)
    data = r.json()
    if data["status"] != "OK":
        raise RuntimeError(f"contest.list error: {data.get('comment')}")
    contests = data["result"]
    round_type_by_contest = {c["id"]: classify_round(c["name"]) for c in contests}
    on_progress(f"{len(contests)} contests classified")
    return round_type_by_contest


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


def find_unsolved_by_letter(problems, stats, allowed_contest_ids, letter, user_solved, past, count):
    """`letter` (ej. "C") matches that exact index AND subletters like "C1"/
    "C2" — most CF problems past a certain difficulty get split into an
    easy/hard version this way, so an exact-only match would miss most of
    them."""
    candidates = []
    for p in problems:
        if "contestId" not in p or p["contestId"] not in allowed_contest_ids:
            continue
        if not p["index"].upper().startswith(letter):
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


def generate_recommendations(
    users, mode, *, difficulties=None, letters=None, round_type="div2",
    users_vjudge=None, on_progress, should_stop=lambda: False, past=None,
):
    """Core logic, with no config.json/file I/O of its own (besides reading
    the anti-repeat cache via the `past` param, which callers control) — the
    same function console, GUI and the web backend all call, each supplying
    its own `users`/`mode`/etc. instead of this function reading them off
    disk itself. Mirrors the pattern atcoder.find_recommended_abc() and
    gym.find_untouched_gyms()/select_recommendations() already use.

    Returns (result_lines, newly_recommended_keys, items) — items is the
    full structured dicts (key/url/name/index/solvedCount) in the same order
    they were found, for callers that want data instead of re-parsing
    result_lines text (the web backend saves `items` to Mongo). Writing
    result_lines to a file is the caller's job, same as the other two
    modules leave `output_links`/`output_csv` writing to main().
    """
    users_vjudge = users_vjudge or []
    if not users and not users_vjudge:
        raise ValueError("'users' and 'users_vjudge' are both empty")
    if mode not in ("letters", "difficulties"):
        raise ValueError(f"mode must be 'letters' or 'difficulties', got {mode!r}")
    letter_mode = mode == "letters"

    letters = letters or []
    difficulties = difficulties or []
    if letter_mode and not letters:
        raise ValueError("'letters' is empty (mode is 'letters')")
    if not letter_mode and not difficulties:
        raise ValueError("'difficulties' is empty (mode is 'difficulties')")
    if letter_mode and round_type not in ROUND_TYPE_GROUPS:
        raise ValueError(f"'round_type' must be one of {sorted(ROUND_TYPE_GROUPS)}, got {round_type!r}")

    if past is None:
        past = set()

    on_progress(f"Users ({len(users)}): {', '.join(users)}")
    on_progress(f"vjudge users ({len(users_vjudge)}): {', '.join(users_vjudge)}")

    on_progress("=== Step 1: Collecting solved problems ===")
    user_solved = get_group_solved(users, users_vjudge, on_progress=on_progress, should_stop=should_stop)
    on_progress(f"Total unique accepted problems across all users: {len(user_solved)}")

    on_progress("=== Step 2: Fetching problemset ===")
    problems, stats = fetch_problemset(on_progress=on_progress)

    on_progress(f"Previously recommended (skipped): {len(past)}")

    on_progress("=== Results ===")
    newly_recommended = []
    result_lines = []
    items = []

    if letter_mode:
        allowed_round_types = ROUND_TYPE_GROUPS[round_type]
        on_progress(f"Round type: {round_type} (covers: {', '.join(sorted(allowed_round_types))})")
        round_type_by_contest = fetch_contest_round_types(on_progress=on_progress)
        allowed_contest_ids = {cid for cid, rt in round_type_by_contest.items() if rt in allowed_round_types}
        on_progress(f"{len(allowed_contest_ids)} contests match the configured round type")

        letter_count = Counter(l.upper() for l in letters)
        for letter, needed in sorted(letter_count.items()):
            found = find_unsolved_by_letter(problems, stats, allowed_contest_ids, letter, user_solved, past, needed)

            on_progress(f"[{letter}] {len(found)}/{needed} problems:")
            result_lines.append(f"[{letter}] {len(found)}/{needed} problems:")
            for p in found:
                line = f"  [{letter}→{p['index']}] {p['url']}  |  {p['name']}  (solved by {p['solvedCount']} on CF)"
                on_progress(line)
                result_lines.append(line)
                newly_recommended.append(p["key"])
                items.append({**p, "label": letter})

            if len(found) < needed:
                note = f"  (only {len(found)} unsolved problems available for letter {letter} in {round_type}-type rounds)"
                on_progress(note)
                result_lines.append(note)
            result_lines.append("")
    else:
        diff_count = Counter(int(d) for d in difficulties)
        on_progress("Problems needed per difficulty:")
        for r, c in sorted(diff_count.items(), reverse=True):
            on_progress(f"  {r}: {c}")

        for rating in sorted(diff_count.keys(), reverse=True):
            needed = diff_count[rating]
            found = find_unsolved(problems, stats, rating, user_solved, past, needed)

            on_progress(f"[{rating}] {len(found)}/{needed} problems:")
            result_lines.append(f"[{rating}] {len(found)}/{needed} problems:")
            for p in found:
                line = f"  [{rating}] {p['url']}  |  {p['name']}  (solved by {p['solvedCount']} on CF)"
                on_progress(line)
                result_lines.append(line)
                newly_recommended.append(p["key"])
                items.append({**p, "label": str(rating)})

            if len(found) < needed:
                note = f"  (only {len(found)} unsolved problems available at this rating)"
                on_progress(note)
                result_lines.append(note)
            result_lines.append("")

    return result_lines, newly_recommended, items


def main(on_progress=print, should_stop=lambda: False):
    """on_progress defaults to print for the console entry point (`py main.py
    codeforces` / `python app.py`). The GUI calls this same function with its
    own callback instead, so both share the exact same logic, output files,
    and config.json reading — no separate codepath to keep in sync. Reads
    config.json and the solved.txt cache, then delegates the actual search
    to generate_recommendations() — same split as atcoder.py/gym.py already
    have between their main() and their config-free core functions."""
    cfg = load_config()
    cf_cfg = cfg.get("codeforces", {})
    users = cf_cfg.get("users", [])
    users_vjudge = cf_cfg.get("users_vjudge", [])
    diff_list = cf_cfg.get("difficulties", [])
    letters = cf_cfg.get("letters", [])
    round_type = cf_cfg.get("type", "div2")
    mode = cf_cfg.get("mode", "difficulties")
    output_path = cf_cfg.get("output_links", "results.txt")

    if not users and not users_vjudge:
        raise ValueError("config.json['codeforces']['users'/'users_vjudge'] is empty")

    past = load_past()

    result_lines, newly_recommended, _items = generate_recommendations(
        users, mode,
        difficulties=diff_list, letters=letters, round_type=round_type,
        users_vjudge=users_vjudge,
        on_progress=on_progress, should_stop=should_stop, past=past,
    )

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(result_lines))

    save_past(newly_recommended)
    on_progress(f"Saved {len(newly_recommended)} problems to {PAST_FILE}.")
    on_progress(f"Full results saved to {output_path}")


if __name__ == "__main__":
    main()
