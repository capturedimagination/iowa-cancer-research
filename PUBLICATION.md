# Public research snapshot

Prepared November 3, 2026 for the public `capturedimagination/iowa-cancer-research` repository. The evidence retains its original observation periods, retrieval dates and limitations. Publication does not mean the research has been peer reviewed or that a treatment or cure has been established.

## What is published

All original project reports, research memos, source ledgers, evidence tables, derived factual data, methods, protocols, audit findings, benchmark results and analysis code are included. The authored 19-page report PDF is included. Federal NCI/EPA tabular downloads, the specifically licensed DepMap/PRISM metadata archives and the public ODbL clinical snapshot are included with attribution.

Cached publisher/state/agency source PDFs, OCR, copied web pages, unlicensed author code/data and the mixed-rights full-text SQLite database remain in the original local workspace. Their original links, identifiers, hashes and the project's findings remain available. Read [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for the source-specific scope. No project findings were withheld because a cached original was not mirrored.

[source-manifest.json](publication/source-manifest.json) inventories local snapshot files with `included`, `linked_source_only` or `local_generated` status, bytes, SHA-256 and stable upstream URLs where recorded. [included-files.txt](publication/included-files.txt) is the public-file selection. These statuses supplement historical `local_status` and `local_paths`; they do not rewrite what was downloaded during the research.

Temporary publisher signing queries were removed from one public transport manifest, and a local account path was replaced by a project-relative path. [sanitization-log.json](publication/sanitization-log.json) records original/public hashes and changes. Original source data values, recorded artifact hashes, results and the frozen scientific specification were preserved.

## Reproduce the clinical benchmark

The saved calculation used Python 3.12.14 and NumPy 2.3.5. Use Python 3.12 with the pinned dependencies:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python research/treatment-discovery/audit_clinical_snapshot.py
python scripts/run_nsclc_benchmark.py
```

The benchmark script regenerates the existing results directory. Run in a disposable clone if you want to preserve the published timestamp/provenance byte-for-byte. Source hashes, patient/sample cardinality and the frozen specification are checked before calculation. The result should be rank AUC `0.6137405980554027` for 69 YES and 158 NO outcomes, with 13 NE records explicitly excluded. The 10,000-draw conditional percentile interval is approximately `0.531279–0.694873` with the recorded environment and seed. This is a retrospective reproduction of a known association, not independent clinical validation.

The [analysis specification](research/treatment-discovery/clinical-pilot-analysis-spec.md), [result interpretation](research/treatment-discovery/results/nsclc-tmb-dcb-2026-10-29/RESULTS.md) and [independent arithmetic review](research/treatment-discovery/results/nsclc-tmb-dcb-2026-10-29/independent-review.md) explain specimen-timing, assay-vintage, endpoint and treatment-comparison limits. No predictive cutoff or clinical treatment-selection model was fitted.

## Rebuild the searchable library

```sh
python scripts/build_knowledge_base.py
python scripts/query_research.py search "formaldehyde"
python scripts/query_research.py search "EGFR"
```

The rebuild uses the published tabular inputs and available research text; it downloads nothing. The generated `knowledge/research.sqlite` is intentionally ignored by Git. Its text corpus, hash and search-record counts differ from the original full local cache because source mirrors are omitted. The dated original build manifest describes the local research snapshot; a new rebuild replaces it with the new build's values. Neither the rebuild nor a successful check establishes scientific or medical validity.

## Sources available by link

The Maynard metadata audit and preclinical model-overlap findings are published, but some upstream originals are not redistributed. Their adjacent manifests identify the original files and hashes. To rerun the Maynard audit, obtain `S01_metacells.csv` from the source listed in its manifest, subject to the source's terms, and place it at the documented path. The audit rejects a changed hash. The expression matrix and exact paper-signature mapping remain separate unmet requirements; published metadata counts are candidates before malignant-cell and assay QC.

The preclinical overlap JSON is a dated audit result. Its metadata sources and identifiers are documented; a standalone complete overlap-reproduction script was not saved. Do not present that artifact as a fully automated pipeline. The TRI historical download script refreshes remote data and is not an exact historical restoration tool; for a pinned reproduction use the included originals and their manifest hashes.

PDF regeneration is optional. `scripts/build_report.py` accepts `IOWA_CANCER_FONT_DIR` containing the original Libertine/Rubik font files, discovers compatible local fonts, and otherwise falls back to built-in ReportLab fonts. Layout/page count can differ under fallback fonts. Existing source extraction and OCR tools may require original linked PDFs; Apple Vision OCR additionally requires macOS, Swift and Poppler. Their presence is not required to read the findings or run the clinical benchmark.

## Publication checks

`scripts/check_publication.py` checks indexed Git blobs for large/private/generated files, recognizable credential patterns, local account paths, signed download URLs and broken relative Markdown links. It prints paths and issue categories rather than secret values. It is a scoped publication check, not a comprehensive security audit.

```sh
python scripts/check_publication.py --manifest publication/source-manifest.json
```

The original reports are dated research outputs. Refresh time-sensitive clinical, regulatory and dataset-access facts before consequential use, and preserve each source's population, units and observation period.
