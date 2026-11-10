# Kuchen dictionary evidence

Reviewed 2026-11-10. **The reporting form resolves the source-declared biological-replicate labels. Exact timing, uninterrupted observation and export inclusion remain unresolved.** This source audit adds no Q, covariance, hazard, model or graph-derived survival outcome. Previous files and anomalies remain unchanged. The [assertion ledger](source-assertion-ledger.json) gives individual evidence tiers, source locators, search limits and hashes; [acquisition](source-acquisition.json) preserves three newly retrieved originals in the excluded source archive.

## New evidence

The author-supplied reporting form explicitly identifies rep1–3, -myc1/2 and rap1/2 as biological replicates. It also reports 68 analyzed control lineages and exclusions of early departures producing short trees. These statements support the named labels, not an all-founder denominator or future-independent workbook cohort. The paper's broader biological-and-technical wording is retained; culture dates, well/batch relationships and shared preparations remain unspecified. [Reporting form, p2, Replicates](https://cdn.elifesciences.org/articles/51002/elife-51002-transrepform-v2.pdf).

A source-ordering discrepancy is now explicit: the overview assigns corrected generation limits 6/7/5 to rep1/2/3, whereas the paper lists 7/6/5 without naming each sheet in that sentence. This is separate from the known rapamycin discrepancy: the overview assigns rap1=40 nM, 117 h, 8 generations and rap2=20 nM, 115 h, 7 generations, opposite the prior export duration/generation pairing. Neither discrepancy establishes a swap. [Overview, p1](https://cdn.elifesciences.org/articles/51002/elife-51002-fig1-data1-v2.pdf); [paper, p11 and Appendix1 Censoring](https://cdn.elifesciences.org/articles/51002/elife-51002-v2.pdf).

## Dictionary decision

| Field or rule | Evidence and retained limit |
|---|---|
| Time unit and origin | Figure1 axes use hours; workbook headers omit units. No exact mapping of H=0 to recording, plating or treatment was found. Retain raw time coordinates and the source-supported hours interpretation separately. |
| Frame/event precision | General cadence is 6–15 min; the illustrative rep3 clip uses 6 min. Neither supplies full per-sheet frame maps, event landmarks, rounding or tie conventions. Decimal precision is not event precision. |
| Continuous tracking | Figure1A describes continuous microscopy and Appendix1 names manual tracking. No per-cell gap/re-entry rules certify an entire birth-to-event interval. |
| Division and fate | The row asserts two siblings, a mother, shared birth and separate cycle/death/loss fields. Endpoint sums are derived arithmetic. A missing successor does not certify two complete unobserved daughter trajectories or extinction. |
| Loss and end of recording | Loss and death are distinct. Migration and finite observation are discussed, but no workbook reason code separates migration, tracking failure and administrative end. Whole-hour overview durations are not exact frame boundaries. |
| Export eligibility | Raw-data captions and deeper exported generations do not prove that excluded early-leavers were retained. Published endpoint-dependent generation selection must not define a new prospective birth cohort. |

Sources: [paper Figure1 and Appendix1, pp3/16–18](https://cdn.elifesciences.org/articles/51002/elife-51002-v2.pdf); [source-file captions and video legend](https://pmc.ncbi.nlm.nih.gov/articles/PMC7018508/); pinned workbook schema and package metadata in the ledger. The author-linked [key-resources file](https://cdn.elifesciences.org/articles/51002/elife-51002-supp1-v2.doc) identifies reagents/software but supplies no event/export dictionary.

## Consequences for the graph

Proceed with namespaced source identities, recorded relation assertions and provenance. Keep observation support separate from event identity and arithmetic time. Do not turn a microscopy description into a certified alive interval, migration into independent censoring, plated-cell count into a tracked denominator, or a source-declared biological sheet into evidence of identical treatment dose.

Retain the four negative loss durations and absent descendant pair as unresolved. Preserve both generation and rapamycin accounts. If later masks require binary completion, an event-boundary convention or an uninterrupted interval, label that as a separately frozen assumption with sensitivity analysis; it is not resolved by this audit. Source-ascertainment uncertainty still restricts interpretation to the retained record.

No author was contacted. The bounded search did not locate an original export script or fuller acquisition dictionary; it cannot establish that none exists. Newly archived sources remain excluded from Git; this public record contains links, hashes and paraphrases only.
