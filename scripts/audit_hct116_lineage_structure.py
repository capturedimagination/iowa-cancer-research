#!/usr/bin/env python3
"""Audit HCT116 lineage encoding without fitting or reporting biological outcomes.

Public outputs are structural aggregates. Cell/frame mappings stay in ignored tmp.
Uses only the standard library; never modifies the published workbook.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
EXPECTED = "212e5ca40af8fe5f1b07baf613459f275c7b97a2ec99e31fa2505af252a3f130"
NAMES = ("Divisions", "p53", "Apoptosis", "Lineage")
EXCLUSIONS = {1, 189, 205, 256, 258, 261, 279, 281, 284, 287, 288,
              295, 296, 298, 314, 316, 317, 338}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def col_index(ref: str) -> int:
    n = 0
    for char in ref:
        if not char.isalpha():
            break
        n = 26 * n + ord(char) - 64
    return n - 1


def parse_workbook(path: Path) -> tuple[dict, list]:
    if digest(path) != EXPECTED:
        raise ValueError("Workbook hash differs from the frozen original")
    arrays, schema = {}, []
    with zipfile.ZipFile(path) as z:
        book = ET.fromstring(z.read("xl/workbook.xml"))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        targets = {r.attrib["Id"]: r.attrib["Target"] for r in rels}
        for sheet in book.find("m:sheets", NS):
            name = sheet.attrib["name"]
            if name not in NAMES:
                raise ValueError(f"Unexpected sheet: {name}")
            target = targets[sheet.attrib[REL]]
            target = target.lstrip("/") if target.startswith("/") else "xl/" + target
            tree = ET.fromstring(z.read(target))
            a = [[None] * 243 for _ in range(394)]
            count = 0
            for cell in tree.findall(".//m:sheetData/m:row/m:c", NS):
                ref = cell.attrib["r"]
                row = int("".join(c for c in ref if c.isdigit())) - 1
                col = col_index(ref)
                val = cell.find("m:v", NS)
                if cell.find("m:f", NS) is not None or cell.attrib.get("t", "n") != "n":
                    raise ValueError(f"Unexpected formula/type at {name}!{ref}")
                if val is None or a[row][col] is not None:
                    raise ValueError(f"Missing/duplicate cell at {name}!{ref}")
                number = float(val.text)
                if not math.isfinite(number):
                    raise ValueError(f"Nonfinite value at {name}!{ref}")
                a[row][col] = number
                count += 1
            if count != 394 * 243 or any(v is None for row in a for v in row):
                raise ValueError(f"Unexpected dimensions or missing values: {name}")
            if name != "p53":
                if any(v < 0 or v != int(v) for row in a for v in row):
                    raise ValueError(f"Noninteger/negative code in {name}")
                a = [[int(v) for v in row] for row in a]
            if name in ("Divisions", "Apoptosis"):
                if set(v for row in a for v in row) - {0, 1}:
                    raise ValueError(f"Unexpected event code in {name}")
            arrays[name] = a
            schema.append({"sheet": name, "rows": 394, "columns": 243,
                           "range": "A1:II394", "numeric_cells": count,
                           "missing_cells": 0, "formula_cells": 0})
    if set(arrays) != set(NAMES):
        raise ValueError("Required sheet absent")
    return arrays, schema


def frame_groups(lineage: list[list[int]]) -> list[dict[int, list[int]]]:
    groups = []
    for t in range(len(lineage[0])):
        g = defaultdict(list)
        for r, row in enumerate(lineage):
            if row[t] != 0:
                g[row[t]].append(r)
        groups.append(dict(sorted(g.items())))
    return groups


def topology(lineage: list[list[int]], divisions: list[list[int]] | None = None) -> dict:
    """Candidate episodes; optional event flags split retained daughter labels."""
    groups = frame_groups(lineage)
    nodes, edges, issues, transitions = {}, [], [], []
    assignments = []
    previous = {}
    for t, current in enumerate(groups):
        incoming, outgoing = defaultdict(set), defaultdict(set)
        arrivals, departures = defaultdict(list), defaultdict(list)
        if t:
            for r, row in enumerate(lineage):
                a, b = row[t - 1], row[t]
                if a and b:
                    incoming[b].add(a)
                    outgoing[a].add(b)
                elif b:
                    arrivals[b].append(r)
                elif a:
                    departures[a].append(r)
        mapping = {}
        for label, rows in current.items():
            parents = sorted(incoming[label])
            prior_division = bool(t and divisions is not None and
                                  any(divisions[r][t-1] for r in groups[t-1].get(label, [])))
            stable = (t > 0 and parents == [label] and outgoing[label] == {label}
                      and not prior_division)
            if stable:
                node = previous[label]
                nodes[node]["last_frame"] = t + 1
                nodes[node]["source_rows"].update(r + 1 for r in rows)
            else:
                node = f"L{label}_F{t+1}"
                nodes[node] = {"id": node, "label": label, "first_frame": t + 1,
                               "last_frame": t + 1, "source_rows": {r + 1 for r in rows}}
                for parent in parents:
                    edges.append({"parent": previous[parent], "child": node,
                                  "boundary_frame": t + 1,
                                  "source_label_pair": [parent, label]})
            mapping[label] = node
            if len(parents) > 1:
                issues.append({"kind": "multiple_parent_labels", "frame": t + 1,
                               "label": label, "parents": parents, "node": node})
            if t and arrivals[label] and parents:
                issues.append({"kind": "partial_row_arrival", "frame": t + 1,
                               "label": label, "rows": [r + 1 for r in arrivals[label]], "node": node})
        if t:
            for parent in sorted(groups[t-1]):
                children = outgoing[parent]
                child_labels = sorted(children)
                flagged = divisions is not None and any(divisions[r][t-1] for r in groups[t-1][parent])
                if not children and not flagged:
                    continue
                if len(children) != 1 or children != {parent} or flagged:
                    kind = ("binary_split" if len(children) == 2 else
                            "excess_offspring_labels" if len(children) > 2 else
                            "division_one_observed_daughter" if flagged and len(children) == 1 else
                            "division_no_observed_daughter" if flagged else "label_rename")
                    transitions.append({"kind": kind, "frame": t + 1,
                                        "parent_label": parent, "child_labels": child_labels,
                                        "parent_node": previous[parent],
                                        "child_nodes": [mapping[c] for c in child_labels]})
                    if kind != "binary_split":
                        issues.append({"kind": kind, "frame": t + 1,
                                       "label": parent, "node": previous[parent]})
                if departures[parent] and children:
                    issues.append({"kind": "partial_row_departure", "frame": t + 1,
                                   "label": parent, "rows": [r + 1 for r in departures[parent]],
                                   "node": previous[parent]})
        assignments.append(mapping)
        previous = mapping
    for node in nodes.values():
        node["source_rows"] = sorted(node["source_rows"])
    return {"groups": groups, "nodes": nodes, "edges": edges, "issues": issues,
            "transitions": transitions, "assignments": assignments}


def fixtures() -> dict:
    # Retained mother label must become a new episode at a binary division.
    tree = topology([[1, 1, 1, 1], [1, 1, 2, 2]])
    assert len(tree["nodes"]) == 3 and len(tree["edges"]) == 2
    assert tree["assignments"][1][1] != tree["assignments"][2][1]
    assert tree["transitions"][0]["kind"] == "binary_split"
    assert not tree["issues"]
    # A merger is retained rather than forced into a unique-parent tree.
    assert any(i["kind"] == "multiple_parent_labels"
               for i in topology([[1, 3], [2, 3]])["issues"])
    assert any(i["kind"] == "label_rename"
               for i in topology([[1, 2]])["issues"])
    assert any(i["kind"] == "excess_offspring_labels"
               for i in topology([[1, 1], [1, 2], [1, 3]])["issues"])
    assert any(i["kind"] == "partial_row_arrival"
               for i in topology([[1, 1], [0, 1]])["issues"])
    assert any(i["kind"] == "partial_row_departure"
               for i in topology([[1, 1], [1, 0]])["issues"])
    late = topology([[0, 0, 5, 5]])
    assert len(late["nodes"]) == 1 and next(iter(late["nodes"].values()))["first_frame"] == 3
    single = topology([[1, 1, 1]], [[0, 1, 0]])
    assert len(single["nodes"]) == 2 and len(single["edges"]) == 1
    assert single["transitions"][0]["kind"] == "division_one_observed_daughter"
    none = topology([[1, 0]], [[1, 0]])
    assert none["transitions"][0]["kind"] == "division_no_observed_daughter"
    mixed, _ = audit({"Lineage": [[10, 10, 10], [20, 20, 20]],
                      "Divisions": [[0, 0, 0], [0, 1, 0]],
                      "Apoptosis": [[0, 0, 0], [0, 0, 0]],
                      "p53": [[1., 1., 1.], [1., 1., 1.]]})
    assert mixed["candidate_root_review"]["roots_with_any_structural_issue"] == 1
    assert mixed["candidate_root_review"]["roots_without_detected_structural_issue"] == 1
    assert mixed["candidate_root_review"]["initial_roots_without_detected_issue"] == 1
    # An upstream missing sister does not invalidate a later observed node's subtree.
    later, _ = audit({"Lineage": [[20, 20, 20, 20]],
                     "Divisions": [[0, 1, 0, 0]],
                     "Apoptosis": [[0, 0, 0, 0]], "p53": [[1., 1., 1., 1.]]},
                    baseline_frames=[3])
    assert later["baseline_subtree_checks"][0]["without_detected_post_baseline_issue"] == 1
    assert later["baseline_subtree_checks"][0]["with_prior_component_issue"] == 1
    return {"passed": True, "cases": 11,
            "scope": "Hand-constructed topology fixtures, not biological validation."}


def audit(arrays: dict, baseline_frames: list[int] | None = None) -> tuple[dict, dict]:
    L, D, A, P = (arrays[n] for n in ("Lineage", "Divisions", "Apoptosis", "p53"))
    graph = topology(L, D)
    groups, nodes = graph["groups"], graph["nodes"]
    issues = graph["issues"]
    consistency = Counter()
    event_keys = {"Divisions": set(), "Apoptosis": set()}
    for t, g in enumerate(groups):
        for label, rows in g.items():
            for name, arr in (("Divisions", D), ("Apoptosis", A), ("p53", P)):
                vals = {arr[r][t] for r in rows}
                if len(vals) > 1:
                    consistency[name] += 1
                    issues.append({"kind": f"same_label_{name}_disagreement", "frame": t + 1,
                                   "label": label, "node": graph["assignments"][t][label],
                                   "source_rows": [r + 1 for r in rows]})
                if name in event_keys and 1 in vals:
                    event_keys[name].add((label, t + 1))
    mask_checks = Counter()
    mask_group_keys = set()
    for r in range(len(L)):
        for t in range(len(L[0])):
            l0, pm = L[r][t] == 0, P[r][t] == -1
            if l0 != pm:
                mask_checks["lineage_zero_vs_p53_minus1_disagreements"] += 1
                direction = "lineage_zero_p53_present" if l0 else "lineage_present_p53_minus1"
                mask_checks[direction] += 1
                if not l0:
                    mask_group_keys.add((L[r][t], t+1))
                # Attach provenance only; this does not infer a missing biological fate.
                candidates = [j for j in range(len(L[0])) if L[r][j] != 0]
                if candidates:
                    near = min(candidates, key=lambda j: (abs(j-t), j))
                    label = L[r][near]
                    issues.append({"kind": direction, "frame": t + 1,
                                   "source_row": r + 1,
                                   "node": graph["assignments"][near][label]})
            for name, arr in (("Divisions", D), ("Apoptosis", A)):
                if arr[r][t] and l0:
                    mask_checks[name + "_ones_with_lineage_zero"] += 1
                if arr[r][t] and pm:
                    mask_checks[name + "_ones_with_p53_minus1"] += 1
    mask_checks["distinct_positive_label_frame_mask_disagreements"] = len(mask_group_keys)

    split_checks, matches = Counter(), set()
    split_detail = []
    for tr in graph["transitions"]:
        if tr["kind"] != "binary_split":
            continue
        f, a, children = tr["frame"], tr["parent_label"], tr["child_labels"]
        prior = (a, f - 1) in event_keys["Divisions"]
        new = [(c, f) in event_keys["Divisions"] for c in children]
        following = [(c, f + 1) in event_keys["Divisions"] for c in children]
        pattern = f"prior={int(prior)},new_daughters={sum(new)},next_daughters={sum(following)}"
        split_checks[pattern] += 1
        split_detail.append({**tr, "division_flag_prior_parent": prior,
                             "division_flags_new_children": new,
                             "division_flags_next_children": following})
        for key in [(a, f - 1)] + [(c, f) for c in children] + [(c, f + 1) for c in children]:
            if key in event_keys["Divisions"]:
                matches.add(key)
        if not prior and not any(new) and not any(following):
            issues.append({"kind": "binary_split_without_nearby_division_flag",
                           "frame": f, "label": a, "node": tr["parent_node"]})
    unmatched = sorted(event_keys["Divisions"] - matches)
    # Unmatched binary flags now become explicit observed one/no-daughter divisions
    # through event-aware topology, rather than silently extending the parent episode.

    # Structural annotation persistence, without reporting fate frequencies.
    pulse = {}
    for name, arr in (("Divisions", D), ("Apoptosis", A)):
        pulse[name] = {"adjacent_positive_pairs": sum(row[t] == row[t+1] == 1
                                for row in arr for t in range(len(row)-1)),
                       "max_consecutive_positive_run": max(
                           max((len(run) for run in "".join(str(v) for v in row).split("0")), default=0)
                           for row in arr)}

    children_by_node, parents_by_node = defaultdict(list), defaultdict(list)
    for edge in graph["edges"]:
        children_by_node[edge["parent"]].append(edge["child"])
        parents_by_node[edge["child"]].append(edge["parent"])
        assert nodes[edge["parent"]]["last_frame"] < nodes[edge["child"]]["first_frame"]
    roots = sorted(n for n in nodes if not parents_by_node[n])
    root_sets = {}
    for n in sorted(nodes, key=lambda n: (nodes[n]["first_frame"], n)):
        root_sets[n] = set().union(*(root_sets[p] for p in parents_by_node[n])) if parents_by_node[n] else {n}
    for n in nodes:
        nodes[n]["parent_nodes"] = sorted(parents_by_node[n])
        nodes[n]["child_nodes"] = sorted(children_by_node[n])
        nodes[n]["candidate_roots"] = sorted(root_sets[n])

    # A path ending before the final frame with no child is not automatically death.
    # Conversely, an annotation can precede disappearance of the tracked debris.
    end_check = Counter()
    for n, node in nodes.items():
        label, f = node["label"], node["last_frame"]
        annotations = [j for j in range(node["first_frame"], f+1)
                       if (label, j) in event_keys["Apoptosis"]]
        node["apoptosis_annotation_frames_in_episode"] = annotations
        if len(annotations) > 1:
            issues.append({"kind": "multiple_apoptosis_annotations_in_episode", "frame": f,
                           "label": label, "node": n})
        if annotations:
            node["tracking_frames_after_apoptosis_annotation"] = f - min(annotations)
            if f > min(annotations):
                end_check["episodes_with_tracking_after_apoptosis_annotation"] += 1
                end_check["maximum_tracking_frames_after_apoptosis_annotation"] = max(
                    end_check["maximum_tracking_frames_after_apoptosis_annotation"], f-min(annotations))
            if children_by_node[n]:
                issues.append({"kind": "candidate_descendants_after_apoptosis_annotation", "frame": f,
                               "label": label, "node": n})
        if not children_by_node[n] and f < len(L[0]) and not annotations:
            end_check["early_leaf_without_apoptosis_annotation_in_episode"] += 1
            issues.append({"kind": "early_leaf_without_apoptosis_annotation_in_episode", "frame": f,
                           "label": label, "node": n})

    issue_roots = defaultdict(set)
    for i in issues:
        for root in root_sets[i["node"]]:
            issue_roots[root].add(i["kind"])
    root_records = []
    for r in roots:
        node = nodes[r]
        members = [n for n in nodes if r in root_sets[n]]
        ambiguous = sorted(issue_roots.get(r, set()))
        root_records.append({"root": r, "source_label": node["label"],
                             "first_frame": node["first_frame"],
                             "candidate_cell_episodes": len(members),
                             "structural_issue_kinds": ambiguous,
                             "published_exclusion_label_match": node["label"] in EXCLUSIONS})
    descendants = {}
    for n in sorted(nodes, key=lambda n: (nodes[n]["first_frame"], n), reverse=True):
        descendants[n] = {n}.union(*(descendants[c] for c in children_by_node[n]))
    issues_by_node = defaultdict(list)
    for issue in issues:
        issues_by_node[issue["node"]].append(issue)
    baseline_checks, baseline_rosters = [], {}
    for frame in baseline_frames or []:
        if frame < 1 or frame > len(groups):
            raise ValueError("Baseline frame outside observed matrix")
        roster = []
        for label, rows in groups[frame-1].items():
            n = graph["assignments"][frame-1][label]
            if any(P[r][frame-1] == -1 for r in rows):
                continue
            if any(f < frame for f in nodes[n]["apoptosis_annotation_frames_in_episode"]):
                continue
            future_issues = [i for v in descendants[n] for i in issues_by_node[v]
                             if i["frame"] >= frame]
            prior = [i for i in issues
                     if (i["frame"] < frame or nodes[i["node"]]["last_frame"] < frame)
                     and root_sets[i["node"]] & root_sets[n]]
            roster.append({"node": n, "source_label": label, "frame": frame,
                           "candidate_roots": sorted(root_sets[n]),
                           "post_baseline_issue_kinds": sorted({i["kind"] for i in future_issues}),
                           "prior_component_issue": bool(prior)})
        kinds = Counter(k for record in roster for k in record["post_baseline_issue_kinds"])
        baseline_rosters[str(frame)] = roster
        baseline_checks.append({
            "frame": frame, "candidate_observed_baseline_nodes": len(roster),
            "without_detected_post_baseline_issue": sum(not r["post_baseline_issue_kinds"] for r in roster),
            "with_post_baseline_issue": sum(bool(r["post_baseline_issue_kinds"]) for r in roster),
            "with_prior_component_issue": sum(r["prior_component_issue"] for r in roster),
            "post_baseline_issue_kind_affected_node_counts": dict(sorted(kinds.items())),
            "completeness_filter_uses_future_recording_information": True})
    # These are candidate components. Do not label an issue-free component a verified family.
    summary = {
        "frame_groups": {"candidate_cell_frame_groups": sum(map(len, groups)),
                         "same_label_disagreements": {name: consistency[name] for name in NAMES if name != "Lineage"}},
        "candidate_topology": {"cell_episodes": len(nodes), "edges": len(graph["edges"]),
                               "root_episodes": len(roots),
                               "roots_present_first_frame": sum(nodes[n]["first_frame"] == 1 for n in roots),
                               "roots_first_seen_later": sum(nodes[n]["first_frame"] != 1 for n in roots),
                               "transition_kinds": dict(sorted(Counter(x["kind"] for x in graph["transitions"]).items())),
                               "nodes_with_multiple_parents": sum(len(v) > 1 for v in parents_by_node.values()),
                               "child_edge_count": sum(map(len, children_by_node.values())),
                               "each_child_starts_after_parent_last_frame": True,
                               "acyclic_by_frame_order": True},
        "division_flag_alignment": {"binary_split_patterns": dict(sorted(split_checks.items())),
                                    "unmatched_label_frame_flags_within_prior_new_next_window": len(unmatched),
                                    "window_is_structural_check_not_validated_event_timing": True},
        "tracking_end_annotation_checks": dict(sorted(end_check.items())),
        "mask_concordance": dict(sorted(mask_checks.items())),
        "event_encoding_persistence": pulse,
        "structural_issue_counts": dict(sorted(Counter(i["kind"] for i in issues).items())),
        "candidate_root_review": {
            "roots_with_any_structural_issue": len(issue_roots),
            "roots_without_detected_structural_issue": len(roots) - len(issue_roots),
            "initial_roots_without_detected_issue": sum(nodes[n]["first_frame"] == 1 and n not in issue_roots for n in roots),
            "published_exclusion_labels_matching_candidate_roots": len({nodes[n]["label"] for n in roots} & EXCLUSIONS),
            "unmatched_published_exclusion_labels": sorted(EXCLUSIONS - {nodes[n]["label"] for n in roots}),
            "published_identifier_namespace_not_verified": True,
            "no_issue_is_not_proof_of_complete_or_unselected_sampling": True},
        "baseline_subtree_checks": baseline_checks,
        "outcomes_fitted_or_curves_computed": False,
    }
    private = {"nodes": list(nodes.values()), "edges": graph["edges"], "roots": root_records,
               "issues": issues, "split_alignment": split_detail,
               "baseline_rosters": baseline_rosters,
               "event_annotation_keys": {k: sorted(v) for k, v in event_keys.items()}}
    return summary, private


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    public = root / "research/treatment-discovery/lineage-audit-2026-11-10/hct116-structure"
    private_dir = root / "tmp/hct116-lineage-structure"
    source = root / "research/treatment-discovery/sources/lineage-2026-11-10/41467_2018_7788_MOESM5_ESM.xlsx"
    plan = public / "protocol.json"
    if not plan.exists():
        raise FileNotFoundError("Frozen structural protocol is required")
    fixed = json.loads(plan.read_text())
    for field in ("source_workbook", "source_dictionary", "source_exclusions"):
        if digest(root / fixed[field]["path"]) != fixed[field]["sha256"]:
            raise ValueError(f"Pinned {field} hash changed")
    fixture_results = fixtures()
    arrays, schema = parse_workbook(source)
    baseline_frames = fixed["baseline_structural_extension"]["frames"]
    summary, private = audit(arrays, baseline_frames)
    # Repeat independent object construction to check determinism.
    summary2, private2 = audit(arrays, baseline_frames)
    assert summary == summary2 and private == private2
    write_json(private_dir / "candidate-graph.json", private)
    summary.update({"version": 2, "source_sha256": digest(source),
                    "protocol_sha256": digest(plan), "code_sha256": digest(Path(__file__)),
                    "schema": schema, "fixtures": fixture_results,
                    "repeat_run_identical": True,
                    "private_graph_path": "tmp/hct116-lineage-structure/candidate-graph.json",
                    "private_graph_sha256": digest(private_dir / "candidate-graph.json")})
    write_json(public / "results.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
