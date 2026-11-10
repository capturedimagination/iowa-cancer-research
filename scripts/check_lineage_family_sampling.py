"""Independent explicit-tree Gillespie check; imports no project simulator."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import math
import time
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research/treatment-discovery/lineage-audit-2026-11-10"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def full_tree(lam, mu, horizon, rng):
    """Every living descendant is explicit, including after the tag dies."""
    alive = [0]
    next_id = 1
    tag = 0
    tag_death = math.inf
    divisions = deaths = 0
    t = 0.0
    while alive and lam + mu > 0:
        t += float(rng.exponential(1.0 / (len(alive) * (lam + mu))))
        if t > horizon:
            break
        index = int(rng.integers(len(alive)))
        cell = alive[index]
        if rng.random() < lam / (lam + mu):
            alive[index] = next_id
            alive.append(next_id + 1)
            if cell == tag:
                tag = next_id + int(rng.integers(2))
            next_id += 2
            divisions += 1
        else:
            alive[index] = alive[-1]
            alive.pop()
            if cell == tag:
                assert math.isinf(tag_death)
                tag_death = t
                tag = None
            deaths += 1
    assert len(alive) == 1 + divisions - deaths
    assert tag is None or tag in alive
    assert alive or tag is None
    return len(alive), tag_death, divisions, deaths


def family_probability(lam, mu, horizon):
    if lam == mu:
        return 1.0 / (1.0 + lam * horizon)
    if lam == 0:
        return math.exp(-mu * horizon)
    if mu == 0:
        return 1.0
    r = lam - mu
    return r / (lam - mu * math.exp(-r * horizon))


def selected_tag_survival(lam, mu, t):
    if lam == mu:
        return math.exp(-lam * t) * (1.0 + lam * t)
    return (lam * math.exp(-mu * t) - mu * math.exp(-lam * t)) / (lam - mu)


def probability_check(successes, trials, exact):
    assert trials > 0
    observed = successes / trials
    analytic_se = math.sqrt(exact * (1.0 - exact) / trials)
    observed_se = math.sqrt(observed * (1.0 - observed) / trials)
    residual = observed - exact
    return {"successes":int(successes), "trials":int(trials), "observed":observed,
            "analytic":exact, "monte_carlo_se_at_analytic_probability":analytic_se,
            "estimated_monte_carlo_se":observed_se, "difference":residual,
            "difference_in_analytic_mc_se":residual / analytic_se if analytic_se else None,
            "within_predeclared_six_mc_se":abs(residual) <= 6 * analytic_se + 1e-12}


def main():
    started = time.monotonic()
    spec_path = OUT / "full-tree-review-protocol.json"
    spec = json.loads(spec_path.read_text())
    freeze = json.loads((OUT / "full-tree-review-freeze.json").read_text())
    assert sha(spec_path) == freeze["sha256"]
    assert sha(OUT / "sampling-simulation-plan.json") == spec["root_plan_sha256"]
    assert np.__version__ == "2.3.5"
    rng = np.random.default_rng(spec["seed"])
    n = spec["founder_trees_per_pair"]
    horizon = spec["horizon"]
    cases = []
    for lam, mu in spec["rate_pairs"]:
        terminal = np.empty(n, dtype=np.int64)
        tagged_death = np.empty(n)
        births = np.empty(n, dtype=np.int64)
        deaths = np.empty(n, dtype=np.int64)
        for i in range(n):
            terminal[i], tagged_death[i], births[i], deaths[i] = full_tree(lam, mu, horizon, rng)
        selected = terminal > 0
        assert np.array_equal(terminal, 1 + births - deaths)
        tag_alive_end = tagged_death > horizon
        assert (selected[tag_alive_end]).all()
        points = []
        for t in spec["observation_times"]:
            alive = tagged_death > t
            points.append({"time":t,
                "prospective_tag_survival":probability_check(int(alive.sum()), n, math.exp(-mu * t)),
                "family_selected_tag_survival":probability_check(int((alive & selected).sum()), int(selected.sum()), selected_tag_survival(lam, mu, t))})
        if lam == 0:
            assert int((selected & ~tag_alive_end).sum()) == 0 and int(births.sum()) == 0
        if mu == 0:
            assert selected.all() and tag_alive_end.all() and int(deaths.sum()) == 0
        if lam == mu == 0:
            assert (terminal == 1).all() and (births == 0).all() and (deaths == 0).all()
        case = {"lambda":lam,"mu":mu,"founder_trees":n,
                "family_inclusion":probability_check(int(selected.sum()), n, family_probability(lam, mu, horizon)),
                "selected_tag_deaths_before_horizon":int((selected & ~tag_alive_end).sum()),
                "total_population_divisions":int(births.sum()),"total_population_deaths":int(deaths.sum()),
                "mean_terminal_population":float(terminal.mean()),
                "expected_terminal_population":math.exp((lam - mu) * horizon),
                "mc_se_mean_terminal_population":float(terminal.std(ddof=1) / math.sqrt(n)),
                "population_balance_checked_for_every_tree":True,"survival_points":points}
        cases.append(case)
        print("full-tree case finished", lam, mu, "selected",int(selected.sum()), "selected tag deaths",case["selected_tag_deaths_before_horizon"],flush=True)
    comparisons = [c["family_inclusion"] for c in cases]
    comparisons += [point[k] for c in cases for point in c["survival_points"] for k in ("prospective_tag_survival","family_selected_tag_survival")]
    z = [abs(x["difference_in_analytic_mc_se"]) for x in comparisons if x["difference_in_analytic_mc_se"] is not None]
    result = {"reviewed_at_utc":datetime.now(timezone.utc).isoformat(),
              "protocol_sha256":freeze["sha256"],"root_protocol_sha256":spec["root_plan_sha256"],
              "checker_sha256":sha(__file__),"numpy_version":np.__version__,"seed":spec["seed"],
              "scope":"Explicit full branching Gillespie simulation, independent of the tag-plus-sidebranch shortcut; synthetic only.",
              "horizon":horizon,"total_founder_trees":n * len(cases),"all_cases":cases,
              "probability_comparisons":len(comparisons),"all_probability_checks_within_predeclared_bound":all(x["within_predeclared_six_mc_se"] for x in comparisons),
              "maximum_absolute_deviation_in_analytic_mc_se":max(z,default=0),
              "all_exact_edge_and_population_balance_checks_passed":True,
              "runtime_seconds":time.monotonic() - started,
              "limits":["This validates the homogeneous branching/sampling identity, not the actual workbook selection rule or cancer biology.",
                        "Family selection and endpoint-connected ancestry are different; a selected tag may die while its side-branch family survives.",
                        "Survival points from one tree are correlated; no multiple-testing discovery claim is made.",
                        "No patient or workbook event data were used. No event-rate or treatment-effect inference."]}
    (OUT / "full-tree-review.json").write_text(json.dumps(result,indent=2,allow_nan=False) + "\n")
    print(json.dumps({"total_founder_trees":result["total_founder_trees"],"checks_pass":result["all_probability_checks_within_predeclared_bound"],"max_abs_mc_se":result["maximum_absolute_deviation_in_analytic_mc_se"],"runtime_seconds":result["runtime_seconds"]},indent=2),flush=True)


if __name__ == "__main__":
    main()
