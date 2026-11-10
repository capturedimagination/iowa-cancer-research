# Draft: Kuchen source dictionary and observation graph

Status: **planning draft, not a frozen analysis protocol; outcome analyses are not yet specified**. Prepared from the existing durable [source audit](README.md), [schema](kuchen-schema.json), [first structural audit](kuchen-structural-audit.json), [independent verification](structural-verification.json), [acquisition record](acquisition.json), and the existing structural-parser code. No workbook was reopened for this draft, no new graph was constructed, and no Q, covariance, survival rate, hazard, prediction or treatment comparison was calculated.

The next bounded deliverable should be a versioned dictionary, candidate graph and observation-mask audit. Its purpose is to determine which later estimands the export could support. A syntactically valid graph is insufficient evidence for a prospective cohort.

## 1. Preserve source identity before interpreting it

Verify the two original XLSX hashes and saved schema hash before parsing, and again after the read. Use the workbook's actual XML sheet mapping and Excel row numbers. Preserve original source bytes; save parsing and derived outputs separately. The current source hashes and download/rights basis are in acquisition.json and license-record.json. A changed source or schema requires a new version and an explicit comparison with the first audit.

The current export has seven sheets and starts at recorded generation 2. Those facts, the four negative loss durations, the missing successor pair and the unresolved rapamycin overview/export discrepancy are already known from the audit. Do not infer a label swap, relabel conditions, repair durations, or reconstruct original founder counts from these patterns.

Proposed identifiers:

| Entity | Proposed key | Important distinction |
|---|---|---|
| Source version | Original workbook SHA256 | Filename alone is insufficient |
| Sheet | Workbook SHA256 plus exact sheet name | Repeated IDs in different sheets must stay separate |
| Pair observation | Workbook SHA256, sheet, original Excel row | A row is a recorded sister pair, not a prospective founder |
| Recorded cell | Workbook SHA256, sheet, opaque sibling-ID token | Do not decode generation or ancestry from digits |
| External parent reference | Same namespace and opaque mother-ID token, with `observed_episode=false` | A reference is not an observed cell history |
| Source lineage label | Workbook SHA256, sheet, opaque Lineage ID | Keep separate from graph-component identity and original-founder identity |
| Graph component | Versioned deterministic identifier for a connected recorded ancestry structure | Never call it an original founder without source evidence |

Do not include Lineage ID in the cell's join key: doing so could conceal a contradictory mother-child link across lineage labels. Instead retain the lineage label as a source field and audit its consistency after joining. Do not join across workbooks or sheets merely because numeric-looking IDs match. If lexically different ID tokens appear equivalent after numeric conversion, flag the possible alias; do not silently merge them through floating-point conversion.

Every field needs provenance: workbook hash, sheet, XML sheet path, Excel row, Excel column/cell, sibling side where relevant, raw token, XML cell type and parser rule/version. Record field status separately from value: `present`, literal `NaN`, absent XML cell, nonfinite/invalid value, or unresolved interpretation. A missing ID is not the string key for an ordinary shared cell.

## 2. Dictionary before a graph

Use the saved column map literally. Both workbook types provide lineage label, two sibling IDs, a mother ID, shared sibling birth time, three separate fate-duration fields per sibling, generation, mother/grandmother cycle lengths and a grandmother ID. Controls also provide birth coordinates; perturbation sheets do not. Their different column positions must be bound by schema, not guessed from one workbook's layout.

For each proposed derived field, the dictionary should state:

- The original name, source locator, raw type, missing encoding and unit evidence.
- Whether it is an observation, source-authored annotation, derived arithmetic, parent-reference assertion, or unresolved fact.
- Its time origin and whether a duration ends in division, death or loss.
- The source-supported precision and event-boundary convention, where available.
- Its permitted use in identity, chronology, observation masks, cohort eligibility or later prediction.

The existing audit expresses time in hours. Preserve that interpretation with a source-located unit reference before constructing a physical-time grid. Do not derive frame numbers or measurement precision from decimal formatting or from the small floating-point parent-child residuals. Imaging cadence and event annotation precision must be separately verified.

Keep shared birth time H as the source assertion for both siblings. Map the three fate fields separately: a cycle-length value is an observed division-duration annotation, not an uncensored potential timer for a competing-risk model; a time-to-death value is a death annotation; a time-to-loss value is an observation-loss annotation whose mechanism remains unresolved. Mother/grandmother cycle-length fields are source annotations, not permission to manufacture unrecorded ancestor episodes.

Do not use observed maximum birth-plus-duration as the recording end. The overview and export maxima disagree for rapamycin sheets, and a sample maximum is not an administrative design parameter. Preserve both accounts without assigning one sheet another sheet's dose or duration.

## 3. Proposed candidate graph

Expand each pair row into two recorded-cell nodes, retaining the common pair key and separate sibling source locators. Link a child's mother reference to a recorded cell only when its exact namespaced ID is present. Otherwise retain an external-parent reference with no fabricated birth, death, continuous observation interval or founder status.

