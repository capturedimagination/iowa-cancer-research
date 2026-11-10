# Exact covariance endpoints with unknown outcomes

**The first exhaustive synthetic verification passed.** The formulas and constructive endpoint witnesses agreed with every completion of all 7,381 ordered mask sequences of length zero through four: 69,905 completed assignments. These are exact integer/rational checks, not Monte Carlo estimates. No experimental survival outcomes were extracted.

This provides a reusable calculation for a fixed roster of paired binary outcomes when some entries remain unknown. It avoids assuming that a lost cell died or that missing outcomes are random. Whether this particular formulation or biological application is new remains unestablished; missing-data bounds and covariance optimization have extensive prior art. See the [derivation and source review](../compatibility-proposal.md). That proposal is preserved as the pre-run record; its then-unrun mathematical checks are now documented here, while its empirical plan remains unexecuted.

## What is bounded

For N completed pairs, let A and B be the two positive marginal counts, J the joint-positive count and D=A+B. The two separate targets are:

```text
ordered covariance:      J/N - A*B/N^2
symmetrized covariance:  J/N - D^2/(4*N^2)
```

The second is invariant to swapping the two sisters within any pair. It is covariance under an empirical distribution that randomly orients each pair; it does not create extra independent observations. The formulas bound a finite recorded roster. They are not confidence intervals, an unbiased population estimate, a causal inheritance test, or a clinical prediction.

The production implementation evaluates exact extrema at every feasible marginal count and returns rational endpoints. It runs in O(N) time after a single count pass. It currently stores the fixed-margin results, so its working storage is O(N); the mathematical endpoint scan can use constant extra storage. Both targets are undefined for N=0. For N=1, ordered covariance is zero, while the symmetrized target may equal −1/4.

## Verification

The [plan](protocol.json), [code hashes](freeze-record.json), and first [complete result](verification-first.json) were pinned or preserved before any corrections. No first-run failure occurred. The root analyst wrote both the formula implementation and different reference algorithms; that is algorithmic separation, not independent analyst replication.

| Check | Completed comparisons |
|---|---:|
| Fixed-D joint-count extrema against enumeration | 7,381 masks |
| Fixed-A ordered extrema against enumeration | 7,381 masks |
| Fixed-D extrema against contribution-state dynamic programming | 7,381 masks |
| Symmetrized endpoint witnesses | 52,898 |
| Ordered endpoint witnesses | 33,830 |
| Global exact endpoints | 14,760 |
| Arbitrary within-pair relabelling, symmetrized target | 111,150 |
| Global swap, ordered target | 7,380 |
| One-bit refinement endpoint nesting | 76,272 |

Complete-data collapse, all-unknown extrema, empty-roster handling and a discrete zero-gap example also passed. The report retains all individual check-category counts.

A separately authored [independent check and algebra review](independent-review.md) then passed all 4,290 distinct nine-pattern count vectors with N=5 or6. Its integer-state dynamic program recovered 51,818 attainable `(A,B,J)` states across those fixtures and checked 132,132 endpoint witnesses in canonical and reversed row order. This follow-up was planned after seeing the first test pass and frozen before its own run. Count-vector coverage does not mean every literal row permutation was separately enumerated; row permutations leave the targets unchanged. Both first verification runs passed without code corrections.

The five small logical fixtures cover shared variables, absorbing extinction, parent-child OR, an unknown daughter branch and contradictory asserted observations. They enumerate declared Boolean assignments, not biological event histories. Contradictory observations correctly produce an infeasible logical set rather than a fabricated numeric bound.

## Why lineage constraints matter

The independent-mask endpoints are attained when every unknown bit may vary separately. Actual lineage records can share the same uncertain descendant or constrain later survival by earlier extinction.

For example, consider `(Z,0),(Z,1)` with one shared unknown Z. Its ordered covariance is always zero. If the two appearances of Z are incorrectly treated as independent, the interval expands to `[−1/4,+1/4]`. Thus the simple endpoints remain valid outer bounds under sound additional constraints, but their witnesses need not describe one possible lineage history.

A second example, `(1,?),(0,1),(0,0)`, has ordered covariance either −1/9 or +1/9. Zero lies inside the enclosing interval but is not attainable. Report endpoint ranges precisely; an interval containing zero does not prove a zero-valued completion exists.

Even a positive lower endpoint would establish only a finite-roster sign property under the declared observation assumptions. Shared environment, calendar context and export selection can still explain dependence.

## Reproduce

From the repository root, using standard-library Python:

```sh
python3 -B scripts/verify_lineage_compatibility.py \
  --protocol research/treatment-discovery/lineage-audit-2026-11-10/kuchen-source-audit/graph-audit/compatibility-bounds/protocol.json \
  --freeze research/treatment-discovery/lineage-audit-2026-11-10/kuchen-source-audit/graph-audit/compatibility-bounds/freeze-record.json \
  --output tmp/compatibility-reproduced.json
```

Use a new output filename each time. The command checks implementation hashes, reads no source data and uses no random numbers. The scientific comparison counts and logical-fixture results must match the first report; timestamps differ.

An empirical application still requires a separately frozen roster, elapsed lag, source timing interpretation, observation model and shared-branch constraints. The [structural graph protocol](../protocol.json) deliberately calculates none of those outcomes.
