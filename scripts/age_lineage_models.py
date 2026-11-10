"""Deterministic model probabilities for the frozen cell-cycle specificity study.

No data are read and no numerical outcomes are generated on import.
Time and rates are hypothetical. These routines do not fit biological data.
"""
from functools import lru_cache
import math

import numpy as np
from scipy.integrate import quad, solve_ivp
from scipy.special import gammainc


class ErlangModel:
    def __init__(self, case, maximum_time=4.0, rtol=1e-10, atol=1e-12):
        self.case = case
        self.k = int(case["k"])
        self.means = np.asarray(case["means"], dtype=float)
        self.types = len(self.means)
        self.mu = float(case["mu"])
        self.rho = float(case["rho"])
        self.alpha = self.k / self.means
        self.kernel = self.rho * np.eye(self.types) + (1 - self.rho) / self.types
        self.initial = np.zeros((self.types, self.k))
        if case["initialization"] == "newborn":
            self.initial[:, 0] = 1 / self.types
        elif case["initialization"] == "uniform_stage":
            self.initial[:] = 1 / (self.types * self.k)
        else:
            raise ValueError("Unsupported founder initialization")
        self.rtol, self.atol = rtol, atol
        self.maximum_time = maximum_time
        self.survival_solution = solve_ivp(
            self._survival_rhs, (0.0, maximum_time), np.ones(self.types * self.k),
            method="DOP853", dense_output=True, rtol=rtol, atol=atol)
        if not self.survival_solution.success:
            raise RuntimeError(self.survival_solution.message)

    def _survival_rhs(self, _, flat):
        h = flat.reshape(self.types, self.k)
        result = -(self.mu + self.alpha[:, None]) * h
        if self.k > 1:
            result[:, :-1] += self.alpha[:, None] * h[:, 1:]
        daughters = self.kernel @ h[:, 0]
        result[:, -1] += self.alpha * (2 * daughters - daughters * daughters)
        return result.ravel()

    def survival_by_state(self, t):
        if not 0 <= t <= self.maximum_time:
            raise ValueError("Survival evaluation outside solved interval")
        return self.survival_solution.sol(t).reshape(self.types, self.k)

    def family_survival(self, horizon):
        return float(np.sum(self.initial * self.survival_by_state(horizon)))

    def selected_path_survival(self, t, horizon):
        if not 0 <= t <= horizon <= self.maximum_time:
            raise ValueError("Need 0 <= t <= horizon <= maximum_time")
        h_T = self.family_survival(horizon)
        if h_T <= 0:
            return None
        if t == 0:
            return 1.0
        gap = horizon - t

        def rhs(x, flat):
            joint = flat.reshape(self.types, self.k)
            result = -(self.mu + self.alpha[:, None]) * joint
            if self.k > 1:
                result[:, :-1] += self.alpha[:, None] * joint[:, 1:]
            hbar = self.kernel @ self.survival_by_state(x)[:, 0]
            jbar = self.kernel @ joint[:, 0]
            m = math.exp(-self.mu * (x - gap))
            result[:, -1] += self.alpha * ((1 - hbar) * jbar + m * hbar)
            return result.ravel()

        solution = solve_ivp(rhs, (gap, horizon), self.survival_by_state(gap).ravel(),
                             method="DOP853", rtol=self.rtol, atol=self.atol)
        if not solution.success:
            raise RuntimeError(solution.message)
        numerator = float(np.dot(self.initial.ravel(), solution.y[:, -1]))
        return numerator / h_T

    def pair_summary(self, lag, cutoff=2.0):
        remaining = np.arange(self.k, 0, -1)
        effective = self.alpha + self.mu
        probability = (self.alpha[:, None] / effective[:, None]) ** remaining
        probability *= gammainc(remaining, effective[:, None] * cutoff)
        type_mass = np.sum(self.initial * probability, axis=1)
        eligible = float(type_mass.sum())
        if eligible <= 0:
            return {"eligibility_probability": eligible, "defined": False}
        weights = type_mass / eligible
        newborn_h = self.survival_by_state(lag)[:, 0]
        g = self.kernel @ newborn_h
        mean = float(weights @ g)
        covariance = float(weights @ ((g - mean) ** 2))
        identity = (self.rho ** 2 * weights[0] * weights[1] *
                    (newborn_h[0] - newborn_h[1]) ** 2) if self.types == 2 else 0.0
        return {"defined": True, "eligibility_probability": eligible,
                "qualifying_mother_type_weights": weights.tolist(),
                "newborn_type_subtree_survival": newborn_h.tolist(),
                "daughter_survival_given_mother_type": g.tolist(),
                "daughter_survival_mean": mean,
                "joint_daughter_survival": float(weights @ (g * g)),
                "covariance": covariance, "closed_covariance_identity": float(identity)}

    def selected_path_loss(self, t, horizon):
        """Positive tagged-death/family-survival probability, scaled by stage.

        Stage j (zero based) has small-time order k-j+1. Scaling each state
        separately avoids both subtracting Q from one and tiny ODE states.
        """
        if not 0 <= t <= horizon <= self.maximum_time:
            raise ValueError("Invalid common time")
        if t == 0 or self.mu == 0:
            return 0.0
        orders = np.arange(self.k + 1, 1, -1)

        def rhs(v, flat):
            scaled = flat.reshape(self.types, self.k)
            result = -(self.mu + self.alpha[:, None]) * t * scaled
            if self.k > 1:
                result[:, :-1] += self.alpha[:, None] * scaled[:, 1:]
            x = horizon - t * (1 - v)
            hbar = self.kernel @ self.survival_by_state(x)[:, 0]
            dbar = self.kernel @ scaled[:, 0]
            source = -math.expm1(-self.mu * t * v) / t
            result[:, -1] += self.alpha * (t ** self.k * (1 - hbar) * dbar + source * hbar)
            return result.ravel()

        solved = solve_ivp(rhs, (0.0, 1.0), np.zeros(self.types * self.k),
                           method="DOP853", rtol=self.rtol, atol=self.atol)
        if not solved.success:
            raise RuntimeError(solved.message)
        death_joint = solved.y[:, -1].reshape(self.types, self.k) * t ** orders
        return float(np.sum(self.initial * death_joint)) / self.family_survival(horizon)

    def early_time_coefficient(self, horizon):
        h = self.survival_by_state(horizon)
        g = self.kernel @ h[:, 0]
        denominator = self.family_survival(horizon)
        if self.case["initialization"] == "newborn":
            order = self.k + 1
            weighted = np.sum(self.initial[:, 0] * self.alpha ** self.k * g)
            coefficient = self.mu * weighted / (math.factorial(order) * denominator)
        else:
            order = 2
            weighted = np.sum(self.initial[:, -1] * self.alpha * g)
            coefficient = self.mu * weighted / (2 * denominator)
        return {"nominal_order": order, "coefficient": float(coefficient),
                "positive_leading_term": bool(coefficient > 0)}


