# Independent graph verification

**PASS within the declared structural scope.** A separate XML parser, decimal timing calculations, directed-cycle traversal and component reconstruction agree with the production graph for all seven sheets, 4,678 pair rows and 9,356 recorded child observations. No production algorithm was imported. The independent source reference was saved before production outputs were inspected.

The [final comparison](independent-comparison-v3.json) records 1,603,255 field, set and bookkeeping checks, with zero mismatches. This count is verification work, not a number of independent biological observations. The maximum absolute numeric difference is 2.842170943040401e-14 source time units, below the comparison tolerance of 1e-9. The frozen arithmetic-consistency rule remains 1e-6; neither tolerance asserts imaging precision.

## Coverage

The independent reconstruction checks literal source strings and cell coordinates; formula and XML provenance; namespace and row/side identity; external references; parent assertions and their availability states; exclusive parent fate; birth-time residuals; repeated mother/grandmother annotations; raw and consistent edge sets; cyclic strongly connected components; all component and conservative related-group memberships; and successor uncertainty. It also verifies the seven-file production manifest, hashes, source read checks and matching public/private summaries.

The source parser uses `Decimal` calculations and the graph implementation uses iterative Kosaraju traversal plus undirected flood-fill components. These implementations are separate from the producer. Issue-code naming was **not** independently reimplemented: its counts, affected-observation bookkeeping and group issue-code unions are checked internally, while the underlying identity, fate and chronology semantics are checked independently. See the category ledger for the precise comparison coverage; this is not a claim that every free-text field or every producer-specific diagnostic was independently regenerated.

Four absence-of-mask assertions are explicit: unknown recording end, unresolved event boundary, unresolved continuous tracking and no death-at-query absorbing mask. The tracking and absorbing-mask checks were added after the first comparison and are labeled accordingly. They do not construct an outcome mask.

## Preserved first attempts

1. The first pinned source reader stopped on an extra formatted header cell, R1 in rap1. It has no text, formula or child XML elements. The reader had incorrectly required the header coordinate set to contain no extra cells. The [failure](independent-reference.json.failure.json), original pin and exact [v1 source](verification-history/verify_kuchen_graph-v1.py) remain. Three completed control-sheet reconstructions survive in the excluded partial artifact.
2. The narrowly revised parser retains genuinely empty extra header cells and unmapped row cells, while rejecting unexpected nonempty or formula headers. The [v2 pin](independent-code-pin-v2.json) preceded the first complete [reference](independent-reference-v2.json). Its 23 synthetic checks passed. This reference has not been regenerated or altered.
3. The [first comparison](independent-comparison-first.json) reported FAIL: 9,356 checks expected a null event-boundary value, whereas production correctly used the frozen token `unresolved`. All other 1,575,187 checks matched. This was an adapter expectation error, not a graph discrepancy. The exact [v2 source](verification-history/verify_kuchen_graph-v2.py) is archived. That historical command returned process exit 0 despite the recorded FAIL; the current harness returns a failing exit status when its result is FAIL.
4. The comparison-only revision corrected the boundary token, added the two expressly labeled mask-support assertions and a numeric-difference diagnostic, and separated the immutable reference pin from the current comparator pin. The [v3 pin](independent-comparator-pin-v3.json) preceded the successful rerun. All 24 current synthetic checks passed. Parser and graph-construction functions are unchanged from the saved v2 reference implementation.

The [machine-readable review](independent-review.json) records hashes, stages and scope. Original workbooks, expanded graphs, partial reference records and comparison details remain in the excluded source archive. Public files contain aggregate verification, original code and provenance.

## Reuse

Run from the project root with Python 3.12 or later; the verifier uses only the standard library. The following comparison reuses the immutable v2 reference and writes fresh outputs; substitute unused output names when reproducing it.

```sh
kuchen_graph=research/treatment-discovery/lineage-audit-2026-11-10/kuchen-source-audit/graph-audit
kuchen_derived=research/treatment-discovery/sources/lineage-2026-11-10/kuchen-graph-2026-11-10/derived
python3 -B scripts/verify_kuchen_graph.py compare \
  --pin "$kuchen_graph/independent-comparator-pin-v3.json" \
  --reference-code-pin "$kuchen_graph/independent-code-pin-v2.json" \
  --reference "$kuchen_derived/independent-reference-v2.json" \
  --production-directory "$kuchen_derived/first" \
  --production-summary "$kuchen_graph/results.json" \
  --output "$kuchen_graph/independent-comparison-replay.json" \
  --private-output "$kuchen_derived/independent-comparison-replay.json"
```

To replay an earlier implementation, restore its archived source to `scripts/verify_kuchen_graph.py` **in an isolated project copy**, retaining the matching protocol, schema, source inputs and code pin. Do not execute the archived script in place: its project-root resolution expects the `scripts/` location. Use fresh output names and preserve the expected first failure. The current program requires private outputs beneath the frozen excluded prefix and refuses existing output paths.

## What this does not establish

Agreement verifies the declared observation graph and its source assertions. It does not establish uninterrupted tracking, exact event-time boundaries, complete original founder families, future-independent export eligibility, or dose-specific metadata repairs. No scientific lag, subtree survival mask, covariance, hazard, predictive score or population test was calculated. A subsequent compatibility analysis requires its own frozen roster, observation assumptions and endpoint definitions.
