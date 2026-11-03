#!/usr/bin/env python3
"""Validate canonical catalog JSON and render its Markdown view.

Edit research/data-source-catalog.json directly to update source metadata.
This script downloads nothing and does not change that canonical JSON.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "research/data-source-catalog.json"
OUTPUT = ROOT / "research/data-source-catalog.md"
PUBLICATION_MANIFEST = ROOT / "publication/source-manifest.json"
OMITTED_STATUSES = {"linked_source_only", "local_generated"}


def sentence(text):
    return text.rstrip(". ") + "."


def publication_entries():
    if not PUBLICATION_MANIFEST.exists():
        return {}
    manifest = json.loads(PUBLICATION_MANIFEST.read_text(encoding="utf-8"))
    return {item["path"].rstrip("/"): item for item in manifest["files"]}


def entries_for_path(path, entries):
    path = path.rstrip("/")
    if path in entries:
        return [entries[path]]
    # Catalog entries may point to an archived directory rather than one file.
    return [item for name, item in entries.items() if name.startswith(path + "/")]


def intentionally_omitted(path, entries):
    matches = entries_for_path(path, entries)
    # A missing directory with included descendants is still an unexpected loss.
    return bool(matches) and all(item["publication_status"] in OMITTED_STATUSES for item in matches)


def main():
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    records = data["resources"]
    assert data["resource_count"] == len(records)
    assert len({row["id"] for row in records}) == len(records)
    published = publication_entries()
    missing = [path for row in records for path in row["local_paths"] if not (ROOT / path).exists()]
    unexpected_missing = [path for path in missing if not intentionally_omitted(path, published)]
    assert not unexpected_missing, unexpected_missing
    required = {"id", "name", "publisher", "source_urls", "geographic_coverage", "time_coverage", "record_grain", "join_keys", "units", "access", "limitations", "intended_use", "local_status", "verified_date"}
    for row in records:
        assert required <= row.keys(), row["id"]
        assert all(url.startswith("https://") for url in row["source_urls"])
    lines = [
        "# Primary data-source catalog for future Iowa cancer models", "",
        "Snapshot: October 22, 2026. The JSON companion is the canonical structured catalog. This is a source and method index, not a merged causal dataset. Documentation and links were verified; not every remote table or access path was downloaded/tested. A related archived report is distinguished from a downloaded dataset.", "",
        "Archived State Cancer Profiles incidence is 2019-2023 and mortality 2020-2024. USCS June 2026 tables extend incidence through 2023. UCMR 5's final dataset was released August 2026. USGS final 2018-2022 pesticide estimates are planned for December 2026, after this cutoff. The 2025 ACS 1-year release is scheduled October 29, 2026, also after cutoff. Use each source's data period rather than its publication year.", "",
        "## Join and model rules", "",
        *[f"- {sentence(rule)}" for rule in data["join_and_model_rules"]],
    ]
    if PUBLICATION_MANIFEST.exists():
        lines[4:4] = [
            "Local status and paths below describe the dated research workspace. The public copy excludes some cached sources and generated files; [publication/source-manifest.json](../publication/source-manifest.json) records availability and upstream source links. An excluded file may still be present in the original local workspace.", "",
        ]
    current_group = None
    for row in records:
        if row["group"] != current_group:
            current_group = row["group"]
            lines += ["", f"## {current_group}", ""]
        links = "; ".join(f"[Source {index + 1}]({url})" for index, url in enumerate(row["source_urls"]))
        local = "; ".join(f"`{path}`" for path in row["local_paths"]) or "No dataset downloaded for this catalog"
        lines += [
            f"### {row['id']}: {row['name']}", "",
            f"Publisher: {row['publisher']}. {links}.", "",
            "**Coverage/time:** " + sentence(row["geographic_coverage"]) + " " + sentence(row["time_coverage"]), "",
            "**Grain/joins:** " + sentence(row["record_grain"]) + " Keys: " + sentence("; ".join(row["join_keys"])), "",
            "**Units/access:** " + sentence(row["units"]) + " " + sentence(row["access"]), "",
            "**Use/limits:** " + sentence(row["intended_use"]) + " " + sentence(row["limitations"]), "",
            f"**Local status:** `{row['local_status']}`. {sentence(local)}", "",
        ]
        omitted = {item["path"]: item["publication_status"]
                   for path in row["local_paths"] for item in entries_for_path(path, published)
                   if item["publication_status"] in OMITTED_STATUSES}
        if omitted:
            availability = "; ".join(f"`{path}` (`{status}`)" for path, status in sorted(omitted.items()))
            lines += [f"**Public copy exclusions:** {availability}. See the publication manifest for source links and restoration details.", ""]
    lines += [
        "## Practical acquisition order", "",
        "For an initial county model, start with the already archived cancer extracts and compatible population denominators. Add historical chemical-specific exposure series and independently measured or model-aware covariates after defining cancer site and latency. Use ACS 5-year estimates for all 99 counties, BRFSS for direct state trends, and PLACES for limited cross-sectional local context. Retrieve actual finished-water measurements and service areas before assigning water exposure. Keep QCEW/CBP workplace employment separate from residential populations. Obtain approved registry data when finer subtype or geography is required; public county products cannot provide individual job or residential history.", "",
        "Full USCS/SEER case databases, complete USGS pesticide files, USDA county panels, UCMR 5, IWIS/PWTS, AQS, ACS, QCEW/CBP and population/geographic files were not downloaded for this catalog. These are acquisition gaps, not evidence that exposure or disease is absent.", "",
    ]
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"resources": len(records), "missing_local_paths": missing, "canonical": str(CATALOG), "rendered": str(OUTPUT)}, indent=2))


if __name__ == "__main__":
    main()