class DeterministicModel:
    def __init__(self, mu, age=1.0):
        self.mu, self.age = mu, age

    @lru_cache(maxsize=None)
    def family_survival(self, horizon):
        if horizon < 0:
            raise ValueError("Negative horizon")
        if horizon < self.age:
            return math.exp(-self.mu * horizon)
        child = self.family_survival(horizon - self.age)
        return math.exp(-self.mu * self.age) * child * (2 - child)

    def joint(self, t, horizon):
        if not 0 <= t <= horizon:
            raise ValueError("Invalid common time")
        if t <= self.age:
            return self.family_survival(horizon)
        child = self.family_survival(horizon - self.age)
        selected = self.joint(t - self.age, horizon - self.age)
        return math.exp(-self.mu * self.age) * (
            selected * (1 - child) + math.exp(-self.mu * (t - self.age)) * child)

    def selected_path_survival(self, t, horizon):
        h = self.family_survival(horizon)
        return self.joint(t, horizon) / h if h > 0 else None

    def pair_summary(self, lag, cutoff=2.0):
        if self.age > cutoff:
            return {"defined": False, "eligibility_probability": 0.0}
        h = self.family_survival(lag)
        return {"defined": True, "eligibility_probability": math.exp(-self.mu * self.age),
                "daughter_survival_mean": h, "joint_daughter_survival": h * h,
                "covariance": 0.0, "closed_covariance_identity": 0.0}


