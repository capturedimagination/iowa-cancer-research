# Monte Carlo results and reproduction

The first complete-tree run retained all 20 cases, 200,000 prospective founders and 5,163,538 born cells. Its 800 checkpoint hashes were verified. The frozen comparison contains 3,070 exact-binomial diagnostics, all not flagged, and 720 bounded-mean diagnostics: 576 not flagged and 144 structural agreements. There are no undefined checks. Each diagnostic family has alpha 0.001; the union bound across the two tree families is 0.002. See [tree comparison](tree-monte-carlo/comparison.md) and [all diagnostic records](tree-monte-carlo/comparison.json).

The first calibration run generated all 720 settings, 7,200 batches and 36,000,000 independent whole experiments, then exited with a report-packaging error. A metadata list named `methods` replaced the per-method result dictionary. This failure was missed in the initial static review and remains recorded. The original source is archived byte-for-byte at `scripts/simulate_shared_calibration_v1.py` (SHA `e32fa093559cba285e31c0cddd07779f54bccf1f2e740727d2ae0bc611bdaeb2`).

A separately reviewed recovery script used the saved sufficient statistics, without any random draws or simulator import. It verified every batch hash, all count and seed labels, recorded RNG-state continuity, and 23,760 recoverable original setting fields. The maximum raw-versus-centered moment identity difference was `1.42e-14`. All 5,760 frozen calibration checks are present: 5,184 not flagged and 576 structural agreements. The first recovered outcomes remain in [results.json](calibration-monte-carlo/results.json); the original failure and reconstruction are recorded in [the recovery ledger](calibration-monte-carlo/recovery-ledger.json) and [the recovery freeze](calibration-monte-carlo/recovery-freeze.json).

The current runner changes exactly one metadata key, from `methods` to `method_names`. No formula, probability, random draw, seed, loop, batch size, sample count or threshold changed. Its SHA is `b996075a2080f4a308e055d3aedc2f55d2ae2ceef038ab9a8068c2bcdb634cda`; [the v2 freeze](calibration-monte-carlo/clean-v2-freeze.json) records this lineage. The clean run uses the same seeds and separate output paths. It is an exact reproduction, not a new statistical replica or a replacement for the first run.

Both clean runs completed. The [first exact-equality report](monte-carlo-reproduction.json) confirms all 10,400 saved tree arrays, 800 tree batches, 7,200 calibration batches, 2,880 estimator records and every diagnostic outcome agree at the value level. After that first comparison, independent review requested explicit array dtype/shape checks and stronger top-level and batch provenance checks. The [supplementary comparison](monte-carlo-reproduction-supplement.json) passed those additional checks on the same saved outputs, without further simulation. Its [separate freeze](monte-carlo-reproduction-supplement-freeze.json) records that timing; the first checker remains archived at `scripts/check_age_calendar_reproduction_v1.py`. Both successful comparisons and the original failure remain available.

These checks concern hypothetical branching and calibration models. They do not validate cancer mechanisms or treatment effects. The earlier study's two flagged approximate comparisons and 168 unresolved low-count checks remain unchanged.

## Run from a fresh checkout

Use Python 3.12.14, NumPy 2.3.5 and SciPy 1.16.3 to match the recorded environment. Run commands from the repository root. Local synthetic checkpoints are regenerated; no private empirical dataset is needed. Bit-for-bit reproduction was checked in the recorded environment, not promised across arbitrary hardware or numerical libraries. Output paths must be fresh; the tools refuse to overwrite first results.

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install numpy==2.3.5 scipy==1.16.3

.venv/bin/python scripts/simulate_age_calendar_trees.py --run \
  --local tmp/reproduce/tree \
  --output tmp/reproduce/tree-results.json

.venv/bin/python scripts/compare_age_calendar_trees.py --run \
  --mc tmp/reproduce/tree-results.json \
  --checkpoints tmp/reproduce/tree \
  --output tmp/reproduce/tree-comparison.json \
  --markdown tmp/reproduce/tree-comparison.md

.venv/bin/python scripts/simulate_shared_calibration.py --run \
  --reference research/treatment-discovery/lineage-audit-2026-11-10/age-calendar-calibration/results.json \
  --independent-gate research/treatment-discovery/lineage-audit-2026-11-10/age-calendar-calibration/independent-comparison.json \
  --local tmp/reproduce/calibration \
  --output tmp/reproduce/calibration-results.json
```

All three scripts run deterministic fixtures before their requested evaluation. Both generators require an explicit `--resume` to continue an existing run and verify its code/environment/RNG provenance. Inspect completion counts and retained failures, not just the exit code. A completed comparison with no flags is numerical evidence under the frozen model and gates; it is not a proof of every numerical or biological assumption.

## Reproduce the archived failure and recovery

This is optional provenance work. The archived v1 intentionally preserves the known final-report defect and exits 1 after all calibration batches. Supply a new output directory and preserve its log. The recovery takes the archived source path explicitly, so the corrected current source does not rewrite the original provenance.

```sh
mkdir -p tmp/reproduce
.venv/bin/python scripts/simulate_shared_calibration_v1.py --run \
  --reference research/treatment-discovery/lineage-audit-2026-11-10/age-calendar-calibration/results.json \
  --independent-gate research/treatment-discovery/lineage-audit-2026-11-10/age-calendar-calibration/independent-comparison.json \
  --local tmp/reproduce/calibration-v1 \
  --output tmp/reproduce/v1-report-not-written.json \
  > tmp/reproduce/calibration-v1.log 2>&1

.venv/bin/python scripts/recover_shared_calibration_report.py --run \
  --local tmp/reproduce/calibration-v1 \
  --original-simulator scripts/simulate_shared_calibration_v1.py \
  --original-log tmp/reproduce/calibration-v1.log \
  --output tmp/reproduce/calibration-v1-recovered.json \
  --ledger tmp/reproduce/calibration-v1-recovery-ledger.json
```

The full local equality checker is `scripts/check_age_calendar_reproduction.py`; its `--help` lists explicit input/checkpoint paths for two regenerated tree runs and the recovered-v1/current-v2 calibration runs. It compares scientific arrays, batch moments, seed components, RNG states, estimator records and gate outcomes with **exact equality**. It excludes only timestamps, execution duration, byte-container hashes (which themselves are verified), the documented code hashes, and the renamed metadata key. The first equality-check definition is [recorded here](monte-carlo-reproduction-freeze.json); the current checker adds the [separately pinned supplementary coverage](monte-carlo-reproduction-supplement-freeze.json).
