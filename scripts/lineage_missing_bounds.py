"""Conservative chronological-mass and finite-roster ratio bounds.

No data files are read on import. Intervals describe a relaxation of missing
tree information, not a sampling confidence interval or a cancer-model test.
"""
from __future__ import annotations

from functools import lru_cache
from math import fsum
from collections import defaultdict


class GraphMass:
    def __init__(self, graph):
        self.nodes = {n["id"]: n for n in graph["nodes"]}
        if len(self.nodes) != len(graph["nodes"]):
            raise ValueError("Duplicate episode ID")
        self.children = {n: [] for n in self.nodes}
        incoming = {n: [] for n in self.nodes}
        edge_keys = set()
        for e in graph["edges"]:
            p, c = e["parent"], e["child"]
            if (p, c) in edge_keys:
                raise ValueError("Duplicate graph edge")
            edge_keys.add((p, c))
            if self.nodes[p]["last_frame"] + 1 != self.nodes[c]["first_frame"]:
                raise ValueError("Unverified nonadjacent episode transition")
            self.children[p].append(c)
            incoming[c].append(p)
        if any(len(x) > 2 for x in self.children.values()) or any(len(x) > 1 for x in incoming.values()):
            raise ValueError("Nonbinary or multiple-parent graph")
        # Strictly increasing frame order proves acyclicity; also bound numerical depth.
        depths = {}
        for n in sorted(self.nodes, key=lambda x: self.nodes[x]["first_frame"]):
            depths[n] = 0 if not incoming[n] else depths[incoming[n][0]] + 1
        if max(depths.values(), default=0) >= 900:
            raise ValueError("Graph depth exceeds the supported floating-point range")
        divs = {(int(label), int(frame)) for label, frame in graph["event_annotation_keys"]["Divisions"]}
        deaths = {(int(label), int(frame)) for label, frame in graph["event_annotation_keys"]["Apoptosis"]}
        divs_by_label, deaths_by_label = defaultdict(list), defaultdict(list)
        for label, frame in divs:
            divs_by_label[label].append(frame)
        for label, frame in deaths:
            deaths_by_label[label].append(frame)
        self.division = {}
        self.apoptosis = {}
        self.ambiguities = {n: set() for n in self.nodes}
        for key, n in self.nodes.items():
            start, end, label = n["first_frame"], n["last_frame"], n["label"]
            if start > end:
                raise ValueError("Reversed episode interval")
            ds = sorted(f for f in divs_by_label[label] if start <= f <= end)
            aps = sorted(f for f in deaths_by_label[label] if start <= f <= end)
            if len(ds) > 1 or (ds and ds[0] != end):
                raise ValueError("Division does not end a single episode")
            if sorted(n.get("apoptosis_annotation_frames_in_episode", aps)) != aps:
                raise ValueError("Apoptosis event/episode mapping differs")
            if len(aps) > 1:
                raise ValueError("Unresolved repeated apoptosis annotations")
            if self.children[key] and not ds:
                raise ValueError("Daughter edge without division annotation")
            self.division[key] = ds[0] if ds else None
            self.apoptosis[key] = aps[0] if aps else None
            if ds and aps:
                # A simultaneous or earlier death cannot be silently given fate priority.
                self.ambiguities[key].add(min(ds[0], aps[0]))
        for issue in graph.get("issues", []):
            kind, n, f = issue["kind"], issue["node"], issue["frame"]
            if kind == "lineage_present_p53_minus1":
                self.ambiguities[n].add(f)
            elif kind in ("division_one_observed_daughter", "division_no_observed_daughter"):
                expected = 1 if kind == "division_one_observed_daughter" else 0
                if self.division[n] is None or len(self.children[n]) != expected:
                    raise ValueError("Missing-daughter issue does not match graph")
            else:
                raise ValueError("Unhandled source issue kind: " + kind)

    @lru_cache(maxsize=None)
    def mass(self, node_id, frame, baseline, death_offset=0, ambiguity_policy="first_issue"):
        """Return (known live, known dead, unknown), with unit entry mass.

        A baseline node is observed alive under the prespecified eligibility
        rule. Prior component ambiguities do not remove that recorded cell.
        Unknown branches are never replaced by an available daughter.
        """
        if death_offset not in (0, 1) or ambiguity_policy not in ("first_issue", "whole_episode"):
            raise ValueError("Unspecified annotation sensitivity")
        n = self.nodes[node_id]
        if frame < baseline or frame < n["first_frame"]:
            raise ValueError("Query precedes the cell episode or baseline")
        if frame == baseline:
            if not n["first_frame"] <= baseline <= n["last_frame"]:
                raise ValueError("Baseline node is not recorded at baseline")
            if self.apoptosis[node_id] is not None and self.apoptosis[node_id] + death_offset <= baseline:
                raise ValueError("Baseline cell is dead under the specified annotation offset")
            return (1.0, 0.0, 0.0)
        issues = [f for f in self.ambiguities[node_id] if f > baseline]
        cutoff = None
        if issues:
            cutoff = min(issues) if ambiguity_policy == "first_issue" else max(n["first_frame"], baseline + 1)
        ap = self.apoptosis[node_id]
        death = None if ap is None else ap + death_offset
        # A prior, unambiguous death stays absorbing despite later image/mask records.
        if death is not None and frame >= death and (cutoff is None or death < cutoff):
            return (0.0, 1.0, 0.0)
        if cutoff is not None and frame >= cutoff:
            return (0.0, 0.0, 1.0)
        div = self.division[node_id]
        if div is not None and frame >= div + 1:
            values = [self.mass(c, frame, baseline, death_offset, ambiguity_policy)
                      for c in self.children[node_id]]
            missing = 2 - len(values)
            answer = tuple(fsum(v[j] for v in values) / 2 for j in range(3))
            answer = (answer[0], answer[1], answer[2] + missing / 2)
        elif frame <= n["last_frame"]:
            answer = (1.0, 0.0, 0.0)
        else:
            # Undocumented termination is not certified biological death.
            answer = (0.0, 0.0, 1.0)
        if min(answer) < 0 or abs(fsum(answer) - 1) > 1e-12:
            raise AssertionError("Chronological mass not conserved")
        return answer


