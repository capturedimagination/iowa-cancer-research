"""Joint finite-roster bounds for a common-probability nested relaxation.

No source files are read. This exact discrete optimization uses floating-point
costs; it is not a stochastic test or a certificate of tree-sharp bounds.
"""
from __future__ import annotations

from math import fsum, isfinite
import numpy as np

STATES = ((0, 0), (1, 0), (1, 1))


def joint_bounds(rows, *, max_working_bytes=64 * 1024 * 1024,
                 max_state_updates=500_000_000):
    """Bound later-minus-earlier means using shared per-row probabilities.

    Rows are (lower, upper, status_early, status_late), statuses 0/1/None.
    Positive later selection is required; unknown selected probabilities may
    approach zero in this closure relaxation. The caller supplies endpoint
    compatibility if t equals a selection horizon. Invalid known statuses
    raise ValueError. Resource guards raise rather than dropping cases.
    """
    if max_working_bytes <= 0 or max_state_updates <= 0:
        raise ValueError("Resource budgets must be positive")
    fixed = {s: [] for s in STATES}
    variable = []
    base_early = base_late = 0
    possible_values = []
    zero_denominator_possible = True
    row_count = 0
    for index, row in enumerate(rows):
        if len(row) != 4:
            raise ValueError(f"Expected four fields in row {index}")
        lo, hi, early, late = row
        lo, hi = float(lo), float(hi)
        if not (isfinite(lo) and isfinite(hi) and 0 <= lo <= hi <= 1):
            raise ValueError(f"Invalid probability interval in row {index}")
        if early not in (0, 1, None) or late not in (0, 1, None):
            raise ValueError(f"Invalid selection status in row {index}")
        allowed = [s for s in STATES
                   if (early is None or early == s[0])
                   and (late is None or late == s[1])
                   and (hi > 0 or s == (0, 0))]
        if not allowed:
            raise ValueError(f"Inconsistent nested selection or zero upper mass in row {index}")
        row_count += 1
        zero_denominator_possible &= any(s[1] == 0 for s in allowed)
        if any(s[0] for s in allowed):
            possible_values.append((lo, hi))
        if len(allowed) == 1:
            state = allowed[0]
            fixed[state].append((lo, hi))
            base_early += state[0]
            base_late += state[1]
        else:
            first = min(s[0] for s in allowed)
            second = min(s[1] for s in allowed)
            base_early += first
            base_late += second
            variable.append((lo, hi, tuple((s, s[0]-first, s[1]-second) for s in allowed)))

    xcap = sum(max(dx for _, dx, _ in v[2]) for v in variable)
    ycap = sum(max(dy for _, _, dy in v[2]) for v in variable)
    shape = (xcap + 1, ycap + 1)
    cells = shape[0] * shape[1]
    # Six float arrays per batch member conservatively cover old/new extrema
    # and a transition temporary; feasibility uses two additional bool arrays.
    overhead_bytes = 2 * cells + 4096
    bytes_per_candidate = 6 * cells * np.dtype(np.float64).itemsize
    available = max_working_bytes - overhead_bytes
    if available < bytes_per_candidate:
        raise MemoryError("Joint-bound DP exceeds working-array budget even at batch size one")
    transitions_per_cell = sum(len(v[2]) for v in variable)
    feasibility_updates = cells * transitions_per_cell
    if feasibility_updates > max_state_updates:
        raise RuntimeError("Joint-bound feasibility DP exceeds state-update budget")

    reachable = np.zeros(shape, dtype=bool)
    reachable[0, 0] = True
    for _, _, choices in variable:
        new = np.zeros(shape, dtype=bool)
        for _, dx, dy in choices:
            new[dx:, dy:] |= reachable[:shape[0]-dx, :shape[1]-dy]
        reachable = new
    coordinates = np.argwhere(reachable)
    candidates = []
    for x, y in coordinates:
        n1, n2 = base_early + int(x), base_late + int(y)
        if n2 > 0:
            if n2 > n1:
                raise AssertionError("Reachable counts violate nesting")
            candidates.append((n1, n2, int(x), int(y)))
    pairs = [[n1, n2] for n1, n2, _, _ in candidates]
    diagnostics = {
        "rows": row_count, "fixed_rows": sum(map(len, fixed.values())),
        "variable_rows": len(variable), "base_selected_counts": [base_early, base_late],
        "increment_grid_shape": list(shape), "feasible_count_pair_count": len(pairs),
        "feasible_count_pairs": pairs, "zero_denominator_possible": bool(zero_denominator_possible),
        "working_array_budget_bytes": int(max_working_bytes),
        "feasibility_state_updates_upper_bound": int(feasibility_updates),
    }
    if not candidates:
        return {**diagnostics, "defined_for_some_completion": False,
                "lower": None, "upper": None, "lower_count_pair": None,
                "upper_count_pair": None, "batch_size": 0,
                "state_updates_upper_bound": int(feasibility_updates)}

    diagonal = [c for c in candidates if c[0] == c[1]]
    active = [c for c in candidates if c[0] != c[1]]
    same_point = (bool(possible_values) and all(lo == hi == possible_values[0][0]
                                               for lo, hi in possible_values))
    if not active or len(possible_values) == 1 or same_point:
        witness = pairs[0]
        return {**diagnostics, "defined_for_some_completion": True,
                "lower": 0.0, "upper": 0.0, "lower_count_pair": witness,
                "upper_count_pair": witness, "batch_size": 0,
                "state_updates_upper_bound": int(feasibility_updates), "shortcut": "identical_means"}

    update_bound = feasibility_updates + len(active) * cells * transitions_per_cell
    if update_bound > max_state_updates:
        raise RuntimeError("Joint-bound DP exceeds state-update budget; no count pair was omitted")
    batch_size = min(len(active), max(1, available // bytes_per_candidate))
    min_value, max_value = (0.0, 0.0) if diagonal else (np.inf, -np.inf)
    min_pair = max_pair = list(diagonal[0][:2]) if diagonal else None
    fixed_10_lo = fsum(x[0] for x in fixed[(1, 0)])
    fixed_10_hi = fsum(x[1] for x in fixed[(1, 0)])
    fixed_11_lo = fsum(x[0] for x in fixed[(1, 1)])
    fixed_11_hi = fsum(x[1] for x in fixed[(1, 1)])
    for start in range(0, len(active), batch_size):
        block = active[start:start+batch_size]
        n1 = np.array([c[0] for c in block], dtype=float)
        n2 = np.array([c[1] for c in block], dtype=float)
        inv1 = 1.0 / n1
        positive = 1.0 / n2 - inv1
        low = np.full((len(block), *shape), np.inf)
        high = np.full((len(block), *shape), -np.inf)
        low[:, 0, 0] = high[:, 0, 0] = 0.0
        for lo, hi, choices in variable:
            next_low = np.full_like(low, np.inf)
            next_high = np.full_like(high, -np.inf)
            for state, dx, dy in choices:
                if state == (0, 0):
                    cost_low = cost_high = np.zeros_like(inv1)
                elif state == (1, 0):
                    cost_low, cost_high = -hi*inv1, -lo*inv1
                else:
                    cost_low, cost_high = lo*positive, hi*positive
                source = (slice(None), slice(0, shape[0]-dx), slice(0, shape[1]-dy))
                target = (slice(None), slice(dx, None), slice(dy, None))
                np.minimum(next_low[target], low[source] + cost_low[:, None, None], out=next_low[target])
                np.maximum(next_high[target], high[source] + cost_high[:, None, None], out=next_high[target])
            low, high = next_low, next_high
        indices = np.arange(len(block))
        xs, ys = np.array([c[2] for c in block]), np.array([c[3] for c in block])
        lows = low[indices, xs, ys] - fixed_10_hi*inv1 + fixed_11_lo*positive
        highs = high[indices, xs, ys] - fixed_10_lo*inv1 + fixed_11_hi*positive
        if not (np.all(np.isfinite(lows)) and np.all(np.isfinite(highs))):
            raise AssertionError("Feasible count pair missing from cost DP")
        imin, imax = int(np.argmin(lows)), int(np.argmax(highs))
        if lows[imin] < min_value:
            min_value, min_pair = float(lows[imin]), list(block[imin][:2])
        if highs[imax] > max_value:
            max_value, max_pair = float(highs[imax]), list(block[imax][:2])
    if min_value > max_value + 1e-12 or min_value < -1-1e-12 or max_value > 1+1e-12:
        raise AssertionError("Invalid joint extrema")
    return {**diagnostics, "defined_for_some_completion": True,
            "lower": float(min_value), "upper": float(max_value),
            "lower_count_pair": min_pair, "upper_count_pair": max_pair,
            "batch_size": int(batch_size), "state_updates_upper_bound": int(update_bound),
            "estimated_working_array_bytes": int(overhead_bytes + batch_size*bytes_per_candidate)}


def self_checks():
    checks = []
    def expect(name, rows, expected, **kwargs):
        value = joint_bounds(rows, **kwargs)
        if expected is None:
            assert not value["defined_for_some_completion"] and value["lower"] is value["upper"] is None
        else:
            assert value["defined_for_some_completion"]
            assert abs(value["lower"]-expected[0]) < 1e-12
            assert abs(value["upper"]-expected[1]) < 1e-12
        checks.append(name)
        return value
    expect("empty", [], None)
    expect("no_later_selection", [(1, 1, 1, 0)], None)
    expect("optional_zero_upper", [(0, 0, None, None)], None)
    expect("single_possible_founder", [(0.1, 0.9, None, None)], (0, 0))
    expect("identical_point_values", [(0.4, 0.4, None, None)]*4, (0, 0))
    expect("different_excluded_value_ignored", [(0.4, 0.4, None, None), (1, 1, 0, 0)], (0, 0))
    expect("shared_intervals", [(0.25, 0.75, None, None)]*2, (-0.25, 0.25))
    expect("known_negative", [(0.25, 0.25, 1, 1), (0.75, 0.75, 1, 0)], (-0.25, -0.25))
    expect("known_positive", [(0.75, 0.75, 1, 1), (0.25, 0.25, 1, 0)], (0.25, 0.25))
    expect("fixed_state_intervals", [(0.25, 0.75, 1, 1), (0, 1, 1, 0)], (-0.375, 0.375))
    value = expect("known_late_forces_early", [(0.25, 0.75, None, 1)], (0, 0))
    assert value["feasible_count_pairs"] == [[1, 1]] and not value["zero_denominator_possible"]
    value = expect("unknown_early_zero_late", [(0.25, 0.75, 0, None)], None)
    assert value["zero_denominator_possible"]
    for name, rows, error, kwargs in [
        ("contradictory_known_statuses", [(0.1, 0.9, 0, 1)], ValueError, {}),
        ("selected_zero_upper_rejected", [(0, 0, 1, None)], ValueError, {}),
        ("memory_guard", [(0.1, 0.9, None, None)]*3, MemoryError, {"max_working_bytes": 1}),
        ("work_guard", [(0.1, 0.9, None, None)]*3, RuntimeError, {"max_state_updates": 1}),
    ]:
        try:
            joint_bounds(rows, **kwargs)
        except error:
            checks.append(name)
        else:
            raise AssertionError(name)
    rows = [(0.25, 0.75, None, None)]*3
    full = joint_bounds(rows)
    batched = joint_bounds(rows, max_working_bytes=5000)
    assert full["lower"] == batched["lower"] and full["upper"] == batched["upper"]
    assert full["feasible_count_pairs"] == batched["feasible_count_pairs"]
    assert batched["batch_size"] == 1
    checks.append("single_candidate_batches_equal_full_batch")
    return {"passed": True, "fixtures": len(checks), "checks": checks,
            "scope": "Synthetic deterministic implementation fixtures; no empirical data"}


if __name__ == "__main__":
    import json
    print(json.dumps(self_checks(), indent=2))
