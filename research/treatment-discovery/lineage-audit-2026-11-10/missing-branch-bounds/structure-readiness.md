# Structural readiness for finite-record missing-branch bounds

**The graph can support a frozen, conservative recorded-data functional with explicit unknown branches.** It does not support silently completing pedigrees or treating tracked fluorescence as biological viability. One additional fate conflict must be quarantined before implementation: a single candidate episode has division and apoptosis annotated in the same frame.

No conditional death curve, family-survival fraction, empirical bound, hypothesis comparison or preferred window was calculated here. The [structured note](structure-readiness.json) records source hashes, schema, checks and the proposed implementation contract. The earlier published structural outputs are unchanged.

## Inputs and a newly detected ambiguity

The local candidate graph is `tmp/hct116-lineage-structure/candidate-graph.json`, SHA-256 `89257469c39355c2b145bfb8a13a88cec54156317b43f3ed171af3d87a5d9b4e`. It matches the [published structural audit](../hct116-structure/results.json). The original XLSX and [DOCX dictionary](https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-018-07788-5/MediaObjects/41467_2018_7788_MOESM6_ESM.docx) were rechecked against their pinned hashes in the durable ignored source archive.

Each division and apoptosis annotation maps to exactly one candidate cell episode. The new checks find no multiple apoptosis flags within an episode, no division strictly after an apoptosis flag, no descendant edge from an apoptosis-marked episode, and no child edges lacking a single parental division annotation. **There is one same-frame division/apoptosis co-annotation.** Event order or intended correction is unknown. Neither a death-first parser nor a division-first parser should resolve it by convention. Mark the affected episode/path unknown before ordinary fate classification. Its exact source locator is retained privately in `tmp/hct116-lineage-structure/bounds-readiness-conflicts.json`.

This conflict was not a separate issue category in the earlier graph audit. The bounds implementation must detect it independently from the deduplicated event keys; reading only the graph's existing `issues` list will miss it.

## Schema needed for propagation

| Object | Relevant fields | Interpretation |
|---|---|---|
| Node | `id`, `label`, `first_frame`, `last_frame` | `id` identifies a cell episode; the source label can remain unchanged across division. Record coverage is not necessarily living time. |
| Node links | `parent_nodes`, `child_nodes` | Observed edges only. Missing daughter slots have not been materialized. |
| Fate annotations | `apoptosis_annotation_frames_in_episode`; `event_annotation_keys` | Deduplicated source events. Map division keys by label and inclusive episode interval. |
| Edge | `parent`, `child`, `boundary_frame` | Child begins at this frame; parent division annotation is one frame earlier. |
| Provenance | `source_rows`, `candidate_roots` | Repeated ancestor rows are not repeated cells. Candidate component roots are not verified original population founders. |
| Baseline roster | Keys `97` through `101`, with `node`, `frame`, `source_label` and issue metadata | Use the full chosen roster. Do not retain only cells without future issues. |

The source dictionary defines event flags and untracked-value conventions. It does not directly supply a normalized parent-ID table, independent experiment identifiers or the original founder-selection denominator.

## Preserve the probability of unobserved daughters

Set the tag weight of each chosen baseline cell to one. Let \(g\) count divisions **after that baseline**, not generations from the original candidate root. After \(g\) fair daughter choices, the path weight is \(2^{-g}\).

At a documented division receiving weight \(w\):

- Two observed daughters receive \(w/2\) each.
- One observed daughter receives \(w/2\); the unobserved daughter retains unknown mass \(w/2\).
- No observed daughter leaves two unknown daughter possibilities, with total unknown mass \(w\).

A daughter retaining its parent's numeric label still counts as a division and halves the weight. Do not renormalize onto available daughters, uniform terminal rows or surviving descendants. A recorded, unconflicted death ends that path; its weight cannot move to a sibling. Once a branch is unresolved, keep its total tag mass unknown rather than inventing hidden divisions. Unknown frontier entries must not overlap: stop traversal when a path is quarantined, so descendants do not charge the same probability twice.

For a disjoint path frontier, resolved-status mass plus unknown mass must sum to one for each baseline cell. That is an implementation invariant, not an outcome bound computed in this note.

## Recorded fate is different from track presence

A source apoptosis flag is affirmative recorded death evidence, subject to the frozen frame convention and annotation consistency. Track disappearance is not death. Conversely, nonzero lineage labels and fluorescence can persist after apoptosis; the earlier audit found retention up to seven frames. That period must not become additional living person-time.

For an intact path, positive lineage identity, an available measurement and no prior death annotation can define **recorded present/not-death-annotated** status. Interpreting it as biological survival adds an observation assumption: manual death annotation must be correct and complete at the stated resolution. Fluorescence positivity alone does not establish viability or functional drug tolerance.

For the inconsistent Lineage/p53 masks, a conservative default is to quarantine the entire affected cell episode and its tagged continuation as unknown. A still broader whole-baseline-path rule is possible, but its meaning must be fixed before calculating bounds. Do not decide which mask is correct after inspecting results. An earlier issue on a sibling branch need not invalidate a later observed cell's subtree, although founder clustering remains a separate uncertainty.

## Fixed frame coordinates and available support

Use one-based frame coordinates and make any elapsed-time convention explicit:

\[
\tau_b(f)=\tfrac12(f-b)\ \text{hours},\qquad f=b+2\tau.
\]

This is a relative coordinate on the recorded half-hour grid, not a claim about an exact biological event instant. It provides the following maximum recorded coordinates through frame 243:

| Baseline frame \(b\) | Last relative coordinate | Same-frame division annotations in the existing roster |
|---:|---:|---:|
| 97 | 73 hours | 3 |
| 98 | 72.5 hours | 4 |
| 99 | 72 hours | 6 |
| 100 | 71.5 hours | 3 |
| 101 | 71 hours | 5 |

The common support is therefore **at most 71 hours** under this coordinate rule. A 72-hour endpoint is unavailable for baseline frames 100 and 101. No query horizons are selected here.

None of the five current rosters has a same-frame apoptosis annotation, but same-frame divisions make a before/after-event convention at time zero material. The codebook states treatment after 49 hours and just before frame 98; the main methods state 50 hours. Preserve all five source-origin brackets. Within each bracket, use the same roster for every horizon.

The flag-to-child relation is known in frame indices, but continuous-time ordering within the half-hour interval is not. Freeze whether a query sees events at the annotation frame or at the next-frame child boundary, or leave a one-frame boundary band unknown. Do not silently extend a parent until a convenient child time, turn post-death tracking into survival, or extrapolate past frame 243.

## Requirements before calculating bounds

The empirical functional must specify baseline-cell versus original-founder weighting, event-boundary equality, query frames, the observation assumption, and the mask/conflict policy. Retain all unresolved paths in the fixed roster; do not filter by future completeness or nondivision.

Family inclusion and tagged survival must arise from the **same possible completed family**. A live tag requires a live family. Unknown daughter completions must also remain consistent across query times and selection horizons. Independent upper/lower assignments at every point can produce incompatible histories and overly strong claims.

These checks support conservative bounds on a finite recorded cohort under explicit rules. They do not supply unconditional population estimates or an unqualified test of a biological branching model. The implementation should stop if source pins change or a new contradiction cannot be represented by its unknown-state rules.
