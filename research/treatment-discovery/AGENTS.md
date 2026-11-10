# Treatment research

Start with README.md, then the relevant source ledger and actual dataset dictionary. This folder contains a retrospective biomarker benchmark and a separate proposed EGFR residual-state mechanism study. Do not pool their treatment classes or endpoints.

- The MSK public clinical cohort is pinned, deidentified and ODbL-licensed. Preserve originals, attribution, license and hashes. It is not an Iowa cohort or a randomized treatment comparison.
- The completed TMB benchmark is an already-published within-cohort association, not a trained clinical predictor or a discovery. It cannot resolve pretreatment specimen timing. Do not turn AUC into accuracy, individual response probability or cure fraction.
- Read the frozen clinical protocol and audit before rerunning. Do not silently change the TMB field, NE handling, patient unit, threshold, exclusions or statistical method. Version any new analysis separately.
- For single-cell work, group by real patient/sample and preserve malignant annotation, driver, drug, tissue and biopsy state. Cells from one donor are not independent patient replicates. A signature derived from a dataset cannot be externally validated in that same dataset.
- Start current molecular work with `updates/2026-11-10/README.md`. Exact Maynard signature identity is resolved; source metadata must be reindexed by cell ID to its expression object. Original candidate-pair counts precede malignant-cell attrition.
- GSE292469 has unmatched patients and major stage/site/kit imbalance. Its fixed raw-UMI comparison has a lower pooled residual score but a positive small-v4-stratum difference. Preserve both directions, source kit contradictions, transformed-histology exclusions, and the distinction from SoupX-corrected expression. Do not turn this comparison into a causal resistance or clinical prediction claim.
- Basal CRISPR, PRISM and GDSC outcomes have different assays, dose ranges, units and identifiers. Metadata overlap is not drug-specific response availability. Preserve related-model/source-patient groups across splits and inspect aliases.
- A gene-expression association, basal dependency or cell-line drug response does not establish a causal resistance target, normal-tissue safety, combination synergy or patient efficacy.
- Keep molecular resources, clinical outcomes and environmental population data distinct. Refresh regulatory status, release versions and access terms for consequential current use.
