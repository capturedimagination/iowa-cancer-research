"""Read-only search and SQL access to the saved Iowa cancer research library."""
from pathlib import Path
import argparse
import json
import re
import sqlite3

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
s=p.add_subparsers(dest="command",required=True)
q=s.add_parser("search");q.add_argument("terms");q.add_argument("--limit",type=int,default=8)
q=s.add_parser("sql");q.add_argument("query");q.add_argument("--limit",type=int,default=100)
s.add_parser("tables")
q=s.add_parser("record");q.add_argument("evidence_id")
a=p.parse_args()
db=sqlite3.connect((ROOT/"knowledge/research.sqlite").as_uri()+"?mode=ro",uri=True)
db.row_factory=sqlite3.Row
db.execute("PRAGMA query_only=ON")
if a.command=="search":
    tokens=re.findall(r"[\w]+",a.terms,flags=re.UNICODE)
    if not tokens: p.error("Provide at least one word")
    match=" AND ".join('"'+t+'"' for t in tokens)
    rows=db.execute("SELECT kind,record_key,title,path,snippet(search_index,4,'[',']',' … ',35) AS excerpt FROM search_index WHERE search_index MATCH ? ORDER BY rank LIMIT ?",(match,a.limit)).fetchall()
elif a.command=="record":
    rows=db.execute("SELECT * FROM evidence WHERE evidence_id=?",(a.evidence_id,)).fetchall()
elif a.command=="tables":
    rows=db.execute("SELECT * FROM table_notes ORDER BY table_name").fetchall()
else:
    # URI read-only + query_only also reject writes through CTEs or pragmas.
    cursor=db.execute(a.query)
    rows=cursor.fetchmany(a.limit)
print(json.dumps([dict(row) for row in rows],ensure_ascii=False,indent=2))
db.close()