def inclusion_status(mass):
    live, dead, unknown = mass
    if live > 0:
        return 1
    if live + unknown == 0:
        return 0
    return None


def ratio_bounds(rows):
    """Sharp interval for a rectangular interval/optional-selection relaxation.

    Each row is (lower, upper, family_inclusion_status). Positive earlier tag
    survival does not require later family inclusion. No-positive-denominator
    cases are undefined; zero is never substituted for them.
    """
    mandatory, optional = [], []
    excluded = 0
    for lo, hi, status in rows:
        if not 0 <= lo <= hi <= 1 or status not in (0, 1, None):
            raise ValueError("Invalid interval or family status")
        if status == 1:
            if hi == 0:
                raise ValueError("Later family survival contradicts zero earlier upper mass")
            mandatory.append((lo, hi))
        elif status is None and hi > 0:
            optional.append((lo, hi))
        else:
            excluded += 1
    n, m = len(mandatory), len(optional)
    common = {"mandatory_selected": n, "optional_selected": m,
              "excluded": excluded, "maximum_selected": n + m,
              "zero_denominator_possible": n == 0}
    if n + m == 0:
        return {**common, "defined_for_some_completion": False,
                "lower": None, "upper": None,
                "lower_optional_count": None, "upper_optional_count": None}
    lows = sorted(x[0] for x in optional)
    highs = sorted((x[1] for x in optional), reverse=True)
    low_sum, high_sum = fsum(x[0] for x in mandatory), fsum(x[1] for x in mandatory)
    choices_low, choices_high = [], []
    for k in range(m + 1):
        if k:
            low_sum += lows[k - 1]
            high_sum += highs[k - 1]
        if n + k:
            choices_low.append((low_sum / (n + k), k))
            choices_high.append((high_sum / (n + k), k))
    low, kl = min(choices_low)
    high, kh = max(choices_high)
    return {**common, "defined_for_some_completion": True,
            "lower": low, "upper": high,
            "lower_optional_count": kl, "upper_optional_count": kh}


