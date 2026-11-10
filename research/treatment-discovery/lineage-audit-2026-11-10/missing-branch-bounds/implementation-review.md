# Source and implementation review before outcome calculation

**Pass for the frozen, pinned-source descriptive calculation.** No blocking mismatch was found between the protocol, source mapping, and event-order rules. This review does not authorize population inference, establish biological annotation accuracy, or validate the separate ratio/contrast mathematics.

The reviewed protocol is `c46e452f3b17b96a8f98e6bc834540d830af9b4a1e3b39b8d3a2c1665f342771`; the core is `27bb3b07186b015a5d573d45ffe1da6515131ea0b3da09e677531c468eb4513e`; the caller is `31dcbbeb9ff04c0ab6eb49ea99f5e1d63c9525cc69d0f3c1e3652cc63821d17c`. Full pins and gate metadata are in [implementation-review.json](implementation-review.json).

## What was checked

The reviewer reread the pinned source codebook and the two implementation files. The original XLSX was parsed read-only using the already published structural parser. A separate label/frame reconciliation compared the workbook with the candidate graph and `GraphMass` constructor. Before construction, outcome entry points were replaced with raising stubs. **No source mass, family-survival fraction, ratio, bound, or horizon contrast was calculated.** No root-owned code was modified. The inline gate calculation is documented here; this is not a claim of a separate public checker implementation.

- All 49,407 positive-label/frame groups reconcile with unique cell episodes. Source event keys match exactly, map to one episode each, and have no zero-lineage events. Shared-row observations agree.
- Every edge has the documented parent division followed by the next-frame child boundary, consistent label metadata, and matching node child lists.
- The constructor independently discovers the one simultaneous division/apoptosis conflict even though the earlier graph issue list omitted it. Its ambiguity set exactly matches that conflict plus the 10 source mask label/frame groups. No strictly post-apoptosis division was found.
- Direct workbook eligibility reconstruction matches all five baseline rosters. The caller excludes no additional rows for apoptosis at or before baseline in this dataset. No future-completeness filter is applied.

## Event order and observation meaning

| Rule | Review finding |
|---|---|
| Division and apoptosis in the same frame | The conflict creates an ambiguity cutoff before either fate is classified. Equality between death and cutoff returns unknown. |
| Death offset 0 or 1 | Death is absorbing at annotation plus offset. The empirical caller uses the same stricter baseline eligibility for both offsets. |
| Core baseline API | The core checks offset-adjusted death, allowing a synthetic first-interval death with annotation 0 and offset 1. This does not change the caller's frozen empirical eligibility. |
| Death before a later mask | Death remains absorbing when strictly before the selected cutoff, despite later image tracking. Under the more conservative whole-episode policy, the deliberately earlier cutoff may instead discard that episode history. |
| Earlier ambiguity | Only ambiguity frames strictly after baseline coarsen the forward path. A prior component issue does not remove a later observed baseline cell. |
| Whole-episode policy | Its cutoff is `max(first_frame, baseline+1)`, preserving the time-zero snapshot. |
| Missing daughter | Each observed child receives half the incoming mass; each absent child retains an unknown half. Available daughters are never renormalized. |
| Division at baseline | Time zero is the parent snapshot. The division flag transfers mass to children at the next frame. All observed graph edges support this coordinate rule. |
| Fixed roster | One eligible roster is created per baseline and reused across every offset, ambiguity policy, and selection horizon. |

“Known live” remains shorthand for recorded and not death-annotated under the protocol's observation assumptions. Neither available fluorescence nor a positive lineage label independently proves viability. Recorded tracking can continue after apoptosis; it does not delay death. Undocumented termination remains unknown. These meanings follow the [original codebook](https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-018-07788-5/MediaObjects/41467_2018_7788_MOESM6_ESM.docx), with the timing and ambiguity sensitivities explicitly imposed by this project.

## Fixed roster and frame checks

| Baseline frame | Eligible recorded cells | Division flags at baseline | Selection frames at 24 / 48 / 60 hours |
|---:|---:|---:|---|
| 97 | 277 | 3 | 145 / 193 / 217 |
| 98 | 280 | 4 | 146 / 194 / 218 |
| 99 | 284 | 6 | 147 / 195 / 219 |
| 100 | 289 | 3 | 148 / 196 / 220 |
| 101 | 291 | 5 | 149 / 197 / 221 |

Every frozen query falls on an integer half-hour coordinate and within the final source frame 243. All five treatment-origin interpretations remain in the analysis; none was selected for a result. The original 49-versus-50-hour treatment discrepancy remains unresolved.

## Limits and a future reuse gate

The constructor is not a complete validator for arbitrary replacement graphs: exhaustive event-key mapping, unique episode assignment, and issue-frame membership were independently verified here for the hash-pinned source. A replacement graph needs the same gates or stricter constructor validation. The caller pins the graph and earlier structural results; this review additionally checked the original workbook and codebook hashes.

Original population eligibility, replicate mapping, the exclusion-label namespace, and independent experiment counts remain unknown. The code computes a conditional envelope for a finite recorded roster. The intervals neither estimate annotation error nor become confidence intervals. The rectangular relaxations can include incompatible complete-tree histories, so their bounds need not be sharp. No disease mechanism or treatment effect follows from this structural pass.
