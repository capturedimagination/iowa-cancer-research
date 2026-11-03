#!/usr/bin/env python3
"""Reproduce the complete 2024 Iowa DNR Title V Appendix A extraction.

Requires pypdf. No network access; the archived original is the input.
IDs are DNR inventory IDs, not EPA FRS or TRI IDs. Read the provenance JSON.
"""
import argparse
import csv
import hashlib
import json
import re
from decimal import Decimal
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "sources/industries/food-agprocessing/iowa-point-source-emissions-2024-feb2026.pdf"
DEFAULT_OUTPUT = ROOT / "research/iowa-title-v-facilities-emissions-2024.csv"
SOURCE_URL = "https://www.iowadnr.gov/media/2277/download?inline="
POLLUTANTS = ["pm25_primary_tons", "pm10_primary_tons", "so2_tons", "nox_tons", "voc_tons", "co_tons", "lead_tons", "ammonia_tons", "total_haps_tons"]
FIELDS = ["facility_id", "facility_name", "pdf_page", *POLLUTANTS, "data_year", "units", "source_url", "limits"]
LIMITS = "Title V point sources only. HAP mass is not cancer risk; HAPs include noncarcinogens. Not a verified causal ranking."
ROW = re.compile(r"^\s*(\d{2}-\d{2}-\d{3}(?:-\d{2})?)\s+(.+?)\s+((?:[\d,]+\.\d{2}\s+){8}[\d,]+\.\d{2})\s*$")
HEADER = re.compile(r"^(Facility ID|PRI\b|HAPs\b|Facility Name|Appendix A - Emissions Summary)")


def extract(pdf_path):
    reader = PdfReader(pdf_path)
    rows = []
    unexpected = []
    # Appendix A: physical PDF pages 20 through 30, inclusive.
    for index in range(19, 30):
        for line in reader.pages[index].extract_text(extraction_mode="layout").splitlines():
            stripped = line.strip()
            match = ROW.match(line)
            if match:
                fid, name, numbers = match.groups()
                values = [value.replace(",", "") for value in numbers.split()]
                assert len(values) == 9
                rows.append(dict(zip(FIELDS, [fid, name.strip(), index + 1, *values, 2024, "tons/year (report wording; ton definition not specified in PDF)", SOURCE_URL, LIMITS])))
            elif not stripped or stripped.isdigit() or HEADER.match(stripped):
                continue
            elif rows and not re.search(r"\d+\.\d{2}", stripped):
                # Long facility names continue in the otherwise empty name column.
                rows[-1]["facility_name"] += " " + stripped
            else:
                unexpected.append({"pdf_page": index + 1, "line": line})
    assert not unexpected, unexpected
    assert len(rows) == 283, len(rows)
    assert len({row["facility_id"] for row in rows}) == 283
    assert sum(Decimal(row["total_haps_tons"]) for row in rows) == Decimal("5483.81")
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    rows = extract(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"rows": len(rows), "unique_dnr_facility_ids": 283, "sum_total_haps_tons": "5483.81", "source_sha256": hashlib.sha256(args.source.read_bytes()).hexdigest(), "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
