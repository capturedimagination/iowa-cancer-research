#!/usr/bin/env python3
"""Exhaustive synthetic verification; reference enumeration/DP do not use formulas.

The reference algorithms and production implementation were written by the same
analyst, separately. They are algorithmically different, not an independent
analyst replication. Reports pin both files and preserve first-run failures.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from fractions import Fraction
from itertools import product
import hashlib
import json
from pathlib import Path
import sys
import lineage_compatibility_bounds as production

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = tuple(product((0, 1, None), repeat=2))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def completions(mask):
    options = [tuple(product(*(range(2) if x is None else (x,) for x in p))) for p in mask]
    yield from product(*options)


def totals(rows):
    a = sum(p[0] for p in rows); b = sum(p[1] for p in rows)
    return a, b, sum(p[0]*p[1] for p in rows)


def sym_dp(mask):
    states = {(0, 0)}
    for pair in mask:
        contributions = {(x+y, x*y) for x, y in next_pair_options(pair)}
        states = {(d+delta, j+joint) for d, j in states for delta, joint in contributions}
    result = defaultdict(list)
    for d, j in states:
        result[d].append(j)
    return sorted((d, min(values), max(values)) for d, values in result.items())


def next_pair_options(pair):
    # Deliberately separate from the closed formulas and greedy witnesses.
    return [(x, y) for x in (0, 1) for y in (0, 1)
            if (pair[0] is None or x == pair[0]) and (pair[1] is None or y == pair[1])]


def verify_witness(mask, witness):
    return len(witness) == len(mask) and all(
        len(w) == 2 and all(y in (0, 1) and (x is None or x == y) for x, y in zip(p, w))
        for p, w in zip(mask, witness))


def graph_fixtures(check):
    results = []
    specifications = [
        ('shared_variable', ('z',), (('z', 0), ('z', 1)), lambda v: True),
        ('absorbing_extinction', ('early', 'late'), (('early', 0), ('late', 1)), lambda v: v['late'] <= v['early']),
        ('parent_child_or', ('parent', 'left', 'right'), (('parent', 0), ('left', 'right')), lambda v: v['parent'] == (v['left'] or v['right'])),
        ('missing_branch_or', ('parent', 'unknown_child'), (('parent', 0), ('unknown_child', 1)), lambda v: v['parent'] == (0 or v['unknown_child'])),
        ('contradictory_known_extinction', ('early', 'late'), (('early', 0), ('late', 1)), lambda v: v['early'] == 0 and v['late'] == 1 and v['late'] <= v['early'])]
    for name, variables, targets, predicate in specifications:
        mask = tuple(tuple(None if isinstance(x, str) else x for x in p) for p in targets)
        feasible = []
        for bits in product((0, 1), repeat=len(variables)):
            values = dict(zip(variables, bits))
            if predicate(values):
                rows = tuple(tuple(values[x] if isinstance(x, str) else x for x in p) for p in targets)
                a, b, j = totals(rows); n = len(rows)
                feasible.append((Fraction(n*j-a*b, n*n), Fraction(4*n*j-(a+b)**2, 4*n*n)))
        if not feasible:
            check(name == 'contradictory_known_extinction', 'unexpected_empty_graph', name)
            results.append({'name': name, 'status': 'INFEASIBLE_DECLARED_LOGIC', 'assignments': 0})
            continue
        bounds = {}
        for index, sym in ((0, False), (1, True)):
            outer = production.endpoints(mask, sym)
            inner = min(v[index] for v in feasible), max(v[index] for v in feasible)
            check(outer[0] <= inner[0] <= inner[1] <= outer[1], 'graph_outer_containment', name)
            bounds['symmetrized' if sym else 'ordered'] = {'mask': list(map(str, outer)), 'logical': list(map(str, inner))}
        if name == 'shared_variable':
            check(bounds['ordered'] == {'mask': ['-1/4', '1/4'], 'logical': ['0', '0']}, 'shared_variable_exact', name)
        results.append({'name': name, 'status': 'FEASIBLE_LOGICAL_FIXTURE', 'assignments': len(feasible), 'bounds': bounds})
    return results


def run(plan_path, freeze_path, output):
    plan = json.loads(plan_path.read_text()); freeze = json.loads(freeze_path.read_text())
    if output.exists():
        raise FileExistsError('First reports are immutable; choose a fresh path')
    if digest(plan_path) != freeze['protocol_sha256'] or not plan['status'].startswith('FROZEN'):
        raise ValueError('Frozen verification plan mismatch')
    for path, expected in freeze['implementation_sha256'].items():
        if digest(ROOT/path) != expected:
            raise ValueError('Implementation hash mismatch: '+path)
    report = {'status': 'STARTED', 'created_utc': datetime.now(timezone.utc).isoformat(),
              'protocol_sha256': digest(plan_path), 'freeze_sha256': digest(freeze_path),
              'implementation_sha256': freeze['implementation_sha256'], 'counts': {},
              'source_data_read': False, 'random_numbers_used': False}
    counts = Counter()
    def check(condition, kind, context):
        counts[kind] += 1
        if not condition:
            raise AssertionError(json.dumps({'kind': kind, 'context': context}))
    try:
        for n in range(5):
            for mask in product(PATTERNS, repeat=n):
                counts['masks'] += 1
                by_d = defaultdict(list); by_a = defaultdict(list)
                sym_values = []; ordered_values = []
                for rows in completions(mask):
                    counts['completed_assignments'] += 1
                    a, b, j = totals(rows)
                    by_d[a+b].append(j); by_a[a].append(n*j-a*b)
                    if n:
                        sym_values.append(Fraction(4*n*j-(a+b)**2, 4*n*n))
                        ordered_values.append(Fraction(n*j-a*b, n*n))
                fixed_sym = production.sym_fixed(mask); fixed_ordered = production.ordered_fixed(mask)
                check(fixed_sym == sorted((d, min(v), max(v)) for d, v in by_d.items()), 'fixed_D_enumeration', mask)
                check(fixed_ordered == sorted((a, min(v), max(v)) for a, v in by_a.items()), 'fixed_A_enumeration', mask)
                check(fixed_sym == sym_dp(mask), 'fixed_D_dynamic_program', mask)
                for d, lo, hi in fixed_sym:
                    for maximize, expected in ((False, lo), (True, hi)):
                        witness = production.sym_witness(mask, d, maximize); a, b, j = totals(witness)
                        check(verify_witness(mask, witness) and a+b == d and j == expected, 'sym_witness', mask)
                for a, lo, hi in fixed_ordered:
                    for maximize, expected in ((False, lo), (True, hi)):
                        witness = production.ordered_witness(mask, a, maximize); aa, b, j = totals(witness)
                        check(verify_witness(mask, witness) and aa == a and n*j-a*b == expected, 'ordered_witness', mask)
                if not n:
                    check(production.endpoints(mask) is None and production.endpoints(mask, False) is None, 'empty_undefined', mask)
                    continue
                bounds = {True: production.endpoints(mask), False: production.endpoints(mask, False)}
                for sym, values in ((True, sym_values), (False, ordered_values)):
                    check(bounds[sym] == (min(values), max(values)), 'global_exact_endpoints', mask)
                for flips in product((False, True), repeat=n):
                    relabelled = tuple(p[::-1] if flip else p for p, flip in zip(mask, flips))
                    check(production.endpoints(relabelled) == bounds[True], 'within_pair_sym_invariance', mask)
                check(production.endpoints(tuple(p[::-1] for p in mask), False) == bounds[False], 'global_ordered_swap_invariance', mask)
                for i, pair in enumerate(mask):
                    for j, bit in enumerate(pair):
                        if bit is None:
                            for value in (0, 1):
                                refined = [list(p) for p in mask]; refined[i][j] = value
                                for sym in (True, False):
                                    lo, hi = production.endpoints(refined, sym)
                                    check(bounds[sym][0] <= lo <= hi <= bounds[sym][1], 'one_bit_refinement_nesting', mask)
                if all(x is not None for p in mask for x in p):
                    check(all(lo == hi for lo, hi in bounds.values()), 'complete_data_collapse', mask)
                if all(x is None for p in mask for x in p):
                    check(bounds[True] == (Fraction(-1, 4), Fraction((n*n)//4, n*n)), 'all_unknown_sym_control', mask)
        gap = ((1, None), (0, 1), (0, 0))
        actual = {Fraction(3*totals(r)[2]-totals(r)[0]*totals(r)[1], 9) for r in completions(gap)}
        check(actual == {Fraction(-1, 9), Fraction(1, 9)}, 'zero_interval_gap', gap)
        report['logical_fixtures'] = graph_fixtures(check)
        check(counts['masks'] == 7381 and counts['completed_assignments'] == 69905, 'frozen_roster_counts', dict(counts))
        report['status'] = 'PASS'
        report['interpretation'] = 'Exact synthetic mask bounds and witnesses verified; no source outcomes, sampling inference, or novelty claim. Logical fixtures do not prove full-history attainability.'
    except Exception as exc:
        report['status'] = 'FAIL'; report['failure_class'] = type(exc).__name__; report['failure'] = str(exc)
        raise
    finally:
        report['counts'] = dict(counts)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open('x') as f:
            json.dump(report, f, indent=2); f.write('\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--protocol', required=True, type=Path)
    parser.add_argument('--freeze', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    report = run(args.protocol, args.freeze, args.output)
    print(json.dumps({'status': report['status'], 'counts': report['counts']}, indent=2))
