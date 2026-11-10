# Independent verification of joint contrast bounds

**First run: PASS.** Exact rational small-case enumeration agrees with the joint solver, and every defined contrast in the prescribed synthetic subset is contained within its bound at the frozen `1e-12` tolerance. No empirical graph, workbook or private per-cell input was read.

This is a **post-primary-results methodological refinement**: the original empirical outer intervals were already known to include zero. The [joint plan](joint-refinement-plan.json) was frozen after that finding and before joint outputs. The independent test design was stated before this verification's numerical outcomes. The underlying probabilities, time grid, masks and rosters were unchanged; no tests were selected by their results.

The [verifier](../../../../scripts/verify_lineage_joint_bounds.py) and [complete results](joint-verification.json) preserve all exact cases, invalid-input controls and synthetic contrasts, plus code/plan hashes, environments and failures (none). This checks the [joint implementation](../../../../scripts/lineage_joint_bounds.py); it does not establish population inference or sharpness over complete biological trees.

## Exhaustive rational controls

The fixed interval catalog is `[0,0]`, `[0,1]`, `[1/4,3/4]` and `[1/2,1/2]`. For each interval, all known/unknown early and late status combinations are considered. A row is included in the valid catalog when at least one nested state `00`, `10` or `11` is possible, excluding selected states when its upper bound is zero. This produces 28 row types.

The verifier checks every multiset of one, two or three catalog rows and the empty roster: **4,495 cases**. For each case, it independently enumerates all allowed nested selection assignments and all interval-endpoint assignments. Both conditional means are calculated directly with exact `Fraction` arithmetic, using the **same** probability for a row in both means. It does not reproduce the solver's cost formula or dynamic program. There are 34,797 enumerated positive-later-denominator endpoint completions across the catalog.

Every case with at least two rows is also passed to the solver in reverse order. The 8,961 valid-input solver calls match exact extrema, feasible selected-count pairs, defined/undefined status and zero-denominator feasibility. The largest absolute extremum discrepancy is `1.665e-16`. All 969 cases with no possible positive later denominator remain undefined.

Four further controls correctly reject incompatible input: known late selection with known early exclusion, and three variants of a known selected row whose upper probability bound is zero. A selected lower bound of zero is allowed when the upper bound is positive, as required by the closed relaxation. Such a zero may represent an unattained infimum for biological trees with unrestricted hidden depth. Single possible founders and identical point-valued probabilities are included in the exhaustive catalog and give zero contrast whenever defined.

## Synthetic forest subset: 36 founders, not 900

The verifier regenerates each entire original 300-founder forest from the [earlier fixed forest experiment](forest-verification.md), with its unchanged seeds and masks. Complete-forest, mask and annotated-graph hashes must match the original results. It then evaluates only the **first 12 founders by creation index in each case**—36 founders total. These are not the first survivors or the first complete trees. This is explicitly **not joint validation on all 900 founders**.

Ground truth remains independent of the joint solver: complete biological birth/death records supply exact chronological path weights and actual living-descendant counts. The existing data-free mass core constructs the input intervals from masked observations; its broader containment verification was performed separately. Both death offsets and both ambiguity policies are retained, along with all four fixed masks.

| Case: division / death probabilities | Selected founder IDs | True families surviving frame 48 / 96 / 120 |
|---|---|---|
| 0.04 / 0.06 | 1–12 | 2 / 1 / 0 |
| 0.06 / 0.04 | 1–12 | 4 / 4 / 3 |
| 0.03 / 0.03 | 1–12 | 3 / 3 / 3 |

Evaluation frames are `0,12,24,36,48`; horizon pairs are `(48,96)`, `(48,120)` and `(96,120)`. All **720 combinations** are retained. The three complete forests, four masks and repeated annotation settings are reused; these combinations are not independent biological samples.

| Verification | Result |
|---|---|
| Defined complete-tree contrasts contained in joint intervals | **560 / 560**, largest numerical excess `3.730e-17` |
| Undefined complete-tree contrasts explicitly retained | **160**, all permit a zero later denominator |
| Defined joint intervals contained within the earlier conservative outer intervals | **640 / 640**, largest numerical excess `1.111e-16` |
| Full-forest, mask and graph identity versus original fixed experiment | All hashes match |
| Failures at `1e-12` tolerance | **0** |

An undefined true contrast can coexist with a defined interval for other compatible completions of the incomplete record. The corresponding zero-denominator flag remains explicit. No zero value is substituted for undefined truth. The reported tiny excesses arise from floating-point arithmetic relative to exact rational targets and are below the predetermined tolerance.

## Scope and provenance

The joint solver was finalized with its feasibility-operation guard before the verifier's first numerical run. Its final code hash is pinned; hashes are checked again after execution. No post-result code, grid, probability, subset or tolerance changes were made.

The checks establish agreement on the stated exhaustive finite catalog and containment on the fixed synthetic subset. They do not prove correctness on every possible input or certify sharp bounds for actual trees. The shared probability is enforced between the two means within each horizon pair; separate optimized pairs do not certify one common completion across all times and horizons. None of this repairs unknown original eligibility or supplies a sampling confidence interval.

The first run used Python 3.12.14, NumPy 2.3.5 and exact `fractions.Fraction` reference arithmetic. Its timestamp is `2026-11-10T19:43:21.053160+00:00`. Exact controls use no random seed; forest generation reuses base seed `2026111011` and the previously recorded stream rules.

| Artifact | SHA-256 |
|---|---|
| Joint refinement plan | `531ac9e5c63a5ed000ca59d282038bee1d6ad66a192d54d4aeb8cf9a4811532b` |
| Final joint solver | `f24fe1d3a99d2abfd3fdb453d74b87e2b28ad44017845cd3c8ac3b429984802d` |
| Independent joint verifier | `bb4b1571c95731444d3870bad704a2c205cf93b2b5d23ea9010cde8617418a13` |
| First-run joint verification results | `b409ffe1cf84e9c2a184c47c36abfd945e379cf45d9c925b4c408f246451dd30` |

The JSON records the additional primary-plan, mass-core, earlier forest-verifier and original forest-result hashes. Reproduction uses the published code, protocols and synthetic aggregate result file, without any empirical dataset:

```sh
python scripts/verify_lineage_joint_bounds.py --out tmp/joint-verification-reproduction.json
```
