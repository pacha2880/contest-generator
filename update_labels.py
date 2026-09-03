"""
update_labels.py
Actualiza SOLO el texto visible de los hipervínculos en las filas de cabecera
de cada contest, añadiendo el identificador del problema CF.

Nuevo formato: "A - #2135B"  (letra del sheet - #contestId + índice CF)

No toca colores, notas, ni ninguna otra celda.
"""

import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import gspread
from google.oauth2.service_account import Credentials

CF_URL_RE = re.compile(r"/contest/(\d+)/problem/([A-Z0-9]+)", re.I)
HL_RE = re.compile(r'=HYPERLINK\("([^"]+)","([^"]+)"\)', re.I)


def new_label(sheet_letter, url):
    m = CF_URL_RE.search(url)
    if not m:
        return sheet_letter
    return f"{sheet_letter} - #{m.group(1)}{m.group(2)}"


def main():
    with open("config.json") as f:
        cfg = json.load(f)

    creds = Credentials.from_service_account_file(
        cfg["credentials_file"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ],
    )
    gc = gspread.authorize(creds)
    ws = gc.open_by_url(cfg["sheets_url"]).sheet1

    rows = ws.get_all_values(value_render_option="FORMULA")

    # Header rows (0-indexed): 0, 6, 12, 18, 24
    header_rows = [i * 6 for i in range(5)]

    updates = []
    for ri in header_rows:
        if ri >= len(rows):
            break
        row = rows[ri]
        for ci, cell in enumerate(row):
            if ci == 0:
                continue  # "Contest N" label — skip
            m = HL_RE.match(str(cell))
            if not m:
                continue  # manually edited or empty — leave untouched
            url = m.group(1)
            current_label = m.group(2)

            # Only update if label is still a plain letter (not already updated)
            if " - #" in current_label:
                print(f"  R{ri+1}C{ci+1}: already updated ({current_label!r}), skipping")
                continue

            label = new_label(current_label, url)
            new_formula = f'=HYPERLINK("{url}","{label}")'
            a1 = gspread.utils.rowcol_to_a1(ri + 1, ci + 1)
            updates.append({"range": a1, "values": [[new_formula]]})
            print(f"  R{ri+1}C{ci+1}: {current_label!r}  →  {label!r}")

    if not updates:
        print("Nothing to update.")
        return

    ws.batch_update(updates, value_input_option="USER_ENTERED")
    print(f"\nDone — {len(updates)} cells updated, nothing else touched.")


if __name__ == "__main__":
    main()
