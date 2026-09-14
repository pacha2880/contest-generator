import json
import os
import re
import subprocess
import sys
import tempfile
import time

import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CF_API = "https://codeforces.com/api"
GYM_ID_MIN = 100000  # gym contest ids all fall above this; regular contests never reach it

# Every gym page has a `Codeforces.setupTutorials(...)` JS boilerplate call that
# has nothing to do with the "Contest materials" sidebar, so matching "tutorial"
# against the whole page gives a false positive on every single gym. Scope the
# search to the sidebar itself, delimited by its own heading and the next
# section ("second-level-menu", the Problems/Submit/Standings tab bar) that
# always follows it.
MATERIALS_RE = re.compile(r"Contest materials(.*?)second-level-menu", re.IGNORECASE | re.DOTALL)
TUTORIAL_RE = re.compile(r"tutorial|editorial", re.IGNORECASE)


def load_config(path="config.json"):
    with open(path) as f:
        return json.load(f)


def fetch_gym_contests():
    print("Fetching gym contest list...", end="", flush=True)
    r = requests.get(f"{CF_API}/contest.list", params={"gym": "true"}, timeout=30)
    data = r.json()
    if data["status"] != "OK":
        raise RuntimeError(f"contest.list error: {data.get('comment')}")
    contests = data["result"]
    print(f" {len(contests)} gyms loaded")
    return contests


def matches_filters(contest, filters):
    """A None/missing filter value means "no constraint" for that field."""
    if filters.get("type") and contest.get("type") != filters["type"]:
        return False

    kinds = filters.get("kind")
    if kinds and contest.get("kind") not in kinds:
        return False

    region = filters.get("icpc_region")
    if region and contest.get("icpcRegion") != region:
        return False

    difficulty = contest.get("difficulty")
    dmin = filters.get("difficulty_min")
    dmax = filters.get("difficulty_max")
    if dmin is not None and (difficulty is None or difficulty < dmin):
        return False
    if dmax is not None and (difficulty is None or difficulty > dmax):
        return False

    duration = contest.get("durationSeconds")
    durmin = filters.get("duration_min_seconds")
    durmax = filters.get("duration_max_seconds")
    if durmin is not None and (duration is None or duration < durmin):
        return False
    if durmax is not None and (duration is None or duration > durmax):
        return False

    season = contest.get("season")
    season_from = filters.get("season_from")
    season_to = filters.get("season_to")
    if season_from and (season is None or season < season_from):
        return False
    if season_to and (season is None or season > season_to):
        return False

    return True


def fetch_user_touched_gyms(user):
    """Gym submissions show up in the normal user.status history; their
    contestId is just >= GYM_ID_MIN. Any verdict counts as "touched"."""
    print(f"  [{user}] fetching submissions...", end="", flush=True)
    touched = set()
    try:
        r = requests.get(
            f"{CF_API}/user.status",
            params={"handle": user, "from": 1, "count": 10000},
            timeout=20,
        )
        data = r.json()
        if data["status"] == "OK":
            for sub in data["result"]:
                contest_id = sub.get("contestId")
                if contest_id is not None and contest_id >= GYM_ID_MIN:
                    touched.add(contest_id)
            print(f" {len(touched)} gyms touched")
        else:
            print(f" API error: {data.get('comment', '?')}")
    except Exception as e:
        print(f" request failed: {e}")
    time.sleep(0.3)
    return touched


def find_recommended_gyms(users, filters, count):
    contests = fetch_gym_contests()
    candidates = [c for c in contests if matches_filters(c, filters)]
    print(f"{len(candidates)}/{len(contests)} gyms match the configured filters\n")

    print("=== Fetching user submissions ===")
    touched = set()
    for user in users:
        touched |= fetch_user_touched_gyms(user)
    print(f"  Gyms touched by the group: {len(touched)}\n")

    untouched = [c for c in candidates if c["id"] not in touched]
    untouched.sort(key=lambda c: c.get("startTimeSeconds", 0), reverse=True)
    return untouched[:count]


def stars(difficulty):
    if difficulty is None:
        return "?????"
    return "★" * difficulty + "☆" * (5 - difficulty)


def has_editorial(contest_id, cookie_jar):
    """Scrape the gym page's "Contest materials" sidebar for a tutorial/editorial
    link. Uses curl instead of `requests`: Codeforces's Cloudflare protection
    blocks requests' TLS fingerprint with a fake 200/403 challenge page, but lets
    curl through. Reusing a cookie jar across calls + a delay keeps it that way."""
    url = f"https://codeforces.com/gym/{contest_id}"
    try:
        result = subprocess.run(
            ["curl", "-s", "-c", cookie_jar, "-b", cookie_jar,
             "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", url],
            capture_output=True, encoding="utf-8", errors="replace", timeout=20,
        )
        html = result.stdout
        if not html or "Just a moment" in html:
            return None
        materials = MATERIALS_RE.search(html)
        if not materials:
            return False
        return bool(TUTORIAL_RE.search(materials.group(1)))
    except Exception:
        return None


def check_editorials(recommended):
    editorials = {}
    with tempfile.TemporaryDirectory() as tmp_dir:
        cookie_jar = os.path.join(tmp_dir, "cf_cookies.txt")
        for contest in recommended:
            editorials[contest["id"]] = has_editorial(contest["id"], cookie_jar)
            time.sleep(0.9)
    return editorials


def main():
    cfg = load_config()
    gym_cfg = cfg.get("gym", {})
    users = cfg.get("users_gym", [])
    filters = gym_cfg.get("filters", {})
    count = gym_cfg.get("count", 10)
    output_path = gym_cfg.get("output_links", "outputs/gym_links.txt")

    if not users:
        print("No hay usuarios configurados en config.json['users_gym'].")
        return

    print(f"Users ({len(users)}): {', '.join(users)}")
    print(f"Filters: {filters}")
    print(f"Recommending up to {count} gyms.\n")

    recommended = find_recommended_gyms(users, filters, count)

    print(f"=== Checking contest materials for {len(recommended)} recommended gyms ===")
    editorials = check_editorials(recommended)

    print(f"\n=== Recommended gyms ({len(recommended)}/{count}) ===")
    links = []
    for contest in recommended:
        link = f"https://codeforces.com/gym/{contest['id']}"
        links.append(link)
        found = editorials.get(contest["id"])
        if found is True:
            note = "tutorial/editorial found"
        elif found is False:
            note = "no tutorial/editorial"
        else:
            note = "couldn't check (page fetch blocked)"
        print(f"  {stars(contest.get('difficulty'))}  {contest['id']}  |  {contest['name']}  |  {note}  |  {link}")

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for link in links:
            f.write(link + "\n")

    print(f"\nSaved {len(links)} links to {output_path}")


if __name__ == "__main__":
    main()
