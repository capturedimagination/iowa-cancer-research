"""Reconstruct the pinned GSE292469 sample audit from separately acquired sources.

Uses only Python's standard library. No downloads, expression scoring, or Git
operations occur. The explicit output directory receives derived sample-level
metadata and aggregate audit counts; original source bodies remain untouched.
Hashes pin the November 10, 2026 retrieval of the November 1 public release.
A changed upstream record requires a separately reviewed snapshot/version.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import gzip
import hashlib
import json
from pathlib import Path
import re


PINNED = {
    "GSE292469-series.txt": (
        6706, "5a777bf9541d9e21d91ae03106adc703409bf2f3e8ce6e442fdefece5f6441fd"),
    "GSE292469-samples.txt": (
        296198, "b51d6e9652b8976302911d0ed56a1dc596a83e9e40eca04fc847ad1f9705d83a"),
    "GSE292469_cell_metadata.tsv.gz": (
        18852668, "9b16b89922bade9d1334ebaeb002763dcca9fd2652a3e9616befb98f04777012"),
}
FIELDS = [
    "cell_id", "cell_type", "nCount_RNA", "nFeature_RNA", "sample_id", "core_id",
    "time_point", "is_tumor_cell", "scDblFinder.class", "scDblFinder.score",
    "scDblFinder.weighted", "scDblFinder.cxds_score",
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def validate_source(path, canonical_name):
    size, expected_hash = PINNED[canonical_name]
    require(path.stat().st_size == size, f"Changed source size: {canonical_name}")
    actual = digest(path)
    require(actual == expected_hash, f"Changed source SHA-256: {canonical_name}")
    return actual


def audit_cells(path):
    cells, cell_ids, core_owner = {}, set(), {}
    with gzip.open(path, "rt", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        require(reader.fieldnames == FIELDS, "Changed cell metadata schema")
        for row in reader:
            require(row["cell_id"] and row["cell_id"] not in cell_ids,
                    "Missing or duplicate cell_id")
            cell_ids.add(row["cell_id"])
            require(row["time_point"] in {"TN", "MRD", "PD"}, "Unknown state")
            require(row["is_tumor_cell"] in {"TRUE", "FALSE"}, "Unknown tumor flag")
            require((row["is_tumor_cell"] == "TRUE") == (row["cell_type"] == "Tumor Cell"),
                    "Tumor flag and cell-type annotation disagree")
            require(row["scDblFinder.class"] == "singlet", "Non-singlet in pinned snapshot")
            sid, core = row["sample_id"], row["core_id"]
            require(sid and core, "Missing sample/core ID")
            require(core_owner.setdefault(core, sid) == sid, "Core belongs to multiple samples")
            z = cells.setdefault(sid, {
                "states": set(), "cores": Counter(), "nuclei": 0, "malignant_nuclei": 0})
            z["states"].add(row["time_point"])
            z["cores"][core] += 1
            z["nuclei"] += 1
            z["malignant_nuclei"] += row["is_tumor_cell"] == "TRUE"
    require(len(cell_ids) == 457724, "Changed cell count")
    require(len(cells) == 73 and len(core_owner) == 74, "Changed sample/core count")
    return cells


def parse_libraries(path, cells, series_text):
    libraries = []
    for section in path.read_text().split("^SAMPLE = ")[1:]:
        lines = section.splitlines()
        d, raw, protocols = {"gsm": lines[0]}, {}, []
        for line in lines[1:]:
            if line.startswith("!Sample_title = "):
                d["title"] = line.split(" = ", 1)[1]
            if line.startswith("!Sample_characteristics_ch1 = "):
                key, value = line.split(" = ", 1)[1].split(": ", 1)
                require(key not in raw, f"Duplicate characteristic in {d['gsm']}: {key}")
                raw[key] = value
            if line.startswith("!Sample_description = Library name: "):
                d["library_name"] = line.split("Library name: ", 1)[1]
            if line.startswith("!Sample_extract_protocol_ch1 = "):
                protocols.append(line)
        title_id = d["title"].split(", ")[-1]
        match = re.fullmatch(r"((?:TN|MRD|PD|LX)\d+)(?: \(core ([12]) of 2\))?", title_id)
        require(match is not None, f"Unrecognized sample title: {d['gsm']}")
        sid, core_number = match.groups()
        require(sid in cells, f"GSM sample missing from cell metadata: {sid}")
        require((core_number is None) or sid == "MRD2", "Unexpected repeated-core specimen")
        d["sample_id"] = sid
        d["core_id"] = f"{sid}_core{core_number}" if core_number else sid
        require(d["core_id"] in cells[sid]["cores"], "GSM core missing from cell metadata")
        d["state"] = raw["time point"]
        for field in ("genotype", "tissue", "procedure", "histology"):
            d[field] = raw[field]
            require(d[field] not in {"", "NA"}, f"Missing {field}: {sid}")
        d["stage"] = raw["tumor stage"]
        day_keys = [k for k in ("days on osimertinib at collection",
                               "days on_osimertinib_at_collection") if k in raw]
        require(len(day_keys) == 1, f"Ambiguous/missing treatment duration: {sid}")
        days = raw[day_keys[0]]
        d["days_osimertinib_at_collection"] = None if days in {"NA", ""} else int(days)
        require(d["days_osimertinib_at_collection"] is None or
                d["days_osimertinib_at_collection"] >= 0, "Negative treatment duration")
        d["batch_reported"] = raw.get("batch")
        # This is the explicit Series rule, not a correction of the GSM prose.
        require("twelve libraries with LX identifiers" in series_text and
                "Chromium 3' v4 kit" in series_text, "Series kit-assignment wording changed")
        d["kit_series_implied"] = "v4" if d["library_name"].startswith("LX") else "v3.1"
        protocol_kits = set(re.findall(r"\bv(3\.1|4)\b", " ".join(protocols)))
        require(len(protocol_kits) == 1, f"Ambiguous GSM kit prose: {d['gsm']}")
        d["kit_gsm_extract_protocol"] = "v" + next(iter(protocol_kits))
        d["kit_conflict"] = d["kit_series_implied"] != d["kit_gsm_extract_protocol"]
        d["source_url"] = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=" + d["gsm"]
        libraries.append(d)
    require(len(libraries) == 74, "Changed number of GEO sample/library records")
    for key in ("gsm", "core_id", "library_name"):
        require(len({d[key] for d in libraries}) == 74, f"Duplicate library {key}")
    expected_gsms = set(re.findall(r"^!Series_sample_id = (GSM\d+)$", series_text, re.M))
    require(expected_gsms == {d["gsm"] for d in libraries}, "Series/GSM membership mismatch")
    require(Counter(d["kit_series_implied"] for d in libraries) == {"v3.1": 62, "v4": 12},
            "Series kit counts do not reconcile")
    return libraries


def build_samples(cells, libraries):
    samples = []
    for sid, c in cells.items():
        matched = [d for d in libraries if d["sample_id"] == sid]
        require(len(c["states"]) == 1, f"Conflicting cell states: {sid}")
        state = next(iter(c["states"]))
        require({d["state"] for d in matched} == {state}, f"GSM/cell state conflict: {sid}")
        require({d["core_id"] for d in matched} == set(c["cores"]), f"Unmapped core: {sid}")
        z = {"sample_id": sid, "state": state, "nuclei": c["nuclei"],
             "malignant_nuclei": c["malignant_nuclei"], "core_nuclei": dict(c["cores"]),
             "source_gsm": [d["gsm"] for d in matched], "libraries": matched}
        for key in ("genotype", "tissue", "procedure", "histology", "stage",
                    "days_osimertinib_at_collection"):
            values = {d[key] for d in matched}
            require(len(values) == 1, f"Conflicting sample characteristic: {sid}, {key}")
            z[key] = next(iter(values))
        kits = {d["kit_series_implied"] for d in matched}
        z["kit_series_implied"] = "mixed" if len(kits) > 1 else matched[0]["kit_series_implied"]
        z["kit_conflict"] = any(d["kit_conflict"] for d in matched)
        samples.append(z)
    require(Counter(s["state"] for s in samples) == {"TN": 28, "MRD": 14, "PD": 31},
            "Changed specimen-level state counts")
    return samples


def summarize(samples):
    summary = {}
    for threshold in (1, 20, 100):
        included = [x for x in samples if x["malignant_nuclei"] >= threshold]
        summary[str(threshold)] = {}
        for restriction in ("all_histologies", "LUAD_only"):
            selected = included if restriction == "all_histologies" else [
                x for x in included if x["histology"] == "LUAD"]
            counts = {}
            for state in ("TN", "MRD", "PD"):
                rows = [x for x in selected if x["state"] == state]
                counts[state] = {"n": len(rows),
                                 "site": dict(Counter(x["tissue"] for x in rows)),
                                 "procedure": dict(Counter(x["procedure"] for x in rows)),
                                 "stage": dict(Counter(x["stage"] for x in rows)),
                                 "kit_series_implied": dict(Counter(x["kit_series_implied"] for x in rows)),
                                 "sample_ids": [x["sample_id"] for x in rows]}
            summary[str(threshold)][restriction] = counts
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--series", type=Path, required=True)
    parser.add_argument("--sample-records", type=Path, required=True)
    parser.add_argument("--cell-metadata", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True,
                        help="Explicit local output directory (normally ignored tmp/)")
    args = parser.parse_args()
    paths = {"GSE292469-samples.txt": args.sample_records,
             "GSE292469_cell_metadata.tsv.gz": args.cell_metadata,
             "GSE292469-series.txt": args.series}
    hashes = {name: validate_source(path, name) for name, path in paths.items()}
    series_text = args.series.read_text()
    require(series_text.startswith("^SERIES = GSE292469\n"), "Wrong GEO accession")
    cells = audit_cells(args.cell_metadata)
    libraries = parse_libraries(args.sample_records, cells, series_text)
    samples = build_samples(cells, libraries)
    output = {"retrieved_utc_date": "2026-11-10", "source_accession": "GSE292469",
              "source_sha256": hashes,
              "notes": ["No expression values were inspected.",
                        "sample_id is patient unit per GEO overall design, not individual nuclei.",
                        "MRD2 two cores are one specimen/patient.",
                        "Kit assignment is inferred from Series description of LX vs non-LX libraries; the GSM protocol paragraphs all say v3.1, so kit uncertainty is retained.",
                        "Only days on osimertinib at collection was harmonized from old and new characteristic key spelling; raw field strings remain in archived source."],
              "samples": samples}
    summary = summarize(samples)
    args.out.mkdir(parents=True, exist_ok=True)
    for filename, value in (("sample-metadata-derived.json", output),
                            ("sample-confounder-audit.json", summary)):
        path = args.out / filename
        body = json.dumps(value, indent=2, allow_nan=False) + "\n"
        if path.exists():
            require(path.read_text() == body, f"Refusing to overwrite different output: {filename}")
        else:
            path.write_text(body)
        print(f"Verified {filename}: SHA-256 {digest(path)}")
    print("Validated 457724 nuclei, 73 patients/specimens, 74 libraries; no expression scoring.")


if __name__ == "__main__":
    main()
