# Maynard alveolar signature verified

Checked **November 10, 2026**. The 17-gene vector previously labeled “AT2 differentiation” in author code **exactly matches the published alveolar signature**. This resolves the gene-set uncertainty in the October 29 preflight. No expression scores were calculated in this verification. [Structured audit and source hashes](signature-verification.json).

## Exact gene set

Table S2, sheet `3. Cancer Cell Signature Genes`, cells `A2:A18`, contains the following genes, in supplement order:

`LAMP1, AGER, FOXA2, NAPSA, HOPX, IGFBP2, SFTA3, NKX2-1, GATA6, ABCA3, SCGB3A1, AQP4, CLDN18, PGC, SFTPD, SFTPB, SFTPC`

All 17 match `AT2_genes` in pinned author scripts NI08 and NI16; the workbook lists them in reverse order, which does not change their arithmetic mean. The source column header is misspelled `Avelolar Signature `. The paper describes this as a combined AT1/AT2 alveolar program; “AT2” in the code is therefore an abbreviated label for this exact published gene set. The paper's regenerative-state interpretation is distinct from demonstrating causal drug resistance. [Original paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC7484178/), [Table S2](https://pmc.ncbi.nlm.nih.gov/articles/instance/7851114/bin/mmc2.xlsx), [NI08 author code](https://github.com/czbiohub-sf/scell_lung_adenocarcinoma/blob/de138c79bcfc2fa3a28c8a039a28ab560da78099/scripts/NI08_Gene_expression_plotting.Rmd).

The workbook is 16,400 bytes, SHA-256 `3d8f7283df9d25f4b05a95dee1e42eb7a1e1102309f5bab221734aeb3106f141`. It was recovered from the official Europe PMC supplementary archive, with ZIP-entry size and CRC checked. Raw supplement/source files remain in the local ignored archive; this report publishes factual gene identities and provenance.

## Operational scoring rule

The inspected code chain removes ERCC spike-in rows before creating the RNA assay, selects malignant cells using the author inferCNV annotations, and calls `NormalizeData()` with default settings. NI08/NI16 then use `FetchData()` and take each cell's unweighted arithmetic mean across the 17 genes. Although they also call `ScaleData()`, `FetchData()` defaults to the `data` slot in official Seurat v3.0.0 and v3.1.0 source. Thus the score uses normalized log expression, not the separate `scale.data` matrix. [Input preparation](https://github.com/czbiohub-sf/scell_lung_adenocarcinoma/blob/de138c79bcfc2fa3a28c8a039a28ab560da78099/scripts/02_Create_Seurat_object.Rmd), [malignant-cell normalization](https://github.com/czbiohub-sf/scell_lung_adenocarcinoma/blob/de138c79bcfc2fa3a28c8a039a28ab560da78099/scripts/NI04_Cancer_cells_DEgenes.Rmd), [Seurat v3.0.0 FetchData](https://github.com/satijalab/seurat/blob/v3.0.0/R/objects.R#L756), [Seurat v3.1.0 normalization](https://github.com/satijalab/seurat/blob/v3.1.0/R/preprocessing.R#L1846).

For cell `c`, the corresponding explicit rule is the mean over all 17 genes of `ln(1 + 10000 × gene_count / total_nonERCC_gene_counts)`. It does not subtract matched control-gene expression. NI17 averages these cell scores within samples for its PD heatmap. A future patient-paired comparison is a separately specified reanalysis. [NI17 aggregation](https://github.com/czbiohub-sf/scell_lung_adenocarcinoma/blob/de138c79bcfc2fa3a28c8a039a28ab560da78099/scripts/NI17_cancercell_PDsigs.Rmd).

The paper identifies Seurat v3, but the exact historical patch/session was not found in the inspected notebooks. Any implementation should explicitly pin the assay, normalization, denominator and aggregation instead of inheriting modern defaults. Require all 17 genes and finite values before scoring: this is a proposed guard for the new analysis. Author `rowMeans(..., na.rm=TRUE)` is not permission to silently substitute an incomplete gene set.

## Cohort details that affect reproduction

The paper reports 49 samples from 30 patients, 23,261 post-QC cells, 5,581 epithelial cells and 3,754 malignant cells. The code uses strict `>500` detected genes, `>50000` counts and `>10` cells per sample; its equality boundaries differ from the prose exclusion wording. The merged workflow incorporates neo-osi samples before later annotation, so those samples cannot serve as independent external validation. [Paper methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC7484178/), [merge step](https://github.com/czbiohub-sf/scell_lung_adenocarcinoma/blob/de138c79bcfc2fa3a28c8a039a28ab560da78099/scripts/03_Merge_in_NeoOsi.Rmd), [sample filtering](https://github.com/czbiohub-sf/scell_lung_adenocarcinoma/blob/de138c79bcfc2fa3a28c8a039a28ab560da78099/scripts/03.1_Subset_and_general_annotations.Rmd).

NI16's driver-specific comparison also excludes `LT_S41`; that is separate from NI08's all-malignant-cell score. Matching expression, malignant-cell identities, timing and usable patient pairs still need to pass the analysis audit. The signature partly originated in these source state comparisons, so a successful calculation within this cohort is reproduction, not independent validation. [Driver-specific code](https://github.com/czbiohub-sf/scell_lung_adenocarcinoma/blob/de138c79bcfc2fa3a28c8a039a28ab560da78099/scripts/NI16_cancercell_EGFR_ALK.Rmd), [paper methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC7484178/).
