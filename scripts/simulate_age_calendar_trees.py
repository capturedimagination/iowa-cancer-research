#!/usr/bin/env python3
"""Independent complete-tree verification of the frozen common-clock study.

The default action is deterministic implementation fixtures. Scientific runs
require --run, after external code review. No primary ODE code is imported.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import sys
import tempfile
import time
import traceback

import numpy as np
import scipy


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "research/treatment-discovery/lineage-audit-2026-11-10/age-calendar-calibration/protocol.json"
PROTOCOL_SHA = "53d76bf43d0b1f47355d57d95ec6d7f43fce67541aed7631510a3cbff0b42919"
LOCAL = ROOT / "tmp/age-calendar-2026-11-10/tree-monte-carlo"
PUBLIC = ROOT / "research/treatment-discovery/lineage-audit-2026-11-10/age-calendar-calibration/tree-monte-carlo/results.json"
FOUNDERS = 10_000
BATCH = 250
MAX_CELLS = 50_000_000
MAX_FRONTIER = 5_000_000
HORIZON = 4.0
BASE_SEED = 2026111013
LAGS = np.array([0.5, 1.0, 2.0])


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(value, indent=2, allow_nan=False) + "\n"
    temporary = path.with_name(path.name + ".partial-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f"))
    with temporary.open("x") as f:
        f.write(serialized)
        f.flush()
        os.fsync(f.fileno())
    os.link(temporary, path)  # Atomic publication, fails if a first result exists.
    temporary.unlink()


# The breadth-first/checkpoint design is derived from the independent older
# simulator (cbbdb12707fb55641bd2701a3be0c862f4f47d0b758bec7b829239cb6f084c46).
# This file does not import it or a primary numerical model. All cell times here
# are operational; fixed physical queries and birth-specific lags are mapped.
DERIVED_FROM_SHA = 'cbbdb12707fb55641bd2701a3be0c862f4f47d0b758bec7b829239cb6f084c46'
TIMES = np.array([0., .5, 1., 1.5, 2., 3., 4.])
HORIZONS = (2., 3., 4.)
EVALUATIONS = (.5, 1., 1.5, 2.)
CONTRAST_PAIRS = ((2., 3.), (2., 4.), (3., 4.))


def protocol_load():
    if sha256(PROTOCOL) != PROTOCOL_SHA:
        raise ValueError('Frozen protocol hash mismatch')
    p = json.loads(PROTOCOL.read_text())
    assert len(p['cases']) == 20
    assert p['tree_simulation']['seed_entropy'] == BASE_SEED
    assert p['tree_simulation']['roots_per_case'] == FOUNDERS
    assert p['tree_simulation']['batch_size'] == BATCH
    return p


class SimulationFailure(RuntimeError):
    def __init__(self, message, diagnostics=None):
        super().__init__(message)
        self.diagnostics = diagnostics or {}


def operational_time(case, physical):
    t = np.asarray(physical, dtype=float)
    return t + case['amplitude'] * case['period'] / (2 * np.pi) * (1 - np.cos(2 * np.pi * t / case['period']))


def physical_time(case, operational):
    """Monotone inverse on [0,4]; endpoint identities are exact."""
    target = np.asarray(operational, dtype=float)
    end = float(operational_time(case, HORIZON))
    if np.any(~np.isfinite(target)) or np.any(target < 0) or np.any(target > end):
        raise ValueError('Operational inverse outside finite [0,R(4)]')
    if case['amplitude'] == 0:
        return target.copy()
    lo = np.zeros(target.shape)
    hi = np.full(target.shape, HORIZON)
    # 43 bisections give physical bracket <= 4/2^43 < 1e-12.
    for _ in range(43):
        mid = (lo + hi) / 2
        value = operational_time(case, mid)
        equal = value == target
        below = value < target
        lo = np.where(equal | below, mid, lo)
        hi = np.where(equal | ~below, mid, hi)
    answer = (lo + hi) / 2
    return np.where(target == 0, 0., np.where(target == end, HORIZON, answer))


def children_types(mother_types, rho, uniforms):
    mothers = np.repeat(mother_types, 2)
    uniforms = np.asarray(uniforms)
    if uniforms.shape != mothers.shape:
        raise ValueError('One independent uniform per daughter required')
    return np.where(uniforms < (1 + rho) / 2, mothers, 1 - mothers)


def allocate_observations(n):
    return {'U': np.zeros((n, len(TIMES))),
            'N': np.zeros((n, len(TIMES)), dtype=np.int64),
            'pair_N': np.zeros((n, len(LAGS), 2), dtype=np.int64),
            'eligible': np.zeros(n, dtype=bool),
            'first_division': np.full(n, np.nan),
            'first_division_operational': np.full(n, np.nan),
            'pair_query_operational': np.full((n, len(LAGS)), np.nan),
            'mother_type': np.full(n, -1, dtype=np.int64)}


def add_cells(obs, query_operational, roots, birth, exit_time, generation, sides):
    n_roots = obs['U'].shape[0]
    if np.any(exit_time <= birth):
        raise SimulationFailure('Nonpositive computed cell lifetime')
    weight = math.ldexp(1., -int(generation))
    if weight == 0:
        raise SimulationFailure('Underflowed chronological path weight')
    for j, query in enumerate(query_operational):
        live = (birth <= query) & (query < exit_time)
        if np.any(live):
            counts = np.bincount(roots[live], minlength=n_roots)
            obs['N'][:, j] += counts
            obs['U'][:, j] += counts * weight
    valid = (sides >= 0) & obs['eligible'][roots]
    if np.any(valid):
        r = roots[valid]
        keys = 2 * r + sides[valid]
        for j in range(len(LAGS)):
            query = obs['pair_query_operational'][r, j]
            live = (birth[valid] <= query) & (query < exit_time[valid])
            if np.any(live):
                obs['pair_N'][:, j, :] += np.bincount(keys[live], minlength=2 * n_roots).reshape(n_roots, 2)


def guard_cells(case_offset, generated, next_frontier, generation):
    diagnostics = dict(prior_case_cells=int(case_offset), batch_generated_cells=int(generated),
                       proposed_frontier=int(next_frontier), generation=int(generation))
    if case_offset + generated + next_frontier > MAX_CELLS:
        raise SimulationFailure('50M generated-cell case guard', diagnostics)
    if next_frontier > MAX_FRONTIER:
        raise SimulationFailure('5M proposed-frontier guard', diagnostics)


def simulate_batch(case, rng, n=BATCH, case_offset=0):
    """Complete branching in R time; future-blind fair-path mass is 2^-g.

    RNG order: initial type integers (two types only); initial stage integers
    (uniform-stage only); each BFS frontier Gamma division durations, then Exp
    death durations (no draw if mu=0); then daughter uniforms, interleaved in
    stable parent order (two types only, including rho=0 and rho=1).
    """
    guard_cells(case_offset, 0, n, 0)
    query_operational = operational_time(case, TIMES)
    end = float(query_operational[-1])
    cutoff = float(operational_time(case, 2.))
    obs = allocate_observations(n)
    two_type = len(case['means']) == 2
    types = rng.integers(0, 2, size=n) if two_type else np.zeros(n, dtype=np.int64)
    k = case['k']
    stages = (rng.integers(1, k + 1, size=n) if case['initialization'] == 'uniform_stage'
              else np.ones(n, dtype=np.int64))
    obs['founder_type'], obs['founder_stage'] = types.copy(), stages.copy()
    roots, birth, sides = np.arange(n, dtype=np.int64), np.zeros(n), np.full(n, -1, dtype=np.int64)
    generated, generation, events, divisions, deaths, max_frontier = n, 0, 0, 0, 0, n
    try:
        while len(roots):
            shape, scale = k - stages + 1, np.asarray(case['means'])[types] / k
            div = birth + rng.gamma(shape, scale)
            death = (birth + rng.exponential(1. / case['mu'], size=len(roots))
                     if case['mu'] > 0 else np.full(len(roots), np.inf))
            if np.any(~np.isfinite(div)) or np.any(div <= birth) or np.any(death <= birth):
                raise SimulationFailure('Invalid potential lifetime')
            exit_time = np.minimum(div, death)
            is_div = (div < death) & (div <= end)
            is_death = (death <= div) & (death <= end)
            if generation == 0:
                obs['first_division_operational'][roots[is_div]] = div[is_div]
                obs['first_division'][roots[is_div]] = physical_time(case, div[is_div])
                qualify = is_div & (div <= cutoff)
                qualified_roots = roots[qualify]
                obs['eligible'][qualified_roots] = True
                obs['mother_type'][qualified_roots] = types[qualify]
                # Snap exact known cutoff before mapping lag queries, so a
                # synthetic division at b=2 cannot drift beyond query 4.
                obs['first_division'][qualified_roots] = np.where(
                    div[qualify] == cutoff, 2., obs['first_division'][qualified_roots])
                pair_times = obs['first_division'][qualified_roots, None] + LAGS[None, :]
                obs['pair_query_operational'][qualified_roots] = operational_time(case, pair_times)
            add_cells(obs, query_operational, roots, birth, exit_time, generation, sides)
            ndiv, ndeath = int(np.sum(is_div)), int(np.sum(is_death))
            events += ndiv + ndeath
            divisions += ndiv
            deaths += ndeath
            child_count = 2 * ndiv
            guard_cells(case_offset, generated, child_count, generation + 1)
            if not child_count:
                break
            parent_roots, parent_sides, parent_types = roots[is_div], sides[is_div], types[is_div]
            next_birth, next_roots = np.repeat(div[is_div], 2), np.repeat(parent_roots, 2)
            next_sides = np.repeat(parent_sides, 2)
            if generation == 0:
                next_sides = np.where(np.repeat(obs['eligible'][parent_roots], 2), np.tile([0, 1], ndiv), -1)
            next_types = (children_types(parent_types, case['rho'], rng.random(child_count))
                          if two_type else np.zeros(child_count, dtype=np.int64))
            birth, roots, sides, types = next_birth, next_roots, next_sides, next_types
            stages = np.ones(child_count, dtype=np.int64)
            generation += 1
            generated += child_count
            max_frontier = max(max_frontier, child_count)
    except (MemoryError, OverflowError) as exc:
        raise SimulationFailure(type(exc).__name__, dict(batch_generated_cells=int(generated),
                                generation=generation, prior_case_cells=int(case_offset), frontier=len(roots))) from exc
    if np.any(obs['U'] < 0) or np.any(obs['U'] > 1 + 1e-12) or np.any(~np.isfinite(obs['U'])):
        raise SimulationFailure('Chronological mass outside [0,1]')
    if not np.array_equal(obs['N'] > 0, obs['U'] > 0):
        raise SimulationFailure('Family/path mass identity failed')
    if not np.all(obs['U'][:, 0] == 1) or not np.all(obs['N'][:, 0] == 1):
        raise SimulationFailure('Time-zero identity failed')
    if np.any(np.diff(obs['U'], axis=1) > 1e-12):
        raise SimulationFailure('Chronological mass increased')
    obs['F'], obs['pair_A'] = obs['N'] > 0, obs['pair_N'] > 0
    obs['query_times'] = TIMES.copy()
    return obs, dict(generated_cells=generated, biological_events=events, divisions=divisions,
                     deaths=deaths, max_generation=generation, max_frontier=max_frontier)


def bins():
    return [dict(bin_id=f'w{width:g}-b{j}', width=width, left=j * width, right=(j + 1) * width)
            for width in (2., 1., .5, .25) for j in range(round(2 / width))]


def bin_mask(obs, b):
    # Compare original operational times directly with transformed physical
    # boundaries in aggregation; see aggregate_case. This generic physical
    # fixture function is also used to establish the published convention.
    t = obs['first_division']
    return obs['eligible'] & (t >= b['left']) & ((t < b['right']) if b['right'] < 2 else (t <= b['right']))


def aggregate_case(case, obs, diagnostics):
    n = len(obs['eligible'])
    idx = {float(t): j for j, t in enumerate(obs['query_times'])}
    U, F, eligible = obs['U'], obs['F'], obs['eligible']
    family, qrows, urows, contrasts, binrows, pairrows = [], [], [], [], [], []
    for T in HORIZONS:
        f = F[:, idx[T]]
        selected = int(np.sum(f))
        family.append(dict(T=T, count=selected, total=n, estimate=selected/n))
        for t in sorted(set([0., *EVALUATIONS, T])):
            u = U[:, idx[t]]
            qrows.append(dict(t=t, T=T, count=selected, defined=selected > 0,
                              estimate=float(np.mean(u[f])) if selected else None,
                              sum=float(np.sum(u[f])), sum_squares=float(np.dot(u[f], u[f])),
                              positive_loss_count=int(np.sum(u[f] < 1))))
    for t in TIMES:
        u = U[:, idx[float(t)]]
        urows.append(dict(t=float(t), total=n, estimate=float(np.mean(u)), sum=float(np.sum(u)),
                          sum_squares=float(np.dot(u, u)), positive_loss_count=int(np.sum(u < 1))))
    for T1, T2 in CONTRAST_PAIRS:
        f1, f2 = F[:, idx[T1]], F[:, idx[T2]]
        if np.any(f2 & ~f1):
            raise SimulationFailure('Family selection is not nested')
        removed = f1 & ~f2
        n1, n2, nr = int(np.sum(f1)), int(np.sum(f2)), int(np.sum(removed))
        for t in EVALUATIONS:
            u = U[:, idx[t]]
            loss = (1 - u) * removed
            contrasts.append(dict(t=t, T_early=T1, T_late=T2, defined=n1 > 0 and n2 > 0,
                estimate=float(np.mean(u[f2]) - np.mean(u[f1])) if n1 and n2 else None,
                early_count=n1, late_count=n2, removed_count=nr, total=n,
                removed_loss_mean=float(np.mean(loss)), removed_loss_sum=float(np.sum(loss)),
                removed_loss_sum_squares=float(np.dot(loss, loss)),
                removed_loss_contributor_count=int(np.sum(loss > 0)),
                conditional_removed_loss=float(np.mean(1-u[removed])) if nr else None))
    for b in bins():
        # Original operational clocks avoid inverse-roundoff changing bin
        # membership for exact synthetic internal-boundary births.
        first = obs['first_division_operational']
        left, right = float(operational_time(case, b['left'])), float(operational_time(case, b['right']))
        mask = eligible & (first >= left) & ((first < right) if b['right'] < 2 else (first <= right))
        nb = int(np.sum(mask))
        type0 = int(np.sum(obs['mother_type'][mask] == 0))
        binrows.append(dict(**b, count=nb, total=n, estimate=nb/n, type0_count=type0,
                            mother_type0_weight=type0/nb if nb else None))
        for j, lag in enumerate(LAGS):
            a, bb = obs['pair_A'][mask, j, 0], obs['pair_A'][mask, j, 1]
            s1, s2, both = int(np.sum(a)), int(np.sum(bb)), int(np.sum(a & bb))
            pairrows.append(dict(bin_id=b['bin_id'], lag=float(lag), count=nb,
                first_count=s1, second_count=s2, both_count=both,
                first_mean=s1/nb if nb else None, second_mean=s2/nb if nb else None,
                joint_mean=both/nb if nb else None, covariance_defined=nb >= 2,
                covariance=(both-s1*s2/nb)/(nb-1) if nb >= 2 else None))
    ne = int(np.sum(eligible))
    accounting = dict(root_count=n, q_rows=len(qrows), u_rows=len(urows), contrast_rows=len(contrasts),
        bin_rows=len(binrows), pair_rows=len(pairrows),
        family_path_positive_identity=bool(np.array_equal(F, U > 0)),
        time_zero_identity=bool(np.all(U[:, 0] == 1)),
        birth_partitions_cover_eligible=all(sum(b['count'] for b in binrows if b['width'] == w) == ne for w in (2., 1., .5, .25)))
    if [len(qrows), len(urows), len(contrasts), len(binrows), len(pairrows)] != [17, 7, 12, 15, 45]:
        raise SimulationFailure('Frozen aggregate row count mismatch')
    if not all(accounting[k] for k in ('family_path_positive_identity','time_zero_identity','birth_partitions_cover_eligible')):
        raise SimulationFailure('Aggregate accounting failed')
    return dict(status='complete', case_id=case['case_id'], configuration=case,
                prospective_founders=n, eligible_count=ne,
                eligible_type0_count=int(np.sum(obs['mother_type'][eligible] == 0)),
                family=family, Q=qrows, U=urows, contrasts=contrasts, bins=binrows, pairs=pairrows,
                accounting=accounting, diagnostics=diagnostics)


def save_batch_new(path, obs, metadata):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".partial-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f"))
    with temporary.open("xb") as f:
        np.savez_compressed(f, **obs, metadata=np.array(json.dumps(metadata, allow_nan=False)))
        f.flush()
        os.fsync(f.fileno())
    os.link(temporary, path)
    temporary.unlink()


def load_batch(path):
    with np.load(path, allow_pickle=False) as data:
        metadata = json.loads(str(data["metadata"]))
        obs = {key: data[key].copy() for key in data.files if key != "metadata"}
    return obs, metadata


def combine_batches(batches):
    first = batches[0]
    if any(not np.array_equal(b["query_times"], first["query_times"]) for b in batches):
        raise ValueError("Inconsistent checkpoint query times")
    return {key: first[key] if key == "query_times" else np.concatenate([b[key] for b in batches], axis=0)
            for key in first}


def sum_diagnostics(diagnostics):
    return {key: (max(d[key] for d in diagnostics) if key.startswith("max_")
                  else sum(d[key] for d in diagnostics)) for key in diagnostics[0]}


def run_case(case, case_index, folder, code_hash):
    case_dir = folder / case["case_id"]
    result_path = case_dir / "aggregate.json"
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([BASE_SEED, case_index])))
    batches, diagnostics = [], []
    generated = 0
    started = time.monotonic()
    for start in range(0, FOUNDERS, BATCH):
        path = case_dir / "batches" / f"{start:05d}.npz"
        before = rng.bit_generator.state
        if path.exists():
            obs, metadata = load_batch(path)
            expected = {"protocol_sha256": PROTOCOL_SHA, "code_sha256": code_hash,
                        "case_id": case["case_id"], "case_index": case_index, "root_start": start, "root_count": BATCH,
                        "rng_before": before, "case_generated_before": generated}
            for key, value in expected.items():
                if metadata.get(key) != value:
                    raise ValueError(f"Checkpoint mismatch for {path}: {key}")
            rng.bit_generator.state = metadata["rng_after"]
            diag = metadata["diagnostics"]
        else:
            try:
                obs, diag = simulate_batch(case, rng, BATCH, generated)
                metadata = {"protocol_sha256": PROTOCOL_SHA, "code_sha256": code_hash,
                            "case_id": case["case_id"], "case_index": case_index, "root_start": start, "root_count": BATCH,
                            "case_generated_before": generated, "rng_before": before,
                            "rng_after": rng.bit_generator.state, "diagnostics": diag,
                            "created_utc": utc_now()}
                save_batch_new(path, obs, metadata)
            except (SimulationFailure, MemoryError, OSError) as exc:
                failure = {"status": "incomplete", "created_utc": utc_now(),
                           "case_id": case["case_id"], "protocol_sha256": PROTOCOL_SHA,
                           "code_sha256": code_hash, "completed_founders": start,
                           "completed_cells": generated, "error": str(exc),
                           "error_class": type(exc).__name__, "rng_batch_before": before,
                           "rng_at_failure": rng.bit_generator.state,
                           "diagnostics": getattr(exc, "diagnostics", {})}
                failure_path = case_dir / "failures" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f") + ".json")
                write_json_new(failure_path, failure)
                return failure
        batches.append(obs)
        diagnostics.append(diag)
        generated += diag["generated_cells"]
    obs = combine_batches(batches)
    if len(obs["eligible"]) != FOUNDERS:
        raise ValueError("Incomplete cohort cannot be aggregated as complete")
    if result_path.exists():
        result = json.loads(result_path.read_text())
        if result["protocol_sha256"] != PROTOCOL_SHA or result["code_sha256"] != code_hash:
            raise ValueError("Existing case aggregate provenance mismatch")
        for record in result["batch_files"]:
            if sha256(folder / record["path"]) != record["sha256"]:
                raise ValueError("Completed case checkpoint hash mismatch")
        return result
    result = aggregate_case(case, obs, sum_diagnostics(diagnostics))
    result.update({"created_utc": utc_now(), "protocol_sha256": PROTOCOL_SHA,
                   "code_sha256": code_hash, "runtime_seconds_this_invocation": time.monotonic() - started,
                   "batch_files": [{"path": str(p.relative_to(folder)), "sha256": sha256(p)}
                                   for p in sorted((case_dir / "batches").glob("*.npz"))]})
    write_json_new(result_path, result)
    return result


def run_all(folder=LOCAL, public_path=PUBLIC, resume=False):
    protocol = protocol_load()
    code_hash = sha256(__file__)
    folder, public_path = Path(folder), Path(public_path)
    manifest_path = folder / "run-manifest.json"
    signature = {"protocol_sha256": PROTOCOL_SHA, "code_sha256": code_hash,
                 "python_version": platform.python_version(), "numpy_version": np.__version__,
                 "scipy_version": scipy.__version__,
                 "derived_from_older_independent_simulator_sha256": DERIVED_FROM_SHA,
                 "batch_paths_relative_to": "explicit checkpoint root",
                 "base_seed": BASE_SEED, "founders_per_case": FOUNDERS, "batch_size": BATCH}
    if manifest_path.exists():
        if not resume:
            raise FileExistsError("Run exists; use --resume without changing code/environment")
        old = json.loads(manifest_path.read_text())
        if any(old.get(k) != v for k, v in signature.items()):
            raise ValueError("Resume provenance/environment mismatch")
    else:
        if resume:
            raise FileNotFoundError("No run manifest to resume")
        if folder.exists() and any(folder.iterdir()):
            raise FileExistsError("Unmanifested nonempty output folder")
        write_json_new(manifest_path, {**signature, "created_utc": utc_now(),
                                      "case_ids": [c["case_id"] for c in protocol["cases"]]})
    if public_path.exists():
        raise FileExistsError("Aggregate publication path already exists; first outcomes are preserved")
    results = []
    for case_index, case in enumerate(protocol["cases"]):
        print(f"Starting {case['case_id']}", flush=True)
        try:
            result = run_case(case, case_index, folder, code_hash)
        except Exception as exc:
            # Keep unexpected aggregation/checkpoint failures visible too.
            result = {"status": "incomplete", "created_utc": utc_now(),
                      "case_id": case["case_id"], "protocol_sha256": PROTOCOL_SHA,
                      "code_sha256": code_hash, "error": str(exc),
                      "error_class": type(exc).__name__, "traceback": traceback.format_exc(),
                      "checkpoint_folder": case["case_id"]}
            failure_path = folder / case["case_id"] / "failures" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f") + ".json")
            write_json_new(failure_path, result)
        results.append(result)
        print(f"Finished {case['case_id']}: {result['status']}", flush=True)
    report = {"created_utc": utc_now(), **signature,
              "scope": "Independent complete-tree Monte Carlo numerical verification, not biological uncertainty.",
              "primary_reference_comparisons": "Pending separate comparison against saved primary aggregates; no primary implementation imported.",
              "planned_cases": 20, "completed_cases": sum(r["status"] == "complete" for r in results),
              "incomplete_cases": sum(r["status"] != "complete" for r in results), "cases": results}
    write_json_new(public_path, report)
    return report


def fixtures():
    """Constructed records/fake clocks only; no stochastic study outcomes."""
    passed = []
    def check(ok, name):
        if not ok:
            raise AssertionError(name)
        passed.append(name)
    case = dict(case_id='fixture', k=4, means=[1.], rho=0., initialization='newborn',
                mu=1., amplitude=0., period=2.)
    variable = {**case, 'amplitude': .75, 'period': 4.}
    grid = np.array([0., .25, .5, 1., 1.75, 2., 3., 4.])
    check(np.array_equal(operational_time(case, grid), grid), 'constant clock identity')
    check(np.max(np.abs(physical_time(variable, operational_time(variable, grid))-grid)) <= 1e-12,
          'strict monotone clock inversion at fixed synthetic points')
    check(physical_time(variable, np.array([0., 4.])).tolist() == [0., 4.], 'exact clock endpoints')
    check(float(operational_time(variable, 4.)) == 4., 'last physical and operational horizon agree')
    try:
        physical_time(variable, [4.001])
        raise AssertionError('missing inverse bounds')
    except ValueError:
        passed.append('clock inverse rejects out-of-support input')
    obs = allocate_observations(1)
    obs['eligible'][0] = True
    obs['first_division'][0] = 1.
    obs['first_division_operational'][0] = 1.
    obs['pair_query_operational'][0] = 1 + LAGS
    add_cells(obs, TIMES, np.array([0]), np.array([0.]), np.array([1.]), 0, np.array([-1]))
    add_cells(obs, TIMES, np.array([0,0]), np.array([1.,1.]), np.array([1.5,5.]), 1, np.array([0,1]))
    check(obs['N'].tolist() == [[1,1,2,1,1,1,1]], 'division and death half-open boundaries')
    check(obs['U'].tolist() == [[1,1,1,.5,.5,.5,.5]], 'chronological mass fair sister path')
    check(obs['pair_N'].tolist() == [[[0,1],[0,1],[0,1]]], 'sister subtree equal-lag survival')
    check(children_types(np.array([0,1]), .5, [.1,.9,.1,.9]).tolist() == [0,1,1,0], 'daughter uniforms independent conditional mother')
    check(children_types(np.array([0,1]), 1., [.99,.1,.99,.1]).tolist() == [0,0,1,1], 'rho one copies both daughter types')
    # Fake RNG returns declared potential lifetimes without random draws.
    class FixedClocks:
        def __init__(self, division=1., death=10., stages=None):
            self.division, self.death, self.stages = division, death, stages
            self.calls = []
            self.shapes = []
        def gamma(self, shape, scale):
            self.calls.append(('gamma',len(shape)))
            self.shapes.append(np.array(shape).tolist())
            return np.full(len(shape), self.division)
        def exponential(self, scale, size):
            self.calls.append(('exponential', size))
            return np.full(size, self.death)
        def integers(self, low, high, size):
            self.calls.append(('integers',low,high,size))
            return np.array(self.stages if self.stages is not None else [low]*size)
        def random(self, size):
            self.calls.append(('random',size))
            return np.zeros(size)
    fake = FixedClocks()
    full, diag = simulate_batch(case, fake, n=1)
    check(diag['generated_cells'] == 31 and full['N'][0,-1] == 16, 'complete endpoint generation has all sixteen live descendants')
    check(np.all(full['U'] == 1) and full['pair_N'].tolist() == [[[1,1],[2,2],[4,4]]], 'whole-tree chronological and subtree mass')
    check(fake.calls == sum(([('gamma',n),('exponential',n)] for n in (1,2,4,8,16)), []), 'stable BFS clock draw order including endpoint daughters')
    death, diag = simulate_batch(case, FixedClocks(1.,1.), n=1)
    check(diag['generated_cells'] == 1 and diag['deaths'] == 1 and not death['eligible'][0], 'synthetic tied death beats division')
    zero_fake = FixedClocks(10.)
    zero, diag = simulate_batch({**case,'mu':0.}, zero_fake, n=4)
    check(np.all(zero['U'] == 1) and zero_fake.calls == [('gamma',4)], 'zero-death fixture does not consume death RNG')
    stage_rng = FixedClocks(10.,stages=[1,2,3,4])
    simulate_batch({**case,'initialization':'uniform_stage'}, stage_rng, n=4)
    check(stage_rng.shapes[0] == [4,3,2,1], 'uniform-stage founders have correct residual Erlang shape')
    two_rng = FixedClocks(2.)
    two, _ = simulate_batch({**case,'means':[.5,1.5],'rho':1.}, two_rng, n=1)
    check(two_rng.calls[:4] == [('integers',0,2,1),('gamma',1),('exponential',1),('random',2)], 'two-type root and daughter stream ordering')
    at, _ = simulate_batch(variable, FixedClocks(float(operational_time(variable,2.))), n=1)
    after, _ = simulate_batch(variable, FixedClocks(float(operational_time(variable,2.))+1e-8), n=1)
    check(at['eligible'][0] and not after['eligible'][0] and at['first_division'][0] == 2., 'physical pair cutoff uses exact operational boundary')
    check(at['pair_query_operational'][0,-1] == 4., 'pair born at cutoff has exact last query at four')
    half_birth = float(physical_time(variable, operational_time(variable, .5)))
    nonlinear = allocate_observations(1)
    nonlinear['eligible'][0] = True
    nonlinear['pair_query_operational'][0] = operational_time(variable, half_birth + LAGS)
    add_cells(nonlinear, operational_time(variable, TIMES), np.array([0, 0]),
              np.full(2, float(operational_time(variable, .5))),
              np.full(2, float(operational_time(variable, 1.))), 1, np.array([0, 1]))
    check(half_birth == .5 and np.all(nonlinear['pair_N'][0] == 0),
          'nonlinear-clock exact daughter death at equal lag is excluded')
    probe = dict(eligible=np.ones(4,bool), first_division=np.array([0.,.5,1.,2.]))
    check([int(np.sum(bin_mask(probe,b))) for b in bins() if b['width']==.5] == [1,1,1,1], 'left-closed birth bins and final inclusive endpoint')
    # Correct physical-lag transformation is not R(b)+R(lag).
    check(abs(float(operational_time(variable,1.5)) - (float(operational_time(variable,1.))+float(operational_time(variable,.5)))) > .1,
          'birth-specific calendar lag cannot be added as operational durations')
    no_pairs = aggregate_case(case, zero, diag)
    check(no_pairs['eligible_count']==0 and all(not r['covariance_defined'] for r in no_pairs['pairs']), 'undefined empty-bin covariance retained')
    check(len(no_pairs['Q'])==17 and len(no_pairs['contrasts'])==12 and len(no_pairs['U'])==7, 'frozen Q U and contrast row counts')
    check(all(r['removed_count']==0 and r['removed_loss_mean']==0 and r['conditional_removed_loss'] is None for r in no_pairs['contrasts']),
          'zero removed cohort has defined unconditional zero loss and undefined conditional loss')
    extinct, extinct_diag = simulate_batch(case, FixedClocks(10., .25), n=2)
    report = aggregate_case(case, extinct, extinct_diag)
    check(all(not r['defined'] and r['estimate'] is None for r in report['Q']), 'zero-selected Q remains undefined')
    for which in ('cells','frontier'):
        try:
            guard_cells(MAX_CELLS if which=='cells' else 0,0,1 if which=='cells' else MAX_FRONTIER+1,0)
            raise AssertionError('missing guard')
        except SimulationFailure:
            passed.append(f'{which} resource guard before allocation')
    with tempfile.TemporaryDirectory(prefix='age-calendar-fixture-') as tmp:
        p=Path(tmp)/'batch.npz'
        save_batch_new(p,full,{'fixture':True})
        reload, meta=load_batch(p)
        check(meta=={'fixture':True} and all(np.array_equal(full[k],reload[k],equal_nan=True) for k in full),'checkpoint exact round trip')
        before=sha256(p)
        try:
            save_batch_new(p,zero,{})
            raise AssertionError('overwritten checkpoint')
        except FileExistsError:
            check(sha256(p)==before,'first checkpoint cannot be overwritten')
    return dict(status='pass',count=len(passed),fixtures=passed,scientific_simulations_run=False,
                protocol_sha256=PROTOCOL_SHA,code_sha256=sha256(__file__),created_utc=utc_now())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',action='store_true')
    parser.add_argument('--resume',action='store_true')
    parser.add_argument('--fixture-report',type=Path)
    parser.add_argument('--local',type=Path,default=LOCAL)
    parser.add_argument('--output',type=Path,default=PUBLIC)
    args=parser.parse_args()
    protocol_load()
    report=fixtures()
    if args.fixture_report:
        write_json_new(args.fixture_report,report)
    print(json.dumps(report,indent=2),flush=True)
    if args.run:
        run_all(args.local,args.output,args.resume)
    elif args.resume:
        parser.error('--resume requires --run')


if __name__=='__main__':
    main()
