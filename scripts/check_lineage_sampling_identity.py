#!/usr/bin/env python3
"""Independently check the selected-tag lifetime identity on 500 fixed cases.

This packages the earlier review-only scratch calculation after its results and
the root simulator results had been inspected. The rate grids, horizon grids,
time fractions, quadrature tolerances and matrix calculation are unchanged.
It is not a prospectively frozen experiment or an independent biological test.

No random draws, empirical data, or imports from the simulator are used.
The comparison is valid for a lifetime right-censored at the selection horizon;
it makes no assertion about the tag's lifetime after that horizon.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform

import numpy as np
import scipy
from scipy.integrate import quad
from scipy.linalg import expm


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = (
    ROOT / "research/treatment-discovery/lineage-audit-2026-11-10"
    / "identity-check-results.json"
)
RATE_GRID = [0.1, 0.5, 1, 2, 3]
HORIZON_GRID = [0.5, 1, 2, 5]
TIME_FRACTIONS = [0, 0.1, 0.5, 0.9, 1]


def check_identity():
    cases = []
    for lam in RATE_GRID:
        for mu in RATE_GRID:
            r = lam - mu

            def survival(u):
                if r == 0:
                    return 1 / (1 + lam * u)
                return r / (lam - mu * np.exp(-r * u))

            for horizon in HORIZON_GRID:
                for fraction in TIME_FRACTIONS:
                    t = horizon * fraction
                    q = 1 - survival(horizon - t)
                    sister_factor = np.exp(
                        -lam * quad(
                            lambda u: survival(horizon - u),
                            0,
                            t,
                            epsabs=1e-12,
                            epsrel=1e-12,
                        )[0]
                    )
                    pgfl = (
                        np.exp(-mu * t) * (1 - q * sister_factor)
                        / survival(horizon)
                    )
                    if r == 0:
                        closed = np.exp(-lam * t) * (1 + lam * t)
                    else:
                        closed = (
                            lam * np.exp(-mu * t) - mu * np.exp(-lam * t)
                        ) / r
                    generator = np.array([[-lam, lam], [0.0, -mu]])
                    sequential = (np.array([1.0, 0.0]) @ expm(generator * t)).sum()
                    cases.append({
                        "lam": lam,
                        "mu": mu,
                        "T": horizon,
                        "t": t,
                        "pgfl": float(pgfl),
                        "closed": float(closed),
                        "sequential": float(sequential),
                    })
    return {
        "n_cases": len(cases),
        "max_abs_pgfl_vs_closed": max(
            abs(x["pgfl"] - x["closed"]) for x in cases
        ),
        "max_abs_sequential_vs_closed": max(
            abs(x["sequential"] - x["closed"]) for x in cases
        ),
        "methods": [
            "Poisson generating functional with scipy.integrate.quad epsabs=epsrel=1e-12",
            "Closed form with exact critical case",
            "Two-transient-state generator scipy.linalg.expm",
        ],
        "scope": "Independent analytic identity check, not tree Monte Carlo and not observed cancer data",
        "cases": cases,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = check_identity()
    result.update({
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
        },
        "seed": None,
        "seed_reason": "Deterministic numerical integration and matrix exponentiation; no RNG.",
        "grids": {
            "lambda": RATE_GRID,
            "mu": RATE_GRID,
            "horizons": HORIZON_GRID,
            "time_fractions": TIME_FRACTIONS,
        },
        "packaging_status": (
            "Packaged after original scratch results and root simulator results were inspected; "
            "all 500 original cases and numerical methods retained. Not a new frozen protocol."
        ),
        "limits": [
            "Only 0<=t<=T, corresponding to right censoring at the selection horizon.",
            "Positive-rate check; zero-rate cases belong to the frozen simulator and full-tree review.",
            "Numerical discrepancies are floating-point differences, not uncertainty intervals.",
            "No source workbook, observed outcomes or calibrated biological parameters are read.",
        ],
    })
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "cases"}, indent=2))


if __name__ == "__main__":
    main()