The pair row supplies a parent-child assertion and common daughter-birth time. If the mother's own episode is absent, these observations do not become a complete maternal trajectory. A division time inferred from daughter birth, if later stored, must be labelled as that inference and kept separate from an observed maternal division-duration field.

For each recorded division, look for its successor-pair row. If it is missing, retain an unresolved descendant branch after the division, not a terminal death. Under a source-certified binary-division convention, this can be represented by two unknown daughter slots with no invented observed IDs; otherwise the offspring-count assumption is another gate. Never renormalize an observed daughter to represent the entire family or tag merely because its sister is unrecorded.

Use grandmother references and repeated cycle-length annotations as independent consistency checks. They must not overwrite the mother links. If multiple assertions conflict, preserve the original assertions and mark the affected edge/episode unresolved. Do not select the version that produces a more complete tree.

Report at least three distinct structures: source Lineage ID groups, connected components under verified recorded-parent edges, and the earliest recorded cells/external parent references in each component. All are properties of the retained export. None is automatically an original prospective founder. Components may share an unrecorded earlier ancestor; component disconnection is not proof of biological independence.

## 4. Conservative time and observation masks

Maintain event identity, event time, and observation support separately. A useful mask vocabulary is `certified_alive`, `certified_dead`, `unknown`, `outside_recording_support`, and `conflicting_annotation`. Whether the source certifies continuous tracking between birth and a terminal annotation must be resolved before calling that whole interval observed.

Proposed handling, subject to a frozen dictionary:

| Source situation | Conservative representation |
|---|---|
| Valid birth and one nonnegative division duration | Candidate division at birth plus duration; require a consistent successor assertion or retain unknown descendants |
| Valid birth and one nonnegative death duration | Candidate death at birth plus duration; absorbing death is usable only after excluding contradictory later descendants/events |
| Valid birth and one nonnegative loss duration | Observation may end at birth plus duration; subsequent fate remains unknown. Do not code death or assume independent administrative censoring |
| Negative fate duration | Invalid terminal timing. Preserve the source token; post-birth support remains unknown unless separately established. Do not clamp, take an absolute value, or replace it with another record's time |
| No finite fate, multiple finite fates, invalid birth or conflicting chronology | Retain the node/assertions as unresolved. Do not choose a convenient fate or silently discard the record |
| Mother divides but successor pair is missing | Known division assertion with unknown descendant mass, not extinction |
| Tracking loss followed by another source assertion | Preserve the observation conflict and possible gap. Do not infer continuous observation or automatically equate loss with biological impossibility |

Negative absolute birth times, if encountered in a later parse, would need their own source-time-origin interpretation; they are not automatically negative-duration errors. Zero-duration events and exact event/query ties need an explicit recording convention. Until timing precision is verified, boundary observations may need interval-valued timing rather than an arbitrary right/left convention copied from a synthetic simulator.

For a later family-survival mask, observing one certified living descendant can establish survival at a queried time. Extinction requires all possible branches to be accounted for and dead by that time. An unresolved daughter or tracking loss prevents a certified extinction conclusion. This is a proposed logical rule, not an instruction to calculate family-survival outcomes in the structural phase.

Localize uncertainty by source-supported time and ancestry. Do not automatically discard every descendant of a component with an earlier unrelated anomaly. Conversely, do not use later complete branches to erase uncertainty about an unobserved branch. A separate sensitivity policy could coarsen an entire affected episode; it must be frozen before outcome calculations.

## 5. Candidate birth cohort and selection gate

A useful future target is a recorded-at-birth sister cohort. Define its roster from the pair's documented birth, source namespace, and a **predeclared** recording-support rule. No lag, birth cutoff, early/late window, or favorable sheet is chosen in this draft. Their values must be motivated by the scientific question and verified acquisition metadata before querying future outcomes.

Do not determine eligibility from whether either sister later survives, completes a division, has a long cycle, supplies a deep tree, has a complete subtree, or remains in the field. Retain incomplete follow-up through unknown masks or a separately justified observation model. If an event-time origin cannot be established, retain that record in an untimeable-record ledger rather than silently treating it as absent from the prospective population.

Crucially, a past-only analysis rule cannot undo future-dependent source export selection. The existing methods describe exclusion of early-leaving cells and generation truncation in published analyses; whether those choices affected these workbooks is unresolved. The graph must carry a source-ascertainment status. Until the export denominator and rule are certified, claims are limited to the retained record and compatibility/bounds under explicit assumptions. Do not label the cohort prospective merely because the new code uses only birth fields.

Use equal weighting at the declared unit, and specify it before analysis. An all-recorded-birth cohort naturally weights families with more recorded births more heavily than an equal-founder cohort; those are different estimands. Do not change weights after seeing results or infer an original-founder denominator from generation-2 rows.

For later validation, prevent related ancestry from crossing training/test splits. When source lineage labels support a broader related group than the reconstructed component, retain that conservative clustering information. A sheet is not a certified independent biological replicate: the biological/technical allocation remains unresolved. Mother-history predictors must be restricted to information available by the prediction time, with their source and event-time provenance intact.

