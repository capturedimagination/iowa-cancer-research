# Next empirical resource: reconstruct the HCT116 trees

**The original HCT116 deposit is a concrete next target.** It supplies a small workbook with division, apoptosis, p53 and lineage arrays, plus an explicit codebook. Proceed with tree reconstruction and eligibility checks. Outcome modeling still needs verified event ordering, missing-branch handling and a defensible founder cohort. The public U2OS material located here is insufficient for a full-tree test.

This is a resource audit, not a fitted biological result. The [JSON record](next-empirical-resource.json) contains exact URLs, hashes, inspected fields, unresolved items and the proposed test. Originals are hash-verified in the ignored durable archive `research/treatment-discovery/sources/lineage-2026-11-10/`; temporary originals are also preserved. No raw data or movies are republished.

## What can actually be acquired

| Resource | File and verified size | Content and decision |
|---|---|---|
| HCT116 events | [Chakrabarti 2018 Supplementary Data 1](https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-018-07788-5/MediaObjects/41467_2018_7788_MOESM5_ESM.xlsx), XLSX, **1,446,947 bytes** | Acquired and structurally parsed. Four numeric arrays, each 394 rows × 243 columns. **Go for reconstruction.** |
| HCT116 codebook | [Supplementary Data 2](https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-018-07788-5/MediaObjects/41467_2018_7788_MOESM6_ESM.docx), DOCX, **17,442 bytes** | Acquired and read. Explains event flags, tracking masks, lineage labels and timing. |
| Iyer supporting methods | [Supporting Text](https://journals.plos.org/ploscompbiol/article/file?id=10.1371/journal.pcbi.1013446.s001&type=supplementary), PDF, **2,059,025 bytes**, 25 pages | Acquired and read. Contains explicit excluded-lineage labels and modeling details; no additional repository URL was found. |
| Iyer-specific code | [Shaonlab account](https://github.com/Shaonlab), the destination named by the paper | No matching public repository located in the bounded searches. The five account-search results concerned other projects. This is an access finding, not proof that unpublished or unindexed code does not exist. |
| U2OS events | No machine-readable event deposit located in the inspected [Granada 2020 article](https://pmc.ncbi.nlm.nih.gov/articles/PMC7185964/) and supplement inventory | **No-go for a full-tree test.** Single-sister tracking also omits the other descendant subtree by design. |

The HCT116 workbook SHA-256 is `212e5ca40af8fe5f1b07baf613459f275c7b97a2ec99e31fa2505af252a3f130`; the codebook SHA-256 is `6f863bac4ce6157dfcf59f802e61b3fcf457251d7d6e7e489a6f0d69627d944b`. All four workbook ranges are `A1:II394`, with 95,742 numeric cells each, no formula cells and no text headers. These are structure checks, not event counts or independent sample sizes.

## The HCT116 dictionary is useful but not complete

The source workbook uses HCT116 cells with p53-Venus and H2B-ECFP reporters. This is colorectal cancer, not EGFR-mutant lung cancer. The [original article](https://www.nature.com/articles/s41467-018-07788-5) explicitly identifies its workbook and companion dictionary as the lineage-data deposit.

| Field | Affirmative source meaning | Remaining work |
|---|---|---|
| `Divisions` | Binary annotation: one indicates division at that timepoint | Deduplicate shared ancestral records and resolve exact event/frame ordering |
| `Apoptosis` | One indicates death at that timepoint | Reconcile flags with observation coverage and prevent duplicated counting |
| `p53` | Fluorescence; −1 means untracked because of death or ambiguous identity at the beginning | It is not a complete independent censoring-reason field |
| `Lineage` | Shared frame-specific labels identify a common tracked cell/history; label splits encode relationships; zero means untracked | Reconstruct cell episodes and parent links. One descendant may retain the old label, so an unchanged label does not imply no division |
| Time | 243 nominal 30-minute points; codebook reports 121.5 hours, treatment just before frame 98 after 49 hours | Main methods describe 50 hours before treatment. Preserve that difference and verify the first-frame and event-boundary conventions |
| Treatment | One source-described 12.5 μM cisplatin trajectory | No per-row arm or dose field; this is not a multi-dose workbook |
| Replication | The paper reports two experiments for some analyses | No movie, field, well, experiment or replicate identifiers appear in these arrays |

The DOCX micro symbol is a Symbol-font character; simple text extraction drops it. The unit was checked against the original article. The codebook supplies much more timing information than the Oren export, but no separate absolute timestamp vector is deposited.

A row contains repeated ancestral history and is not an independent founder or a ready-made parent/child record. A normalized event table must be derived without inventing missing branches. The proposed reconstruction should retain source row/frame references, source labels, inferred cell-episode IDs, parent IDs, division/death intervals, tracking status and every ambiguous mapping.

## Selection and loss are material, documented limitations

Iyer's Supporting Text reports 83 original HCT116 ancestor trees, retaining 65: 49 present at the first frame and 16 entering later. Table A lists 18 excluded founder labels. Five have missing or abrupt identity relationships; 13 never divide. Some excluded cells die and some appear late. Those published choices cannot be reused as an outcome-independent eligibility rule.

The JSON preserves the exact 18 labels and distinguishes the five identity-related groups. These are source-reported classifications, not a graph reconstruction we have independently verified. Keep the never-divider sensitivity separate from genuine missing-identity handling. Retain delayed entry explicitly. Never infer a complete initial founder denominator from 394 workbook rows.

The next useful artifact is a **reconciled event graph and founder roster**, with checks for daughter multiplicity, orphan or merged identities, duplicated ancestral events, contradictions between death and tracking annotations, and complete versus partial post-treatment follow-up. Do not silently repair the published exceptions. Without replicate identifiers, any resulting performance estimate remains within the recorded experiment.

## Existing work and one proposed test

The [Iyer paper](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1013446) already compares age-structured and inherited-state models, analyzes competing risks and lineage-fate correlations, simulates barcode diversity, and repeatedly samples random daughters for a Luria–Delbrück statistic. The original HCT116 study already analyzed timing correlations, p53 associations and oscillatory models. Repeating these claims would not establish a new result.

**Proposed question:** Can a model trained on prospective event histories predict both family survival and the selected-tag death-time distribution in entirely held-out founder families, without inherited latent states?

Use a cause-specific division/death baseline that permits cell age and time since treatment, with a common observed risk set and explicit censoring. Compare it with a prespecified inherited-family or inherited-state alternative using the same observable-event likelihood. A constant-rate branching model can serve as a restricted reference. This avoids inferring unobserved counterfactual waiting times directly from event-specific histograms.

Freeze the cohort, model complexity, split seed and score before fitting. Keep every descendant and repeated ancestor from one founder in the same fold. Suggested endpoints are 24, 48 and 72 hours after treatment, subject to the verified frame map. Score family-survival calibration and the conditional death-time distribution produced by random forward tags from endpoint-surviving held-out families. Integrate branch sampling or repeat it with fixed seeds, and quantify uncertainty at the founder level. Report never-divider inclusion, delayed-entry, treatment-origin and frame-boundary sensitivities.

This tests predictive transport to an ascertainment design withheld from training. It does **not** test the identity `Q × h = prospective tag survival`, which is an accounting identity once the same cohort is used. A successful baseline would reduce the need for added state structure for this prediction. Failure would not uniquely prove memory: other heterogeneity, environmental variation or censoring errors could explain it. No outcomes have been fitted, and novelty remains unestablished.

## Access and reuse boundaries

The [HCT116 article](https://www.nature.com/articles/s41467-018-07788-5) uses CC BY 4.0 for its article-associated material, subject to separately credited exceptions. No contrary notice was identified in this acquired workbook or codebook. Attribution, source links and clear descriptions of transformations are required; this audit publishes only metadata and links. The original computational modeling code was offered on request, and generic p53Cinema availability does not supply the study-specific analysis scripts.

The U2OS article uses CC BY-NC-SA 3.0 and offers additional custom MATLAB code on request. Its listed supplement is a roughly 1.6 MB PDF; exact bytes and contents were not acquired because attachment requests returned a browser check or HTTP 403. Four example movies are listed at approximately 6.2, 5.9, 4.8 and 4 MB. Movies were not downloaded and are not a substitute for event records. No author contact was made.
