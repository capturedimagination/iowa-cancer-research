"""Rebuild a local, searchable research library from saved sources; never fetch live data.

Run with the bundled Python to index PDFs (pypdf). CSV/JSON import uses stdlib.
Raw source fields survive in JSON; numeric SQL fields are convenience approximations.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
import csv
import hashlib
import io
import json
import re
import sqlite3
import contextlib
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "knowledge"
DEST.mkdir(exist_ok=True)
TEMP = DEST / "research.building.sqlite"
FINAL = DEST / "research.sqlite"
SNAPSHOT = "2026-10-29"

def dump(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def relative(path):
    return path.relative_to(ROOT).as_posix()

def records(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def number(value):
    if value is None or str(value).strip() in ("", "NA", "N/A", "*", "**", "Suppressed"):
        return None
    return float(Decimal(str(value).replace(",", "")))

def quote(name):
    return '"' + name.replace('"', '""') + '"'

if TEMP.exists():
    TEMP.unlink()
db = sqlite3.connect(TEMP)
db.executescript("""
CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE files(path TEXT PRIMARY KEY, sha256 TEXT NOT NULL, bytes INTEGER, role TEXT, records INTEGER);
CREATE TABLE table_notes(table_name TEXT PRIMARY KEY, grain TEXT, units TEXT, join_keys TEXT, limitations TEXT);
CREATE TABLE tri_forms(
 row_id INTEGER PRIMARY KEY, reporting_year INTEGER, trifd TEXT, frs_id TEXT,
 doc_control_number TEXT, facility_name TEXT, city TEXT, county_name TEXT, state TEXT,
 latitude REAL, longitude REAL, horizontal_datum TEXT, primary_naics TEXT, primary_sic TEXT,
 industry_sector TEXT, chemical_name TEXT, chemical_id TEXT, cas_number TEXT,
 osha_carcinogen_flag TEXT, pbt_flag TEXT, pfas_flag TEXT, form_type TEXT, unit_of_measure TEXT,
 fugitive_air REAL, stack_air REAL, reported_air REAL, reported_water REAL,
 reported_onsite_release REAL, reported_offsite_release REAL, reported_total_release REAL,
 source_file TEXT, source_row INTEGER, source_url TEXT, retrieved TEXT, raw_record_json TEXT NOT NULL
);
CREATE INDEX tri_year ON tri_forms(reporting_year);
CREATE INDEX tri_facility_year ON tri_forms(trifd,reporting_year);
CREATE INDEX tri_chemical_year ON tri_forms(cas_number,reporting_year);
CREATE TABLE evidence(
 evidence_id TEXT PRIMARY KEY, source_record_id TEXT, family TEXT, sector TEXT, process TEXT,
 agent TEXT, cancer_evidence TEXT, iowa_evidence TEXT, facility TEXT, source_url TEXT,
 data_period TEXT, limitations TEXT, evidence_type TEXT, source_file TEXT, source_row INTEGER,
 raw_record_json TEXT NOT NULL
);
CREATE TABLE references_catalog(
 reference_id TEXT PRIMARY KEY, family TEXT, title TEXT, url TEXT, source_file TEXT,
 raw_record_json TEXT NOT NULL
);
CREATE TABLE datasets(dataset_id TEXT PRIMARY KEY, title TEXT, source_file TEXT, raw_record_json TEXT NOT NULL);
CREATE TABLE airtox_risk_values(
 row_id INTEGER PRIMARY KEY, geography TEXT, fips TEXT, county TEXT, state TEXT,
 model_population INTEGER, assessment_year INTEGER, series TEXT, component TEXT, is_total INTEGER,
 risk_per_million REAL, original_value TEXT, source_file TEXT, source_row INTEGER, source_url TEXT,
 risk_interpretation TEXT
);
CREATE INDEX airtox_county ON airtox_risk_values(fips,series);
CREATE TABLE documents(
 document_id INTEGER PRIMARY KEY, path TEXT UNIQUE, title TEXT, origin TEXT,
 text_status TEXT, pages INTEGER, sha256 TEXT, body TEXT
);
CREATE VIRTUAL TABLE search_index USING fts5(kind,record_key,title,path,body,tokenize='unicode61');
CREATE VIEW tri_reporting_coverage AS
 SELECT reporting_year,unit_of_measure,form_type,COUNT(*) AS forms,
 COUNT(DISTINCT trifd) AS reporting_facilities FROM tri_forms
 GROUP BY reporting_year,unit_of_measure,form_type;
