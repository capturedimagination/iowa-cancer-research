# HCT116 lineage reconstruction: observed graph, missing branches

**A deterministic candidate graph is recoverable, but the whole-cohort horizon test is not yet justified.** The workbook supports 328 binary divisions with internally consistent shared histories. Another 73 annotated divisions have only one observed daughter, and one has no observed daughter. An absent branch is unknown, not dead. Some original-root components and many later cell subtrees have no detected structural issue, but selecting them by future completeness changes the observation process.

This audit checks representation, identity continuity and recording eligibility. It does not estimate cancer outcomes, compare biological hypotheses, calculate survival/death curves or select favorable time windows. [Current results](results.json), [structural protocol and amendment](protocol.json), [resource/codebook audit](../next-empirical-resource.md).

## Source and reproducible mapping

The source is [Chakrabarti et al. 2018 Supplementary Data 1](https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-018-07788-5/MediaObjects/41467_2018_7788_MOESM5_ESM.xlsx), with its [companion dictionary](https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-018-07788-5/MediaObjects/41467_2018_7788_MOESM6_ESM.docx). The original four 394×243 numeric arrays are complete and contain no formulas. The original workbook, DOCX and Iyer supporting PDF now have hash-verified durable copies in the ignored `research/treatment-discovery/sources/lineage-2026-11-10/` archive. Temporary originals were preserved.

The [audit script](../../../../scripts/audit_hct116_lineage_structure.py) uses the Python standard library. Run from the repository root:

```sh
python3 scripts/audit_hct116_lineage_structure.py
```

It verifies the three source hashes, parses the workbook without modification, runs small structural fixtures, constructs the graph twice and requires identical results. Public outputs contain original aggregate checks. The candidate cell episodes, edges, source row/frame references, baseline rosters and issue records remain in ignored `tmp/hct116-lineage-structure/candidate-graph.json`; its hash is recorded in the results. Those cell-level records are not part of the public package.

The mapping rules are deterministic:

1. At each frame, group rows sharing a positive lineage label. The same-label rows must agree in division, apoptosis and p53 values. This prevents duplicated ancestral rows becoming independent cells or repeated events.
2. Link adjacent-frame groups through the original rows. Do not invent parents, repair names or force mergers into trees.
3. End a biological cell episode at every annotated division, including when a daughter retains the old label. Start observed daughter episodes at the next frame. Preserve divisions with zero or one observed daughter as incomplete branches.
4. Use recorded apoptosis annotations separately from disappearance of lineage or fluorescence records. Retained image data after an annotation do not establish additional living time.
5. Keep observation masks, delayed root entry, original source labels and any unresolved identity joins explicit.

This produces a **candidate** graph. Agreement with its invariants does not establish that every biological cell was captured, that source selection was independent of outcome, or that the export includes every original experiment.

## Structural findings

| Check | Current result | Interpretation |
|---|---:|---|
| Shared-label cell/frame groups | 49,407 | Repeated source rows were grouped before interpretation |
| Within-group division, apoptosis or p53 disagreements | 0 | Shared-history values agree exactly |
| Candidate cell episodes / parent-child edges | 795 / 729 | Acyclic; every child begins after its parent episode ends; no multiple-parent node |
| Candidate roots | 66 | 49 present at the first recorded frame; 17 appear later |
| Divisions with two observed daughters | 328 | Every split follows a division annotation in the immediately preceding frame |
| Divisions with one / no observed daughter | 73 / 1 | Missing branch information; neither class is coded as death |
| Positive lineage but p53 −1 | 42 source row/frame entries, representing 10 distinct label/frame groups | Conflicting observation indicators; these are not 42 independent cells |
| Tracking retained after apoptosis annotation | Up to 7 frames | A tracking mask cannot substitute for an alive-at-risk mask |
| Roots with no detected structural issue | 20, including 13 first-frame roots | Structural subset only; completeness is not proof of unbiased eligibility |

Both event arrays contain isolated binary flags, without consecutive positive entries. The 328 fully observed splits establish a consistent flag-to-label convention in this export: the division flag occurs in the last parent frame and the daughter labels appear one frame later. This is a frame relationship, not proof of the exact continuous-time event instant. Interval timing and treatment alignment still require explicit conventions.

All observed early terminal episodes have an apoptosis annotation somewhere within the episode. Some continue to retain tracking values after that annotation. An initial check that demanded the annotation be within one frame of disappearance was too restrictive; its flagged exits were not evidence of unexplained biological loss. The remaining important deficiencies are incomplete daughter branches and inconsistent observation indicators. Their source provenance is retained rather than corrected.

## A later baseline can have a more complete descendant subtree

