#!/usr/bin/env python3
"""Check a finite-horizon identity for shared calendar-time branching rates.

No data, random draws, fitted parameters, or root-simulator imports are used.
The derivation was known before the local protocol freeze. This numerical
verification compares backward branching survival/PGFL to direct quadrature
and an independently solved forward two-state system.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform

import numpy as np
import scipy
from scipy.integrate import quad, solve_ivp


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/treatment-discovery/lineage-audit-2026-11-10/horizon-invariance"
PROTOCOL = BASE / "protocol.json"
FROZEN_HASH = "752885ddeb5de119deaa3a36dcd1d28e2735cf6bc222add08bb3dfb150133996"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rates(case, t):
    if case == "constant_unequal":
        return 0.5, 2.0
    if case == "constant_equal":
        return 2.0, 2.0
    if case == "increasing_both":
        return 0.4 + 0.2 * t, 0.3 + 0.35 * t
    if case == "increasing_birth_decreasing_death":
        return 0.5 + 0.15 * t, 2.5 / (1 + 0.7 * t)
    if case == "piecewise_opposite":
        return (0.3, 2.0) if t < 0.8 else ((2.2, 0.4) if t < 2 else (0.6, 1.8))
    if case == "oscillatory":
        return 1.1 + 0.7 * np.sin(1.3 * t), 1.2 + 0.7 * np.cos(0.9 * t)
    if case == "zero_birth":
        return 0.0, 0.4 + 0.2 * t
    if case == "zero_death":
        return 0.3 + 0.15 * t, 0.0
    if case == "zero_both":
        return 0.0, 0.0
    raise ValueError(case)


def cumulative_rates(case, t):
    if case == "constant_unequal":
        return 0.5 * t, 2.0 * t
    if case == "constant_equal":
        return 2.0 * t, 2.0 * t
    if case == "increasing_both":
        return 0.4 * t + 0.1 * t * t, 0.3 * t + 0.175 * t * t
    if case == "increasing_birth_decreasing_death":
        return 0.5 * t + 0.075 * t * t, (2.5 / 0.7) * np.log1p(0.7 * t)
    if case == "piecewise_opposite":
        a, b, c = min(t, 0.8), max(0.0, min(t, 2.0) - 0.8), max(0.0, t - 2.0)
        return 0.3 * a + 2.2 * b + 0.6 * c, 2.0 * a + 0.4 * b + 1.8 * c
    if case == "oscillatory":
        return 1.1 * t + (0.7 / 1.3) * (1 - np.cos(1.3 * t)), 1.2 * t + (0.7 / 0.9) * np.sin(0.9 * t)
    if case == "zero_birth":
        return 0.0, 0.4 * t + 0.1 * t * t
    if case == "zero_death":
        return 0.3 * t + 0.075 * t * t, 0.0
    if case == "zero_both":
        return 0.0, 0.0
    raise ValueError(case)


def breakpoints(case, endpoint):
    return [x for x in [0.8, 2.0] if 0 < x < endpoint] if case == "piecewise_opposite" else []


def integrate(fn, endpoint, case, cfg):
    if endpoint == 0:
        return 0.0
    points = [0.0] + breakpoints(case, endpoint) + [endpoint]
    return sum(quad(fn, a, b, epsabs=cfg["quadrature_epsabs"],
                    epsrel=cfg["quadrature_epsrel"], limit=200)[0]
               for a, b in zip(points[:-1], points[1:]))


def ode_solution(case, endpoint, backward, cfg):
    points = [0.0] + breakpoints(case, endpoint) + [endpoint]
    if backward:
        points = points[::-1]
    y = np.array([1.0]) if backward else np.array([1.0, 0.0])
    pieces = []
    for a, b in zip(points[:-1], points[1:]):
        # Piecewise rates use the segment interior at both integration endpoints.
        mid = (a + b) / 2
        def rhs(t, values):
            lam, mu = rates(case, mid if case == "piecewise_opposite" else t)
            if backward:
                h = values[0]
                return [(mu - lam) * h + lam * h * h]
            x1, x2 = values
            return [-lam * x1, lam * x1 - mu * x2]
        result = solve_ivp(rhs, (a, b), y, method=cfg["ode_method"],
                           rtol=cfg["ode_rtol"], atol=cfg["ode_atol"],
                           max_step=cfg["ode_max_step"], dense_output=True)
        if not result.success:
            raise RuntimeError(result.message)
        pieces.append((min(a, b), max(a, b), result.sol))
        y = result.y[:, -1]
    def evaluate(t):
        for lo, hi, sol in pieces:
            if lo <= t <= hi:
                return sol(t)
        raise ValueError(f"Time outside domain: {t}")
    return evaluate


def run():
    if sha256(PROTOCOL) != FROZEN_HASH:
        raise ValueError("Frozen protocol hash mismatch")
    protocol = json.loads(PROTOCOL.read_text())
    cfg = protocol["numerics"]
    threshold = cfg["absolute_agreement_threshold"]
    rows, horizon_checks, failures = [], [], []
    maximum_errors = {key: 0.0 for key in ["pgfl_vs_direct", "forward_vs_direct", "endpoint_joint_identity", "horizon_spread", "zero_control", "constant_closed_form"]}
    for definition in protocol["rate_cases"]:
        case = definition["id"]
        shared = {}
        for horizon in protocol["horizons"]:
            h = ode_solution(case, horizon, True, cfg)
            forward = ode_solution(case, horizon, False, cfg)
            h0 = float(h(0)[0])
            if not 0 < h0 <= 1 + cfg["probability_range_tolerance"]:
                failures.append({"case": case, "T": horizon, "check": "positive_family_inclusion", "value": h0})
            times = sorted(set([horizon * f for f in protocol["time_fractions_each_horizon"]] + [t for t in protocol["additional_shared_absolute_times_when_le_horizon"] if t <= horizon]))
            last = {"pgfl": 1.0, "direct": 1.0, "forward": 1.0}
            for t in times:
                L, M = cumulative_rates(case, t)
                A = np.exp(-integrate(lambda u: rates(case, u)[0] * h(u)[0], t, case, cfg))
                pgfl = float(np.exp(-M) * (1 - (1 - h(t)[0]) * A) / h0)
                def integrand(u):
                    Lu, Mu = cumulative_rates(case, u)
                    return rates(case, u)[0] * np.exp(Mu - Lu)
                direct = float(np.exp(-L) + np.exp(-M) * integrate(integrand, t, case, cfg))
                forward_q = float(sum(forward(t)))
                errors = {"pgfl_vs_direct": abs(pgfl - direct), "forward_vs_direct": abs(forward_q - direct)}
                if t == horizon:
                    errors["endpoint_joint_identity"] = abs(pgfl * h0 - np.exp(-M))
                if case.startswith("zero_"):
                    errors["zero_control"] = max(abs(pgfl - 1), abs(direct - 1), abs(forward_q - 1))
                if case.startswith("constant_"):
                    lam, mu = rates(case, 0)
                    closed = np.exp(-lam * t) * (1 + lam * t) if lam == mu else (lam * np.exp(-mu * t) - mu * np.exp(-lam * t)) / (lam - mu)
                    errors["constant_closed_form"] = abs(direct - closed)
                for key, value in errors.items():
                    maximum_errors[key] = max(maximum_errors[key], value)
                    if value > threshold:
                        failures.append({"case": case, "T": horizon, "t": t, "check": key, "value": value})
                values = {"pgfl": pgfl, "direct": direct, "forward": forward_q}
                for key, value in values.items():
                    tol = cfg["probability_range_tolerance"]
                    if value < -tol or value > 1 + tol or value > last[key] + tol or (t == 0 and abs(value - 1) > tol):
                        failures.append({"case": case, "T": horizon, "t": t, "check": "probability_or_monotonicity", "method": key, "value": value})
                    last[key] = value
                rows.append({"case": case, "T": horizon, "t": t, "family_survival_h0T": h0, **values, "errors": errors})
                if t in protocol["additional_shared_absolute_times_when_le_horizon"]:
                    shared.setdefault(t, []).append({"T": horizon, "pgfl": pgfl})

        for t, vals in sorted(shared.items()):
            if len(vals) > 1:
                spread = max(x["pgfl"] for x in vals) - min(x["pgfl"] for x in vals)
                maximum_errors["horizon_spread"] = max(maximum_errors["horizon_spread"], spread)
                horizon_checks.append({"case": case, "t": t, "values": vals, "spread": spread})
                if spread > cfg["shared_time_horizon_spread_threshold"]:
                    failures.append({"case": case, "t": t, "check": "horizon_spread", "value": spread})
    return {"generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "PASS" if not failures else "FAIL", "seed": None,
            "type": "Deterministic mathematical verification; no empirical data or fitted outcomes",
            "protocol_sha256": sha256(PROTOCOL), "script_sha256": sha256(Path(__file__).resolve()),
            "environment": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__, "platform": platform.platform()},
            "case_count": len(protocol["rate_cases"]), "case_horizon_time_count": len(rows),
            "shared_time_horizon_checks": len(horizon_checks), "maximum_absolute_errors": maximum_errors,
            "failures": failures, "horizon_comparisons": horizon_checks, "all_points": rows,
            "limits": protocol["not_covered"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=BASE / "results.json")
    args = parser.parse_args()
    result = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({key: result[key] for key in ["status", "case_count", "case_horizon_time_count", "shared_time_horizon_checks", "maximum_absolute_errors", "failures", "protocol_sha256", "script_sha256"]}, indent=2))
    raise SystemExit(0 if result["status"] == "PASS" else 1)
