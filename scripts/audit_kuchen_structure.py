"""Read-only structural audit of downloaded eLife 51002 source workbooks.

No survival, covariance, hazard, treatment association, or model fitting.
Uses the saved schema's workbook XML paths. Raw sources are never rewritten.
"""
import argparse
from pathlib import Path
from collections import Counter
import hashlib
import json
import math
import re
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/treatment-discovery/lineage-audit-2026-11-10/kuchen-source-audit"
SOURCES = ROOT / "research/treatment-discovery/sources/lineage-2026-11-10/alternative-lineage-2026-11-10"
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def read_rows(path, xml_path):
    with zipfile.ZipFile(path) as archive:
        shared = ["".join(x.itertext()) for x in ET.fromstring(
            archive.read("xl/sharedStrings.xml")).findall("m:si", NS)]
        records = []
        for row in ET.fromstring(archive.read(xml_path)).findall("m:sheetData/m:row", NS):
            values = {}
            for cell in row.findall("m:c", NS):
                value = cell.find("m:v", NS)
                if value is not None:
                    values[re.sub(r"[0-9]", "", cell.attrib["r"])] = (
                        shared[int(value.text)] if cell.attrib.get("t") == "s" else value.text)
            records.append((int(row.attrib["r"]), values))
        return records[1:]


def inspect(meta, source_dir):
    rows = read_rows(source_dir / meta["file"], meta["xml_path"])
    gcol = "P" if meta["file"] == "kuchen-control.xlsx" else "L"
    children, mother_counts, issues, counts, residuals = {}, Counter(), [], Counter(), []
    for rownum, row in rows:
        mother_counts[row["K"]] += 1
        for side, idcol, fcols in [(1, "I", "BCD"), (2, "J", "EFG")]:
            cell_id = row[idcol]
            assert cell_id not in children, (meta["sheet"], cell_id, "duplicate")
            durations = {kind: float(row[col]) for kind, col in zip(
                ["division", "death", "loss"], fcols) if math.isfinite(float(row[col]))}
            counts[f"finite_fate_fields_{len(durations)}"] += 1
            for kind in durations:
                counts[kind] += 1
            children[cell_id] = {"birth": float(row["H"]), "durations": durations,
                                 "mother": row["K"], "generation": int(float(row[gcol]))}
            for kind, col in zip(["division", "death", "loss"], fcols):
                if math.isfinite(float(row[col])) and float(row[col]) < 0:
                    issues.append({"kind": "negative_duration", "cell": f"{col}{rownum}",
                                   "id": cell_id, "field": kind, "source_value": row[col]})
    for cell_id, child in children.items():
        if child["mother"] in children:
            mother = children[child["mother"]]
            if "division" not in mother["durations"]:
                issues.append({"kind": "parent_without_division", "id": cell_id})
            else:
                residual = abs(child["birth"] - mother["birth"] - mother["durations"]["division"])
                residuals.append(residual)
                if residual > 1e-6:
                    issues.append({"kind": "parent_time_mismatch", "id": cell_id,
                                   "absolute_residual": residual})
        elif child["generation"] != 2:
            issues.append({"kind": "unrecorded_parent_after_generation_2", "id": cell_id})
        if "division" in child["durations"] and cell_id not in mother_counts:
            issues.append({"kind": "division_without_successor_pair", "id": cell_id})
    return {
        "file": meta["file"], "sheet": meta["sheet"], "pair_rows": len(rows),
        "unique_children": len(children), "lineage_id_count": len({r["A"] for _, r in rows}),
        "duplicate_mother_rows": sum(n - 1 for n in mother_counts.values()),
        "field_counts": dict(counts), "issues": issues,
        "largest_parent_time_residual_hours": max(residuals, default=None),
        "generation_min": min(c["generation"] for c in children.values()),
        "generation_max": max(c["generation"] for c in children.values()),
        "largest_recorded_birth_plus_duration": max(c["birth"] + d for c in children.values()
                                                       for d in c["durations"].values()),
    }


EXPECTED_WORKBOOKS = {'kuchen-control.xlsx': '8ecdd5c66a466b71b5ee4790c79c2b9ce38fd1ec6daf59f88347d67e4fa1b86e', 'kuchen-perturbation.xlsx': '0065797f9d1cb12dc695bf9baa516f68afea1d6c6077b75c2a9830389806a6f3'}
EXPECTED_SCHEMA = 'c0b676bd16c3a1eeac12dadf061498e7f7830fdfeded69f6d7d042396768f3db'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=SOURCES)
    parser.add_argument("--schema", type=Path, default=BASE / "kuchen-schema.json")
    parser.add_argument("--out", type=Path, default=BASE / "structural-verification.json")
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError("Preserve the first audit; choose a new --out")
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    for name, expected in EXPECTED_WORKBOOKS.items():
        if digest(args.source_dir / name) != expected:
            raise ValueError("Changed source workbook: " + name)
    if digest(args.schema) != EXPECTED_SCHEMA:
        raise ValueError("Changed source schema; freeze a new version before use")
    schemas = json.loads(args.schema.read_text())
    result = {
        "status": "STRUCTURAL_ONLY_NOT_ANALYSIS_READY",
        "scope": "No Q, covariance, survival/hazard estimate, association, or model fit.",
        "script_sha256": digest(Path(__file__)),
        "input_sha256": {**EXPECTED_WORKBOOKS, "kuchen-schema.json": EXPECTED_SCHEMA},
        "records": [inspect(meta, args.source_dir) for meta in schemas],
        "source_preservation": "Read-only ZIP/XML parsing; source hashes are verified before and after.",
        "parser_origin": "Portable version of the initial independently written structural parser; identical inspection logic.",
    }
    assert all(digest(args.source_dir / name) == expected for name, expected in EXPECTED_WORKBOOKS.items())
    encoded = json.dumps(result, indent=2, allow_nan=False) + "\n"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as stream:
        stream.write(encoded)
    print(json.dumps({"sheets": len(result["records"]),
                      "pair_rows": sum(r["pair_rows"] for r in result["records"]),
                      "children": sum(r["unique_children"] for r in result["records"]),
                      "issues": sum(len(r["issues"]) for r in result["records"])}))


if __name__ == "__main__":
    main()
