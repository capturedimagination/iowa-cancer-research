"""Inventory this public research snapshot without publishing raw mixed-rights caches.

Generates publication/source-manifest.json and .gitignore. Source files stay local.
This is an explicit snapshot selection, not a claim that upstream rights changed.
"""
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit
import hashlib
import json
import re

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"publication/source-manifest.json"
MAYNARD="research/treatment-discovery/sources/maynard-2026-10-29/"
PRECLINICAL="research/treatment-discovery/sources/preclinical/2026-10-29/"
EGFR_SOURCE="research/treatment-discovery/sources/egfr-resistance-2026-11-10/"
LINEAGE_SOURCE="research/treatment-discovery/sources/lineage-2026-11-10/"
MAYNARD_KEEP={"manifest.json","repository-tree.json","derived-published-AT2-signature.json",
    "egfr-main-metadata-audit.json","egfr-main-sample-audit.csv"}

def policy(name):
    p=Path(name)
    if any(x in p.parts for x in (".git",".publication",".venv","__pycache__")):
        return "local_generated","Private working/archive directory; not publication input"
    if name.startswith("tmp/") or p.suffix in (".sqlite",".pyc",".png"):
        return "local_generated","Rebuildable database, bytecode or rendering cache"
    if name.startswith((EGFR_SOURCE,LINEAGE_SOURCE)):
        return "linked_source_only","Public research originals retained for local reanalysis; publish original findings and source provenance, not raw participant-level or publisher/author source mirrors"
    if name.startswith(MAYNARD):
        if name[len(MAYNARD):] in MAYNARD_KEEP:
            return "included","Authored factual audit/derived gene list or public source path/hash inventory; upstream attribution retained"
        return "linked_source_only","Copied upstream code/data/HTML has no verified redistribution license; findings and source pointers are published"
    if name.startswith(PRECLINICAL):
        tail=name[len(PRECLINICAL):]
        if tail.startswith("figshare-"):
            return "included","Exact archived DepMap/PRISM Figshare versions licensed CC BY 4.0; see THIRD_PARTY_NOTICES.md"
        if tail in ("archive-manifest.json","gdsc2-workbook-availability.json"):
            return "included","Authored source provenance or HTTP availability result; temporary signing queries removed"
        return "linked_source_only","Sanger source terms or copied forum/browser/PDF body are not cleared for public redistribution"
    if name.startswith("sources/"):
        if p.suffix in (".csv",".xlsx"):
            return "included","Federal EPA/NCI/AHS factual public data; agency/source attribution retained"
        if p.suffix==".json":
            return "included","Authored download, extraction or provenance metadata"
        return "linked_source_only","Cached source body/OCR not mirrored; consult original publisher and source terms"
    if name.startswith("research/sources/") and p.suffix!=".csv":
        return "linked_source_only","Cached access/error response; not substantive source evidence"
    if name.startswith("research/treatment-discovery/data/nsclc_pd1_msk_2018/"):
        return "included","Official public pseudonymous cBioPortal study snapshot, ODbL 1.0; attribution and source license retained"
    if name.endswith("cohort-flow.jsonl"):
        return "included","Derived cBioPortal database under ODbL 1.0; attribution and transformation code retained"
    return "included","Original project findings, code, reports or factual derived data; source-specific rights remain applicable"

def clean_url(url):
    try:
        p=urlsplit(url)
        if any(k.lower().startswith("x-amz-") for k in re.findall(r"(?:^|&)([^=]+)=",p.query)):
            return urlunsplit((p.scheme,p.netloc,p.path,"",""))
        return url
    except ValueError:return ""

