#!/usr/bin/env python3
"""Exact deterministic checks of a conservative finite-roster relaxation.

No empirical files, random draws, fitted rates or other project code are used.
"""
from datetime import datetime, timezone
from fractions import Fraction as F
from itertools import product
from pathlib import Path
import hashlib
import json

BASE = Path(__file__).resolve().parent


def normalize(status, lower, upper, endpoint=False):
    status, lower, upper = list(status), list(map(F, lower)), list(map(F, upper))
    if not len(status) == len(lower) == len(upper):
        raise ValueError("Unequal row counts")
    for i, (s, a, b) in enumerate(zip(status, lower, upper)):
        if s not in (0, 1, None) or not 0 <= a <= b <= 1:
            raise ValueError("Invalid status or interval")
        # A finite surviving family implies positive tagged survival at t<=T.
        if s == 1 and b == 0:
            raise ValueError("Selected family has zero possible tagged survival")
        if b == 0:
            status[i] = 0
        if endpoint:
            if status[i] == 0:
                if a > 0:
                    raise ValueError("Endpoint extinction conflicts with positive lower bound")
                lower[i] = upper[i] = F(0)
            elif status[i] is None and a > 0:
                status[i] = 1
    return status, lower, upper


def sorting_bounds(status, lower, upper, endpoint=False):
    s, a, b = normalize(status, lower, upper, endpoint)
    mandatory = [i for i, v in enumerate(s) if v == 1]
    optional = [i for i, v in enumerate(s) if v is None]
    n = len(mandatory)
    if not n and not optional:
        return None
    low = sorted(a[i] for i in optional)
    high = sorted((b[i] for i in optional), reverse=True)
    low_sum, high_sum = sum((a[i] for i in mandatory), F(0)), sum((b[i] for i in mandatory), F(0))
    values = []
    for k in range(0 if n else 1, len(optional) + 1):
        values.append(((low_sum + sum(low[:k], F(0))) / (n+k),
                       (high_sum + sum(high[:k], F(0))) / (n+k)))
    return min(x[0] for x in values), max(x[1] for x in values)


def selection_vectors(status):
    return product(*[(0, 1) if s is None else (s,) for s in status])


def exhaustive_bounds(status, lower, upper, endpoint=False):
    # Closed rectangle: selected p=0 may represent an unattained infimum.
    s, a, b = normalize(status, lower, upper, endpoint)
    values = []
    for selected in selection_vectors(s):
        count = sum(selected)
        if not count:
            continue
        for probabilities in product(*[tuple(set((x, y))) for x, y in zip(a, b)]):
            values.append(sum((f*p for f, p in zip(selected, probabilities)), F(0))/count)
    return None if not values else (min(values), max(values))


def display(bounds):
    return None if bounds is None else [str(x) for x in bounds]


