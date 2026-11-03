# Independent benchmark review

Reviewed October 29, 2026 against the frozen specification, saved source tables, article methods and source license. This check did not change the analysis specification or the source inputs.

- Read `scripts/run_nsclc_benchmark.py`: it uses original continuous `MUTATION_RATE`, excludes only the 13 source NE outcomes, preserves a one-to-one patient/sample join and implements the fixed class-stratified bootstrap. No learned model, cutoff search or treatment-effect estimate was fitted.
- Recomputed the point statistic with Python standard-library pair counting independently of NumPy: **6,552 wins**, **278 ties**, **10,902 YES/NO pairs**. With half credit for ties, AUC = **6,691 / 10,902 = 0.6137405980554027**, matching the result.
- Parsed the saved `.npy` bootstrap array using Python `struct` and independently evaluated sorted linear quantiles: **0.5312786644652358 to 0.6948725004586315**, matching the reported interval. This checks the saved draws and quantile arithmetic; it is not an independent clinical validation cohort.
- Verified all **240** saved cohort-flow patient/sample IDs against their reported source line numbers, the **227** inclusions, current source hashes against result provenance, and unchanged frozen-protocol SHA-256 `4bca018fb1c712c859a519d8a3c30eabb7e4fa9182c760a1bf97a45e64d373e0`.
- Original study timing, source ODbL license and outcome limitations are preserved. The 36 post-treatment specimens cannot be isolated from available public columns. DCB is a source-adjudicated durable-benefit outcome, not cure; the source's progression time is not automatically a standard progression-or-death endpoint.

No material discrepancy was found between the saved calculation and the frozen starter specification. The result remains a retrospective known-association replication with conditional resampling uncertainty, not a treatment-benefit prediction model or new efficacy finding.