urls=defaultdict(set)
def record_paths(obj,parent):
    if isinstance(obj,dict):
        candidates=[]
        for k in ("path","local_path","file","filename","original_file","source_file"):
            if isinstance(obj.get(k),str):
                name=obj[k]
                candidates.extend([name,(parent/name).as_posix()])
        found=set()
        for key in ("url","source_url","requested_url","download_url","public_url"):
            if isinstance(obj.get(key),str) and obj[key].startswith(("https://","http://")):
                found.add(clean_url(obj[key]))
        for name in candidates:
            p=Path(name)
            if p.is_absolute():
                try:name=p.relative_to(ROOT).as_posix()
                except ValueError:continue
            if (ROOT/name).is_file():urls[name].update(found)
        for value in obj.values():record_paths(value,parent)
    elif isinstance(obj,list):
        for value in obj:record_paths(value,parent)

all_paths=[p for p in ROOT.rglob("*") if p.is_file() and p.relative_to(ROOT).parts[0] != "tmp" and not any(x in p.relative_to(ROOT).parts for x in (".git",".publication",".venv","__pycache__"))]
for path in all_paths:
    if path.suffix==".json" and path!=OUT:
        try:record_paths(json.loads(path.read_text()),path.parent.relative_to(ROOT))
        except (ValueError,UnicodeDecodeError):pass

rows=[]
def file_sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(8*1024*1024),b""):h.update(block)
    return h.hexdigest()

for path in sorted(all_paths):
    name=path.relative_to(ROOT).as_posix()
    if name in ("publication/source-manifest.json","publication/included-files.txt"):continue
    status,basis=policy(name)
    rows.append({"path":name,"bytes":path.stat().st_size,"sha256":file_sha256(path),
        "publication_status":status,"rights_or_scope_basis":basis,"upstream_urls":sorted(u for u in urls[name] if u)})
OUT.parent.mkdir(exist_ok=True)
included=[r["path"] for r in rows if r["publication_status"]=="included"]+["publication/source-manifest.json","publication/included-files.txt"]
manifest={"initial_publication_date":"2026-11-03","publication_date":datetime.now(timezone.utc).date().isoformat(),"scope":"All original project findings/reports/analyses/code plus redistributable source data; linked-source-only archives remain local",
    "notes":["Original source acquisition dates and data periods remain in the original provenance files.",
             "A path in this inventory does not mean its source body is redistributed; read publication_status.",
             "Hashes identify the local/public snapshot where present, not a promise that a mutable upstream URL still returns identical bytes.",
             "The generated search database is excluded and can be rebuilt from the published subset; its hash/search counts differ from the full local archive.",
             "Ephemeral tmp working files/environments are excluded from the inventory; durable source originals have their own dated paths and provenance."],
    "counts":dict(Counter(r["publication_status"] for r in rows)),"expected_public_files":sorted(included),"files":rows}
(OUT.parent/"included-files.txt").write_text("\n".join(sorted(included))+"\n")
ignore=["# Private archives and rebuildable outputs", ".publication/", ".venv/", "__pycache__/", "*.pyc", "*.sqlite", "*.sqlite-*", "tmp/", "*.png", ".DS_Store", ".env", ".env.*", "*.pem", "*.key", "id_ed25519", "id_rsa", "/"+EGFR_SOURCE, "/"+LINEAGE_SOURCE, "# Source mirrors without publication clearance"]
ignore.extend("/"+r["path"] for r in rows if r["publication_status"]=="linked_source_only")
(ROOT/".gitignore").write_text("\n".join(ignore)+"\n")
# The ignore file is itself published: record its generated bytes, not the
# previous snapshot's bytes. The manifest/list intentionally do not self-hash.
ignore_row=next(r for r in rows if r["path"]==".gitignore")
ignore_row.update(bytes=(ROOT/".gitignore").stat().st_size,sha256=file_sha256(ROOT/".gitignore"))
OUT.write_text(json.dumps(manifest,indent=2)+"\n")
print(json.dumps({"included":len(included),"inventory_counts":dict(Counter(r["publication_status"] for r in rows)),
    "included_bytes":sum(r["bytes"] for r in rows if r["publication_status"]=="included")},indent=2))