## 6. Structural invariants and fixtures to freeze before construction

The next implementation should test these without calculating outcome summaries:

1. Source hashes, schema headers/XML mappings, source row counts and missing markers agree with the pinned audit. All parsed cells retain raw provenance. Output IDs are unique within the chosen namespace, and identical tokens across sheets stay distinct.
2. Each pair has two distinct child identities, a single mother reference and a common recorded birth assertion. A cell cannot be its own parent or sibling. Duplicate child records or multiple parent claims trigger an explicit conflict.
3. Verified parent edges form an acyclic directed graph. Every recorded node has at most one verified parent. A source lineage-label contradiction, generation discontinuity or grandmother mismatch is reported without forced relabelling.
4. For a joined recorded mother, child birth agrees with its division time under a declared arithmetic-consistency tolerance. The existing parser's 1e-6-hour trigger may be carried forward solely as a numeric consistency check; it is not imaging precision. Preserve the residual and do not average inconsistent times.
5. Exactly one usable fate annotation is required for a determinate terminal event. Its duration is nonnegative, its derived time is chronologically valid, and death has no compatible later division/descendant event. Loss remains observation loss.
6. Every recorded division either has a unique consistent successor pair or an explicit unknown-successor state. A missing successor never silently reduces offspring count, tag mass or family size.
7. Component summaries reconcile node/edge counts without conflating external references, recorded roots, source lineage groups and original founders. Do not let bookkeeping structures create an issue for a clean component merely by reading its empty issue list.
8. Graph/source arrays and observation masks do not include any sampled outcome-based exclusion. Cohort-roster generation is a separate, auditable operation with its permitted fields declared.

Synthetic fixtures should cover two sheets reusing an ID; one valid recorded pair and an external mother; a duplicate child or pair; a cycle; contradictory mother/grandmother links; a missing successor; one missing daughter; negative/multiple/missing fate fields; death followed by a descendant; loss followed by an observation gap; generation-2 left truncation; a clean component beside an affected one; and events at a candidate boundary. They should verify unknown preservation and provenance, not simply mirror implementation code.

## 7. Stop/go gates for later analyses

**Graph/dictionary audit may proceed only after a structural protocol is frozen.** It should produce no Q curve, covariance estimate, death fraction, fitted hazard, treatment association, predictive score or selected lag. Source event-label counts already reported by the audit remain record-description counts.

Before Q or original-founder inference, require a verified prospective unit/roster, complete or explicitly bounded family ascertainment, a future-blind tag rule, time mapping and a frozen unknown-branch policy. Without an original-founder denominator, a retained recorded-newborn estimand may still be considered, but it must be labelled as such.

Before sister covariance, require a defined birth-cohort denominator, coherent daughter outcome definitions, observable/unknown masks at predeclared lags, and handling of within-family and experiment dependence. Complete-case deletion based on future tracking is not an acceptable substitute for these gates. Any source selection sensitivity and missing-outcome bounds need a separate frozen plan.

Before hazards or age/context model fitting, additionally require event-time precision, competing-event semantics, entry times, loss/censoring interpretation, and identifiability of the proposed model under that observation process. A field called loss does not establish noninformative censoring. Shared contexts, unobserved states and prior source exclusions remain alternatives.

Before held-out prediction, freeze feature availability, training/validation units and clusters, model families, observation likelihood/bounds, evaluation metrics and all timing choices. Training and evaluation cannot share descendants of the same known lineage. Seven sheets alone do not validate seven biological replications.

Before dose- or condition-specific inference, resolve the rapamycin identity/overview discrepancy and replicate metadata. Preserve source sheet labels in the meantime. No repair, label exchange, dose assignment or author contact is part of this draft.

If the required source assertions cannot be established, stop the corresponding population inference. The useful fallback is a transparently defined retained-record structural analysis or conservative compatibility bounds, with their identity/weighting assumptions stated. Do not interpret an uninformative bound as evidence of no effect.

## 8. Proposed artifacts and publication boundary

After freeze, save a machine-readable dictionary with evidence/status fields; a source-pinned graph-construction protocol; structural code and meaningful fixtures; immutable private per-cell/edge/observation records; and public aggregate checks, uncertainty categories, code/input hashes and a readiness decision. A source clarification ledger should separate affirmative evidence from unresolved questions.

Keep original XLSX/PDFs and all expanded cell-level graph/mask records under the already excluded source/working prefixes. Do not publish raw cell rows, reconstructed per-cell histories, or a relationship table disguised by renamed identifiers. Public outputs can contain schemas, original code, aggregate consistency counts and source URLs/rights provenance. This draft contains no new raw records.

The immediate success criterion is a reproducible, honest answer about what the export can identify and observe. It is not a positive inherited-resistance signal. The published source already studied lineage correlations and temporal/spatial confounds; a later model comparison would need its own justified question and prior-art review.
