# Clean deterministic reproduction

**PASS.** A fresh isolated copy reproduced all scientific values in the primary, strict and independent calculations exactly. Five commands completed with exit code zero. Across those outputs and both fixture reports, 349,971 numeric leaves matched exactly. The 11 preserved original files and all five copied inputs remained byte-identical.

The [machine-readable evidence](deterministic-reproduction.json) records commands, terminal statuses, environment, logs, original/reproduced hashes, comparison counts and exact metadata exclusions. Its SHA256 is `4deda6a4d58a84d207d1dfcd2f38dc34f7fed45002317c310a78ee39e31db377`. All public paths use project-relative or `<project>/` notation.

| Output | Numeric leaves compared | Result |
|---|---:|---|
| Primary results | 117,672 | Exact match |
| Strict results | 117,631 | Exact match |
| Independent reference | 114,636 | Exact match |
| Reference fixtures | 31 | Exact match |
| Primary fixtures | 1 numeric count, plus all labels/statuses | Exact match |

The complete JSON payloads were compared with exact type, key, length and value checks. This includes all 20 cases, all 5,400 calibration settings per calculation, numerical diagnostic fields and provenance hashes. Exclusions were limited to `created_utc`, primary `runtime_seconds`, and reference/fixture `elapsed_seconds`. No scientific values, case fields, solver diagnostics, code hashes, environments or protocol fields were excluded. Different complete-file hashes are expected because those execution metadata changed.

The isolated directory is `tmp/age-calendar-2026-11-10/reproduction/checkout`. Only these necessary inputs were copied:

- `scripts/age_calendar_calibration.py`
- `scripts/age_lineage_models.py`
- `scripts/verify_age_calendar_calibration.py`
- This study's `protocol.json` and `theory.md`

The same scientific environment was used: Python 3.12.14, NumPy 2.3.5 and SciPy 1.16.3. The reference was pinned in the new copy, its off-grid fixtures were rerun, and both primary and reference full grids were calculated from scratch. No full-tree or calibration Monte Carlo job was rerun.

## Reproduce in a fresh copy

Use an unused directory and copy the five inputs with their repository-relative layout. From that isolated root, with the scientific Python environment active, run:

```sh
study_dir=research/treatment-discovery/lineage-audit-2026-11-10/age-calendar-calibration
python scripts/age_calendar_calibration.py --fixture-report "$study_dir/primary-fixtures.json"
python scripts/verify_age_calendar_calibration.py --pin --out "$study_dir/reference-code-pin.json"
python scripts/verify_age_calendar_calibration.py --fixtures --out "$study_dir/reference-fixtures.json"
python scripts/age_calendar_calibration.py --run --out "$study_dir/results.json" --strict-out "$study_dir/strict-results.json"
python scripts/verify_age_calendar_calibration.py --run --out "$study_dir/independent-reference.json"
```

Compare every resulting JSON field with the first published output after removing only the metadata fields listed above. The primary fixture object is also preserved inside `primary-code-pin.json`. The original complete-field comparator deliberately binds the published input hashes; it was not repointed or edited for this reproduction. Because every newly computed scientific value is identical, the existing independent comparison applies to those same values. This is stronger repeatability evidence than merely completing the commands, but it is not an additional independent model derivation.

The local reproduction manifest and command logs are retained under `tmp/age-calendar-2026-11-10/reproduction`. Cross-version or cross-platform bitwise identity is not promised. Repeatability does not establish biological validity, novelty, numerical interval certificates or resolution of any prior statistical flags.
