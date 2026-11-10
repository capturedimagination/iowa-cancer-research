# Independent computation review

Completed November 10, 2026. **The source, patient arithmetic and marginal-expectation checks passed.** This is a separate computational check of the same data and model, not external scientific peer review or independent biological validation.

The [checker](../../../../scripts/check_signature_depth.py) does not import the simulator or replay its random-number stream. Its [machine-readable report](independent-review.json) identifies the exact result, cache, simulator and checker hashes.

## What was checked

- Direct reads from the source HDF5 reproduced all 17 target counts and total UMI counts for 134 selected nuclei, covering every patient. Separate scalar logarithms reproduced their scores.
- The cache contained 121,083 unique nucleus IDs. All 35 patient IDs, per-patient counts and original mean scores agreed. All patient diagnostics, per-gene fractions/contributions and 12 observed metric/stratum contrasts reproduced within numerical tolerance. The full cell-to-patient join was not independently reconstructed from source metadata in this check.
- For the technical simulations, the checker summed one-dimensional **binomial marginal probabilities** to calculate the expected mean-log score. The maximum conservative truncation-error bound was (2.99\times10^{-11}) per score.
- For primary thinning to 1,000 UMIs, it summed the complete **hypergeometric marginal distribution** for every measured target in every nucleus. Probability masses summed to one with maximum absolute error (3.89\times10^{-15}).
- All 12 simulated mean contrasts were within **1.782 Monte Carlo standard errors** of these separately calculated expectations. This checks the reported means; it does not independently verify the joint sampling variance or simulated rank-AUC distribution.

## Independent expected contrasts

Values are residual minus untreated mean scores. The exact expectations condition on the observed molecule pool or the specified homogeneous multinomial model.

| Scenario | Pooled | Source-implied v3.1 | Source-implied v4 |
|---|---:|---:|---:|
| Primary thinning, 1,000 UMIs | −0.209209 | −0.399445 | +0.317682 |
| Common-profile null, observed depths | −0.029789 | −0.011587 | +0.037430 |
| Common-profile null, fixed depth | 0 | 0 | 0 |
| Fixed depth, twofold MRD target proportions | +0.437663 | +0.437663 | +0.437663 |

Numerical sums for the fixed-depth v4 null differed from zero by approximately (10^{-16}). The positive control doubles transcript proportions, not the log score; its expected score difference is therefore not a twofold score change.

## Scientific limits

The kit-stratum reversal remains after equal-depth thinning and is present in the untransformed signature UMI fractions. The restricted technical model also produces opposing stratum directions with equal underlying transcript proportions. Thus **direction alone is not diagnostic of a biological state change**. The observed cohort and the deliberately homogeneous null differ in many other respects. Their magnitude difference cannot quantify what percentage of an observed effect is caused by depth, nor identify the remaining cause.

The simulation percentiles describe variation conditional on the molecules/model. They are not patient confidence intervals, treatment-effect uncertainty or a cure probability. With 100 simulation repetitions, the 2.5th and 97.5th percentiles are coarse tail estimates. This review does not resolve stage/site imbalance, source kit contradictions, ambient RNA, biological heterogeneity or the distinction between residual disease and progression.

The cache-hit path was hardened after the initial review. The rerun now verifies cached source provenance, embedded gene/patient IDs, count types and bounds, unique nucleus membership, the full cell-to-patient/source-depth join, and reproduction of previous patient scores. The results before and after hardening are exactly equal after excluding only creation time and simulator code hash. The independent checker was rerun against the new result and refreshed its hashes; its own direct HDF5 checks remain limited to the 134 selected nuclei. If the simulator or outputs change again, rerun this check.

## Reproduce

After obtaining the same source files and completing the main simulation, use the pinned Python 3.12 environment from `requirements-treatment.txt`:

```sh
python scripts/check_signature_depth.py
```

The checker reads the local source matrix and target-count cache and writes aggregate verification only. It does not publish raw per-nucleus data.