class CalendarModel:
    def __init__(self, mu, epsabs=1e-12, epsrel=1e-10):
        self.mu, self.epsabs, self.epsrel = mu, epsabs, epsrel
        self.quadrature_error_estimates = []

    @staticmethod
    def rate(t):
        return 1 + 0.5 * math.sin(math.pi * t)

    @staticmethod
    def integrated_rate(t):
        return t + 0.5 / math.pi * (1 - math.cos(math.pi * t))

    def integral(self, f, a, b):
        value, error = quad(f, a, b, epsabs=self.epsabs, epsrel=self.epsrel, limit=200)
        self.quadrature_error_estimates.append(error)
        return value

    def survival_between(self, birth, horizon):
        integral = self.integral(lambda u: math.exp(
            -(self.integrated_rate(u) - self.integrated_rate(birth)) + self.mu * (u - birth)),
            birth, horizon)
        return 1 / (1 + self.mu * integral)

    def family_survival(self, horizon):
        return self.survival_between(0, horizon)

    def selected_path_survival(self, t, horizon):
        if not 0 <= t <= horizon:
            raise ValueError("Invalid common time")
        integral = self.integral(lambda u: self.rate(u) * math.exp(
            self.mu * u - self.integrated_rate(u)), 0, t)
        return math.exp(-self.integrated_rate(t)) + math.exp(-self.mu * t) * integral

    def pair_summary(self, lag, cutoff=2.0):
        def density(b):
            return self.rate(b) * math.exp(-self.integrated_rate(b) - self.mu * b)
        eligible = self.integral(density, 0, cutoff)
        mean = self.integral(lambda b: density(b) * self.survival_between(b, b + lag), 0, cutoff) / eligible
        second = self.integral(lambda b: density(b) * self.survival_between(b, b + lag) ** 2, 0, cutoff) / eligible
        # The centered integral avoids subtracting nearly equal second moments.
        covariance = self.integral(lambda b: density(b) * (
            self.survival_between(b, b + lag) - mean) ** 2, 0, cutoff) / eligible
        return {"defined": True, "eligibility_probability": eligible,
                "daughter_survival_mean": mean, "joint_daughter_survival": second,
                "covariance": covariance, "birth_conditioned_residual_cross_product": 0.0}


class NoDivisionModel:
    def __init__(self, mu):
        self.mu = mu

    def family_survival(self, horizon):
        return math.exp(-self.mu * horizon)

    def selected_path_survival(self, t, horizon):
        if not 0 <= t <= horizon:
            raise ValueError("Invalid common time")
        return 1.0

    def pair_summary(self, lag, cutoff=2.0):
        return {"defined": False, "eligibility_probability": 0.0, "covariance": None}


def build_model(case, strict=False):
    if case["kind"] == "erlang":
        return ErlangModel(case, rtol=1e-12 if strict else 1e-10,
                           atol=1e-14 if strict else 1e-12)
    if case["kind"] == "deterministic":
        return DeterministicModel(case["mu"], case["division_age"])
    if case["kind"] == "calendar":
        return CalendarModel(case["mu"], epsabs=1e-14 if strict else 1e-12,
                             epsrel=1e-12 if strict else 1e-10)
    if case["kind"] == "no_division":
        return NoDivisionModel(case["mu"])
    raise ValueError("Unsupported model")
