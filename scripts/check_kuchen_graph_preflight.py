#!/usr/bin/env python3
"""Independent constructed checks; never opens original source workbooks."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import itertools
import json
from pathlib import Path
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / 'scripts/build_kuchen_graph.py'
EXPECTED = 'be80f025ba7137b27cda1c6a755763eef0d9f938243e49be3f943f06881708c6'
PROTOCOL = ROOT / 'research/treatment-discovery/lineage-audit-2026-11-10/kuchen-source-audit/graph-audit/protocol.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run():
    if sha(BUILDER) != EXPECTED:
        raise ValueError('Reviewed source changed; review again before testing')
    spec = importlib.util.spec_from_file_location('reviewed_kuchen_graph', BUILDER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fixture_result = module.fixtures()
    protocol_hash = sha(PROTOCOL)
    plan = module.validate_plan(PROTOCOL, protocol_hash)
    # Independent transitive closure, not the production Kosaraju traversal.
    tested = 0
    for n in (1, 2, 3):
        possible = list(itertools.product(range(n), repeat=2))
        for mask in range(1 << len(possible)):
            edges = [edge for bit, edge in enumerate(possible) if mask & (1 << bit)]
            reach = [[False] * n for _ in range(n)]
            for a, b in edges:
                reach[a][b] = True
            for k in range(n):
                for i in range(n):
                    for j in range(n):
                        reach[i][j] = reach[i][j] or (reach[i][k] and reach[k][j])
            expected = {(a, b) for a, b in edges if reach[b][a]}
            if module.cyclic_edges(list(range(n)), edges) != expected:
                raise AssertionError(('Cycle-edge disagreement', n, mask))
            tested += 1
    assert tested == 530
    assert module.cyclic_edges([], []) == set()

    checks = ['empty directed graph', 'all 530 directed graphs on one through three nodes']
    # Unicode before and inside cells challenges byte offsets versus character offsets.
    original = '<c r="A9" t="inlineStr"><is><t>é &amp; α</t></is></c>'
    xml = ('<worksheet xmlns="' + module.NS['m'] + '"><!-- α before cell -->'
           '<sheetData><row r="9">' + original + '</row></sheetData></worksheet>').encode()
    assert module.exact_xml_cells(xml) == [original]
    raw = io.BytesIO()
    with zipfile.ZipFile(raw, 'w') as archive:
        archive.writestr('xl/worksheets/test.xml', xml)
    with zipfile.ZipFile(io.BytesIO(raw.getvalue())) as archive:
        rows, _ = module.read_worksheet(archive,
            {'xml_path': 'xl/worksheets/test.xml', 'sheet': 'constructed'},
            'constructed.xlsx', 'd' * 64)
    field = rows[0]['cells']['A']
    assert field['raw_xml_cell'] == original and field['resolved_text'] == 'é & α'
    checks.append('UTF-8 byte-exact cell markup with independently expected resolved text')

    row = module.fixture_row(2)
    try:
        module.build_sheet(module.fixture_meta(), [row, row])
    except ValueError as exc:
        assert 'Duplicate source row' in str(exc)
    else:
        raise AssertionError('Duplicate provenance silently accepted')
    checks.append('duplicate row provenance fails instead of overwriting')

    # Verify path guards before nonexistent synthetic inputs can be inspected.
    with tempfile.TemporaryDirectory(prefix='kuchen-review-') as tmp:
        outside = Path(tmp) / 'private'
        try:
            module.run_graph(PROTOCOL, protocol_hash, Path(tmp) / 'no-sources',
                             Path(tmp) / 'no-schema.json', outside, Path(tmp) / 'public.json')
        except ValueError as exc:
            assert 'excluded derived-source prefix' in str(exc)
        else:
            raise AssertionError('Outside private path accepted')
        assert not outside.exists()
        checks.append('private-output escape rejected before source access')

        inside = ROOT / plan['publication']['private_output_prefix'] / 'never-created-review-path'
        assert not inside.exists()
        try:
            module.run_graph(PROTOCOL, protocol_hash, Path(tmp) / 'no-sources',
                             Path(tmp) / 'no-schema.json', inside, inside / 'public.json')
        except ValueError as exc:
            assert 'Public aggregate path must be separate' in str(exc)
        else:
            raise AssertionError('Public report inside private output accepted')
        assert not inside.exists()
        checks.append('public/private output overlap rejected before source access')
    assert sha(BUILDER) == EXPECTED and sha(PROTOCOL) == protocol_hash
    return {
        'status': 'PASS', 'created_utc': datetime.now(timezone.utc).isoformat(),
        'checker_sha256': sha(__file__), 'builder_sha256': EXPECTED,
        'protocol_sha256': protocol_hash,
        'production_fixture_count_rerun': fixture_result['count'],
        'production_fixture_status': fixture_result['status'],
        'independent_exhaustive_graphs': tested,
        'additional_checks': checks,
        'real_source_workbooks_parsed': False,
        'source_graph_outputs_inspected_or_generated': False,
        'biological_outcomes_computed': False,
        'scope': 'Constructed software checks only; not empirical graph validation.'
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    if args.out and args.out.exists():
        raise FileExistsError('Preserve first review output')
    report = run()
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open('x') as handle:
            json.dump(report, handle, indent=2, allow_nan=False)
            handle.write('\n')
    print(json.dumps(report, indent=2))
