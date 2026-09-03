import json, sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import gspread
from google.oauth2.service_account import Credentials

with open('config.json') as f:
    cfg = json.load(f)
creds = Credentials.from_service_account_file(cfg['credentials_file'], scopes=[
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
])
gc = gspread.authorize(creds)
ws = gc.open_by_url(cfg['sheets_url']).sheet1
rows = ws.get_all_values(value_render_option='FORMULA')
HL = re.compile(r'=HYPERLINK\("([^"]+)","([^"]+)"\)', re.I)
for ri, row in enumerate(rows):
    for ci, cell in enumerate(row):
        m = HL.match(str(cell))
        if m:
            print(f'R{ri+1}C{ci+1}: label={m.group(2)!r}  url={m.group(1)}')
