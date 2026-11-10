#!/usr/bin/env python3
"""Independent frozen-grid reference: extinction/spine and Volterra methods.

Does not import age_lineage_models or read primary numerical results. Full-grid
execution is explicit (--run); --fixtures exercises separate synthetic controls.
Reference code/design is pinned before fixtures or full-grid outcomes.
"""
from pathlib import Path
from datetime import datetime, timezone
from functools import lru_cache
from math import exp, expm1, factorial, cos, sin, pi
import argparse
import hashlib
import json
import platform
import time
import traceback
import numpy as np
from scipy.integrate import solve_ivp, quad

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/treatment-discovery/lineage-audit-2026-11-10/cell-cycle-specificity"
PROTOCOL_SHA = "e7fe08e71d614f27f7d312a6afa7cf64d8022cba2af908cc92c7965d7d6caeb5"
RTOL, ATOL = 1e-12, 1e-14
GATE = 1e-8
RUN_PROGRESS = None


def track(name, value):
    if RUN_PROGRESS is not None and RUN_PROGRESS.get("current_case") is not None:
        RUN_PROGRESS["current_case"][name] = value


def serializable(value, path="$", invalid=None):
    """Retain invalid numeric values as diagnostic strings, never hidden nulls."""
    if invalid is None:
        invalid = []
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and not np.isfinite(value):
        diagnostic = "NONFINITE:" + repr(value)
        invalid.append({"path": path, "value": diagnostic})
        return diagnostic
    if isinstance(value, dict):
        return {str(k): serializable(v, path + "." + str(k), invalid) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [serializable(v, path + "[" + str(i) + "]", invalid) for i, v in enumerate(value)]
    if isinstance(value, np.ndarray):
        return serializable(value.tolist(), path, invalid)
    return value


def write_exclusive(path, value):
    invalid = []
    clean = serializable(value, invalid=invalid)
    if invalid:
        raise ValueError("Nonfinite numeric leaves: " + repr(invalid))
    payload = json.dumps(clean, indent=2, allow_nan=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        stream.write(payload)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def integrate(fun, a, b):
    if a == b:
        return 0.0
    value, error = quad(fun, a, b, epsabs=1e-14, epsrel=1e-12, limit=200)
    if not np.isfinite(value + error):
        raise ArithmeticError("Nonfinite quadrature")
    return value


def setup(case):
    k, mu = case["k"], case["mu"]
    rates = np.array([k / m for m in case["means"]], dtype=float)
    n = len(rates)
    kernel = np.ones((1, 1)) if n == 1 else case["rho"] * np.eye(2) + (1 - case["rho"]) / 2
    weights = np.zeros((n, k))
    if case["initialization"] == "newborn":
        weights[:, 0] = 1 / n
    else:
        weights[:] = 1 / (n * k)
    return k, mu, rates, kernel, weights


@lru_cache(maxsize=None)
def extinction(k, mu, rates_tuple, rho):
    rates = np.array(rates_tuple)
    n = len(rates)
    kernel = np.ones((1, 1)) if n == 1 else rho * np.eye(2) + (1 - rho) / 2

    def rhs(x, vector):
        e = vector.reshape(n, k)
        result = mu * (1 - e) - rates[:, None] * e
        if k > 1:
            result[:, :-1] += rates[:, None] * e[:, 1:]
        sister_failure = kernel @ e[:, 0]
        result[:, -1] += rates * sister_failure ** 2
        return result.ravel()

    solution = solve_ivp(rhs, (0, 4), np.zeros(n * k), method="DOP853",
                         rtol=RTOL, atol=ATOL, dense_output=True)
    if not solution.success:
        raise ArithmeticError(solution.message)
    return solution


def stage_reference(case, horizons, queries, lags, cutoff):
    k, mu, rates, kernel, weights = setup(case)
    n = len(rates)
    ext = extinction(k, mu, tuple(rates), case["rho"])
    output = []
    track("Q_records", output)
    for horizon in horizons:
        h = 1 - float(weights.ravel() @ ext.sol(horizon))

        def rhs(u, vector):
            p = vector.reshape(n, k)
            result = -(rates[:, None] + mu) * p
            if k > 1:
                result[:, 1:] += rates[:, None] * p[:, :-1]
            sister_failure = kernel @ ext.sol(horizon - u).reshape(n, k)[:, 0]
            result[:, 0] += (rates * p[:, -1] * sister_failure) @ kernel
            return result.ravel()

        times = sorted(set(t for t in queries if t <= horizon) | {0.0, horizon})
        sol = solve_ivp(rhs, (0, horizon), weights.ravel(), method="DOP853",
                        rtol=RTOL, atol=ATOL, dense_output=True)
        if not sol.success:
            raise ArithmeticError(sol.message)
        for t in times:
            joint_ext = float(sol.sol(t) @ ext.sol(horizon - t))
            numerator = exp(-mu * t) - joint_ext
            output.append({"T": horizon, "t": t, "h": h, "joint": numerator, "Q": numerator / h})
    qualify_by_type = []
    for z, alpha in enumerate(rates):
        stage_probs = weights[z] * n

        def density(b):
            return sum(stage_probs[j] * alpha ** (k - j) * b ** (k - j - 1)
                       * exp(-(alpha + mu) * b) / factorial(k - j - 1) for j in range(k))

        qualify_by_type.append(integrate(density, 0, cutoff))
    qualify = sum(qualify_by_type) / n
    maternal = np.array(qualify_by_type) / sum(qualify_by_type)
    pair = []
    track("pairs", pair)
    for lag in lags:
        newborn = 1 - ext.sol(lag).reshape(n, k)[:, 0]
        conditional = kernel @ newborn
        mean = float(maternal @ conditional)
        joint = float(maternal @ (conditional ** 2))
        covariance = joint - mean ** 2
        identity = 0.0 if n == 1 else case["rho"] ** 2 * maternal[0] * maternal[1] * (newborn[0] - newborn[1]) ** 2
        pair.append({"s": lag, "qualification_probability": qualify,
                     "maternal_weights": maternal.tolist(), "daughter_mean": mean,
                     "joint": joint, "covariance": covariance,
                     "two_type_identity": float(identity), "calendar_residual": None})
    return output, pair, ext


@lru_cache(maxsize=None)
def deterministic_h(duration, mu, d=1.0):
    if duration < d:
        return exp(-mu * duration)
    child = deterministic_h(duration - d, mu, d)
    return exp(-mu * d) * (2 * child - child ** 2)


def deterministic_q(t, horizon, mu, d=1.0):
    # Post-division convention at exact deterministic boundaries.
    generations = int(t // d)
    age = t - generations * d
    remaining = horizon - t
    next_division = d - age
    if remaining < next_division:
        current_h = exp(-mu * remaining)
    else:
        daughter_h = deterministic_h(remaining - next_division, mu, d)
        current_h = exp(-mu * next_division) * (2 * daughter_h - daughter_h ** 2)
    all_sisters_fail = 1.0
    for generation in range(1, generations + 1):
        all_sisters_fail *= 1 - deterministic_h(horizon - generation * d, mu, d)
    joint = exp(-mu * t) * (1 - (1 - current_h) * all_sisters_fail)
    h = deterministic_h(horizon, mu, d)
    return {"T": horizon, "t": t, "h": h, "joint": joint, "Q": joint / h}


def calendar_lambda(t):
    return 1 + 0.5 * sin(pi * t)


def calendar_integral(t):
    return t + 0.5 / pi * (1 - cos(pi * t))


def calendar_h(birth, horizon, mu):
    integral = integrate(lambda u: exp(-(calendar_integral(u) - calendar_integral(birth)
                                        - mu * (u - birth))), birth, horizon)
    return 1 / (1 + mu * integral)


def calendar_reference(case, horizons, queries, lags, cutoff):
    mu = case["mu"]
    output = []
    track("Q_records", output)
    for horizon in horizons:
        h = calendar_h(0, horizon, mu)
        for t in sorted(set(x for x in queries if x <= horizon) | {0.0, horizon}):
            sisters_fail = exp(-integrate(lambda u: calendar_lambda(u) * calendar_h(u, horizon, mu), 0, t))
            joint = exp(-mu * t) * (1 - (1 - calendar_h(t, horizon, mu)) * sisters_fail)
            output.append({"T": horizon, "t": t, "h": h, "joint": joint, "Q": joint / h})
    density = lambda b: calendar_lambda(b) * exp(-calendar_integral(b) - mu * b)
    qualify = integrate(density, 0, cutoff)
    pairs = []
    track("pairs", pairs)
    for lag in lags:
        mean = integrate(lambda b: density(b) * calendar_h(b, b + lag, mu), 0, cutoff) / qualify
        joint = integrate(lambda b: density(b) * calendar_h(b, b + lag, mu) ** 2, 0, cutoff) / qualify
        pairs.append({"s": lag, "qualification_probability": qualify, "maternal_weights": [1.0],
                      "daughter_mean": mean, "joint": joint, "covariance": joint - mean ** 2,
                      "two_type_identity": None, "calendar_residual": 0.0})
    return output, pairs


def basis_matrix(points, nodes):
    weights = (-1.0) ** np.arange(len(nodes))
    weights[[0, -1]] *= 0.5
    difference = points[:, None] - nodes[None, :]
    exact = difference == 0
    safe = np.where(exact, 1.0, difference)
    terms = weights / safe
    result = terms / terms.sum(axis=1, keepdims=True)
    for i in np.flatnonzero(exact.any(axis=1)):
        result[i] = exact[i].astype(float)
    return result


def volterra_scaled(k, mu, rates, kernel, gfun, t, order, quadrature_order):
    """Scaled positive-defect integral equation, no differential-equation solve.

    Solve newborn components by Chebyshev-Lobatto collocation and evaluate all
    residual stages by mapped Gauss-Legendre quadrature. gfun(w)=K h(T-t+t*w).
    """
    n = len(rates)
    nodes = (1 - np.cos(np.pi * np.arange(order) / (order - 1))) / 2
    gauss, gauss_weights = np.polynomial.legendre.leggauss(quadrature_order)
    operator = np.zeros((n * order, n * order))
    forcing = np.zeros((n, order))
    for i, u in enumerate(nodes):
        if u == 0:
            continue
        w = (gauss + 1) * u / 2
        qw = gauss_weights * u / 2
        basis = basis_matrix(w, nodes)
        g = gfun(w)
        source = mu * w if t == 0 else -np.expm1(-mu * t * w) / t
        for z, alpha in enumerate(rates):
            density = alpha ** k / factorial(k - 1) * (u - w) ** (k - 1) * np.exp(-(alpha + mu) * t * (u - w))
            forcing[z, i] = np.sum(qw * density * source * g[z])
            row = (qw * density * t ** k * (1 - g[z])) @ basis
            for v in range(n):
                operator[z * order + i, v * order:(v + 1) * order] = kernel[z, v] * row
    values = np.linalg.solve(np.eye(n * order) - operator, forcing.ravel()).reshape(n, order)
    residual = float(np.max(np.abs((np.eye(n * order) - operator) @ values.ravel() - forcing.ravel())))
    w, qw = (gauss + 1) / 2, gauss_weights / 2
    basis = basis_matrix(w, nodes)
    g = gfun(w)
    source = mu * w if t == 0 else -np.expm1(-mu * t * w) / t
    inner = t ** k * (1 - g) * (kernel @ values @ basis.T) + g * source
    stages = np.zeros((n, k))
    for z, alpha in enumerate(rates):
        for j in range(k):
            remaining = k - j
            density = alpha ** remaining / factorial(remaining - 1) * (1 - w) ** (remaining - 1) * np.exp(-(alpha + mu) * t * (1 - w))
            stages[z, j] = np.sum(qw * density * inner[z])
    return stages, residual


def early_reference(case, ext, horizon, epsilon, order, quadrature_order):
    k, mu, rates, kernel, weights = setup(case)
    n = len(rates)
    t = epsilon / max(rates)

    def gfun(w):
        values = ext.sol(horizon - t + t * w).reshape(n, k, len(w))
        return kernel @ (1 - values[:, 0, :])

    stages, residual = volterra_scaled(k, mu, rates, kernel, gfun, t, order, quadrature_order)
    newborn_h = 1 - ext.sol(horizon).reshape(n, k)[:, 0]
    g = kernel @ newborn_h
    h_initial = 1 - float(weights.ravel() @ ext.sol(horizon))
    if case["initialization"] == "newborn":
        power = k + 1
        scaled = float(np.mean(stages[:, 0]))
        leading_joint = float(mu * np.mean(rates ** k * g) / factorial(k + 1))
    else:
        power = 2
        scaled = float(np.sum(weights * stages * t ** np.arange(k - 1, -1, -1)))
        leading_joint = float(mu * np.mean(rates * g / k) / 2)
    ratio = None if mu == 0 else scaled / leading_joint
    return {"T": horizon, "epsilon": epsilon, "t": t, "power": power,
            "leading_coefficient": leading_joint / h_initial, "scaled_joint": scaled,
            "loss": t ** power * scaled / h_initial, "ratio": ratio,
            "collocation_order": order, "quadrature_order": quadrature_order,
            "linear_system_residual": residual}


def fixtures():
    checks = []
    # Separate values outside the main scientific grid.
    case = {"kind": "erlang", "k": 1, "mu": 0.7, "means": [1 / 1.3], "rho": 0.0, "initialization": "newborn"}
    qs, pairs, ext = stage_reference(case, [0.9], [0.0, 0.2, 0.7], [0.3], 0.6)
    for row in qs:
        t = row["t"]
        expected = (1.3 * exp(-0.7 * t) - 0.7 * exp(-1.3 * t)) / 0.6
        assert abs(row["Q"] - expected) < GATE
    checks.append("homogeneous_k1_analytic_spine")
    assert abs(pairs[0]["covariance"]) < GATE
    expected_q = 1.3 / 2.0 * (-expm1(-2.0 * 0.6))
    assert abs(pairs[0]["qualification_probability"] - expected_q) < GATE
    checks.append("competing_first_division_integral")
    for horizon in (1.4, 1.7):
        q = deterministic_q(1.2, horizon, 0.7)["Q"]
        x, y = exp(-0.7 * 0.2), exp(-0.7 * (horizon - 1))
        assert abs(q - (1 + x - y) / (2 - y)) < GATE
    checks.append("deterministic_sister_product")
    qs, pair = calendar_reference({"mu": 0.7}, [0.9, 1.2], [0.2, 0.7], [0.3], 0.6)
    for row in qs:
        t = row["t"]
        expected = exp(-calendar_integral(t)) + exp(-0.7 * t) * integrate(lambda u: calendar_lambda(u) * exp(0.7 * u - calendar_integral(u)), 0, t)
        assert abs(row["Q"] - expected) < GATE
    checks.append("calendar_reciprocal_quadrature_and_spine")
    nodes = (1 - np.cos(np.pi * np.arange(24) / 23)) / 2
    assert np.max(np.abs(basis_matrix(nodes, nodes) - np.eye(24))) < 1e-14
    checks.append("barycentric_node_reproduction")
    rates, kernel = np.array([1.3, 2.1]), np.array([[0.7, 0.3], [0.3, 0.7]])
    constant = np.array([0.4, 0.8])
    stages, residual = volterra_scaled(3, 0.7, rates, kernel, lambda w: np.repeat(constant[:, None], len(w), axis=1), 0.0, 24, 48)
    expected = np.array([[0.7 * alpha ** (3 - j) * constant[z] / factorial(4 - j) for j in range(3)] for z, alpha in enumerate(rates)])
    assert np.max(np.abs(stages - expected)) < 1e-12 and residual < 1e-12
    checks.append("volterra_zero_t_triangular_coefficient")
    stages, _ = volterra_scaled(3, 0.0, rates, kernel, lambda w: np.ones((2, len(w))), 0.003, 24, 48)
    assert np.array_equal(stages, np.zeros_like(stages))
    checks.append("volterra_zero_death")
    return {"passed": True, "checks": checks, "fixture_count": len(checks),
            "scope": "Separate deterministic code fixtures; no main-grid outcomes or production output read."}


def run_grid(plan):
    global RUN_PROGRESS
    started = time.monotonic()
    times = plan["times"]
    horizons, queries = times["selection_horizons"], times["evaluation_times"]
    lags, cutoff = times["pair_lags"], times["pair_birth_cutoff"]
    all_cases = []
    RUN_PROGRESS = {"completed_cases": all_cases, "current_case": None}
    for case in plan["cases"]:
        RUN_PROGRESS["current_case"] = {"configuration": case}
        kind, mu = case["kind"], case["mu"]
        early, extra = [], []
        track("early_records", early)
        track("deterministic_extras", extra)
        if kind == "erlang":
            output, pair, ext = stage_reference(case, horizons, queries, lags, cutoff)
            for horizon in horizons:
                for epsilon in (0.01, 0.001, 0.0001):
                    low = early_reference(case, ext, horizon, epsilon, 24, 48)
                    track("pending_early", {"T": horizon, "epsilon": epsilon, "lower_order": low})
                    high = early_reference(case, ext, horizon, epsilon, 40, 80)
                    track("pending_early", {"T": horizon, "epsilon": epsilon, "lower_order": low, "higher_order": high})
                    difference = 0.0 if mu == 0 else abs(low["ratio"] - high["ratio"])
                    assert difference <= GATE
                    high["lower_order_ratio"] = low["ratio"]
                    high["order_difference"] = difference
                    if mu == 0:
                        assert high["scaled_joint"] == high["loss"] == 0
                    else:
                        assert high["ratio"] > 0
                        assert exp(-3 * epsilon) - 1e-7 <= high["ratio"] <= exp(6 * epsilon) + 1e-7
                        if epsilon == 0.0001:
                            assert abs(high["ratio"] - 1) <= 0.01
                    early.append(high)
        elif kind == "deterministic":
            output = []
            track("Q_records", output)
            for h in horizons:
                for t in sorted(set(x for x in queries if x <= h) | {0.0, h}):
                    output.append(deterministic_q(t, h, mu, case["division_age"]))
            pair = [{"s": lag, "qualification_probability": exp(-mu * case["division_age"]),
                     "maternal_weights": [1.0], "daughter_mean": deterministic_h(lag, mu),
                     "joint": deterministic_h(lag, mu) ** 2, "covariance": 0.0,
                     "two_type_identity": None, "calendar_residual": None} for lag in lags]
            for h in times["deterministic_extra_horizons"]:
                extra.append(deterministic_q(times["deterministic_extra_evaluation_time"], h, mu))
        elif kind == "calendar":
            output, pair = calendar_reference(case, horizons, queries, lags, cutoff)
        elif kind == "no_division":
            output = [{"T": h, "t": t, "h": exp(-mu * h), "joint": exp(-mu * h), "Q": 1.0}
                      for h in horizons for t in sorted(set(x for x in queries if x <= h) | {0.0, h})]
            pair = [{"s": lag, "qualification_probability": 0.0, "maternal_weights": None,
                     "daughter_mean": None, "joint": None, "covariance": None,
                     "two_type_identity": None, "calendar_residual": None} for lag in lags]
        else:
            raise ValueError(kind)
        track("Q_records", output)
        track("pairs", pair)
        index = {(r["T"], r["t"]): r for r in output}
        contrasts = [{"earlier_T": e, "later_T": l, "t": t,
                      "contrast": index[l, t]["Q"] - index[e, t]["Q"]}
                     for e, l in times["contrast_pairs"] for t in queries]
        track("contrasts", contrasts)
        for row in output:
            assert -GATE <= row["joint"] <= min(row["h"], exp(-mu * row["t"])) + GATE
            assert -GATE <= row["Q"] <= 1 + GATE
            if row["t"] == 0:
                assert abs(row["Q"] - 1) <= GATE
            if row["t"] == row["T"]:
                assert abs(row["joint"] - exp(-mu * row["t"])) <= GATE
        for row in pair:
            if row["two_type_identity"] is not None:
                assert abs(row["covariance"] - row["two_type_identity"]) <= GATE
        all_cases.append({"case_id": case["case_id"], "model": case, "Q_records": output,
                          "contrasts": contrasts, "pairs": pair, "deterministic_extras": extra,
                          "early_records": early})
    RUN_PROGRESS["current_case"] = None
    return {"generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "REFERENCE_GENERATED_WITHOUT_READING_PRODUCTION_OUTPUT",
            "protocol_sha256": PROTOCOL_SHA, "script_sha256": sha(__file__),
            "runtime_seconds": time.monotonic() - started,
            "environment": {"python": platform.python_version(), "numpy": np.__version__},
            "method": "Independent extinction/forward spine; scalar reciprocal calendar quadrature; deterministic discarded-sister product; scaled Volterra collocation.",
            "numeric_settings": {"rtol": RTOL, "atol": ATOL, "absolute_gate": GATE,
                                 "collocation_orders": [24, 40], "quadrature_orders": [48, 80]},
            "counts": {"cases": len(all_cases), "contrasts": sum(len(c["contrasts"]) for c in all_cases),
                       "pair_records": sum(len(c["pairs"]) for c in all_cases),
                       "early_records": sum(len(c["early_records"]) for c in all_cases)},
            "cases": all_cases,
            "limits": ["Numerical verification of stipulated hypothetical models, not empirical or biological validation.",
                       "No production module imported or production output read by this script.",
                       "Volterra order agreement is a numerical check; the finite-epsilon envelope has a separate analytic proof."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    assert sha(BASE / "protocol.json") == PROTOCOL_SHA
    if args.fixtures == args.run:
        parser.error("Choose exactly one of --fixtures or --run")
    destination = args.out or (ROOT / "tmp/age-lineage-2026-11-10/reference-fixtures.json" if args.fixtures
                               else BASE / "independent-reference.json")
    if destination.exists():
        raise FileExistsError("Refusing to overwrite first output: " + str(destination))
    try:
        if args.fixtures:
            result = fixtures()
            result.update(created_utc=datetime.now(timezone.utc).isoformat(), protocol_sha256=PROTOCOL_SHA,
                          script_sha256=sha(__file__))
        else:
            result = run_grid(json.loads((BASE / "protocol.json").read_text()))
        write_exclusive(destination, result)
    except (Exception, KeyboardInterrupt) as error:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        failure = destination.with_name(destination.stem + ".failure-" + stamp + ".json")
        invalid = []
        payload = serializable({"status": "FAILED_OR_INCOMPLETE", "error_type": type(error).__name__,
                                "error": str(error), "traceback": traceback.format_exc(),
                                "protocol_sha256": PROTOCOL_SHA, "script_sha256": sha(__file__),
                                "progress": RUN_PROGRESS, "destination": str(destination)}, invalid=invalid)
        payload["nonfinite_diagnostics"] = invalid
        write_exclusive(failure, payload)
        print(json.dumps({"status": "FAILED_OR_INCOMPLETE", "failure_artifact": str(failure)}))
        raise
    print(json.dumps({k: result[k] for k in result if k not in ("cases",)}, indent=2))


if __name__ == "__main__":
    main()
