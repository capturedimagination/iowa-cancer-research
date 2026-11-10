# Independent synthetic-forest containment verification

**First run: PASS, with no failed checks.** This verification was completed before the empirical bounds calculation. It used the [frozen protocol](protocol.json), independently generated complete biological trees, and the [bounds core](../../../../scripts/lineage_missing_bounds.py). No empirical workbook, candidate graph, baseline roster or outcome file was read.

The [independent verifier](../../../../scripts/verify_lineage_missing_forest.py) retains all fixed cases and writes [complete aggregate results](forest-verification.json), including every evaluated conditional mean and horizon contrast, exact rational truth values, graph/mask hashes, seed rules, environment and all failures (none). Passing establishes containment for these synthetic realizations, not scientific peer review, confidence coverage, sharp bounds or biological validation.

## Independent generation and truth

Each case starts with 300 living founders at frame zero and runs through frame 120. At each frame, one uniform random draw per living cell selects mutually exclusive division, death or no event. An event drawn at frame `f` takes effect at `f+1`; division produces two daughters. Every original founder remains in the roster, including those that die in the first interval.

Complete biological cell histories store birth frame, event frame, fate, family and generation. Ground-truth chronological survival sums exact `Fraction(1, 2**generation)` weights over cells biologically alive at the queried frame. Ground-truth death sums the same weights over dead terminal cells. Each family's live and dead weights sum to exactly one. Family survival is obtained independently by counting its living descendants. None of these truth calculations calls the bounds core.

| Per-frame division / death probabilities | Forest seed | Founders | Generated cell episodes | Divisions | Deaths | First-interval founder deaths |
|---|---:|---:|---:|---:|---:|---:|
| 0.04 / 0.06 | 2026111011 | 300 | 1,276 | 488 | 772 | 15 |
| 0.06 / 0.04 | 2026112011 | 300 | 17,794 | 8,747 | 5,786 | 14 |
| 0.03 / 0.03 | 2026113011 | 300 | 2,706 | 1,203 | 1,138 | 3 |

These are hypothetical discrete-time forests, not calibrated cancer models. The 900 generated families are reused across masking and annotation conditions; repeated checks are not additional independent biological samples.

Four observation policies are applied to each same complete forest: no deletion, independent daughter deletion with probabilities 0.1 and 0.3, and deletion with probability 0.3 only when the daughter's complete subtree has a frame-120 survivor. The last policy deliberately makes missingness depend on the future outcome. Otherwise its deletion probability is zero. This interpretation and the masking order were specified before the first draw. A deleted daughter and her entire subtree become unobserved, but the parent's division flag remains. Founders are never deleted.

The forest seed is `2026111011 + 1000*case_index`. Each nontrivial mask uses `2026111011 + 1000*case_index + 100 + policy_index`, with indices starting at zero in protocol order. There is one masking draw per biological daughter in ascending creation-ID order, even below an already removed ancestor. Complete-forest and mask hashes permit exact reconstruction without publishing a cell-level tree dump.

## Encoding and pre-outcome clarification

For both death-annotation offsets, the biological truth is identical. Division is flagged one frame before daughter entry. Death is annotated at `actual_death-offset`, and the final recorded cell frame is that annotation. Thus offset zero deliberately retains one record at the actual death frame; a record's presence cannot override absorbing death. Every observed parent-child transition is checked for adjacent frames, and the independent complete tree is checked for binary structure, parent identity, family identity and increasing birth times.

Before any forest generation, inspection exposed an API boundary: a founder with actual death at frame one has annotation zero under offset one, yet is biologically alive at baseline zero. The core's baseline check was clarified to use `annotation+offset`. Its empirical caller separately keeps the protocol's conservative common eligibility rule. No synthetic founder was dropped and no first-interval event was suppressed. The 32 first-interval founder deaths above exercise this corrected boundary. This was a pre-outcome implementation clarification, not a change to the frozen probabilities or grid.

Both frozen ambiguity policies are tested. The synthetic graphs have no additional ambiguity issues, so the policies must agree; separate core fixtures address contradictory annotations and masks. The method-level cache is cleared after each completed scenario.

## Results on the fixed grid

Chronological mass is checked at frames `0,12,24,36,48,96,120`. Conditional means use evaluation frames `0,12,24,36,48` and selection horizons `48,96,120`. Contrasts are later minus earlier for pairs `(48,96)`, `(48,120)` and `(96,120)`. All four masks, both annotation offsets and both ambiguity policies are retained.

| Check | Evaluations | Largest numerical discrepancy or excess |
|---|---:|---:|
| True live and dead weights contained in their respective bounds | 201,600 | 0 |
| Known-live + known-dead + unknown mass equals one | 100,800 | 0 |
| Every definite family-inclusion status agrees with complete-tree truth | 100,800 | No contradiction |
| Exact-rational selected means contained in ratio bounds | 720 | 0 |
| Exact-rational paired-horizon contrasts contained in contrast bounds | 720 | `9.975e-17` |
| Complete graphs recover exact live/dead mass with zero unknown mass | 25,200 | 0 |
| Complete graphs recover exact selected means | 180 | 0 |
| Equivalent annotation offsets give identical mass outputs | 12 | Exact equality |
| Ambiguity policies agree on issue-free graphs | 24 | Exact equality |
| Every defined baseline ratio is exactly one | 144 | Exact equality |

The declared numerical tolerance was `1e-12`. The contrast excess is ordinary floating-point subtraction relative to independently retained exact rational differences; it is below that tolerance. No failing case, probability, mask, time point or horizon was removed or adjusted after inspection.

Every realized complete forest has at least one surviving family at each queried horizon, so all truth conditional means and contrasts are defined. Forty reported ratio envelopes nevertheless permit zero-denominator completions of the incomplete record. That possibility remains explicit in the results. This random grid therefore exercises uncertain denominators but does not contain a realized wholly extinct forest; separate deterministic core fixtures cover impossible positive denominators. A zero is never substituted for an undefined conditional value.

## Reproduction and provenance

The verifier uses Python's standard library and the data-free local bounds module. The first run used CPython 3.12.14 on macOS arm64, with `random.Random` and exact rational truth arithmetic. It reads only the frozen protocol and core code, and checks both hashes before and after execution.

```sh
python scripts/verify_lineage_missing_forest.py --out tmp/forest-verification-reproduction.json
```

| Artifact | SHA-256 |
|---|---|
| Frozen protocol | `c46e452f3b17b96a8f98e6bc834540d830af9b4a1e3b39b8d3a2c1665f342771` |
| Reviewed bounds core | `27bb3b07186b015a5d573d45ffe1da6515131ea0b3da09e677531c468eb4513e` |
| Independent verifier | `9c4d02e1a8621e4299df644f4bc7d4de7b150c90a583352498961230e51cf05e` |
| First-run results | `42ff99e11735d753df81a440804cb2ba0247c8a4a75d95a6614a62d56b0cf8d4` |

The result generation timestamp is `2026-11-10T19:36:15.530827+00:00`. This synthetic software verification does not establish the correctness of empirical identity mappings, the completeness of the original cohort, a missingness mechanism, or a cancer process. The [prior-art and interpretation audit](prior-art.md) remains applicable.