def run():
    controls = [
        ("mandatory", [1, 1], ["1/4", "3/4"], ["1/2", "1"], False, (F(1, 2), F(3, 4))),
        ("extinct_later_alive_earlier", [0, 1], ["1", "1/4"], ["1", "1/2"], False, (F(1, 4), F(1, 2))),
        ("optional_low_and_high", [1, None, None], ["1/2", "0", "3/4"], ["1/2", "1/4", "1"], False, (F(1, 4), F(3, 4))),
        ("optional_only", [None, None], ["1/4", "3/4"], ["1/2", "1"], False, (F(1, 4), F(1))),
        ("initial_alive", [1, None], ["1", "1"], ["1", "1"], False, (F(1), F(1))),
        ("selected_zero_infimum", [1], ["0"], ["1/2"], False, (F(0), F(1, 2))),
        ("endpoint_promotes_positive_lower", [None, None], ["1/4", "0"], ["1/2", "1"], True, (F(1, 8), F(3, 4))),
        ("zero_upper_cannot_be_selected", [None, 1], ["0", "1/2"], ["0", "1/2"], False, (F(1, 2), F(1, 2))),
        ("empty_selection", [0, 0], ["1", "0"], ["1", "1/2"], False, None),
    ]
    details, failures = [], []
    for name, status, lower, upper, endpoint, expected in controls:
        got = sorting_bounds(status, lower, upper, endpoint)
        exhaustive = exhaustive_bounds(status, lower, upper, endpoint)
        passed = got == exhaustive == expected
        details.append({"name": name, "sorting": display(got), "exhaustive": display(exhaustive), "expected": display(expected), "passed": passed})
        if not passed:
            failures.append(name)
    for name, status, lower, upper, endpoint in [
        ("inconsistent_endpoint_extinction", [0], ["1/4"], ["1/2"], True),
        ("inconsistent_selected_zero_upper", [1], ["0"], ["0"], False),
    ]:
        try:
            sorting_bounds(status, lower, upper, endpoint)
            passed = False
        except ValueError:
            passed = True
        details.append({"name": name, "invalid_input_rejected": passed})
        if not passed:
            failures.append(name)

    protocol = json.loads((BASE/'verification-protocol.json').read_text())
    pairs = protocol['nested_horizon_grid']['per_row_status_pairs']
    intervals = [(F(a), F(b)) for a, b in protocol['nested_horizon_grid']['intervals_in_row_order']]
    nested_case_count = nested_completion_count = empty_later_case_count = 0
    for size in protocol['nested_horizon_grid']['roster_sizes']:
        lower, upper = zip(*intervals[:size])
        for pair_vector in product(pairs, repeat=size):
            nested_case_count += 1
            early, late = zip(*pair_vector)
            bound_early = sorting_bounds(early, lower, upper)
            bound_late = sorting_bounds(late, lower, upper)
            feasible = 0
            if bound_early is not None and bound_late is not None:
                marginal = (bound_late[0]-bound_early[1], bound_late[1]-bound_early[0])
                max_early = sum(s != 0 for s in early)
                min_positive_late = max(1, sum(s == 1 for s in late))
                radius = 1-F(min_positive_late, max_early)
                tightened = (max(marginal[0], -radius), min(marginal[1], radius))
                for first in selection_vectors(early):
                    for second in selection_vectors(late):
                        if not sum(second) or any(b > a for a, b in zip(first, second)):
                            continue
                        for probabilities in product(*[(a, b) for a, b in intervals[:size]]):
                            feasible += 1
                            first_mean = sum((f*p for f, p in zip(first, probabilities)), F(0))/sum(first)
                            second_mean = sum((f*p for f, p in zip(second, probabilities)), F(0))/sum(second)
                            delta = second_mean-first_mean
                            if not (marginal[0] <= delta <= marginal[1] and tightened[0] <= delta <= tightened[1]):
                                failures.append({"kind": "nested_containment", "size": size, "statuses": pair_vector, "delta": str(delta)})
            if not feasible:
                empty_later_case_count += 1
            nested_completion_count += feasible
    # Shared probabilities make one selected founder's contrast identically zero.
    single = sorting_bounds([1], [F(1, 4)], [F(3, 4)])
    single_marginal = (single[0]-single[1], single[1]-single[0])
    assert single_marginal == (F(-1, 2), F(1, 2))
    positive, negative = F(1)-(F(1)+F(1, 4))/2, F(1, 4)-(F(1)+F(1, 4))/2
    assert positive == F(3, 8) and negative == F(-3, 8)
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    return {
        "version": 1, "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if not failures else "FAIL",
        "protocol_sha256": sha(BASE/'verification-protocol.json'), "code_sha256": sha(Path(__file__)),
        "arithmetic": "Exact fractions; no Monte Carlo or numerical tolerance", "seed": None,
        "controls": details, "nested_status_cases": nested_case_count,
        "nested_probability_selection_combinations_checked": nested_completion_count,
        "nested_status_cases_without_positive_later_selection": empty_later_case_count,
        "nonsharp_example": {"one_founder_selected_at_both_horizons": True, "marginal_subtraction": display(single_marginal), "actual_contrast": "0", "count_tightened_contrast": ["0", "0"]},
        "nested_selection_sign_control": {"positive": str(positive), "negative": str(negative)},
        "failures": failures,
        "scope": "Finite rectangular-closure and nesting verification only; no empirical inference, tree-sharpness proof or sampling-uncertainty calculation"
    }


if __name__ == '__main__':
    result = run()
    (BASE/'verification-results.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k: result[k] for k in ['status', 'nested_status_cases', 'nested_probability_selection_combinations_checked', 'nested_status_cases_without_positive_later_selection', 'failures']}, indent=2))
    raise SystemExit(0 if result['status'] == 'PASS' else 1)
