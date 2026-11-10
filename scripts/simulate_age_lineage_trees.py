#!/usr/bin/env python3
"""Independent complete-tree verification of the frozen cell-cycle study.

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
from scipy.integrate import quad


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "research/treatment-discovery/lineage-audit-2026-11-10/cell-cycle-specificity/protocol.json"
PROTOCOL_SHA = "e7fe08e71d614f27f7d312a6afa7cf64d8022cba2af908cc92c7965d7d6caeb5"
LOCAL = ROOT / "tmp/age-lineage-2026-11-10/monte-carlo"
PUBLIC = ROOT / "research/treatment-discovery/lineage-audit-2026-11-10/cell-cycle-specificity/monte-carlo/results.json"
FOUNDERS = 10_000
BATCH = 250
MAX_CELLS = 50_000_000
MAX_FRONTIER = 5_000_000
HORIZON = 4.0
BASE_SEED = 2026111012
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


def protocol_load():
    if sha256(PROTOCOL) != PROTOCOL_SHA:
        raise ValueError("Frozen protocol hash mismatch")
    protocol = json.loads(PROTOCOL.read_text())
    if len(protocol["cases"]) != 72:
        raise ValueError("Expected all 72 frozen cases")
    return protocol


def query_times(case):
    times = [0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0]
    if case["kind"] == "deterministic":
        times += [1.25, 1.75]
    return np.array(sorted(set(times)))


class SimulationFailure(RuntimeError):
    def __init__(self, message, diagnostics=None):
        super().__init__(message)
        self.diagnostics = diagnostics or {}


def integrated_calendar(t):
    return t + (1.0 - np.cos(np.pi * t)) / (2.0 * np.pi)


def invert_calendar(birth, increment):
    """Invert independent Exp(1) hazard increments only within support."""
    birth = np.asarray(birth, dtype=float)
    increment = np.asarray(increment, dtype=float)
    if np.any(increment <= 0) or np.any(birth > HORIZON):
        raise SimulationFailure("Invalid calendar hazard increment/birth")
    remaining = integrated_calendar(HORIZON) - integrated_calendar(birth)
    inside = increment <= remaining
    answer = np.full(birth.shape, np.inf)
    if np.any(inside):
        lo = birth[inside].copy()
        hi = np.full(lo.shape, HORIZON)
        target = integrated_calendar(lo) + increment[inside]
        while np.max(hi - lo) > 1e-12:
            mid = (lo + hi) / 2.0
            below = integrated_calendar(mid) < target
            lo = np.where(below, mid, lo)
            hi = np.where(below, hi, mid)
        value = (lo + hi) / 2.0
        value[increment[inside] == remaining[inside]] = HORIZON
        answer[inside] = value
    return answer


def division_times(case, birth, types, stages, rng):
    n = len(birth)
    kind = case["kind"]
    if kind == "erlang":
        shape = case["k"] - stages + 1
        scale = np.asarray(case["means"])[types] / case["k"]
        return birth + rng.gamma(shape, scale)
    if kind == "deterministic":
        return birth + case["division_age"]
    if kind == "calendar":
        return invert_calendar(birth, rng.exponential(1.0, size=n))
    if kind == "no_division":
        return np.full(n, np.inf)
    raise ValueError(f"Unsupported kind: {kind}")


def children_types(mother_types, rho, uniforms):
    mothers = np.repeat(mother_types, 2)
    uniforms = np.asarray(uniforms)
    if uniforms.shape != mothers.shape:
        raise ValueError("One independent uniform is required per daughter")
    return np.where(uniforms < (1.0 + rho) / 2.0, mothers, 1 - mothers)


def allocate_observations(n, times):
    return {
        "U": np.zeros((n, len(times))),
        "N": np.zeros((n, len(times)), dtype=np.int64),
        "pair_N": np.zeros((n, len(LAGS), 2), dtype=np.int64),
        "eligible": np.zeros(n, dtype=bool),
        "first_division": np.full(n, np.nan),
        "mother_type": np.full(n, -1, dtype=np.int64),
    }


def add_cells(obs, times, roots, birth, exit_time, generation, sides):
    """Read complete cell records; no future-dependent tag/path choice."""
    n_roots = obs["U"].shape[0]
    if np.any(exit_time <= birth):
        raise SimulationFailure("Nonpositive computed cell lifetime")
    weight = math.ldexp(1.0, -int(generation))
    if weight == 0:
        raise SimulationFailure("Underflowed positive chronological weight")
    for j, q in enumerate(times):
        live = (birth <= q) & (q < exit_time)
        if np.any(live):
            count = np.bincount(roots[live], minlength=n_roots)
            obs["N"][:, j] += count
            obs["U"][:, j] += count * weight
    valid = (sides >= 0) & obs["eligible"][roots]
    if np.any(valid):
        r = roots[valid]
        keys = 2 * r + sides[valid]
        for j, lag in enumerate(LAGS):
            q = obs["first_division"][r] + lag
            live = (birth[valid] <= q) & (q < exit_time[valid])
            if np.any(live):
                obs["pair_N"][:, j, :] += np.bincount(
                    keys[live], minlength=2 * n_roots
                ).reshape(n_roots, 2)


def guard_cells(case_offset, generated, next_frontier, generation):
    diagnostics = {
        "prior_case_cells": int(case_offset),
        "batch_generated_cells": int(generated),
        "proposed_frontier": int(next_frontier),
        "generation": int(generation),
    }
    if case_offset + generated + next_frontier > MAX_CELLS:
        raise SimulationFailure("50M generated-cell case guard", diagnostics)
    if next_frontier > MAX_FRONTIER:
        raise SimulationFailure("5M proposed-frontier guard", diagnostics)


def simulate_batch(case, rng, n=BATCH, case_offset=0):
    """All full trees in a batch; no primary-model imports or references."""
    guard_cells(case_offset, 0, n, 0)
    times = query_times(case)
    obs = allocate_observations(n, times)
    two_type = len(case.get("means", [1.0])) == 2
    types = rng.integers(0, 2, size=n) if two_type else np.zeros(n, dtype=np.int64)
    k = case.get("k", 1)
    stages = (rng.integers(1, k + 1, size=n)
              if case["initialization"] == "uniform_stage"
              else np.ones(n, dtype=np.int64))
    obs["founder_type"] = types.copy()
    obs["founder_stage"] = stages.copy()
    roots = np.arange(n, dtype=np.int64)
    birth = np.zeros(n)
    sides = np.full(n, -1, dtype=np.int64)
    generated = n
    generation = 0
    events = 0
    divisions = 0
    deaths = 0
    max_frontier = n
    try:
        while len(roots):
            # This exact draw order also applies to cells born at time 4.
            div = division_times(case, birth, types, stages, rng)
            death = (birth + rng.exponential(1.0 / case["mu"], size=len(roots))
                     if case["mu"] > 0 else np.full(len(roots), np.inf))
            if np.any(div <= birth) or np.any(death <= birth):
                raise SimulationFailure("Nonpositive computed potential lifetime")
            exit_time = np.minimum(div, death)
            is_div = (div < death) & (div <= HORIZON)
            is_death = (death <= div) & (death <= HORIZON)
            if generation == 0:
                obs["first_division"][roots[is_div]] = div[is_div]
                qualify = is_div & (div <= 2.0)
                obs["eligible"][roots[qualify]] = True
                obs["mother_type"][roots[qualify]] = types[qualify]
            add_cells(obs, times, roots, birth, exit_time, generation, sides)
            ndiv = int(np.sum(is_div))
            ndeath = int(np.sum(is_death))
            events += ndiv + ndeath
            divisions += ndiv
            deaths += ndeath
            child_count = 2 * ndiv
            guard_cells(case_offset, generated, child_count, generation + 1)
            if not child_count:
                break
            parent_roots = roots[is_div]
            parent_types = types[is_div]
            parent_sides = sides[is_div]
            next_birth = np.repeat(div[is_div], 2)
            next_roots = np.repeat(parent_roots, 2)
            next_sides = np.repeat(parent_sides, 2)
            if generation == 0:
                next_sides = np.where(
                    np.repeat(obs["eligible"][parent_roots], 2),
                    np.tile(np.array([0, 1]), ndiv), -1,
                )
            if two_type:
                next_types = children_types(parent_types, case["rho"], rng.random(child_count))
            else:
                next_types = np.zeros(child_count, dtype=np.int64)
            birth, roots, sides, types = next_birth, next_roots, next_sides, next_types
            stages = np.ones(child_count, dtype=np.int64)
            generation += 1
            generated += child_count
            max_frontier = max(max_frontier, child_count)
    except (MemoryError, OverflowError) as exc:
        raise SimulationFailure(type(exc).__name__, {
            "batch_generated_cells": int(generated), "generation": generation,
            "prior_case_cells": int(case_offset), "frontier": len(roots),
        }) from exc
    if np.any(obs["U"] < 0) or np.any(obs["U"] > 1 + 1e-12):
        raise SimulationFailure("Chronological mass outside [0,1]")
    if not np.array_equal(obs["N"] > 0, obs["U"] > 0):
        raise SimulationFailure("Live-family and positive chronological mass disagree")
    if not np.all(obs["U"][:, 0] == 1) or not np.all(obs["N"][:, 0] == 1):
        raise SimulationFailure("Time-zero founder identity failed")
    obs["F"] = obs["N"] > 0
    obs["pair_A"] = obs["pair_N"] > 0
    obs["query_times"] = times
    diagnostics = {
        "generated_cells": generated, "biological_events": events,
        "divisions": divisions, "deaths": deaths,
        "max_generation": generation, "max_frontier": max_frontier,
    }
    return obs, diagnostics


def sample_se(values):
    values = np.asarray(values, dtype=float)
    return float(np.std(values, ddof=1) / math.sqrt(len(values))) if len(values) >= 2 else None


def precision_status(count, se, structural=False):
    if count == 0:
        return "undefined_zero_denominator"
    if count < 100:
        return "low_precision"
    if se is None:
        return "undefined_mcse"
    if se == 0:
        return "structural_exact" if structural else "unresolved_zero_mcse"
    return "eligible_approximate_mcse"


def q_estimate(u, f, structural=False):
    u, f = np.asarray(u, float), np.asarray(f, bool)
    count = int(np.sum(f))
    if count == 0:
        return {"defined": False, "estimate": None, "mcse": None,
                "selected": 0, "precision": "undefined_zero_denominator"}, None
    q = float(np.sum(u[f]) / count)
    influence = f * (u - q) / np.mean(f)
    se = sample_se(influence)
    return {"defined": True, "estimate": q, "mcse": se,
            "selected": count, "precision": precision_status(count, se, structural)}, influence


def covariance_estimate(a, b, structural=False):
    a, b = np.asarray(a, float), np.asarray(b, float)
    m = len(a)
    if m < 2:
        return {"defined": False, "estimate": None, "mcse": None,
                "eligible_pairs": m, "precision": "undefined_fewer_than_two_pairs"}
    p_a, p_b = float(np.mean(a)), float(np.mean(b))
    plugin = float(np.mean(a * b) - p_a * p_b)
    correction = m / (m - 1)
    influence = (a - p_a) * (b - p_b) - plugin
    se = correction * sample_se(influence)
    return {"defined": True, "estimate": correction * plugin, "mcse": se,
            "eligible_pairs": m, "mean_A1": p_a, "mean_A2": p_b,
            "mean_joint": float(np.mean(a * b)),
            "precision": precision_status(m, se, structural)}


def calendar_survival_known(birth, lag, mu):
    """Independent scalar quadrature; no primary ODE implementation used."""
    if mu == 0 or lag == 0:
        return 1.0, 0.0
    lb = birth + (1 - math.cos(math.pi * birth)) / (2 * math.pi)

    def integrand(u):
        lu = u + (1 - math.cos(math.pi * u)) / (2 * math.pi)
        return mu * math.exp(-(lu - lb - mu * (u - birth)))

    value, error = quad(integrand, birth, birth + lag, epsabs=1e-12, epsrel=1e-12)
    if error > 1e-10 or value < 0:
        raise SimulationFailure("Calendar residual quadrature failed tolerance")
    return 1.0 / (1.0 + value), error


def aggregate_case(case, obs, diagnostics):
    times = obs["query_times"]
    index = {float(t): j for j, t in enumerate(times)}
    n = len(obs["eligible"])
    eligible = obs["eligible"]
    m = int(np.sum(eligible))
    horizons = [2.0, 3.0, 4.0]
    if case["kind"] == "deterministic":
        horizons += [1.5, 1.75]
    result = {"case_id": case["case_id"], "case": case, "status": "complete",
              "founders": n, "diagnostics": diagnostics,
              "family": [], "U": [], "Q": [], "contrasts": [], "pairs": [],
              "eligibility": {"count": m, "founders": n, "estimate": m / n,
                              "low_precision": m < 100},
              "qualifying_mother_type": None}
    if len(case.get("means", [1])) == 2:
        zero = int(np.sum(obs["mother_type"][eligible] == 0))
        result["qualifying_mother_type"] = {
            "type0_count": zero, "eligible_pairs": m,
            "estimate": zero / m if m else None, "defined": m > 0,
        }
    for t, j in index.items():
        u = obs["U"][:, j]
        se = sample_se(u)
        result["U"].append({"t": t, "estimate": float(np.mean(u)), "mcse": se,
                            "founders": n, "constant_death_expectation": math.exp(-case["mu"] * t),
                            "precision": precision_status(n, se, case["mu"] == 0 or t == 0)})
    q_lookup = {}
    endpoint_errors = []
    for horizon in horizons:
        f = obs["F"][:, index[horizon]]
        count = int(np.sum(f))
        role = "primary" if horizon in (2.0, 3.0, 4.0) else "deterministic_extra"
        result["family"].append({"T": horizon, "role": role, "count": count,
                                 "founders": n, "estimate": count / n,
                                 "low_precision": count < 100})
        q_times = sorted({0.0, 0.5, 1.0, 1.5, 2.0, horizon}) if role == "primary" else [1.25]
        for t in q_times:
            u = obs["U"][:, index[t]]
            stat, influence = q_estimate(u, f, structural=(t == 0 or case["mu"] == 0 or case["kind"] == "no_division"))
            stat.update({"t": t, "T": horizon, "role": role})
            result["Q"].append(stat)
            q_lookup[(t, horizon)] = (stat, influence)
        endpoint, _ = q_estimate(obs["U"][:, index[horizon]], f)
        if endpoint["defined"]:
            endpoint_errors.append(abs(endpoint["estimate"] * count / n - float(np.mean(obs["U"][:, index[horizon]]))))
    for t in (0.5, 1.0, 1.5, 2.0):
        for early, late in ((2.0, 3.0), (2.0, 4.0), (3.0, 4.0)):
            a, ia = q_lookup[(t, early)]
            b, ib = q_lookup[(t, late)]
            defined = a["defined"] and b["defined"]
            se = sample_se(ib - ia) if defined else None
            count = min(a["selected"], b["selected"])
            result["contrasts"].append({
                "t": t, "T_early": early, "T_late": late, "defined": defined,
                "estimate": b["estimate"] - a["estimate"] if defined else None,
                "mcse": se, "selected_early": a["selected"], "selected_late": b["selected"],
                "precision": precision_status(count, se, case["mu"] == 0 or case["kind"] == "no_division"),
            })
    quadrature_error = 0.0
    for j, lag in enumerate(LAGS):
        a = obs["pair_A"][eligible, j, 0]
        b = obs["pair_A"][eligible, j, 1]
        stat = covariance_estimate(a, b, structural=case["mu"] == 0)
        stat["lag"] = float(lag)
        if case["kind"] == "calendar":
            if m:
                known = [calendar_survival_known(float(birth), float(lag), case["mu"])
                         for birth in obs["first_division"][eligible]]
                h = np.array([v[0] for v in known])
                quadrature_error = max(quadrature_error, max(v[1] for v in known))
                residual = (a.astype(float) - h) * (b.astype(float) - h)
                se = sample_se(residual)
                stat["calendar_residual"] = {
                    "defined": True, "estimate": float(np.mean(residual)), "mcse": se,
                    "eligible_pairs": m, "precision": precision_status(m, se, case["mu"] == 0),
                }
            else:
                stat["calendar_residual"] = {"defined": False, "estimate": None,
                                              "mcse": None, "eligible_pairs": 0,
                                              "precision": "undefined_zero_denominator"}
        result["pairs"].append(stat)
    result["accounting"] = {"max_endpoint_product_error": max(endpoint_errors, default=None),
                             "calendar_quadrature_max_reported_error": quadrature_error,
                             "all_family_indicators_match_positive_U": bool(np.array_equal(obs["F"], obs["U"] > 0))}
    return result


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


def run_case(case, folder, code_hash):
    case_dir = folder / case["case_id"]
    result_path = case_dir / "aggregate.json"
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([BASE_SEED, case["seed_case_index"]])))
    batches, diagnostics = [], []
    generated = 0
    started = time.monotonic()
    for start in range(0, FOUNDERS, BATCH):
        path = case_dir / "batches" / f"{start:05d}.npz"
        before = rng.bit_generator.state
        if path.exists():
            obs, metadata = load_batch(path)
            expected = {"protocol_sha256": PROTOCOL_SHA, "code_sha256": code_hash,
                        "case_id": case["case_id"], "root_start": start, "root_count": BATCH,
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
                            "case_id": case["case_id"], "root_start": start, "root_count": BATCH,
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
            if sha256(ROOT / record["path"]) != record["sha256"]:
                raise ValueError("Completed case checkpoint hash mismatch")
        return result
    result = aggregate_case(case, obs, sum_diagnostics(diagnostics))
    result.update({"created_utc": utc_now(), "protocol_sha256": PROTOCOL_SHA,
                   "code_sha256": code_hash, "runtime_seconds_this_invocation": time.monotonic() - started,
                   "batch_files": [{"path": str(p.relative_to(ROOT)), "sha256": sha256(p)}
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
    for case in protocol["cases"]:
        print(f"Starting {case['case_id']}", flush=True)
        try:
            result = run_case(case, folder, code_hash)
        except Exception as exc:
            # Keep unexpected aggregation/checkpoint failures visible too.
            result = {"status": "incomplete", "created_utc": utc_now(),
                      "case_id": case["case_id"], "protocol_sha256": PROTOCOL_SHA,
                      "code_sha256": code_hash, "error": str(exc),
                      "error_class": type(exc).__name__, "traceback": traceback.format_exc(),
                      "checkpoint_folder": str((folder / case["case_id"]).relative_to(ROOT))}
            failure_path = folder / case["case_id"] / "failures" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f") + ".json")
            write_json_new(failure_path, result)
        results.append(result)
        print(f"Finished {case['case_id']}: {result['status']}", flush=True)
    report = {"created_utc": utc_now(), **signature,
              "scope": "Independent complete-tree Monte Carlo numerical verification, not biological uncertainty.",
              "primary_reference_comparisons": "Pending separate comparison against saved primary aggregates; no primary implementation imported.",
              "planned_cases": 72, "completed_cases": sum(r["status"] == "complete" for r in results),
              "incomplete_cases": sum(r["status"] != "complete" for r in results), "cases": results}
    write_json_new(public_path, report)
    return report


def fixtures():
    """Deterministic constructed inputs only; no scientific grid simulation."""
    passed = []

    def check(condition, name):
        if not condition:
            raise AssertionError(name)
        passed.append(name)

    times = np.array([0.0, 1.0, 1.5, 2.0, 4.0])
    obs = allocate_observations(1, times)
    obs["eligible"][0] = True
    obs["first_division"][0] = 1.0
    # Root -> two daughters; first dies at 1.5, second survives to 4.
    add_cells(obs, times, np.array([0]), np.array([0.0]), np.array([1.0]), 0, np.array([-1]))
    add_cells(obs, times, np.array([0, 0]), np.array([1.0, 1.0]), np.array([1.5, 5.0]), 1, np.array([0, 1]))
    check(np.array_equal(obs["N"][0], [1, 2, 1, 1, 1]), "division/death boundary and surviving sister")
    check(np.array_equal(obs["U"][0], [1, 1, .5, .5, .5]), "fair chronological weights")
    check(np.array_equal(obs["pair_N"][0], [[0, 1], [0, 1], [0, 1]]), "equal-lag paired subtree counts")
    end = allocate_observations(1, np.array([0.0, 4.0]))
    add_cells(end, np.array([0.0, 4.0]), np.array([0]), np.array([0.0]), np.array([4.0]), 0, np.array([-1]))
    add_cells(end, np.array([0.0, 4.0]), np.array([0, 0]), np.array([4.0, 4.0]), np.array([5.0, 5.0]), 1, np.array([-1, -1]))
    check(np.array_equal(end["N"], [[1, 2]]) and np.array_equal(end["U"], [[1, 1]]), "newborns exactly at administrative endpoint")
    rootdeath = allocate_observations(1, np.array([0.0, 1.0]))
    add_cells(rootdeath, np.array([0.0, 1.0]), np.array([0]), np.array([0.0]), np.array([.5]), 0, np.array([-1]))
    check(np.array_equal(rootdeath["U"], [[1, 0]]), "root death before first division")
    check(np.array_equal(children_types(np.array([0, 1]), .5, [.1, .9, .1, .9]), [0, 1, 1, 0]), "independent daughter transition positions")
    check(np.array_equal(children_types(np.array([0, 1]), 1, [.9, .1, .9, .1]), [0, 0, 1, 1]), "perfect type copying")
    check(np.array_equal(4 - np.array([1, 2, 3, 4]) + 1, [4, 3, 2, 1]), "remaining founder stages")
    inverse = invert_calendar(np.array([0.0, .3]), integrated_calendar(np.array([1.0, 2.0])) - integrated_calendar(np.array([0.0, .3])))
    check(np.all(np.abs(inverse - [1.0, 2.0]) <= 1e-12), "calendar integrated-hazard inversion")
    check(np.isinf(invert_calendar(np.array([4.0]), np.array([1.0]))[0]), "calendar endpoint unused clock")
    check(calendar_survival_known(.3, 0, 1)[0] == 1 and calendar_survival_known(.3, 2, 0)[0] == 1, "calendar zero-lag/death identities")
    u, f = np.array([1., .5, 0., .25]), np.array([1, 1, 0, 1], bool)
    q, influence = q_estimate(u, f)
    expected = f * (u - 7 / 12) / .75
    check(abs(q["estimate"] - 7 / 12) < 1e-15 and np.allclose(influence, expected), "Q ratio and founder influence")
    check(abs(q["mcse"] - math.sqrt(float(np.sum(expected ** 2)) / 12)) < 1e-15, "Q cluster standard error")
    check(sample_se(influence - influence) == 0, "paired contrast same-array error")
    cov = covariance_estimate([0, 0, 1, 1], [0, 1, 0, 1])
    check(cov["estimate"] == 0 and abs(cov["mcse"] - 1 / math.sqrt(27)) < 1e-15, "unbiased covariance and influence SE")
    check(not q_estimate(u, np.zeros(4, bool))[0]["defined"], "zero selected denominator retained")
    check(not covariance_estimate([1], [1])["defined"], "one pair covariance undefined")
    check(precision_status(100, 0) == "unresolved_zero_mcse" and precision_status(100, 0, True) == "structural_exact", "nontrivial zero-SE handling")
    try:
        guard_cells(MAX_CELLS, 0, 1, 1)
        raise AssertionError("missing generated-cell guard")
    except SimulationFailure:
        passed.append("generated-cell guard before allocation")
    try:
        guard_cells(0, 0, MAX_FRONTIER + 1, 1)
        raise AssertionError("missing frontier guard")
    except SimulationFailure:
        passed.append("frontier guard before allocation")
    class FixedDeathFixture:
        """Deterministic input stub, not a random scientific simulation."""
        def __init__(self, lifetime):
            self.lifetime = lifetime
            self.draw_sizes = []

        def exponential(self, scale, size):
            self.draw_sizes.append(size)
            return np.full(size, self.lifetime)

    fixture_case = {"kind": "no_division", "mu": 0.0, "initialization": "newborn"}
    constant, diag = simulate_batch(fixture_case, FixedDeathFixture(10), n=1)
    check(np.all(constant["U"] == 1) and diag["generated_cells"] == 1 and not constant["eligible"][0], "zero-birth zero-death complete generator")
    fixture_case = {"kind": "deterministic", "mu": 1.0, "initialization": "newborn", "division_age": 1.0}
    fake = FixedDeathFixture(10)
    complete, diag = simulate_batch(fixture_case, fake, n=1)
    check(diag["generated_cells"] == 31 and complete["N"][0, -1] == 16 and fake.draw_sizes == [1, 2, 4, 8, 16], "full generator includes endpoint descendants and unused clocks")
    check(np.all(complete["U"] == 1) and np.array_equal(complete["pair_N"][0], [[1, 1], [2, 2], [4, 4]]), "complete generator root and sister mass")
    tie, diag = simulate_batch(fixture_case, FixedDeathFixture(1), n=1)
    check(diag["generated_cells"] == 1 and diag["deaths"] == 1 and not tie["eligible"][0], "synthetic division/death tie chooses death")
    at_cutoff, _ = simulate_batch({**fixture_case, "division_age": 2.0}, FixedDeathFixture(10), n=1)
    after_cutoff, _ = simulate_batch({**fixture_case, "division_age": 2.01}, FixedDeathFixture(10), n=1)
    check(at_cutoff["eligible"][0] and not after_cutoff["eligible"][0], "past-only pair birth cutoff")
    with tempfile.TemporaryDirectory(prefix="age-lineage-fixture-") as temporary:
        path = Path(temporary) / "batch.npz"
        save_batch_new(path, complete, {"fixture": True})
        reloaded, meta = load_batch(path)
        check(meta == {"fixture": True} and all(np.array_equal(complete[k], reloaded[k], equal_nan=True) for k in complete), "checkpoint round trip preserves labels and arrays")
        original_hash = sha256(path)
        try:
            save_batch_new(path, constant, {"fixture": "must_not_replace"})
            raise AssertionError("checkpoint overwritten")
        except FileExistsError:
            check(sha256(path) == original_hash, "first checkpoint never overwritten")
    zero_case = {"case_id": "fixture_only", "kind": "no_division", "mu": 0.0, "initialization": "newborn"}
    zero_obs, zero_diag = simulate_batch(zero_case, FixedDeathFixture(10), n=4)
    zero_report = aggregate_case(zero_case, zero_obs, zero_diag)
    check(len(zero_report["contrasts"]) == 12 and all(r["estimate"] == 0 for r in zero_report["contrasts"])
          and all(not r["defined"] for r in zero_report["pairs"])
          and zero_report["accounting"]["max_endpoint_product_error"] == 0,
          "aggregate retains 12 contrasts and structurally undefined pairs")
    return {"status": "pass", "count": len(passed), "fixtures": passed,
            "scientific_simulations_run": False, "code_sha256": sha256(__file__),
            "protocol_sha256": PROTOCOL_SHA, "created_utc": utc_now()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="Execute all frozen scientific cases, only after code review")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--fixture-report", type=Path)
    parser.add_argument("--local", type=Path, default=LOCAL, help="Fresh local run/checkpoint directory")
    parser.add_argument("--output", type=Path, default=PUBLIC, help="New aggregate path; existing results are never overwritten")
    args = parser.parse_args()
    protocol_load()
    report = fixtures()
    if args.fixture_report:
        write_json_new(args.fixture_report, report)
    print(json.dumps(report, indent=2))
    if args.run:
        run_all(folder=args.local, public_path=args.output, resume=args.resume)
    elif args.resume:
        parser.error("--resume requires --run")


if __name__ == "__main__":
    main()
