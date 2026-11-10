# Maynard malignant-cell membership audit

Checked November 10, 2026. The three main-cohort metadata candidate pairs do **not** supply three usable malignant-cell pairs. The saved author annotations contain no cells from the TH205 residual sample, one baseline cancer cell for TH218, and 15 baseline cancer cells for TH226. These are data-availability and sampling findings, not evidence that treatment eliminated a patient's tumor.

| Main-cohort patient | Before treatment | Residual disease | Consequence |
|---|---:|---:|---|
| TH205 | LT_S34: 24 malignant cells | LT_S46: absent from final sample table | No paired malignant expression comparison |
| TH218 | LT_S45: 1 | LT_S55: 17 | Arithmetic comparison possible, but baseline is one cell |
| TH226 | LT_S52: 15 | LT_S57: 194 | One pair has at least 10 malignant cells in each sample |

TH226 also has 13 malignant cells in progression sample LT_S82; progression is a separate state. The 10-malignant-cell threshold above is an audit sensitivity, not the author's sample-QC rule and not a validated power threshold. Cells from the same person remain correlated observations.

## Exact joins and cohort reconciliation

The pinned [inferCNV annotation table](https://github.com/czbiohub-sf/scell_lung_adenocarcinoma/blob/de138c79bcfc2fa3a28c8a039a28ab560da78099/data_out/NI03/results/inferCNV_annotation.csv) contains 6,181 unique cell IDs: 5,581 epithelial cells and 600 control cells. All 3,754 `tumor` labels belong to epithelial clusters. Main metadata matches 3,671 malignant cells; the separately supplied neo-osimertinib metadata matches another 83 using the author cell ID's plate component. Every annotation row maps uniquely to one of these metadata sources.

The [author final count table](https://github.com/czbiohub-sf/scell_lung_adenocarcinoma/blob/de138c79bcfc2fa3a28c8a039a28ab560da78099/data_out/IM06/Table_of_ALL_cell_types_by_sample.csv) independently matches the joined malignant count for **all 49 samples**, including genuine table zeroes. Its totals are 23,261 cells and 3,754 malignant cells across 44 samples with at least one malignant cell. The main input has 51 samples and the neo input adds five; the final table retains 44 main and all five neo samples. Seven main samples are absent: LT_S12, LT_S17, LT_S22, LT_S24, LT_S35, LT_S38 and LT_S46. This audit does not assign a specific upstream exclusion reason to each absent sample.

There are 33 literal patient-ID strings in final retained sample metadata. An explicit crosswalk of TH179_NAT→TH179, TH238_NAT→TH238 and AZ008_NAT→AZ008 yields 30 donor identities, consistent with the paper. This crosswalk uses source identifier semantics and matching resection/sample metadata; preserve the original labels and treat the donor alias interpretation separately from the direct sample-count reconciliation. The neo samples were part of the published discovery dataset, so they cannot provide independent validation of that paper's signature.

## What the published pipeline did

The author [initial Seurat script](https://github.com/czbiohub-sf/scell_lung_adenocarcinoma/blob/de138c79bcfc2fa3a28c8a039a28ab560da78099/scripts/02_Create_Seurat_object.Rmd) retains cells with strictly more than 50,000 counts and 500 detected genes. After adding neo samples, [script 03.1](https://github.com/czbiohub-sf/scell_lung_adenocarcinoma/blob/de138c79bcfc2fa3a28c8a039a28ab560da78099/scripts/03.1_Subset_and_general_annotations.Rmd) retains samples with more than 10 cells in the full object; this is not a minimum of 10 cancer cells. [NI03](https://github.com/czbiohub-sf/scell_lung_adenocarcinoma/blob/de138c79bcfc2fa3a28c8a039a28ab560da78099/scripts/NI03_inferCNV.Rmd) joins saved inferCNV annotations by `cell_id`, and [NI04](https://github.com/czbiohub-sf/scell_lung_adenocarcinoma/blob/de138c79bcfc2fa3a28c8a039a28ab560da78099/scripts/NI04_Cancer_cells_DEgenes.Rmd) selects epithelial cells labeled `tumor`. This audit accepts those saved labels; it does not rerun clustering or claim independently validated malignancy.

## Saved expression object

The author-linked `NI04_tumor_seurat_object.RData` contains the same 3,754 malignant-cell IDs and matching sample, patient, state, cluster and malignancy labels. Its RNA `counts` and `data` matrices contain 26,485 genes. The saved metadata row order differs from matrix column order, requiring an explicit cell-ID join before calculation. The extraction script preserves matrix order and reindexes exported metadata by verified unique cell IDs.

Count totals and detected-gene numbers agree with the corresponding metadata after that join. Saved `data` values are checked against `log1p(count / cell_total * 10000)`; see [the object audit](seurat-object-audit.json) for the numerical tolerance, exact hashes and environment. Extraction reads serialization only and executes no stored R code. The full object, matrices and cell-level exports remain local because no redistribution license has been verified.

## Reproduce

The [aggregate membership audit](malignant-membership-audit.json) preserves source URLs, hashes, candidate sample counts and explicit alias handling. Obtain the main and neo metadata at the source URLs in that audit, subject to their terms, at the documented local source paths. The standard-library audit verifies their hashes and can fetch its two small pinned author tables:

```sh
python3 -B scripts/audit_maynard_malignant_membership.py --fetch-author-files
```

The [object extraction script](../../../../scripts/extract_maynard_seurat_object.py) additionally requires the pinned RData file and the packages recorded in its audit. Its default extraction location is ignored `tmp/`; those exports are not public repository inputs. The [membership script](../../../../scripts/audit_maynard_malignant_membership.py) and object extractor calculate no signature score, fit no model and make no treatment-efficacy claim.