""")

def note(table, grain, units, keys, limits):
    db.execute("INSERT INTO table_notes VALUES(?,?,?,?,?)", (table, grain, units, keys, limits))

def register(path, role, n=None):
    db.execute("INSERT OR REPLACE INTO files VALUES(?,?,?,?,?)", (relative(path), sha(path), path.stat().st_size, role, n))

def index(kind, key, title, path, body):
    db.execute("INSERT INTO search_index VALUES(?,?,?,?,?)", (kind, key, title, path, body))

# Each annual file is used once; the duplicate 2024 download in statewide/ is not reimported.
history_path = ROOT / "research/industries/tri-history-manifest.json"
history = json.loads(history_path.read_text())
register(history_path, "TRI download provenance", len(history["files"]))
assert len(history["files"]) == 38
year_counts = {}
for item in sorted(history["files"], key=lambda x: x["year"]):
    assert item["status"] == "downloaded"
    path = ROOT / item["file"]
    assert sha(path) == item["sha256"], f"Source changed: {path}"
    rows = records(path)
    assert len(rows) == item["rows"]
    values = []
    for line, row in enumerate(rows, 2):
        assert row["8. ST"] == "IA" and int(row["1. YEAR"]) == item["year"]
        form = row["49. FORM TYPE"]
        assert form in ("A", "R")
        # Form A raw zero placeholders are not quantified observations.
        quantities = [number(row[k]) if form == "R" else None for k in (
            "51. 5.1 - FUGITIVE AIR", "52. 5.2 - STACK AIR", "53. 5.3 - WATER",
            "65. ON-SITE RELEASE TOTAL", "88. OFF-SITE RELEASE TOTAL", "107. TOTAL RELEASES")]
        fugitive, stack, water, onsite, offsite, total = quantities
        air = None if fugitive is None or stack is None else fugitive + stack
        values.append((None, item["year"], row["2. TRIFD"], row["3. FRS ID"], row["36. DOC_CTRL_NUM"],
            row["4. FACILITY NAME"], row["6. CITY"], row["7. COUNTY"], row["8. ST"],
            number(row["12. LATITUDE"]), number(row["13. LONGITUDE"]), row["14. HORIZONTAL DATUM"],
            row["30. PRIMARY NAICS"], row["24. PRIMARY SIC"], row["23. INDUSTRY SECTOR"],
            row["37. CHEMICAL"], row["39. TRI CHEMICAL/COMPOUND ID"], row["40. CAS#"],
            row["46. CARCINOGEN"], row["47. PBT"], row["48. PFAS"], form, row["50. UNIT OF MEASURE"],
            fugitive, stack, air, water, onsite, offsite, total,
            relative(path), line, item["url"], item["retrieved"], dump(row)))
    db.executemany("INSERT INTO tri_forms VALUES(" + ",".join("?" for _ in range(35)) + ")", values)
    year_counts[str(item["year"])] = len(rows)
    register(path, "Unmodified EPA TRI annual source", len(rows))
note("tri_forms", "One saved chemical form, not a worker, facility-year, or exposure measurement",
     "Source Pounds or Grams; units must remain separate. Numeric SQL fields are REAL; exact strings in raw_record_json.",
     "trifd and reporting_year for longitudinal review; frs_id is a distinct identifier. No county FIPS auto-assigned.",
     "Form A release fields NULL; nonreporting not zero. Chemicals, thresholds and sectors change. Offsite releases cannot be spatially assigned to originating plant. Modern snapshot can include historical revisions. No causal or dose interpretation.")

# Searchable aliases identify where to query; they do not aggregate mass or assert present-day operation.
alias_query="""SELECT trifd, MIN(reporting_year) AS first_report_year, MAX(reporting_year) AS last_report_year,
 GROUP_CONCAT(DISTINCT facility_name) AS reported_name_aliases,
 GROUP_CONCAT(DISTINCT city) AS reported_cities, GROUP_CONCAT(DISTINCT county_name) AS reported_counties,
 GROUP_CONCAT(DISTINCT industry_sector) AS reported_sectors,
 GROUP_CONCAT(DISTINCT chemical_name) AS reported_chemicals,
 COUNT(*) AS source_forms FROM tri_forms GROUP BY trifd"""
cols=["trifd","first_report_year","last_report_year","reported_name_aliases","reported_cities",
      "reported_counties","reported_sectors","reported_chemicals","source_forms"]
for values in db.execute(alias_query).fetchall():
    row=dict(zip(cols,values))
    row["interpretation"]="Historical inventory lookup only; dates reflect saved reports, not proven operating/exposure periods. No cancer or individual dose inference."
    index("inventory_facility",row["trifd"],"TRI inventory: "+row["reported_name_aliases"],"sources/industries/tri-history/",dump(row))

# Import CSVs without dropping columns, rounding values, guessing numeric missing codes, or relabeling units.
def import_csv(table, path, grain, units, keys, limits):
    rows = records(path)
    assert rows
    fields = list(rows[0])
    assert "source_file" not in fields and "source_row" not in fields
    db.execute(f"CREATE TABLE {quote(table)} (" + ",".join(quote(f) + " TEXT" for f in fields) + ",source_file TEXT,source_row INTEGER)")
    db.executemany(f"INSERT INTO {quote(table)} VALUES(" + ",".join("?" for _ in range(len(fields)+2)) + ")",
                   [tuple(row.values()) + (relative(path), line) for line,row in enumerate(rows,2)])
    register(path, "Curated CSV; all source columns imported as TEXT", len(rows))
    note(table, grain, units, keys, limits)
    return rows

county = import_csv("county_cancer_summary", ROOT/"research/iowa-99-counties-comparison.csv",
    "One Iowa county; all-site cancer summary in different incidence and mortality windows",
    "Age-adjusted rates per 100,000; AAPC percent/year; rounded average annual counts; CIs and rank intervals retained",
    "fips as five-character text", "99 descriptive rows, not an annual count panel. Do not use rounded average annual counts as exact counts or reconstruct denominators from age-adjusted rates. Incidence and mortality periods differ.")
assert len(county)==99 and len({r["fips"] for r in county})==99
title_v = import_csv("title_v_facilities", ROOT/"research/iowa-title-v-facilities-emissions-2024.csv",
    "One DNR inventory facility, 2024", "tons/year as the PDF labels them; short/metric ton definition unconfirmed",
    "facility_id is DNR inventory ID, not TRIFD or FRS ID",
    "283 Title V facilities; pollutant groups overlap; PM2.5 subset of PM10. HAP mass not toxicity-weighted cancer risk. Do not convert to TRI pounds without confirming ton definition.")
assert len(title_v)==283
for table, file, grain, units, keys, limits in [
    ("manufacturing_measurements", "manufacturing-exposure-measurements.csv", "Selected historical observations and summaries", "Agent- and method-specific; see unit, fraction, statistic and sampling_period", "source_id and sample_id only where present", "Range endpoints, averages and sample observations are not independent; historical occupational data, not current community exposure."),
    ("winnebago_dust_samples", "winnebago-2000-personal-wood-dust.csv", "17 historical personal breathing-zone samples", "mg/m3; total and respirable fractions distinct", "sample_id within source_id", "Not full-shift equivalent without sample duration review; no cancer outcome or modern exposure inference."),
    ("cancer_site_summary", "iowa-cancer-types-comparison.csv", "Cancer-site comparison", "Source-defined rates and trends; see fields", "site/source fields; consult data-dictionary.md", "Pediatric anomaly flagged in source export; inspect status before analysis."),
    ("demographic_summary", "iowa-demographic-comparison.csv", "State-level subgroup comparison", "Source-defined rates and trends", "group/source fields", "Potential suppression, small populations and overlapping subgroup rows; not independent observations.")]:
    import_csv(table, ROOT/"research"/file, grain, units, keys, limits)

ahs_summary=ROOT/"sources/cohort-access/ahs-public-cancer-summary-through-2021.csv"
if ahs_summary.exists():
    import_csv("ahs_public_cancer_summary",ahs_summary,
        "46 public cancer-site/participant-group summary rows from AHS Tables 2a/2b; Iowa plus North Carolina",
        "Public count strings, including suppression/qualifiers; registry data through 2021",
        "participant_group and cancer_site; wave/sample columns are overlapping subsets",
        "Not Iowa-only, not participant-level, no person-time denominator. Do not add All to sites or sum phase/DNA/diet columns; counts include previous cancers at other sites. Read original HTML footnotes/provenance.")

for family, filename in [("manufacturing","industry-manufacturing-evidence.csv"),
                         ("food_agprocessing","industry-food-agprocessing-evidence.csv"),
                         ("energy_legacy","industry-energy-legacy-evidence.csv"),
                         ("services","industry-services-evidence.csv")]:
    path=ROOT/"research"/filename
    rows=records(path)
    register(path,"Curated evidence records",len(rows))
    for line,row in enumerate(rows,2):
        original=row.get("record_id") or row.get("claim_id") or ""
        eid=family+":"+(original or f"row-{line}")
        normalized=(eid,original,family,row.get("sector",""),row.get("process",row.get("task_or_process","")),
            row.get("agent",row.get("agents","")),row.get("cancer_evidence",""),row.get("iowa_evidence",""),
            row.get("facility_if_any",""),row.get("source_url",""),row.get("data_period",""),row.get("limitations",""),
            row.get("evidence_type","unspecified_in_source_record"),relative(path),line,dump(row))
        db.execute("INSERT INTO evidence VALUES("+",".join("?" for _ in normalized)+")",normalized)
        index("evidence",eid,row.get("sector","")+": "+row.get("agent",row.get("agents","")),relative(path),dump(row))
note("evidence","One curated claim/source record; not one independent study","Mixed; raw metadata preserved",
     "evidence_id for local lookup, source_record_id from source CSV where available",
     "Repeated cohorts/sources appear in different sectors. No invented confidence or causation score; inspect limitations, allowed/prohibited inference, population and dates.")

for geo in ("county","state"):
    for series in ("poll","srcgrp"):
        path=ROOT/f"research/industries/airtoxscreen-2020-iowa-{geo}-{series}.csv"
        rows=records(path)
        register(path,"EPA modeled lifetime risk Iowa extraction",len(rows))
        metadata={"FIPS","State","EPA Region","County","Population","assessment_year","source_url","retrieved"}
        for line,row in enumerate(rows,2):
            for component,value in row.items():
                if component in metadata: continue
                db.execute("INSERT INTO airtox_risk_values VALUES(NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(
                    geo,row.get("FIPS"),row.get("County"),row["State"],int(float(row["Population"])),2020,series,
                    component,int(component=="Total Cancer Risk (per million)"),number(value),value,relative(path),line,
                    row["source_url"],"Modeled excess lifetime cancer risk per million under assessment assumptions; not annual observed cancer."))
note("airtox_risk_values","One modeled component or total for a county/state and source series",
     "Modeled excess lifetime cancer risk per million, 2020 assessment",
     "fips for counties; geography/series/component. Total repeated in poll and srcgrp: NEVER sum across series.",
     "EPA rounds total to one significant figure; component digits do not imply accuracy. Diesel particulate cancer risk omitted. Population is assessment field, not aligned cancer person-time. Incomplete pathways; no direct source-to-case attribution.")

# Reference metadata are indexed as records; repeated URLs are deliberately not treated as independent studies.
reference_inputs=[("core","research/source-index.json"),("methods","research/model-methods-sources.json"),
    ("therapy","research/treatment-discovery/sources.json"),
    ("preclinical","research/treatment-discovery/preclinical-data-sources.json"),
    ("clinical","research/treatment-discovery/clinical-pilot-sources.json")]
for family, filename in reference_inputs:
    path=ROOT/filename
    if not path.exists(): continue
    obj=json.loads(path.read_text())
    items=obj if isinstance(obj,list) else obj.get("sources",[])
    register(path,"Reference metadata",len(items))
    for i,row in enumerate(items,1):
        key=f"{family}:{row.get('id',row.get('source_id',i))}"
        title=row.get("title",row.get("name",row.get("citation",key)))
        url=row.get("url",row.get("source_url","; ".join(row.get("urls",[]))))
        db.execute("INSERT INTO references_catalog VALUES(?,?,?,?,?,?)",(key,family,title,url,relative(path),dump(row)))
        index("reference",key,title,relative(path),dump(row))

catalog_path=ROOT/"research/data-source-catalog.json"
if not catalog_path.exists():
    raise RuntimeError("Wait for verified data-source-catalog.json, then rebuild.")
catalog_paths=[catalog_path,ROOT/"research/manufacturing-input-datasets.csv"]
cohort_path=ROOT/"research/cohort-data-access.json"
if cohort_path.exists(): catalog_paths.append(cohort_path)
treatment_catalog=ROOT/"research/treatment-discovery/data-access-catalog.json"
if treatment_catalog.exists(): catalog_paths.append(treatment_catalog)
for catalog_path in catalog_paths:
    if catalog_path.suffix==".csv":
        items=records(catalog_path)
    else:
        obj=json.loads(catalog_path.read_text())
        items=obj if isinstance(obj,list) else obj.get("datasets",obj.get("resources",[]))
    assert items, "Dataset catalog requires nonempty records"
    register(catalog_path,"Dataset discovery and access metadata",len(items))
    for i,row in enumerate(items,1):
        key=(f"OCC-{i:02}" if catalog_path.suffix==".csv" else str(row.get("dataset_id",row.get("id",row.get("resource_id",f"dataset-{i:03}")))))
        title=row.get("title",row.get("name",row.get("dataset",key)))
        db.execute("INSERT INTO datasets VALUES(?,?,?,?)",(key,title,relative(catalog_path),dump(row)))
        index("dataset",key,title,relative(catalog_path),dump(row))
note("datasets","One documented data resource","Resource-specific; metadata are not observations","dataset_id",
     "Catalog discovery does not imply data downloaded, permission obtained, harmonized or suitable for a causal model. Read access, local_status/local_paths or retrieval_status in raw_record_json. Supplements may overlap core resources.")

# Search all authored research/guide prose, plus text from archived original PDFs.
pdf_log=[]
memo_paths=sorted(set(ROOT.glob("research/**/*.md")) | set(DEST.glob("*.md")) | {ROOT/"README.md",ROOT/"Iowa-Cancer-Research.md"})
for path in memo_paths:
    text=path.read_text()
    title=next((line.lstrip("# ") for line in text.splitlines() if line.startswith("# ")),path.stem)
    archived="/sources/" in relative(path)
    origin="archived_source_markdown" if archived else "authored_research_or_guide"
    cur=db.execute("INSERT INTO documents VALUES(NULL,?,?,?,?,?,?,?)",(relative(path),title,origin,"text",None,sha(path),text))
    index("source_document" if archived else "document",str(cur.lastrowid),title,relative(path),text)
    register(path,"Archived source Markdown; not independent factual review" if archived else "Authored research or navigation")
try:
    from pypdf import PdfReader
except ImportError as exc:
    raise RuntimeError("Use bundled Python with pypdf to index original PDFs.") from exc
for path in sorted((ROOT/"sources").rglob("*.pdf")):
    errors=io.StringIO()
    try:
        with contextlib.redirect_stderr(errors):
            reader=PdfReader(path)
            pages=[p.extract_text() or "" for p in reader.pages]
        text="\n\n".join(f"[PDF page {i}]\n{t}" for i,t in enumerate(pages,1))
        nonempty=sum(len(t.strip())>30 for t in pages)
        status="text_extracted" if nonempty==len(pages) else "partial_text_requires_page_review"
        if not nonempty: status="empty_text_requires_OCR_or_visual_review"
        entry={"file":relative(path),"pages":len(pages),"pages_with_text":nonempty,"status":status,"sha256":sha(path)}
        ocr_path=path.with_suffix(".ocr.txt")
        if ocr_path.exists():
            # OCR sidecars aid retrieval; numeric/legal wording still requires page verification.
            text="[OCR sidecar; verify against original PDF]\n"+ocr_path.read_text()
            status="ocr_sidecar_requires_page_verification"
            entry.update(status=status,ocr_file=relative(ocr_path),ocr_sha256=sha(ocr_path))
            register(ocr_path,"OCR search sidecar; not authoritative transcription")
            ocr_provenance=path.with_suffix(".ocr.provenance.json")
            if ocr_provenance.exists():
                entry["ocr_provenance"]=relative(ocr_provenance)
                register(ocr_provenance,"OCR method, coverage, hashes and known transcription limits")
        if errors.getvalue(): entry["parser_warnings"]=errors.getvalue()[:1000]
        cur=db.execute("INSERT INTO documents VALUES(NULL,?,?,?,?,?,?,?)",(relative(path),path.stem,"archived_source_pdf",status,len(pages),sha(path),text))
        index("source_pdf",str(cur.lastrowid),path.stem,relative(path),text)
        register(path,"Archived source PDF; extraction not independent factual review")
    except Exception as exc:
        entry={"file":relative(path),"status":"extraction_failed","error":str(exc),"sha256":sha(path)}
    pdf_log.append(entry)

for path in sorted((ROOT/"sources").rglob("*.xml")):
    root=ET.parse(path).getroot()
    if root.tag not in ("PubmedArticleSet","PubmedArticle"): continue
    articles=root.findall(".//PubmedArticle") if root.tag=="PubmedArticleSet" else [root]
    sections=[]
    for article in articles:
        pmid=article.findtext(".//PMID") or "unknown"
        title="".join(article.find(".//ArticleTitle").itertext()) if article.find(".//ArticleTitle") is not None else ""
        abstract="\n".join((a.get("Label","")+": "+"".join(a.itertext())).strip(": ") for a in article.findall(".//AbstractText"))
        sections.append(f"PMID {pmid}\n{title}\n{abstract}")
    body="\n\n".join(sections)
    cur=db.execute("INSERT INTO documents VALUES(NULL,?,?,?,?,?,?,?)",(relative(path),path.stem,"archived_pubmed_metadata","native_XML_abstracts_not_full_papers",None,sha(path),body))
    index("publication_metadata",str(cur.lastrowid),path.stem,relative(path),body)
    register(path,"PubMed citation/abstract XML; not full-paper access",len(articles))

# Inventory saved sources even when they are not parsed as model observations.
for directory in (ROOT/"sources",ROOT/"research/sources",ROOT/"research/treatment-discovery"):
    for path in sorted(directory.rglob("*")):
        if not path.is_file() or db.execute("SELECT 1 FROM files WHERE path=?",(relative(path),)).fetchone(): continue
        role={".csv":"Archived tabular source; inspect footnotes and provenance",
              ".xlsx":"Archived original workbook; inspect source units and metadata",
              ".json":"Source-side metadata, provenance or retrieval log",
              ".html":"Archived retrieval response; verify access status/content before using",
              ".txt":"Archived text/TSV; inspect source definition, license and provenance",
              ".gz":"Archived compressed source; inspect manifest and source terms",
              ".jsonl":"Analysis inclusion/provenance records; not original observations",
              ".npy":"Saved derived statistical array; consult analysis protocol",
              ".Rmd":"Archived author analysis code; inspect version and dependencies before executing",
              ".R":"Archived author analysis code; inspect version and dependencies before executing"}.get(path.suffix)
        if role: register(path,role)

db.executemany("INSERT INTO metadata VALUES(?,?)",[("schema_version","1"),("source_cutoff",SNAPSHOT),
    ("core_iowa_snapshot","2026-10-22"),("treatment_research_extension","2026-10-29"),
    ("built_utc",datetime.now(timezone.utc).isoformat()),("purpose","Source-linked research and analysis library; see dated per-analysis methods/results"),
    ("refresh_policy","Saved snapshot only; rebuild does not refresh live sources"),
    ("source_row_definition","CSV source_row is the 1-based logical CSV record including header, not physical line if embedded newlines occur")])
db.commit()
checks={"integrity_check":db.execute("PRAGMA integrity_check").fetchone()[0],
    "tri_forms":db.execute("SELECT COUNT(*) FROM tri_forms").fetchone()[0],
    "tri_years":db.execute("SELECT COUNT(DISTINCT reporting_year) FROM tri_forms").fetchone()[0],
    "tri_2024_facilities":db.execute("SELECT COUNT(DISTINCT trifd) FROM tri_forms WHERE reporting_year=2024").fetchone()[0],
    "tri_historical_facility_ids":db.execute("SELECT COUNT(DISTINCT trifd) FROM tri_forms").fetchone()[0],
    "form_a_with_nonnull_quantities":db.execute("SELECT COUNT(*) FROM tri_forms WHERE form_type='A' AND (reported_total_release IS NOT NULL OR reported_air IS NOT NULL)").fetchone()[0],
    "county_cancer_rows":len(county),"title_v_rows":len(title_v),
    "ahs_public_summary_rows":db.execute("SELECT COUNT(*) FROM ahs_public_cancer_summary").fetchone()[0] if ahs_summary.exists() else 0,
    "industry_evidence_records":db.execute("SELECT COUNT(*) FROM evidence").fetchone()[0],
    "datasets":db.execute("SELECT COUNT(*) FROM datasets").fetchone()[0],"search_records":db.execute("SELECT COUNT(*) FROM search_index").fetchone()[0],
    "search_smoke_matches":db.execute("SELECT COUNT(*) FROM search_index WHERE search_index MATCH 'formaldehyde'").fetchone()[0],
    "pdfs":dict(Counter(x["status"] for x in pdf_log))}
assert checks["integrity_check"]=="ok"
assert checks["tri_forms"]==60040 and checks["tri_years"]==38 and checks["tri_2024_facilities"]==463
assert checks["form_a_with_nonnull_quantities"]==0 and checks["industry_evidence_records"]==93
assert checks["search_smoke_matches"]>0
expected=json.loads((ROOT/"research/industries/statewide-industry-data-provenance.json").read_text())
total=db.execute("SELECT SUM(reported_total_release) FROM tri_forms WHERE reporting_year=2024 AND unit_of_measure='Pounds'").fetchone()[0]
assert abs(total-float(expected["tri_all_chemicals_reported_total_pounds"]))<0.00001
checks["tri_2024_total_pounds_matches_curated_summary"]=True
db.execute("PRAGMA optimize")
db.close()
TEMP.replace(FINAL)
(DEST/"pdf-text-extraction-log.json").write_text(json.dumps(pdf_log,indent=2))
manifest={"source_cutoff":SNAPSHOT,"schema_version":1,"database":"knowledge/research.sqlite",
    "database_sha256":sha(FINAL),"checks":checks,"tri_records_by_year":year_counts,
    "notes":["Database rebuilds from saved project sources; originals untouched.",
             "No modeled risks treated as observed cases or individual dose. Treatment benchmark is retrospective association, not causal efficacy or cure evidence.",
             "FTS includes original PDF extraction; extraction does not certify complete reading or OCR."]}
(DEST/"build-manifest.json").write_text(json.dumps(manifest,indent=2))
print(json.dumps(checks,indent=2))
