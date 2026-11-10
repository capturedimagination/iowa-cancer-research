# Independent deterministic comparison

**PASS: all 20 cases and all planned fields agree within the frozen tolerances.** The first comparison contains 96,145 numeric fields against each of the primary and stricter calculations: 192,290 comparisons, with no failures. An additional 315 inapplicable no-transmission bounds match as undefined. Field counts include repeated design constants; they are not independent biological observations or hypothesis tests.

The [machine-readable report](independent-comparison.json) preserves exact input hashes, complete case/key coverage, per-case and per-category counts and maxima, and every failure if present. Its SHA256 is `c9c2664a769c19d4932f2014e66434808fb92105119bd68d066508539d115879`.

| Quantity | Primary versus reference: largest absolute difference | Strict versus reference: largest absolute difference |
|---|---:|---:|
| Selected random-path survival Q | 5.46123e-10 | 3.61899e-12 |
| Family survival | 1.53508e-10 | 1.04344e-12 |
| Horizon contrast | 5.45985e-10 | 3.92886e-12 |
| Bin sister-subtree covariance | 1.25926e-11 | 8.53831e-14 |
| Bin eligibility probability | 1.66533e-16 | 1.88738e-15 |
| All calibration mean/variance fields | 1.55287e-11 | 1.05277e-13 |

The frozen absolute gates are 1e-8 for probabilities, contrasts and covariance decompositions, and 1e-10 for calibration means and variances. Declared estimator range endpoints, record keys, configurations and schemas match exactly. The stable covariance decomposition used in production and the independent reference's `j-p^2` calculation both remain in the comparison; their small numerical differences were not discarded.

## Coverage and independence

Each of the three inputs has exactly 60 family-survival records, 340 Q records, 140 unconditional-path records, 240 contrasts, 300 birth-bin eligibility records, 900 pair targets and 5,400 calibration settings. All four estimators' means, variances and both range endpoints are checked at every calibration setting. The comparison uses the independently calculated reference p and j, so it includes propagation of probability-solver differences into calibration moments.

Additional scientific fields are checked rather than omitted: mapped operational horizons, positive Q loss against `1-Q`, joint marked probability, positive removed-stratum loss, direct pair joint integrals, global eligibility/maternal weights, and all partition decompositions reconstructed from reference bins. Only explicitly listed numerical self-check diagnostics, solver error estimates and execution metadata are outside independent numerical comparison. Every numeric input leaf is checked finite, including those diagnostics.

The [reference](independent-reference.json) was saved before primary outcomes were read. It uses extinction/forward-spine equations and adaptive Gauss–Kronrod birth-bin integration; production uses a positive marked system and fixed Gauss–Legendre integration. Calibration moments use independent closed expressions versus finite-binomial sums. Neither the reference nor comparator imports the new production module.

The [reference fixtures](reference-fixtures.json) include two off-grid direct physical-time backward calculations, an off-grid exponential closed-form control, and exact rational enumeration of 54 small calibration settings. The enumeration verifies 432 four-estimator mean/variance identities and 54 paired-estimator covariance identities, including negative covariance and p=0/1. Direct physical versus mapped operational calculations agree within 3.10e-13 in these fixtures.

## First-output and review boundary

The reference code and fixtures were pinned before its first full grid. The comparator was written after both independent calculations existed, then [pinned](comparison-code-pin.json) before evaluating any primary/reference differences. Its [synthetic fixtures](comparison-fixtures.json) reject duplicate, missing and extra result keys; unknown schema fields; nested NaN/infinity; and mismatched undefined values. They also verify retention of an intentional threshold failure and correct coverage counting.

No scientific grid, parameter, seed, tolerance or prior result was changed in response to this comparison. The report summarizes passing scalar differences by case/category rather than duplicating every scalar; the immutable input files retain all values, and the standalone comparator reproduces the complete comparison.

Code and input pins:

- Comparator: `07a866817af1696ddd96989769af00a2e46ff2433fd2e1bfb25251531962e1c1`.
- Reference code: `b8b404480cb4586fddf2d45d22a572ab001e7f0ad76c4fa309a29df8b1a7f626`.
- Protocol: `53d76bf43d0b1f47355d57d95ec6d7f43fce67541aed7631510a3cbff0b42919`.
- Primary output: `4948c049860cbd686ed82fa036dba1bb4f383c525046c8e2154a585a9d36b67d`.
- Strict output: `d060f646c1cac1fa2e7763035bd88c520f62f862d37047dd4fe06e43a72fe110`.
- Independent output: `4660e68638657dd109254a9afd5996b3d579a65cf158603929a6ca785603f1bd`.

From the project root, reproduce this audit with a new output path:

```sh
python scripts/compare_age_calendar_references.py --run --out tmp/age-calendar-comparison-reproduction.json
```

The command verifies the saved comparator/input pins and refuses to overwrite an existing output or failure artifact. This agreement is numerical validation of the stated hypothetical model, not empirical validation, proof of formal numerical error bounds, established novelty, or evidence of a cancer mechanism.
