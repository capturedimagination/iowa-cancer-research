#!/usr/bin/env python3
"""Independent post-first-run exact-mask audit; no source data or random draws.

The reference is a set-valued dynamic program over attainable (A,B,J) totals.
It uses no production helper, bound formula, or production witness to construct
its state set. Production is imported only as the system under test.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import importlib.util
import json
from math import comb
from pathlib import Path
import platform
import sys

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = ((0, 0), (0, 1), (0, None), (1, 0), (1, 1),
            (1, None), (None, 0), (None, 1), (None, None))
# Literal complete-pair contributions: first positives, second positives, joint.
TRANSITIONS = (
    ((0, 0, 0),), ((0, 1, 0),), ((0, 0, 0), (0, 1, 0)),
    ((1, 0, 0),), ((1, 1, 1),), ((1, 0, 0), (1, 1, 1)),
    ((0, 0, 0), (1, 0, 0)), ((0, 1, 0), (1, 1, 1)),
    ((0, 0, 0), (0, 1, 0), (1, 0, 0), (1, 1, 1)))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def compositions(total, slots):
    if slots == 1:
        yield (total,)
    else:
        for first in range(total + 1):
            for tail in compositions(total - first, slots - 1):
                yield (first,) + tail


def reference_states(counts):
    reachable = {(0, 0, 0)}
    for multiplicity, options in zip(counts, TRANSITIONS):
        for _ in range(multiplicity):
            following = set()
            for a, b, j in reachable:
                for da, db, dj in options:
                    following.add((a + da, b + db, j + dj))
            reachable = following
    return reachable


def witness_totals(mask, witness):
    if len(mask) != len(witness):
        raise AssertionError('Witness roster length changed')
    a = b = j = 0
    for observed, completed in zip(mask, witness):
        if len(completed) != 2:
            raise AssertionError('Witness pair length changed')
        x, y = completed
        if type(x) is not int or type(y) is not int or x not in (0, 1) or y not in (0, 1):
            raise AssertionError('Witness is not binary')
        if any(o is not None and o != c for o, c in zip(observed, completed)):
            raise AssertionError('Witness changed an observed bit')
        a += x
        b += y
        j += x * y
    return a, b, j


def run(protocol_path, freeze_path, output):
    if output.exists():
        raise FileExistsError('Preserve previous reports; supply a fresh path')
    plan = json.loads(protocol_path.read_text())
    freeze = json.loads(freeze_path.read_text())
    if plan['sizes'] != [5, 6] or plan['expected_count_vectors'] != {'5': 1287, '6': 3003}:
        raise ValueError('Unexpected frozen roster')
    if digest(protocol_path) != freeze['protocol_sha256']:
        raise ValueError('Frozen protocol hash mismatch')
    for relative, expected in freeze['input_sha256'].items():
        if digest(ROOT / relative) != expected:
            raise ValueError('Pinned input mismatch: ' + relative)
    spec = importlib.util.spec_from_file_location('bounds_under_test', ROOT / 'scripts/lineage_compatibility_bounds.py')
    production = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(production)
    report = {
        'status': 'STARTED', 'created_utc': datetime.now(timezone.utc).isoformat(),
        'timing': 'Additional independent verification designed after the original N=0..4 PASS report; frozen before this N=5..6 run.',
        'protocol_sha256': digest(protocol_path), 'freeze_sha256': digest(freeze_path),
        'input_sha256': freeze['input_sha256'],
        'environment': {'python': platform.python_version(), 'implementation': platform.python_implementation()},
        'source_data_read': False, 'random_numbers_used': False,
        'reference': 'Independent exact integer state DP in (A,B,J), followed by rational objective evaluation.',
        'counts_by_n': {}, 'checks': {}, 'first_failure': None}
    checks = Counter()
    context = None

    def check(ok, label):
        checks[label] += 1
        if not ok:
            raise AssertionError(label)

    try:
        check(reference_states((0,) * 9) == {(0, 0, 0)}, 'reference_empty_control')
        for index, (pattern, choices) in enumerate(zip(PATTERNS, TRANSITIONS)):
            independent = {(x, y, x * y) for x in (0, 1) for y in (0, 1)
                           if all(o is None or o == c for o, c in zip(pattern, (x, y)))}
            check(set(choices) == independent, 'reference_transition_table_control')
        for n in plan['sizes']:
            nc = Counter()
            for counts in compositions(n, 9):
                context = {'n': n, 'pattern_counts': list(counts)}
                nc['count_vectors'] += 1
                states = reference_states(counts)
                nc['attainable_state_entries'] += len(states)
                nc['maximum_states_in_one_vector'] = max(nc['maximum_states_in_one_vector'], len(states))
                by_a = defaultdict(list)
                by_d = defaultdict(list)
                for a, b, j in states:
                    by_a[a].append(n * j - a * b)
                    by_d[a + b].append(j)
                fixed_a = sorted((a, min(values), max(values)) for a, values in by_a.items())
                fixed_d = sorted((d, min(values), max(values)) for d, values in by_d.items())
                expected_ordered = (min(Fraction(n*j-a*b, n*n) for a,b,j in states),
                                    max(Fraction(n*j-a*b, n*n) for a,b,j in states))
                expected_sym = (min(Fraction(4*n*j-(a+b)**2, 4*n*n) for a,b,j in states),
                                max(Fraction(4*n*j-(a+b)**2, 4*n*n) for a,b,j in states))
                canonical = tuple(pair for pair, copies in zip(PATTERNS, counts) for _ in range(copies))
                # Fixed nonadaptive row-order checks, including witness construction.
                for order_name, mask in (('canonical', canonical), ('reversed', canonical[::-1])):
                    context['row_order'] = order_name
                    check(production.sym_fixed(mask) == fixed_d, 'fixed_D_exact_state_dp')
                    check(production.ordered_fixed(mask) == fixed_a, 'fixed_A_exact_state_dp')
                    check(production.endpoints(mask, True) == expected_sym, 'sym_global_rational_endpoint')
                    check(production.endpoints(mask, False) == expected_ordered, 'ordered_global_rational_endpoint')
                    for d, lo, hi in fixed_d:
                        for maximize, expected in ((False, lo), (True, hi)):
                            totals = witness_totals(mask, production.sym_witness(mask, d, maximize))
                            a, b, j = totals
                            check(totals in states and a + b == d and j == expected, 'fixed_D_witness')
                    for a, lo, hi in fixed_a:
                        for maximize, expected in ((False, lo), (True, hi)):
                            totals = witness_totals(mask, production.ordered_witness(mask, a, maximize))
                            aa, b, j = totals
                            check(totals in states and aa == a and n*j-aa*b == expected, 'fixed_A_witness')
                # Global relabelling maps state triples directly; no reference formulas.
                swapped = tuple((y, x) for x, y in canonical)
                check(production.endpoints(swapped, False) == expected_ordered, 'global_sister_swap_ordered')
                check(production.endpoints(swapped, True) == expected_sym, 'global_sister_swap_sym')
                if all(x is not None for pair in canonical for x in pair):
                    check(len(states) == 1 and expected_ordered[0] == expected_ordered[1]
                          and expected_sym[0] == expected_sym[1], 'complete_data_collapse')
                report['counts_by_n'][str(n)] = dict(nc)
            check(nc['count_vectors'] == comb(n + 8, 8) == plan['expected_count_vectors'][str(n)],
                  'complete_count_vector_roster')
        report['status'] = 'PASS'
        report['interpretation'] = ('Exact arithmetic matches the production fixed-margin formulas, global endpoints and all requested witnesses on the frozen roster. '
                                    'This establishes a finite independent-mask computation check, not biological attainability, population coverage or novelty.')
    except Exception as exc:
        report['status'] = 'FAIL'
        report['first_failure'] = {'class': type(exc).__name__, 'message': str(exc), 'context': context}
    finally:
        report['checks'] = dict(checks)
        report['completed_utc'] = datetime.now(timezone.utc).isoformat()
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open('x') as handle:
            json.dump(report, handle, indent=2, allow_nan=False)
            handle.write('\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--freeze', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = run(args.protocol, args.freeze, args.output)
    print(json.dumps({'status': result['status'], 'counts_by_n': result['counts_by_n'],
                      'checks': result['checks'], 'first_failure': result['first_failure']}, indent=2))
    sys.exit(0 if result['status'] == 'PASS' else 1)
