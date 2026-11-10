# Publication packaging note

One source-formatting change was made after the first numerical run: twelve trailing ASCII spaces were removed from the otherwise blank line 171 of `scripts/check_lineage_horizon_invariance.py`. Every other source byte is unchanged, and the Python abstract syntax trees are identical. The frozen protocol, functions, grid, tolerances and scientific interpretation were not changed.

The unchanged checker was rerun. All result fields are exactly equal after excluding only `generated_at_utc` and `script_sha256`; these are the only changed top-level fields. This includes every one of the 270 evaluated points, all 54 horizon comparisons, errors, controls, failures and environment metadata. Both runs pass. This packaging rerun is not an additional independent scientific check.

| Provenance | First run | Packaged rerun |
|---|---|---|
| Generated at UTC | `2026-11-10T19:10:24.016796+00:00` | `2026-11-10T19:16:46.291711+00:00` |
| Script SHA-256 | `7be17332f2f76dad913847ed8b15bc9efe6182186fe663866942597cc13b1aa1` | `1a26eea7ec3b1bf734003e3fa691848d7d21e60f75622b7ee403380b8219be3c` |
| Results SHA-256 | `262aa86d5ee5b7e52f433cb3eea1ebae6f656607cfe32107bd9131d899e93958` | `69b93e07018f468da3af4e1bf261e08f5ab2a8fc8b0c3ec280ad16a82487f798` |

Protocol SHA-256 remains `752885ddeb5de119deaa3a36dcd1d28e2735cf6bc222add08bb3dfb150133996`. The [machine-readable note](packaging-note.json) preserves first-run metadata, environments and the canonical hash of the identical comparison payload. [Current results](results.json) refer to the packaged code. The first-run script is reproducible from the packaged code by restoring twelve spaces on blank line 171; no other edit is required.