A pre-treatment missing branch does not necessarily prevent recovery of a later observed cell's descendants. We therefore assessed **every** prespecified frame in a fixed treatment-origin bracket. A candidate baseline cell must have a positive lineage label, available p53 and no earlier apoptosis annotation in that episode. An event annotated in the baseline frame is not excluded in advance. Structural completeness is assessed through the same final frame, 243, for every row below.

| Baseline frame | Timing interpretation | Observed candidate baseline cells | No detected later structural issue | Later structural issue |
|---:|---|---:|---:|---:|
| 97 | Last recorded snapshot before the codebook's frame 98 | 277 | 248 | 29 |
| 98 | Codebook frame; 49 hours if the first acquisition is at 0.5 hours | 280 | 251 | 29 |
| 99 | 49 hours if the first acquisition is at zero | 284 | 255 | 29 |
| 100 | 50 hours if the first acquisition is at 0.5 hours | 289 | 261 | 28 |
| 101 | 50 hours if the first acquisition is at zero | 291 | 264 | 27 |

These are alternative structural rosters, not a growth curve or treatment-effect estimate. The codebook states 49 hours and just before frame 98; the paper's methods state 50 hours. Neither first-frame origin is silently chosen, and no row is preferred for producing more complete cells.

A prior issue in the same root component may lie on a sibling branch rather than the baseline cell's direct ancestry. The machine-readable results therefore call this `with_prior_component_issue`. Baseline subtrees without a detected later issue can still have uncertain earlier clustering and are not independent experiments.

## Founder identity and exclusions remain unresolved

Iyer's Supporting Text reports 83 original HCT116 founder trees and 65 retained trees, including 49 present initially. Our 66 algorithmic roots do not directly certify or contradict those counts. A published lineage identifier might refer to another original cell/row namespace, and the source versions or processing may differ. Directly matching the published exclusion numbers to current dynamic root labels matches only one; **that is an unverified crosswalk, not proof that the other founders are absent or mislabeled**.

A complete original founder roster, study-specific identifier map, replicate assignments and explicit tracking-loss reasons are still needed. Never-dividing lineages must not be silently excluded because their behavior is inconvenient. Conversely, treating an unresolved identity as a complete pedigree would manufacture information.

## Can these data test cross-horizon invariance?

The intended quantity is the death-time distribution of a future-blind random daughter path, conditional on at least one descendant of its fixed founder surviving to a selection horizon \(T\). Comparing \(Q_T(t)\) at several \(T\) requires the same founder roster, time origin and branch rule for each horizon, evaluated on a common interval in \(t\).

At the 328 verified binary splits, a future-blind choice between the two observed daughters is implementable. At a one-daughter division, forcing the available daughter to be selected changes that rule; imputing the absent daughter as dead also changes it. Family inclusion can be unknown whenever an unobserved subtree could survive. Repeatedly drawing only paths that reach a recorded survivor would answer a different question.

**No-go for a naive whole-cohort horizon-invariance test at present.** This does not mean no empirical work can ever proceed. The later baseline rosters contain many apparently complete descendant subtrees, but selecting only those subtrees uses future recording information and can condition on division history. An unqualified test of a prospective homogeneous branching model cannot ignore that selection. Replicate and founder-denominator gaps also remain.

The subsequent [fixed-roster bounds analysis](../missing-branch-bounds/README.md) implements conservative ranges over unknown daughters and uncertain family inclusion under explicit timing and observation assumptions. It also quarantines a source-verified simultaneous division/apoptosis annotation. All planned settings are retained; every nonzero-time joint interval includes zero. That follow-up does not change this structural audit's frozen outputs or certify a population null test. Source eligibility and identifiers still need validation.

Even after the observation problem is resolved, rejecting horizon invariance would not uniquely identify inheritance: cell-age effects or other departures from the null can also matter. See the project's separate mathematical audit before choosing an empirical model.

## Corrections and verification history

The [first protocol](protocol-v1.json) and [first-pass result payload](first-pass-results.json) are retained. The first pass grouped episodes by label changes alone, despite the codebook warning that an unchanged label can divide. Version 2 also renews episodes at every division flag and explicitly records incomplete daughters.

Root review found a reporting bug: reading every root from a `defaultdict` inserted empty issue sets and falsely reported zero roots without issues. The preserved first-pass file marks those fields **invalidated** in machine-readable metadata; they are not source findings. The corrected tally is 20 roots without detected issues, including 13 first-frame roots. A dedicated clean-plus-affected fixture checks that regression.

The final 11 fixtures also cover retained-label division, missing daughters, mergers, renames, excess offspring, partial row arrivals/departures and late roots. A later-baseline fixture caught and corrected a boundary-classification problem: an ambiguity at a parent-to-child boundary belongs to the earlier component even when the child begins on that same numbered frame. Repeat construction is deterministic, and source hashes are unchanged. These checks establish implementation consistency, not scientific peer review or complete biological validation.