def contrast_bounds(earlier, later):
    """Safe outer bound for later-minus-earlier on the same nested roster."""
    if not later["defined_for_some_completion"]:
        return {"defined_for_some_completion": False, "lower": None, "upper": None,
                "nesting_cap": None, "zero_denominator_possible": True}
    if not earlier["defined_for_some_completion"]:
        raise ValueError("Later inclusion possible but earlier inclusion impossible")
    minimum_later = max(1, later["mandatory_selected"])
    maximum_earlier = earlier["maximum_selected"]
    if minimum_later > maximum_earlier:
        raise ValueError("Inclusion counts contradict nesting")
    cap = 1 - minimum_later / maximum_earlier
    lo = max(later["lower"] - earlier["upper"], -cap)
    hi = min(later["upper"] - earlier["lower"], cap)
    if lo > hi + 1e-12:
        raise AssertionError("Empty contrast relaxation")
    return {"defined_for_some_completion": True, "lower": lo, "upper": hi,
            "nesting_cap": cap, "zero_denominator_possible": later["zero_denominator_possible"]}


def self_checks():
    def node(i, start, end, death=None):
        return {"id": str(i), "label": i, "first_frame": start, "last_frame": end,
                "apoptosis_annotation_frames_in_episode": [] if death is None else [death]}
    def graph(nodes, edges=(), divisions=(), deaths=(), issues=()):
        return {"nodes": nodes, "edges": [{"parent": str(a), "child": str(b)} for a, b in edges],
                "event_annotation_keys": {"Divisions": list(divisions), "Apoptosis": list(deaths)},
                "issues": list(issues)}
    tests = 0
    g = GraphMass(graph([node(1, 0, 1), node(2, 2, 5)], [(1, 2)], [(1, 1)]))
    assert g.mass("1", 3, 0) == (0.5, 0, 0.5); tests += 1
    g = GraphMass(graph([node(1, 0, 1)], divisions=[(1, 1)]))
    assert g.mass("1", 3, 0) == (0, 0, 1); tests += 1
    g = GraphMass(graph([node(1, 0, 8, 3)], deaths=[(1, 3)]))
    assert g.mass("1", 4, 0) == (0, 1, 0); tests += 1
    assert g.mass("1", 3, 0, 1) == (1, 0, 0); tests += 1
    g = GraphMass(graph([node(1, 0, 3, 3)], divisions=[(1, 3)], deaths=[(1, 3)]))
    assert g.mass("1", 3, 0) == (0, 0, 1); tests += 1
    issues = [{"kind": "lineage_present_p53_minus1", "node": "1", "frame": 3}]
    g = GraphMass(graph([node(1, 0, 8, 6)], deaths=[(1, 6)], issues=issues))
    assert g.mass("1", 7, 0) == (0, 0, 1); tests += 1
    assert g.mass("1", 2, 0, 0, "whole_episode") == (0, 0, 1); tests += 1
    assert g.mass("1", 0, 0, 0, "whole_episode") == (1, 0, 0); tests += 1
    assert g.mass("1", 5, 4) == (1, 0, 0); tests += 1
    g = GraphMass(graph([node(1, 0, 8, 1)], deaths=[(1, 1)], issues=issues))
    assert g.mass("1", 4, 0) == (0, 1, 0); tests += 1
    g = GraphMass(graph([node(1, 0, 1), node(2, 2, 5, 3), node(3, 2, 5)],
                        [(1, 2), (1, 3)], [(1, 1)], [(2, 3)]))
    assert g.mass("1", 4, 0) == (0.5, 0.5, 0); tests += 1
    assert ratio_bounds([(1, 1, 0), (0.5, 0.5, 1)])["lower"] == 0.5; tests += 1
    assert not ratio_bounds([(1, 1, 0)])["defined_for_some_completion"]; tests += 1
    a = ratio_bounds([(0.2, 0.8, None)])
    assert contrast_bounds(a, a)["lower"] == contrast_bounds(a, a)["upper"] == 0; tests += 1
    assert ratio_bounds([(1, 1, None), (1, 1, 1)])["lower"] == 1; tests += 1
    g = GraphMass(graph([node(1, 0, 0, 0)], deaths=[(1, 0)]))
    assert g.mass("1", 0, 0, 1) == (1, 0, 0); tests += 1
    try:
        g.mass("1", 0, 0, 0)
    except ValueError:
        tests += 1
    else:
        raise AssertionError("A dead baseline cell was admitted")
    return {"passed": True, "fixtures": tests, "scope": "Deterministic software controls, no source data"}


if __name__ == "__main__":
    import json
    print(json.dumps(self_checks(), indent=2))
