"""Add search sidecars to partial PDFs, rendering only pages with <=30 native chars."""
import concurrent.futures
import datetime
import hashlib
import json
import pathlib
import subprocess
from pypdf import PdfReader

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORK = ROOT / "tmp/pdfs/gap-ocr"
WORK.mkdir(parents=True, exist_ok=True)
LOG = ROOT / "knowledge/pdf-text-extraction-log.json"
selected = [r for r in json.loads(LOG.read_text()) if r["status"] == "partial_text_requires_page_review"]
selected.sort(key=lambda r: ("ames-municipal-power" not in r["file"], r["file"]))
binary = WORK / "ocr"
subprocess.run(["swiftc", str(ROOT/"scripts/ocr_pdf_applevision.swift"), "-o", str(binary)], check=True)
docs = []
for item in selected:
    source = ROOT / item["file"]
    pages = [p.extract_text() or "" for p in PdfReader(source).pages]
    folder = WORK / source.stem
    folder.mkdir(exist_ok=True)
    gaps = [i+1 for i, text in enumerate(pages) if len(text.strip()) <= 30]
    docs.append({"source": source, "pages": pages, "gaps": gaps, "folder": folder,
                 "sha256": hashlib.sha256(source.read_bytes()).hexdigest()})

def ranges(numbers):
    result = []
    for n in numbers:
        if result and n == result[-1][1] + 1:
            result[-1][1] = n
        else:
            result.append([n,n])
    return result

def render(job):
    doc, first, last = job
    subprocess.run(["pdftoppm", "-f", str(first), "-l", str(last), "-r", "180", "-png",
                    str(doc["source"]), str(doc["folder"]/"page")], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return {"file": str(doc["source"].relative_to(ROOT)), "first": first, "last": last}

jobs = [(d, f, l) for d in docs for f,l in ranges(d["gaps"])]
print(json.dumps({"documents": len(docs), "gap_pages": sum(len(d["gaps"]) for d in docs),
                  "total_pages_not_all_rendered": sum(len(d["pages"]) for d in docs)}), flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    futures = [pool.submit(render, job) for job in jobs]
    for future in concurrent.futures.as_completed(futures):
        print("Rendered " + json.dumps(future.result()), flush=True)

results = []
for doc in docs:
    subprocess.run([str(binary), str(doc["folder"]), str(doc["folder"])], check=True)
    ocr_pages = {p["physical_page"]: p for p in json.loads((doc["folder"]/"page-coverage.json").read_text())}
    assert sorted(ocr_pages) == doc["gaps"]
    output = doc["source"].with_suffix(".ocr.txt")
    provenance_path = doc["source"].with_suffix(".ocr.provenance.json")
    parts = ["SEARCH SIDECAR: NATIVE EXTRACTION PLUS GAP-PAGE OCR\n",
             f"Source: {doc['source'].name}\n",
             f"Original SHA-256: {doc['sha256']}\n",
             "Search aid only. Verify numeric tables, labels, exact quotations and layout against original pages.\n",
             "Only pages with 30 or fewer native extracted characters were rendered/OCRed.\n"]
    coverage = []
    for i, native in enumerate(doc["pages"], 1):
        if i in ocr_pages:
            ocr_text = (doc["folder"]/f"page-{i:02d}.txt").read_text()
            method = "ocr" if len(ocr_text.strip()) > 0 else "ocr_no_text_detected_needs_visual_review"
            text = ocr_text
            details = ocr_pages[i]
            if native.strip():
                details["short_native_extraction"] = native.strip()
                if native.strip() != ocr_text.strip():
                    text = "[SHORT NATIVE EXTRACTION, retained separately]\n" + native.strip() + "\n[OCR OF SAME PAGE]\n" + ocr_text
        else:
            method, text, details = "native_extraction", native, {}
        coverage.append({"physical_page": i, "method": method,
                         "native_extracted_characters": len(native.strip()),
                         "sidecar_characters": len(text.strip()), **details})
        parts.append(f"\n=== PDF PHYSICAL PAGE {i} OF {len(doc['pages'])}; METHOD {method} ===\n\n{text}\n")
    output.write_text("".join(parts))
    unchanged = hashlib.sha256(doc["source"].read_bytes()).hexdigest() == doc["sha256"]
    assert unchanged
    provenance = {
        "schema_version": "1.0", "created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "purpose": "Corpus search; no numeric data import or health/legal reinterpretation",
        "original_file": str(doc["source"].relative_to(ROOT)), "original_sha256_before": doc["sha256"],
        "original_sha256_after": doc["sha256"], "original_unchanged": unchanged,
        "sidecar": str(output.relative_to(ROOT)), "sidecar_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "pdf_pages": len(doc["pages"]), "native_text_pages_over_30_chars": len(doc["pages"])-len(doc["gaps"]),
        "ocr_attempted_physical_pages": doc["gaps"], "coverage": coverage,
        "method": {"native_extractor": "pypdf PdfReader.extract_text", "ocr_trigger": "native stripped text length <=30",
                   "renderer": "Poppler pdftoppm 26.05.0", "dpi": 180, "format": "PNG",
                   "ocr": "Apple Vision VNRecognizeTextRequest accurate en-US, language correction enabled",
                   "os": "macOS 26.6.2 build 25G83", "manual_text_corrections": False,
                   "pdf_modified": False, "helper": "scripts/ocr_pdf_applevision.swift",
                   "pipeline": "scripts/add_gap_ocr_sidecars.py"},
        "visual_review": {"pages_reviewed": [], "pending": True},
        "limitations": ["Search aid, not an authoritative transcription or table import",
                        "Native extraction can have ordering/table errors even on pages over the threshold",
                        "OCR may misread letters, numbers, formulas, symbols, charts and handwriting",
                        "An OCR confidence of 1 is not calibrated accuracy",
                        "All physical pages have markers; this does not establish recognition of every visible mark"]}
    provenance_path.write_text(json.dumps(provenance, indent=2)+"\n")
    result = {"file": str(doc["source"].relative_to(ROOT)), "sidecar": str(output.relative_to(ROOT)),
              "provenance": str(provenance_path.relative_to(ROOT)), "pages": len(doc["pages"]),
              "ocr_pages": doc["gaps"], "original_unchanged": unchanged,
              "ocr_empty_pages": [p["physical_page"] for p in coverage if p["method"].startswith("ocr_no_text")]}
    results.append(result)
    print("Saved " + json.dumps(result), flush=True)
(WORK/"batch-results.json").write_text(json.dumps(results, indent=2)+"\n")
