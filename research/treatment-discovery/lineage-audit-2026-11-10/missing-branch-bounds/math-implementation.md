# Joint optimization of shared-path bounds

Implemented November 10, 2026 under the [joint refinement plan](joint-refinement-plan.json). **This is a methodological refinement specified after the primary empirical outer bounds were inspected.** It is not a prospectively chosen independent empirical test. No empirical joint outcomes were used to implement or verify this module.

The new [joint solver](../../../../scripts/lineage_joint_bounds.py) preserves the original marginal solver. Its `joint_bounds(rows)` input contains `(lower, upper, status_early, status_late)` for each member of one fixed recorded roster. Status values are 0, 1 or `None`. Both horizon means use the same row probability at the common evaluation time.

## Optimization and proof

Permitted selection states are `00`, `10` and `11`. Filter them by both supplied statuses. An upper probability bound of zero permits only `00`; incompatible known statuses raise an error. For selected rows with a zero lower bound, the optimization uses the closed relaxation and can return an unattained infimum. The caller must supply endpoint compatibility, as in the primary driver.

At fixed positive counts `N1>=N2>0`, the contrast is

```text
sum_i (f_late_i/N2 - f_early_i/N1) p_i.
```

The per-row minimizing costs for states `00,10,11` are respectively `0`, `-upper_i/N1`, and `(1/N2-1/N1)*lower_i`. Maximization uses `0`, `-lower_i/N1`, and `(1/N2-1/N1)*upper_i`. This respects the same probability appearing in both means; separate marginal extrema do not impose that constraint.

Rows with one permitted state have fixed counts and their endpoint sums are aggregated. For each remaining row, subtract its minimum possible early and late counts to form nonnegative count increments. A Boolean dynamic program enumerates every reachable total pair with nonempty later selection.

For each total pair, a cost dynamic program traverses the variable rows. At each permitted state, it adds that state's cost to the best previous cost at the remaining count increments. Induction over the rows shows that the final entry is the minimum or maximum over every allowed assignment at that total pair. Adding fixed-row costs and optimizing over all feasible pairs gives the global infimum and supremum of the stated relaxation. No selected-count pair is sampled or discarded.

The optimization is exact as a discrete algorithm, using ordinary floating-point costs with the frozen `1e-12` numerical tolerance. It does not provide certified outward rounding. Its bounds are sharp for the **closed common-probability, interval and nested-selection relaxation**. Missing branch constraints, cross-time constraints and source uncertainty can still make these bounds wider than the set of complete biological trees.

## API and safeguards

The return includes `lower`, `upper`, `defined_for_some_completion`, `zero_denominator_possible`, every `feasible_count_pairs` entry and extrema's count witnesses. If no positive later denominator is possible, bounds are `None`. A possible empty later selection is reported separately even when other completions define the contrast.

If the only positive count pairs have `N1=N2`, there is only one possibly selected founder, or every potentially selected row has the same fixed probability, the contrast is exactly zero. An all-zero upper bound instead implies no possible selection; it does not create a zero-valued defined contrast.

Candidate count pairs form a leading NumPy array dimension. Batching bounds estimated DP working-array storage, with a default 64 MiB budget. A separate default limit of 500 million estimated state updates covers feasibility and cost propagation. The arrays' limit is not a claim about total process memory, input records or Python metadata. Resource-limit failures raise explicitly; callers must not silently omit those cases. A pre-empirical implementation revision added the feasibility-work guard before the independent review.

## Verification before empirical joint execution

The module's **17 synthetic fixtures** pass, including fixed negative and positive contrasts, shared intervals, zero-upper exclusions, undefined selection, equal fixed values, a single possible founder, resource failures and one-candidate batches matching a full batch.

The separate [independent verification](joint-verification.json) compared **4,495 exact rational cases**, with **8,961 solver calls** including reversed row order. Extrema, feasible counts and undefined flags matched; maximum arithmetic discrepancy was `1.6653345369377348e-16`. The fixed forest control used the first 12 founders from each of three previously defined 300-founder cases, yielding **36 distinct founders**, not a new 900-founder joint validation. All **560 defined contrasts** contained the complete-tree truth; **160 undefined truth cases** were retained among 720 combinations. No failures were reported. This validates computation and containment under the specified controls, not a biological mechanism or population test.

Final module SHA-256: `f24fe1d3a99d2abfd3fdb453d74b87e2b28ad44017845cd3c8ac3b429984802d`. The [JSON implementation record](math-implementation.json) pins the plan, code and independent checks. Run synthetic fixtures with `python scripts/lineage_joint_bounds.py` in the project's NumPy environment. The module reads no empirical files; empirical application belongs to the separate driver and retains all fixed cases.
