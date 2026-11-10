# Clean deterministic reproduction

**Pass: every scientific value reproduced exactly.** One clean run was performed in an isolated ignored copy, using byte-identical scripts and frozen inputs. No original script, result, protocol, navigation file, or README was edited. This was a deterministic reproduction; Monte Carlo was not rerun.

The [evidence JSON](deterministic-reproduction.json) records the complete command arguments, working directory, start/end times, exit codes, log hashes, input/output hashes, preservation checks, and exhaustive scientific comparisons. The isolated directory is `tmp/age-lineage-2026-11-10/deterministic-reproduction-20261110T202341Z/`; its original inputs, fresh outputs, logs, and reproduction harness remain available locally.

For publication, 17 absolute path metadata fields use the portable `<project>` prefix. The unmodified raw report remains in that ignored directory as `deterministic-reproduction-raw.json`, SHA256 `47c16f8186384dd5c1d58ebf89d4765a1633a65e4b518e6a5becdb4e4b98bec3`. The public JSON records every transformed field. No scientific value or recorded artifact hash changed; reversing the prefix replacement exactly recovers the original report object.

## What ran

The primary and reference CLIs were inspected before execution. The existing scientific Python environment was reused: Python3.12.14, NumPy2.3.5, SciPy1.16.3. All eight commands completed with exit code0:

1. Record the Python/platform/library environment.
2. Inspect the primary driver's `--help` output.
3. Inspect the independent verifier's `--help` output.
4. Run the primary analytic and failure-path fixtures: **10 passed**.
5. Run the independent reference fixtures: **7 passed**.
6. Run all primary and strict deterministic cases to fresh output filenames.
7. Run the complete independent reference to a fresh output filename.
8. Run the unmodified pinned reference comparator to a fresh isolated comparison output.

The substantive commands, executed from the isolated root with the existing scientific environment's Python, were:

```sh
python scripts/check_age_lineage_fixtures.py
python scripts/verify_age_lineage_models.py --fixtures --out research/treatment-discovery/lineage-audit-2026-11-10/cell-cycle-specificity/reproduced-reference-fixtures.json
python scripts/run_age_lineage_models.py --out research/treatment-discovery/lineage-audit-2026-11-10/cell-cycle-specificity/reproduced-results.json --strict-out research/treatment-discovery/lineage-audit-2026-11-10/cell-cycle-specificity/reproduced-strict-results.json
python scripts/verify_age_lineage_models.py --run --out research/treatment-discovery/lineage-audit-2026-11-10/cell-cycle-specificity/reproduced-independent-reference.json
python scripts/compare_age_lineage_references.py
```

The comparator deliberately pins the original result file hashes, including their timestamps. It therefore ran unchanged against byte-identical copies of those original inputs. Separately, every newly reproduced scientific field was exhaustively compared with the corresponding original field. Exact equality establishes the same cross-formulation comparison for the reproduced values, without bypassing the comparator's hash checks or modifying its code.

## Results and exactness

| Artifact | Numeric leaves compared | Result |
|---|---:|---|
| Primary results | 22,031 | Exact match |
| Strict results | 21,883 | Exact match |
| Independent reference | 18,876 | Exact match |
| Pinned comparison report | 80,779 | Exact match |
| Two fixture reports | 2 count fields, plus all check labels and metadata | Exact match |

All other retained keys, list lengths, strings, booleans, nulls, configuration fields, protocol hashes, and code hashes also match. Canonical scientific-payload hashes are identical for all six artifact comparisons. The maximum absolute and relative numeric difference is zero; no fallback tolerance was needed.

The rerun again completed **72 models, 864 primary contrasts, 216 pair records, and 567 early-time records**. The reference retained all expected undefined zero-death ratios and no-division pair quantities. The full comparator again passed its 13,478 scalar comparisons against both production tolerances.

Only explicitly listed root timestamps and elapsed runtime fields were excluded. No scientific values or code/protocol provenance hashes were excluded. Complete output files have different hashes where those execution metadata changed; both file hashes and normalized scientific-payload hashes are retained in the evidence.

## Preservation and limits

All **13 protected originals** have identical before/after hashes. All **10 copied inputs** also remain byte-identical to their source snapshots. Fresh outputs were written under new names in the isolated directory, and first outputs were preserved.

This establishes repeatability on the same machine and scientific Python environment. It is not a cross-platform test, empirical replication, biological validation, or evidence of a cancer treatment effect. The study's interpretation and source limits remain those in the [theory](theory.md) and [independent comparison](independent-comparison.md).
