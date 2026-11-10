#!/usr/bin/env python3
"""Exact finite-record covariance endpoints for independent binary mask completion.

No clinical data, sampling model, graph optimizer, or random numbers. None is an
unknown bit. Bounds are sharp for the independent-mask set; lineage constraints
can make its endpoint witnesses unattainable. See the frozen verification plan.
"""
from collections import Counter
from fractions import Fraction


def checked(mask):
    pairs = tuple(tuple(p) for p in mask)
    if any(len(p) != 2 or any(x not in (0, 1, None) for x in p) for p in pairs):
        raise ValueError('Expected pairs of 0, 1, or None')
    return pairs


def sym_fixed(mask):
    """Return (D, minimum J, maximum J) for every feasible positive-bit total."""
    pairs = checked(mask)
    d = sum(p == (1, 1) for p in pairs)
    e = sum(p in ((0, 1), (1, 0)) for p in pairs)
    f = sum(p in ((1, None), (None, 1)) for p in pairs)
    g = sum(p in ((0, None), (None, 0)) for p in pairs)
    h = sum(p == (None, None) for p in pairs)
    known = 2*d + e + f
    return [(known+k, d+max(0, k-g-h),
             d+min(k, f+h, (k+f)//2)) for k in range(f+g+2*h+1)]


def ordered_fixed(mask):
    """Return (A, minimum K, maximum K), K=N*J-A*B, for every feasible A."""
    pairs = checked(mask); n = len(pairs); c = Counter(pairs)
    a0 = c[1, 0]+c[1, 1]+c[1, None]
    u0, u1, uh = c[None, 0], c[None, 1], c[None, None]
    result = []
    for k in range(u0+u1+uh+1):
        a = a0+k
        lower = ((n-a)*c[1, 1] - a*(c[0, 1]+c[None, 1]+c[0, None]+c[None, None])
                 + a*min(max(k-u0, 0), uh) + n*max(k-u0-uh, 0))
        upper = ((n-a)*(c[1, 1]+c[1, None]) - a*(c[0, 1]+c[None, 1])
                 + n*min(k, u1) + (n-a)*min(max(k-u1, 0), uh))
        result.append((a, lower, upper))
    return result


def endpoints(mask, symmetrized=True):
    pairs = checked(mask); n = len(pairs)
    if n == 0:
        return None
    if symmetrized:
        values = [(4*n*lo-d*d, 4*n*hi-d*d) for d, lo, hi in sym_fixed(pairs)]
        denominator = 4*n*n
    else:
        values = [(lo, hi) for a, lo, hi in ordered_fixed(pairs)]
        denominator = n*n
    return Fraction(min(x[0] for x in values), denominator), Fraction(max(x[1] for x in values), denominator)


def sym_witness(mask, positive_bits, maximize):
    """Construct a completion attaining the fixed-D joint-count endpoint."""
    pairs = checked(mask)
    rows = [[0 if x is None else x for x in p] for p in pairs]
    remaining = positive_bits-sum(sum(p) for p in rows)
    slots = {0: [], 1: [], 2: []}
    for i, p in enumerate(pairs):
        unknown = [j for j, x in enumerate(p) if x is None]
        if len(unknown) == 2:
            slots[2].append(i)
        elif len(unknown) == 1:
            slots[p[1-unknown[0]]].append((i, unknown[0]))
    capacity = len(slots[0])+len(slots[1])+2*len(slots[2])
    if remaining < 0 or remaining > capacity or int(remaining) != remaining:
        raise ValueError('Infeasible D')
    remaining = int(remaining)
    def fill(slot):
        nonlocal remaining
        if remaining:
            rows[slot[0]][slot[1]] = 1
            remaining -= 1
    if maximize:
        for slot in slots[1]:
            fill(slot)
        for i in slots[2]:
            if remaining >= 2:
                fill((i, 0)); fill((i, 1))
        for i in slots[2]:
            for j in (0, 1):
                if rows[i][j] == 0:
                    fill((i, j))
        for slot in slots[0]:
            fill(slot)
    else:
        for slot in slots[0]:
            fill(slot)
        for i in slots[2]:
            fill((i, 0))
        for slot in slots[1]:
            fill(slot)
        for i in slots[2]:
            fill((i, 1))
    if remaining:
        raise AssertionError('Unallocated positive bits')
    return tuple(tuple(p) for p in rows)


def ordered_witness(mask, first_positive, maximize):
    """Construct a completion attaining a fixed-A ordered objective endpoint."""
    pairs = checked(mask)
    rows = [[0 if x is None else x for x in p] for p in pairs]
    remaining = first_positive-sum(p[0] for p in rows)
    unknown_x = [i for i, p in enumerate(pairs) if p[0] is None]
    if remaining < 0 or remaining > len(unknown_x) or int(remaining) != remaining:
        raise ValueError('Infeasible A')
    priority = (1, None, 0) if maximize else (0, None, 1)
    allocation = [i for y in priority for i in unknown_x if pairs[i][1] == y]
    for i in allocation[:int(remaining)]:
        rows[i][0] = 1
    for i, p in enumerate(pairs):
        if p[1] is None:
            rows[i][1] = rows[i][0] if maximize else 1-rows[i][0]
    return tuple(tuple(p) for p in rows)
