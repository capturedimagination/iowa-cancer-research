#!/usr/bin/env python3
"""Independent reference for the frozen age/calendar calibration study.

Extinction/forward-spine ODEs, adaptive Gauss-Kronrod integration, closed
finite-sample moments, and separate direct physical-time/small enumeration
fixtures. No imports of production modules and no reading of primary outcomes.
Full scientific execution is explicit (--run); code is pinned first (--pin).
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from fractions import Fraction
from functools import lru_cache
import hashlib
import json
from math import comb, cos, exp, factorial, pi, sin
from pathlib import Path
import platform
import sys
import time
import traceback

import numpy as np
import scipy
from scipy.integrate import quad, quad_vec, solve_ivp
from scipy.special import gammainc

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/treatment-discovery/lineage-audit-2026-11-10/age-calendar-calibration"
PROTOCOL = BASE / "protocol.json"
PROTOCOL_SHA = "53d76bf43d0b1f47355d57d95ec6d7f43fce67541aed7631510a3cbff0b42919"
THEORY_SHA = "81ed3527f55327728152a5306393ca9160cb5e780b77e79daf1b3edb18f7d99f"
RTOL, ATOL = 2e-13, 2e-15
QUAD_ABS, QUAD_REL = 2e-13, 2e-12
GATE = 1e-8
METHODS = ("oracle_bin_mean", "shared_fitted_mean",
           "shared_fitted_mean_corrected", "unbiased_target_sample_covariance")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def portable(path):
    try:
        return str(Path(path).resolve().relative_to(ROOT))
    except ValueError:
        return "<external>/" + Path(path).name


def clean(value, path="$", invalid=None):
    """Failures retain nonfinite values as labelled diagnostics, never null."""
    if invalid is None:
        invalid = []
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, np.ndarray):
        value = value.tolist()
    if isinstance(value, float) and not np.isfinite(value):
        item = "NONFINITE:" + repr(value)
        invalid.append({"path": path, "value": item})
        return item
    if isinstance(value, dict):
        return {str(k): clean(v, path + "." + str(k), invalid) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v, f"{path}[{i}]", invalid) for i, v in enumerate(value)]
    return value


def write_once(path, value):
    invalid = []
    value = clean(value, invalid=invalid)
    if invalid:
        raise ArithmeticError("Nonfinite scientific values: " + repr(invalid))
    payload = json.dumps(value, indent=2, allow_nan=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        stream.write(payload)


def integrate(fun, left, right):
    value, error, info = quad_vec(fun, left, right, epsabs=QUAD_ABS,
                                  epsrel=QUAD_REL, quadrature="gk21",
                                  limit=500, full_output=True)
    if not info.success or not np.all(np.isfinite(value)) or not np.isfinite(error):
        raise ArithmeticError("Adaptive quadrature failed: " + str(info.message))
    return np.asarray(value), float(error)


def solved(fun, interval, initial):
    result = solve_ivp(fun, interval, initial, method="DOP853", rtol=RTOL,
                       atol=ATOL, dense_output=True)
    if not result.success or not np.all(np.isfinite(result.y)):
        raise ArithmeticError("ODE failed: " + str(result.message))
    return result


@lru_cache(maxsize=None)
def extinction(k, mu, rates_tuple, rho, end):
    rates = np.array(rates_tuple)
    types = len(rates)
    kernel = rho * np.eye(types) + (1 - rho) / types

    def rhs(_, vector):
        e = vector.reshape(types, k)
        change = mu * (1 - e) - rates[:, None] * e
        if k > 1:
            change[:, :-1] += rates[:, None] * e[:, 1:]
        change[:, -1] += rates * (kernel @ e[:, 0]) ** 2
        return change.ravel()

    return solved(rhs, (0, end), np.zeros(types * k))


class Model:
    def __init__(self, case, end=4.0):
        self.case = case
        self.k = int(case["k"])
        self.mu = float(case["mu"])
        self.rates = np.array([self.k / m for m in case["means"]])
        self.types = len(self.rates)
        self.rho = float(case["rho"])
        self.kernel = self.rho * np.eye(self.types) + (1 - self.rho) / self.types
        self.weights = np.zeros((self.types, self.k))
        if case["initialization"] == "newborn":
            self.weights[:, 0] = 1 / self.types
        elif case["initialization"] == "uniform_stage":
            self.weights[:] = 1 / (self.types * self.k)
        else:
            raise ValueError("Unknown initialization")
        self.end = float(self.clock(end))
        self.ext = extinction(self.k, self.mu, tuple(self.rates), self.rho, self.end)

    def rate(self, b):
        return 1 + self.case["amplitude"] * sin(2 * pi * b / self.case["period"])

    def clock(self, b):
        a, period = self.case["amplitude"], self.case["period"]
        return b + a * period / (2 * pi) * (1 - cos(2 * pi * b / period))

    def h(self, operational_duration):
        if operational_duration < -1e-13 or operational_duration > self.end + 1e-13:
            raise ValueError("Extinction evaluation outside integration interval")
        return 1 - self.ext.sol(operational_duration).reshape(self.types, self.k)

    def density(self, b):
        """Unnormalized qualifying maternal-type density per founder."""
        u = self.clock(b)
        answer = np.zeros(self.types)
        for z, alpha in enumerate(self.rates):
            for j in range(self.k):
                remaining = self.k - j
                answer[z] += (self.weights[z, j] * alpha ** remaining
                              * u ** (remaining - 1) / factorial(remaining - 1))
            answer[z] *= exp(-(alpha + self.mu) * u) * self.rate(b)
        return answer

    def gamma_eligibility(self, cutoff):
        u = self.clock(cutoff)
        return sum(self.weights[z, j] * (alpha / (alpha + self.mu)) ** (self.k - j)
                   * gammainc(self.k - j, (alpha + self.mu) * u)
                   for z, alpha in enumerate(self.rates) for j in range(self.k))

    def q_records(self, horizon, physical_times):
        tau = self.clock(horizon)
        family = float(np.sum(self.weights * self.h(tau)))

        def rhs(u, vector):
            spine = vector.reshape(self.types, self.k)
            change = -(self.rates[:, None] + self.mu) * spine
            if self.k > 1:
                change[:, 1:] += self.rates[:, None] * spine[:, :-1]
            failure = self.kernel @ self.ext.sol(tau - u).reshape(self.types, self.k)[:, 0]
            change[:, 0] += (self.rates * spine[:, -1] * failure) @ self.kernel
            return change.ravel()

        spine = solved(rhs, (0, tau), self.weights.ravel())
        rows = []
        for t in physical_times:
            s = self.clock(t)
            failed_mass = float(spine.sol(s) @ self.ext.sol(tau - s))
            joint = exp(-self.mu * s) - failed_mass
            value = joint / family
            if self.mu == 0:
                value, joint, family = 1.0, 1.0, 1.0
            rows.append({"t": float(t), "T": float(horizon), "value": value,
                         "joint_probability": joint})
        return family, rows

    def pair_integrals(self, left, right, lag, mass):
        def integrand(b):
            f = self.density(b)
            total = float(f.sum())
            if total == 0:
                return np.zeros(4)
            delta = self.clock(b + lag) - self.clock(b)
            g = self.kernel @ self.h(delta)[:, 0]
            p = float(f @ g / total)
            conditional_cov = float(f @ (g - p) ** 2)
            return np.array([f @ g, f @ (g * g), conditional_cov, total * p * p])

        values, error = integrate(integrand, left, right)
        p, j, average_conditional, second_context_mean = values / mass
        if self.mu == 0:
            p, j, average_conditional, second_context_mean = 1.0, 1.0, 0.0, 1.0
        c = j - p * p
        birth_variance = second_context_mean - p * p
        bound = None
        if self.types == 1 or self.rho == 0:
            lipschitz = (2 * self.mu * self.case["amplitude"]
                         * abs(sin(pi * lag / self.case["period"])))
            bound = min(0.25, lipschitz ** 2 * (right - left) ** 2 / 4)
        return {"p": float(p), "j": float(j), "c": float(c),
                "mean_conditional_covariance": float(average_conditional),
                "birth_probability_variance": float(birth_variance),
                "no_transmission_bound": bound,
                "adaptive_quadrature_error_estimate": error}


def moments(p, j, m, n):
    """Closed finite-sample expressions; accepts Fraction for exact fixtures."""
    v, c = p * (1 - p), j - p * p
    a = v * v - c * c + c * (1 - 2 * p) ** 2
    common = (a + 2 * v * (v + c) / m) / n
    return {
        "oracle_bin_mean": {"mean": c, "variance": a / n, "range": [-0.25, 1.0]},
        "shared_fitted_mean": {"mean": c + v / m,
            "variance": common + 2 * v * v / (m * m) + v * (1 - 6 * v) / (m ** 3),
            "range": [-0.25, 1.0]},
        "shared_fitted_mean_corrected": {"mean": c,
            "variance": common + 2 * v * v / (m * (m - 1)),
            "range": [-m / (4 * (m - 1)), 1.0]},
        "unbiased_target_sample_covariance": {"mean": c,
            "variance": a / n + (v * v + c * c) / (n * (n - 1)),
            "range": [-n / (4 * (n - 1)), n / (4 * (n - 1))]},
    }


def physical_backward(model, t, horizon):
    """Separate direct-calendar positive H/J fixture; no time-change RHS."""
    def h_rhs(b, vector):
        h = vector.reshape(model.types, model.k)
        a, d = model.rates * model.rate(b), model.mu * model.rate(b)
        change = (a[:, None] + d) * h
        if model.k > 1:
            change[:, :-1] -= a[:, None] * h[:, 1:]
        g = model.kernel @ h[:, 0]
        change[:, -1] -= a * (2 * g - g * g)
        return change.ravel()

    hsol = solved(h_rhs, (horizon, 0), np.ones(model.types * model.k))

    def j_rhs(b, vector):
        joint = vector.reshape(model.types, model.k)
        a, d = model.rates * model.rate(b), model.mu * model.rate(b)
        h = hsol.sol(b).reshape(model.types, model.k)
        g = model.kernel @ h[:, 0]
        marked = model.kernel @ joint[:, 0]
        # Independently integrate the physical death schedule, not R(t)-R(b).
        accumulated, _ = quad(lambda u: model.mu * model.rate(u), b, t,
                              epsabs=1e-13, epsrel=1e-12)
        tag_survival = exp(-accumulated)
        change = (a[:, None] + d) * joint
        if model.k > 1:
            change[:, :-1] -= a[:, None] * joint[:, 1:]
        change[:, -1] -= a * ((1 - g) * marked + tag_survival * g)
        return change.ravel()

    jsol = solved(j_rhs, (t, 0), hsol.sol(t))
    family = float(model.weights.ravel() @ hsol.sol(0))
    joint = float(model.weights.ravel() @ jsol.sol(0))
    return hsol, family, joint / family


def enumerate_moments(p, c, m, n):
    """Exact rational four-category/binomial count enumeration, fixtures only."""
    j = p * p + c
    probs = [1 - 2 * p + j, p - j, p - j, j]  # 00,01,10,11
    means = {name: Fraction(0) for name in METHODS}
    seconds = means.copy()
    cross_sc = Fraction(0)
    probability_sum = Fraction(0)
    for x in range(m + 1):
        training_weight = comb(m, x) * p ** x * (1 - p) ** (m - x)
        q = Fraction(x, m)
        for n00 in range(n + 1):
            for n01 in range(n - n00 + 1):
                for n10 in range(n - n00 - n01 + 1):
                    n11 = n - n00 - n01 - n10
                    counts = [n00, n01, n10, n11]
                    weight = training_weight
                    denominator = 1
                    for count, prob in zip(counts, probs):
                        denominator *= factorial(count)
                        weight *= prob ** count
                    weight *= factorial(n) // denominator
                    total1, total2 = n10 + n11, n01 + n11
                    oracle = Fraction(n11, n) - p * Fraction(total1 + total2, n) + p * p
                    fitted = Fraction(n11, n) - q * Fraction(total1 + total2, n) + q * q
                    corrected = fitted - q * (1 - q) / (m - 1)
                    covariance = (Fraction(n11) - Fraction(total1 * total2, n)) / (n - 1)
                    values = dict(zip(METHODS, [oracle, fitted, corrected, covariance]))
                    probability_sum += weight
                    for name, value in values.items():
                        means[name] += weight * value
                        seconds[name] += weight * value * value
                    cross_sc += weight * corrected * covariance
    assert probability_sum == 1
    result = {name: {"mean": means[name], "variance": seconds[name] - means[name] ** 2}
              for name in METHODS}
    result["cross_sc"] = cross_sc - means[METHODS[2]] * means[METHODS[3]]
    return result


def fixtures(report):
    report["fixtures"] = rows = []
    settings = [
        {"k": 3, "means": [0.7, 1.4], "rho": 0.35, "mu": 0.65,
         "initialization": "uniform_stage", "amplitude": 0.41, "period": 2.7},
        {"k": 2, "means": [0.85], "rho": 0.0, "mu": 0.4,
         "initialization": "newborn", "amplitude": 0.33, "period": 1.7},
    ]
    for index, (case, t, horizon) in enumerate(zip(settings, [0.73, 0.41], [2.37, 1.83])):
        row = {"fixture": "direct_physical_backward", "index": index, "configuration": case}
        rows.append(row)
        model = Model(case)
        family, q = model.q_records(horizon, [t])
        direct, h_direct, q_direct = physical_backward(model, t, horizon)
        state_error = max(float(np.max(abs(direct.sol(b).reshape(model.types, model.k)
                                          - model.h(model.clock(horizon) - model.clock(b)))))
                          for b in [0, 0.17, t, horizon])
        clock_error = max(abs(quad(model.rate, 0, b, epsabs=1e-13)[0] - model.clock(b))
                          for b in [0.17, t, horizon, 4])
        row.update({"family_error": abs(family - h_direct), "Q_error": abs(q[0]["value"] - q_direct),
                    "all_state_survival_error": state_error, "clock_quadrature_error": clock_error})
        assert max(row[k] for k in ["family_error", "Q_error", "all_state_survival_error",
                                    "clock_quadrature_error"]) <= GATE
        row["status"] = "PASS"
    exp_case = {"k": 1, "means": [0.8], "rho": 0.0, "mu": 0.7,
                "initialization": "newborn", "amplitude": 0.41, "period": 2.7}
    model = Model(exp_case)
    u, alpha, mu = model.clock(0.6), model.rates[0], model.mu
    truth = (alpha * exp(-mu * u) - mu * exp(-alpha * u)) / (alpha - mu)
    errors = []
    for horizon in [1.6, 2.3]:
        family, q = model.q_records(horizon, [0.6])
        duration = model.clock(horizon)
        h_truth = (alpha - mu) / (alpha - mu * exp(-(alpha - mu) * duration))
        errors += [abs(family - h_truth), abs(q[0]["value"] - truth)]
    assert max(errors) <= GATE
    rows.append({"fixture": "off_grid_exponential_closed_form", "maximum_error": max(errors), "status": "PASS"})
    rational_cases = [(Fraction(0), Fraction(0)), (Fraction(1, 5), Fraction(-1, 50)),
                      (Fraction(1, 5), Fraction(0)), (Fraction(1, 2), Fraction(1, 10)),
                      (Fraction(4, 5), Fraction(1, 20)), (Fraction(1), Fraction(0))]
    checked = 0
    enumeration = {"fixture": "exact_rational_count_enumeration", "settings_completed": 0}
    rows.append(enumeration)
    for p, c in rational_cases:
        for m in [2, 3, 5]:
            for n in [2, 3, 4]:
                enumeration["current_setting"] = {"p": str(p), "c": str(c), "m": m, "n": n}
                expected = moments(p, p * p + c, m, n)
                observed = enumerate_moments(p, c, m, n)
                for method in METHODS:
                    for field in ["mean", "variance"]:
                        assert observed[method][field] == expected[method][field]
                v = p * (1 - p)
                a = v * v - c * c + c * (1 - 2 * p) ** 2
                assert observed["cross_sc"] == a / n
                checked += 1
                enumeration["settings_completed"] = checked
    enumeration.pop("current_setting")
    enumeration.update({"mean_variance_identities": checked * 4 * 2,
                        "paired_covariance_identities": checked, "status": "PASS"})
    report["status"] = "PASS"


def scientific_run(protocol, report):
    report["cases"] = []
    for configuration in protocol["cases"]:
        current = {"case_id": configuration["case_id"], "configuration": configuration,
                   "family": [], "Q": [], "U": [], "contrasts": [], "bins": [],
                   "pairs": [], "calibration": []}
        report["current_case"] = current
        model = Model(configuration)
        times = protocol["times"]
        for horizon in times["selection_horizons"]:
            queries = sorted(set(times["evaluation_times"] + [0.0, horizon]))
            family, q = model.q_records(horizon, queries)
            current["family"].append({"T": horizon, "probability": family})
            current["Q"].extend(q)
        for t in times["unconditional_path_queries"]:
            current["U"].append({"t": t, "value": exp(-model.mu * model.clock(t))})
        q_lookup = {(r["t"], r["T"]): r["value"] for r in current["Q"]}
        h_lookup = {r["T"]: r["probability"] for r in current["family"]}
        for early, late in times["contrast_pairs"]:
            for t in times["evaluation_times"]:
                loss = h_lookup[early] * (1 - q_lookup[t, early]) - h_lookup[late] * (1 - q_lookup[t, late])
                current["contrasts"].append({"t": t, "T_early": early, "T_late": late,
                    "value": q_lookup[t, late] - q_lookup[t, early], "removed_loss_mean": loss})
        cutoff = times["pair_birth_cutoff"]
        total_eligibility = model.gamma_eligibility(cutoff)
        for width in times["birth_bin_widths"]:
            for index in range(round(cutoff / width)):
                left, right = index * width, (index + 1) * width
                bin_id = f"w{width:g}-b{index}"
                type_mass, error = integrate(model.density, left, right)
                mass = float(type_mass.sum())
                if not mass > 0:
                    raise ArithmeticError("Nonpositive bin eligibility")
                current["bins"].append({"bin_id": bin_id, "width": width, "left": left,
                    "right": right, "probability": mass, "mother_type_weights": (type_mass / mass).tolist(),
                    "adaptive_quadrature_error_estimate": error})
                for lag in times["pair_lags"]:
                    pair = {"bin_id": bin_id, "lag": lag,
                            **model.pair_integrals(left, right, lag, mass)}
                    current["pairs"].append(pair)
                    if min(pair["j"], pair["p"] - pair["j"], 1 - 2 * pair["p"] + pair["j"]) < -GATE:
                        raise ArithmeticError("Invalid Bernoulli joint probabilities")
                    if abs(pair["c"] - pair["mean_conditional_covariance"] - pair["birth_probability_variance"]) > GATE:
                        raise ArithmeticError("Conditional covariance decomposition failed")
                    for m in protocol["calibration"]["m"]:
                        for n in protocol["calibration"]["n"]:
                            current["calibration"].append({"bin_id": bin_id, "lag": lag,
                                "m": m, "n": n, "methods": moments(pair["p"], pair["j"], m, n)})
        current["eligibility_gamma_reference"] = float(total_eligibility)
        current["partition_eligibility_errors"] = {
            f"{width:g}": sum(r["probability"] for r in current["bins"] if r["width"] == width) - total_eligibility
            for width in times["birth_bin_widths"]}
        assert max(abs(v) for v in current["partition_eligibility_errors"].values()) <= GATE
        report["cases"].append(current)
        report["current_case"] = None
        print(configuration["case_id"] + " completed", flush=True)
    report["counts"] = {name: sum(len(c[name]) for c in report["cases"])
                        for name in ["family", "Q", "U", "contrasts", "bins", "pairs", "calibration"]}
    report["status"] = "PASS"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--pin", action="store_true")
    action.add_argument("--fixtures", action="store_true")
    action.add_argument("--run", action="store_true")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    failure_path = args.out.with_name(args.out.stem + ".failure.json")
    if args.out.exists() or failure_path.exists():
        raise FileExistsError("Refusing to overwrite a first output or failure artifact")
    started = time.monotonic()
    report = {"status": "STARTED", "created_utc": datetime.now(timezone.utc).isoformat(),
              "script": portable(__file__), "code_sha256": sha(__file__),
              "protocol": portable(PROTOCOL), "protocol_sha256": sha(PROTOCOL),
              "theory_sha256": sha(BASE / "theory.md"),
              "environment": {"python": platform.python_version(), "numpy": np.__version__,
                              "scipy": scipy.__version__},
              "numerical_settings": {"rtol": RTOL, "atol": ATOL,
                                     "quadrature_epsabs": QUAD_ABS, "quadrature_epsrel": QUAD_REL,
                                     "quadrature": "adaptive scipy quad_vec Gauss-Kronrod 21"},
              "primary_outputs_read": False,
              "routes": ["extinction/forward-spine ODEs", "adaptive birth-bin quadrature",
                         "closed calibration moments", "direct physical backward H/J fixtures",
                         "exact rational small count enumeration fixtures"]}
    try:
        assert report["protocol_sha256"] == PROTOCOL_SHA
        assert report["theory_sha256"] == THEORY_SHA
        protocol = json.loads(PROTOCOL.read_text())
        if args.pin:
            report["status"] = "PINNED_BEFORE_FIXTURES_AND_SCIENTIFIC_GRID"
        elif args.fixtures:
            fixtures(report)
        else:
            scientific_run(protocol, report)
        report["elapsed_seconds"] = time.monotonic() - started
        write_once(args.out, report)
    except Exception as exc:
        report["status"] = "FAILED_PRESERVED"
        report["error"] = {"type": type(exc).__name__, "message": str(exc),
                           "traceback": traceback.format_exc().replace(str(ROOT), "<project>")}
        report["elapsed_seconds"] = time.monotonic() - started
        invalid = []
        diagnostic = clean(report, invalid=invalid)
        diagnostic["nonfinite_diagnostics"] = invalid
        write_once(failure_path, diagnostic)
        raise
    print(json.dumps({"status": report["status"], "output": portable(args.out),
                      "sha256": sha(args.out), "elapsed_seconds": report["elapsed_seconds"]}))


if __name__ == "__main__":
    main()
