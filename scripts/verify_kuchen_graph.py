#!/usr/bin/env python3
"""Independent XML/Decimal structural reference for the frozen Kuchen graph.

No production implementation is imported. This program has no scientific query
time, survival mask, covariance or model-fitting operation. Raw rows stay local.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
import math
from pathlib import Path
import posixpath
import re
import sys
import tempfile
import traceback
import xml.etree.ElementTree as ET
import zipfile
from xml.sax.saxutils import quoteattr

ROOT = Path(__file__).resolve().parents[1]
G = Path('research/treatment-discovery/lineage-audit-2026-11-10/kuchen-source-audit/graph-audit')
PROTOCOL_SHA = '6e0c73303c34a970d5fc17f6ffd7d0dfe478c0854435b7be20f085a8288bceae'
VERSION = 'independent-kuchen-graph-1'
MAIN = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PKG = 'http://schemas.openxmlformats.org/package/2006/relationships'
TOL = Decimal('0.000001')
RESIDUAL_COMPARE_TOL = 1e-9
NO_MASK_CONTRACT = dict(recording_end=None,event_boundary_convention='unresolved',
                        continuous_tracking_support='unresolved',death_is_absorbing_mask=False)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def portable(path):
    try:
        return str(Path(path).resolve().relative_to(ROOT))
    except ValueError:
        return '<external>/' + Path(path).name


def finite_check(value, path='$'):
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError('nonfinite numeric leaf at ' + path)
    if isinstance(value, dict):
        for k, v in value.items():
            finite_check(v, path + '.' + str(k))
    elif isinstance(value, (list, tuple)):
        for i, v in enumerate(value):
            finite_check(v, path + '[' + str(i) + ']')


def write_new(path, payload):
    finite_check(payload)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write('\n')


def frozen_protocol(path):
    assert digest(path) == PROTOCOL_SHA, 'frozen protocol SHA mismatch'
    return json.loads(Path(path).read_text())


def guard_private(path,protocol):
    prefix=(ROOT/protocol['publication']['private_output_prefix']).resolve()
    assert Path(path).resolve().is_relative_to(prefix), 'private output outside frozen excluded prefix'


def key(kind, *parts):
    # Encoding contract supplied without production implementation/outputs.
    token = json.dumps([kind, *parts], ensure_ascii=False, separators=(',', ':'))
    return kind + ':' + hashlib.sha256(token.encode()).hexdigest()


def text_content(element):
    return ''.join(x.text or '' for x in element.iter('{'+MAIN+'}t')) if element is not None else ''


def classify(raw, formula=None, storage_type=None, absent=False):
    if formula is not None:
        return 'formula_unverified', None
    if absent:
        return 'missing_absent', None
    if raw is None or raw == '':
        return 'missing_empty', None
    if raw == 'NaN':
        return 'missing_literal_NaN', None
    if storage_type == 'e':
        return 'xml_error', None
    try:
        value = Decimal(raw)
    except (InvalidOperation, ValueError):
        return 'invalid_numeric', None
    if not value.is_finite():
        return 'nonfinite_numeric', None
    return 'finite', value


def accepted_identity(cell):
    if cell['formula'] is not None or cell['storage_type'] == 'e':
        return None
    raw = cell['text']
    return raw if raw not in (None, '', 'NaN') else None


def numeric(cell):
    return classify(cell['text'], cell['formula'], cell['storage_type'], cell['absent'])


def missing(status):
    return status.startswith('missing_')


def packed_number(value):
    return None if value is None else str(value)


def empty_cell(coordinate):
    return dict(coordinate=coordinate, storage_type=None, raw=None, text=None,
                formula=None, absent=True, shared_string_index=None)


def xml_structure(element):
    return [element.tag, sorted(element.attrib.items()), element.text,
            [xml_structure(child) for child in element]]


def read_xlsx(path, expected_sha, schema_rows):
    """Independent package relationship resolver and literal XML cell parser."""
    assert digest(path) == expected_sha, 'workbook hash mismatch before read'
    with zipfile.ZipFile(path) as archive:
        strings = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            document = ET.fromstring(archive.read('xl/sharedStrings.xml'))
            strings = [text_content(si) for si in document.findall('{'+MAIN+'}si')]
        relationship_root = ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
        paths = {}
        for relationship in relationship_root:
            assert relationship.attrib.get('TargetMode') != 'External', 'external workbook relationship'
            target = relationship.attrib['Target']
            paths[relationship.attrib['Id']] = (target.lstrip('/') if target.startswith('/')
                else posixpath.normpath(posixpath.join('xl', target)))
        book = ET.fromstring(archive.read('xl/workbook.xml'))
        mapping = {s.attrib['name']: paths[s.attrib['{'+REL+'}id']]
                   for s in book.find('{'+MAIN+'}sheets')}
        assert set(mapping) == {s['sheet'] for s in schema_rows}, 'unexpected workbook sheet roster'
        result = []
        for schema in schema_rows:
            assert mapping[schema['sheet']] == schema['xml_path'], 'sheet relationship mismatch'
            source_xml=archive.read(mapping[schema['sheet']])
            worksheet = ET.fromstring(source_xml)
            namespaces={}
            for event,declaration in ET.iterparse(io.BytesIO(source_xml),events=['start-ns']):
                prefix,uri=declaration
                namespaces.setdefault(prefix,uri)
            rows = []
            seen_rows = set()
            for ordinal, row in enumerate(worksheet.find('{'+MAIN+'}sheetData')):
                row_number = int(row.attrib['r'])
                assert row_number not in seen_rows, 'duplicate XML row index'
                seen_rows.add(row_number)
                cells = {}
                for element in row.findall('{'+MAIN+'}c'):
                    coordinate = element.attrib['r']
                    assert coordinate not in cells, 'duplicate XML coordinate'
                    match = re.fullmatch(r'([A-Z]+)([0-9]+)',coordinate)
                    assert match and int(match.group(2)) == row_number, 'XML coordinate/row mismatch'
                    storage_type = element.attrib.get('t')
                    val = element.find('{'+MAIN+'}v')
                    raw = val.text if val is not None else None
                    formula = element.find('{'+MAIN+'}f')
                    formula_text = None if formula is None else (formula.text or '')
                    si = None
                    if storage_type == 's':
                        si = int(raw)
                        assert 0 <= si < len(strings), 'invalid shared string index'
                        resolved = strings[si]
                    elif storage_type == 'inlineStr':
                        resolved = text_content(element.find('{'+MAIN+'}is'))
                    else:
                        resolved = raw
                    cells[coordinate] = dict(coordinate=coordinate, storage_type=storage_type,
                        raw=raw, text=resolved, formula=formula_text, absent=False,
                        shared_string_index=si,xml_structure=xml_structure(element))
                rows.append(dict(row=row_number, ordinal=ordinal, cells=cells))
            assert rows and rows[0]['row'] == 1, 'expected explicit first header row'
            headers = rows[0]['cells']
            declared_headers={column+'1' for column in schema['columns']}
            assert declared_headers <= set(headers), 'declared header coordinate missing'
            extra_headers={k:v for k,v in headers.items() if k not in declared_headers}
            assert all(v['formula'] is None and v['text'] is None and not v['xml_structure'][3]
                       for v in extra_headers.values()), 'undeclared nonempty header cell'
            for column, exact in schema['columns'].items():
                actual = headers.get(column+'1', empty_cell(column+'1'))
                assert actual['formula'] is None and actual['text'] == exact, 'header mismatch'
            assert len(rows) - 1 == schema['data_rows'], 'source row count mismatch'
            assert [r['row'] for r in rows[1:]] == list(range(2, schema['data_rows']+2)), 'unexpected row roster'
            result.append(dict(file=Path(path).name, sheet=schema['sheet'], sha=expected_sha,
                xml_path=schema['xml_path'],xml_namespaces=namespaces,
                xml_sha256=hashlib.sha256(source_xml).hexdigest(),xml_bytes=len(source_xml),
                extra_header_cells=extra_headers,
                columns=schema['columns'], rows=rows[1:]))
    assert digest(path) == expected_sha, 'workbook changed while reading'
    return result


def components(vertices, edges):
    """Undirected flood fill; independent of producer grouping implementation."""
    adjacency = {v: set() for v in vertices}
    for a, b in edges:
        adjacency[a].add(b)
        adjacency[b].add(a)
    unseen = set(vertices)
    result = []
    while unseen:
        seed = min(unseen)
        stack = [seed]
        found = set()
        while stack:
            v = stack.pop()
            if v in found:
                continue
            found.add(v)
            stack.extend(adjacency[v] - found)
        unseen -= found
        result.append(sorted(found))
    return sorted(result)


def strongly_connected(vertices, edges):
    """Iterative Kosaraju decomposition, before timing/annotation filtering."""
    forward = {v: [] for v in vertices}
    reverse = {v: [] for v in vertices}
    for a, b in sorted(edges):
        forward[a].append(b)
        reverse[b].append(a)
    seen = set()
    finish = []
    for start in sorted(vertices):
        if start in seen:
            continue
        seen.add(start)
        stack = [(start, iter(forward[start]))]
        while stack:
            v, iterator = stack[-1]
            child = next(iterator, None)
            if child is None:
                finish.append(v)
                stack.pop()
            elif child not in seen:
                seen.add(child)
                stack.append((child, iter(forward[child])))
    seen.clear()
    groups = []
    for start in reversed(finish):
        if start in seen:
            continue
        group = set()
        stack = [start]
        while stack:
            v = stack.pop()
            if v in seen:
                continue
            seen.add(v)
            group.add(v)
            stack.extend(reverse[v])
        groups.append(sorted(group))
    cyclic = [g for g in groups if len(g)>1 or (g[0],g[0]) in edges]
    memberships = {v:i for i,g in enumerate(cyclic) for v in g}
    internal = {(a,b) for a,b in edges if a in memberships and memberships.get(b)==memberships[a]}
    return sorted(cyclic), internal


def fields_of(sheet, row):
    assert len({h.strip() for h in sheet['columns'].values()})==len(sheet['columns'])
    return {header.strip(): row['cells'].get(column+str(row['row']), empty_cell(column+str(row['row'])))
            for column, header in sheet['columns'].items()}


def fate(fields, side):
    birth_status, birth = numeric(fields['Birth time'])
    durations = {}
    for name, suffix in [('division','cycle length'),('death','time to death'),('loss','time to cell loss')]:
        status, value = numeric(fields[f'Sibling {side} {suffix}'])
        durations[name] = (status, value)
    present = [name for name,(status,value) in durations.items() if not missing(status)]
    usable = None
    if len(present)==1:
        name = present[0]
        status, value = durations[name]
        if status=='finite' and value>=0:
            usable = name
    terminal = birth + durations[usable][1] if usable is not None and birth is not None else None
    return dict(birth_status=birth_status, birth=birth, durations=durations,
                present=present, usable=usable, terminal=terminal)


def identity_check(left, right):
    if left is None or right is None:
        return 'unavailable'
    return 'consistent' if left==right else 'mismatch'


def residual_check(left, right):
    if left is None or right is None:
        return dict(status='unavailable', residual=None)
    delta = left-right
    return dict(status='consistent' if abs(delta)<=TOL else 'mismatch', residual=packed_number(delta))


def reconstruct(sheet):
    namespace = (sheet['sha'], sheet['sheet'])
    observations, pairs = {}, {}
    owners = defaultdict(list)
    successors = defaultdict(list)
    for row in sheet['rows']:
        fields = fields_of(sheet,row)
        pair_id = key('pair',*namespace,row['row'])
        mother = accepted_identity(fields['Mother ID'])
        grandmother = accepted_identity(fields['Grandmother ID'])
        lineage = accepted_identity(fields['Lineage ID'])
        generation_status, generation = numeric(fields['Generation'])
        pair = dict(id=pair_id,row=row['row'],ordinal=row['ordinal'],fields=fields,mother=mother,
                    grandmother=grandmother,lineage=lineage,generation_status=generation_status,
                    generation=generation,observations=[])
        mapped_coordinates={column+str(row['row']) for column in sheet['columns']}
        pair['unmapped_cells']={k:v for k,v in row['cells'].items() if k not in mapped_coordinates}
        pairs[pair_id]=pair
        if mother is not None:
            successors[mother].append(pair_id)
        for side in (1,2):
            oid = key('observation',*namespace,row['row'],side)
            token = accepted_identity(fields[f'Sibling {side} ID'])
            record = dict(id=oid,pair=pair_id,row=row['row'],side=side,token=token,
                          mother=mother,grandmother=grandmother,lineage=lineage,
                          generation=generation,generation_status=generation_status,
                          fate=fate(fields,side))
            observations[oid]=record
            pair['observations'].append(oid)
            if token is not None:
                owners[token].append(oid)
    raw=set()
    for oid, child in observations.items():
        parent_ids=owners.get(child['mother'],[]) if child['mother'] is not None else []
        if len(parent_ids)==1 and child['token'] is not None and len(owners[child['token']])==1:
            raw.add((parent_ids[0],oid))
    sccs, cycle_edges=strongly_connected(observations,raw)
    consistent=set()
    edge_records=[]
    repeats=[]
    for oid,child in observations.items():
        token=child['mother']
        parent_ids=owners.get(token,[]) if token is not None else []
        refkind=('missing' if token is None else 'external' if not parent_ids else
                 'unique' if len(parent_ids)==1 else 'ambiguous')
        parent=observations[parent_ids[0]] if len(parent_ids)==1 else None
        identity_ok=parent is not None and child['token'] is not None and len(owners[child['token']])==1
        rawedge=(parent['id'],oid) if identity_ok else None
        checks=dict(identity='consistent' if identity_ok else 'unavailable',
            successor_pair_uniqueness=('unavailable' if token is None else 'consistent' if len(successors[token])==1 else 'mismatch'),
            cycle='mismatch' if rawedge in cycle_edges else 'consistent' if rawedge else 'unavailable')
        if parent is None:
            checks.update(parent_division='unavailable',parent_child_time=dict(status='unavailable',residual=None),
                          lineage='unavailable',generation='unavailable',grandmother_reference='unavailable')
        else:
            pf=parent['fate']
            checks['parent_division']='consistent' if pf['usable']=='division' else 'mismatch'
            checks['parent_child_time']=residual_check(child['fate']['birth'],pf['terminal'] if pf['usable']=='division' else None)
            checks['lineage']=identity_check(child['lineage'],parent['lineage'])
            pg,cg=parent['generation'],child['generation']
            checks['generation']='unavailable' if pg is None or cg is None else 'consistent' if cg==pg+1 else 'mismatch'
            checks['grandmother_reference']=identity_check(child['grandmother'],parent['mother'])
        allowed=(identity_ok and checks['successor_pair_uniqueness']=='consistent'
                 and checks['cycle']=='consistent' and checks['parent_division']=='consistent'
                 and checks['parent_child_time']['status']=='consistent'
                 and all(checks[k]!='mismatch' for k in ('lineage','generation','grandmother_reference')))
        if allowed:
            consistent.add(rawedge)
        edge_records.append(dict(child=oid,parent=None if parent is None else parent['id'],
            parent_candidates=sorted(parent_ids),parent_token=token,reference_kind=refkind,
            raw=identity_ok,consistent=allowed,checks=checks))
        pair=pairs[child['pair']]
        # Repeated annotations are arithmetic evidence, never identity repair.
        cases=[('mother_cycle','Mother cycle length',parent,'division'),
               ('grandmother_cycle_vs_mother_annotation','Grandmother cycle length',parent,'Mother cycle length')]
        gm_ids=owners.get(child['grandmother'],[]) if child['grandmother'] is not None else []
        gm=observations[gm_ids[0]] if len(gm_ids)==1 else None
        cases.append(('grandmother_cycle','Grandmother cycle length',gm,'division'))
        for kind,header,relative,target in cases:
            status,supplied=numeric(pair['fields'][header])
            if relative is None:
                recorded=None
            elif target=='division':
                recorded=relative['fate']['durations']['division'][1]
            else:
                _,recorded=numeric(pairs[relative['pair']]['fields'][target])
            check=residual_check(supplied,recorded)
            repeats.append(dict(child=oid,reference=None if relative is None else relative['id'],
                kind=kind,header=header,supplied=packed_number(supplied),recorded=packed_number(recorded),
                supplied_status=status,**check))
    relation_buckets=defaultdict(set)
    for oid,obs in observations.items():
        for token in (obs['token'],obs['mother'],obs['grandmother']):
            if token is not None:
                relation_buckets[('identity',token)].add(oid)
        if obs['lineage'] is not None:
            relation_buckets[('lineage',obs['lineage'])].add(oid)
    related_edges=set()
    for nodes in relation_buckets.values():
        ordered=sorted(nodes)
        related_edges.update((ordered[0],x) for x in ordered[1:])
    groups={name:components(observations,edges) for name,edges in
            [('raw',raw),('consistent',consistent),('related',related_edges)]}
    references=defaultdict(set)
    for oid,obs in observations.items():
        for kind in ('mother','grandmother'):
            token=obs[kind]
            if token is not None and token not in owners:
                references[token].add((kind,oid))
    aliases=defaultdict(set)
    for token in set(owners)|set(references):
        try:
            value=Decimal(token)
            if value.is_finite():
                aliases[value].add(token)
        except InvalidOperation:
            pass
    aliases=sorted(sorted(v) for v in aliases.values() if len(v)>1)
    successor_records={}
    for oid,obs in observations.items():
        sp=successors.get(obs['token'],[]) if obs['token'] is not None else []
        successor_records[oid]=dict(pair_ids=sorted(sp),usable_fate=obs['fate']['usable'],
            division_annotation=packed_number(obs['fate']['durations']['division'][1]),
            uniquely_identified=obs['token'] is not None and len(owners[obs['token']])==1)
    summary=dict(file=sheet['file'],sheet=sheet['sheet'],workbook_sha256=sheet['sha'],
        pair_rows=len(pairs),observations=len(observations),unique_nonmissing_cell_tokens=len(owners),
        uniquely_recorded_entities=sum(len(v)==1 for v in owners.values()),
        duplicate_identity_entities=sum(len(v)>1 for v in owners.values()),
        observations_missing_usable_identity=sum(o['token'] is None for o in observations.values()),
        source_lineage_label_groups=len({o['lineage'] for o in observations.values() if o['lineage'] is not None}),
        lexical_numeric_alias_groups=len(aliases),raw_unique_recorded_edges=len(raw),
        consistent_recorded_edges=len(consistent),cyclic_raw_edges=len(cycle_edges),
        directed_cyclic_sccs=len(sccs),self_raw_edges=sum(a==b for a,b in raw),
        external_reference_entities=len(references),
        external_mother_assertions=sum(e['reference_kind']=='external' for e in edge_records),
        group_counts={k:len(v) for k,v in groups.items()},
        group_size_histograms={k:dict(sorted(Counter(map(len,v)).items())) for k,v in groups.items()},
        raw_root_observations=len(observations)-len({b for a,b in raw}),
        consistent_root_observations=len(observations)-len({b for a,b in consistent}),
        usable_fate_labels=dict(Counter(o['fate']['usable'] or 'unresolved' for o in observations.values())),
        repeated_cycle_check_statuses={kind:dict(Counter(r['status'] for r in repeats if r['kind']==kind))
            for kind in ('mother_cycle','grandmother_cycle_vs_mother_annotation','grandmother_cycle')},
        no_outcome_grid=True,no_original_founder_assignment=True,no_continuous_observation_mask=True)
    private=dict(namespace=list(namespace),xml_namespaces=sheet.get('xml_namespaces',{'':MAIN}),
        xml_path=sheet['xml_path'],xml_sha256=sheet.get('xml_sha256'),xml_bytes=sheet.get('xml_bytes'),
        extra_header_cells=sheet.get('extra_header_cells',{}),
        pairs=pairs,observations=observations,entities=dict(owners),
        raw_edges=sorted(raw),consistent_edges=sorted(consistent),cyclic_sccs=sccs,cycle_edges=sorted(cycle_edges),
        edges=edge_records,repeated=repeats,groups=groups,external_references={k:sorted(v) for k,v in references.items()},
        aliases=aliases,successors=successor_records)
    # Convert only independently parsed Decimal quantities; raw strings survive.
    def encode(value):
        if isinstance(value,Decimal):
            return str(value)
        if isinstance(value,dict):
            return {str(k):encode(v) for k,v in value.items()}
        if isinstance(value,(list,tuple)):
            return [encode(v) for v in value]
        return value
    return summary,encode(private)


def fixture_sheet(rows, sheet_name='fixture'):
    headers=['Lineage ID','Sibling 1 cycle length','Sibling 1 time to death','Sibling 1 time to cell loss ',
             'Sibling 2 cycle length','Sibling 2 time to death','Sibling 2 time to cell loss','Birth time ',
             'Sibling 1 ID','Sibling 2 ID ','Mother ID','Generation','Mother cycle length',
             'Grandmother cycle length','Grandmother ID']
    columns={chr(65+i):h for i,h in enumerate(headers)}
    result=[]
    for rn,values in enumerate(rows,2):
        base={h.strip():'NaN' for h in headers}
        base.update(values)
        cells={}
        for col,header in columns.items():
            token=base[header.strip()]
            formula=None
            if isinstance(token,tuple):
                token,formula=token
            cells[col+str(rn)]=dict(coordinate=col+str(rn),storage_type='inlineStr',raw=None,
                text=str(token),formula=formula,absent=False,shared_string_index=None)
        result.append(dict(row=rn,ordinal=rn-1,cells=cells))
    return dict(file='synthetic.xlsx',sheet=sheet_name,sha='synthetic',xml_path='fixture.xml',columns=columns,rows=result)


def fixture_rows():
    return [
        {'Lineage ID':'L','Sibling 1 ID':'a','Sibling 2 ID':'b','Mother ID':'root',
         'Grandmother ID':'older','Generation':'2','Birth time':'0','Sibling 1 cycle length':'1',
         'Sibling 2 time to death':'2'},
        {'Lineage ID':'L','Sibling 1 ID':'c','Sibling 2 ID':'d','Mother ID':'a',
         'Grandmother ID':'root','Generation':'3','Birth time':'1','Mother cycle length':'1',
         'Sibling 1 time to death':'1','Sibling 2 time to cell loss':'2'}]


def run_fixtures():
    cases=[]
    def evaluate(name,rows,check):
        summary,private=reconstruct(fixture_sheet(rows))
        check(summary,private)
        cases.append(name)
    def assert_equal(a,b):
        assert a==b,(a,b)
    evaluate('clean_chain_and_external_parent',fixture_rows(),
             lambda s,p:assert_equal((s['raw_unique_recorded_edges'],s['consistent_recorded_edges'],s['group_counts']['related']),(2,2,1)))
    rows=fixture_rows(); rows[1]['Sibling 1 time to cell loss']='-1'; rows[1]['Sibling 1 time to death']='NaN'
    evaluate('invalid_child_fate_keeps_birth_edge',rows,lambda s,p:assert_equal(s['consistent_recorded_edges'],2))
    for bad in ('garbage','Infinity',('NaN','=bad()')):
        rows=fixture_rows(); rows[0]['Sibling 1 time to death']=bad
        evaluate('invalid_competing_parent_fate_'+str(bad),rows,lambda s,p:assert_equal(s['consistent_recorded_edges'],0))
    rows=fixture_rows(); rows[1]['Sibling 1 ID']='a'
    evaluate('duplicate_identity_does_not_split_related_group',rows,
             lambda s,p:assert_equal((s['duplicate_identity_entities'],s['raw_unique_recorded_edges'],s['group_counts']['related']),(1,0,1)))
    rows=fixture_rows(); rows.append(dict(rows[1],**{'Sibling 1 ID':'e','Sibling 2 ID':'f'}))
    evaluate('duplicate_successor_blocks_all_birth_edges',rows,
             lambda s,p:assert_equal((s['raw_unique_recorded_edges'],s['consistent_recorded_edges']),(4,0)))
    for field,value in [('Lineage ID','other'),('Generation','9'),('Grandmother ID','unrelated'),('Birth time','1.1')]:
        rows=fixture_rows(); rows[1][field]=value
        evaluate('conflict_'+field,rows,lambda s,p:assert_equal(s['consistent_recorded_edges'],0))
    rows=fixture_rows(); rows[1]['Mother cycle length']='9'
    evaluate('repeated_duration_does_not_block_birth_edges',rows,lambda s,p:assert_equal(s['consistent_recorded_edges'],2))
    rows=fixture_rows(); rows[1]['Lineage ID']='NaN'; rows[1]['Generation']='NaN'; rows[1]['Grandmother ID']='NaN'
    evaluate('unavailable_annotations_are_not_matches',rows,
             lambda s,p:assert_equal((s['consistent_recorded_edges'],p['edges'][-1]['checks']['lineage']),(2,'unavailable')))
    cyc=fixture_rows(); cyc[0]['Mother ID']='c'; cyc[1]['Sibling 1 cycle length']='1';cyc[1]['Sibling 1 time to death']='NaN'
    evaluate('cycle_basis_precedes_timing_filter',cyc,
             lambda s,p:assert_equal((s['directed_cyclic_sccs'],s['cyclic_raw_edges']),(1,2)))
    assert components([0,1,2],[(0,1)])==[[0,1],[2]]
    cases.append('clean_component_beside_affected')
    assert strongly_connected([0,1,2],{(0,0),(0,1),(1,2)})==([[0]],{(0,0)})
    cases.append('self_cycle_keeps_downstream')
    assert residual_check(Decimal('1.000001'),Decimal(1))['status']=='consistent'
    assert residual_check(Decimal('1.0000010001'),Decimal(1))['status']=='mismatch'
    cases.append('exact_decimal_tolerance_boundary')
    assert key('observation','sha','one',2,1)!=key('observation','sha','two',2,1)
    cases.append('namespace_separation')
    rows=fixture_rows(); rows[0]['Sibling 1 ID']='1';rows[1]['Mother ID']='1.0'
    evaluate('numeric_alias_does_not_join',rows,
             lambda s,p:assert_equal((s['raw_unique_recorded_edges'],s['lexical_numeric_alias_groups']),(0,1)))
    assert classify('NaN')[0]=='missing_literal_NaN'
    assert classify('nan')[0]=='nonfinite_numeric'
    assert classify('2','=1+1')[0]=='formula_unverified'
    cases.append('explicit_missing_formula_nonfinite_rules')
    with tempfile.TemporaryDirectory() as td:
        out=Path(td)/'new.json';write_new(out,{'okay':True})
        try:
            write_new(out,{'overwrite':True})
        except FileExistsError:
            pass
        else:
            raise AssertionError('overwrite guard failed')
        try:
            write_new(Path(td)/'nonfinite.json',{'bad':float('nan')})
        except ValueError:
            pass
        else:
            raise AssertionError('nonfinite output accepted')
        # A miniature original-format package, containing shared, inline, numeric
        # and formula cells. This does not access either scientific workbook.
        zpath=Path(td)/'synthetic.xlsx'
        schema=[dict(file='synthetic.xlsx',sheet='s',xml_path='xl/worksheets/sheet1.xml',
                     columns={'A':'Header'},data_rows=1)]
        with zipfile.ZipFile(zpath,'w') as z:
            z.writestr('xl/workbook.xml',f'<workbook xmlns="{MAIN}" xmlns:r="{REL}"><sheets><sheet name="s" r:id="r1"/></sheets></workbook>')
            z.writestr('xl/_rels/workbook.xml.rels',f'<Relationships xmlns="{PKG}"><Relationship Id="r1" Target="worksheets/sheet1.xml"/></Relationships>')
            z.writestr('xl/sharedStrings.xml',f'<sst xmlns="{MAIN}"><si><r><t>Hea</t></r><r><t>der</t></r></si></sst>')
            z.writestr('xl/worksheets/sheet1.xml',f'<worksheet xmlns="{MAIN}"><sheetData><row r="1"><c r="A1" t="s"><v>0</v></c><c r="D1" s="1"/></row><row r="2"><c r="A2" t="inlineStr"><is><t>01</t></is></c><c r="B2"><f/><v>2</v></c><c r="C2" t="n"><v>3</v></c></row></sheetData></worksheet>')
        decoded=read_xlsx(zpath,digest(zpath),schema)[0]['rows'][0]['cells']
        assert decoded['A2']['text']=='01' and decoded['A2']['raw'] is None
        assert decoded['B2']['formula']=='' and numeric(decoded['B2'])[0]=='formula_unverified'
        assert decoded['C2']['storage_type']=='n' and numeric(decoded['C2'])[1]==3
        assert read_xlsx(zpath,digest(zpath),schema)[0]['rows'][0]['ordinal']==1
        assert set(read_xlsx(zpath,digest(zpath),schema)[0]['extra_header_cells'])=={'D1'}
        original=ET.fromstring(f'<c xmlns="{MAIN}" r="A1"><v>7</v></c>')
        wrapped=ET.fromstring(f'<root xmlns="{MAIN}"><c r="A1"><v>7</v></c></root>')[0]
        assert xml_structure(original)==xml_structure(wrapped)
    cases.append('independent_xml_package_provenance')
    cases.append('blank_formatted_header_retained_without_new_field')
    assert NO_MASK_CONTRACT==dict(recording_end=None,event_boundary_convention='unresolved',
                                 continuous_tracking_support='unresolved',death_is_absorbing_mask=False)
    for field,replacement in [('recording_end',0),('event_boundary_convention',None),
                              ('continuous_tracking_support','continuous'),('death_is_absorbing_mask',True)]:
        wrong=dict(NO_MASK_CONTRACT);wrong[field]=replacement
        assert wrong!=NO_MASK_CONTRACT
    cases.append('post_first_comparison_explicit_four_no_mask_contract_tokens')
    cases.append('no_overwrite_and_no_nonfinite_output')
    return dict(status='PASS',fixture_count=len(cases),fixtures=cases)


def compare_reference(args):
    """Schema adapter only: compare all independent structural reference fields."""
    assert args.reference and args.production_directory and args.private_output and args.production_summary
    protocol=frozen_protocol(args.protocol)
    guard_private(args.private_output,protocol)
    assert not args.output.exists() and not args.private_output.exists()
    reference_hash=digest(args.reference)
    reference=json.loads(args.reference.read_text())
    assert reference['status']=='PASS' and reference['protocol_sha256']==PROTOCOL_SHA
    reference_pin_path=args.reference_code_pin or args.pin
    reference_pin=json.loads(reference_pin_path.read_text())
    assert reference['code_sha256']==reference_pin['code_sha256'], 'immutable reference code differs from its pin'
    assert reference_pin['protocol_sha256']==PROTOCOL_SHA
    pin=json.loads(args.pin.read_text())
    assert pin['code_sha256']==digest(__file__) and pin['protocol_sha256']==PROTOCOL_SHA
    counts=Counter(); mismatches=[]; producer_hashes=[];numeric_differences=[]
    def compare(category,path,expected,actual,number=False):
        counts[category]+=1
        equal=expected==actual
        if number and expected is not None and actual is not None:
            difference=abs(float(expected)-float(actual))
            numeric_differences.append(difference)
            equal=math.isfinite(float(actual)) and difference<=RESIDUAL_COMPARE_TOL
        if not equal:
            mismatches.append(dict(category=category,path=path,expected=expected,actual=actual))
    def normalized_groups(items):
        return sorted(sorted(x['observation_ids']) for x in items)
    def numeric_compare(path,expected,actual):
        compare('numeric',path,expected,actual,number=True)
    try:
        production_summary_hash=digest(args.production_summary)
        published=json.loads(args.production_summary.read_text());finite_check(published)
        assert published['status']=='STRUCTURAL_GRAPH_ONLY_NOT_ANALYSIS_READY'
        assert published['protocol_sha256']==PROTOCOL_SHA
        assert published['schema_sha256']==protocol['implementation_contract']['schema_sha256']
        assert published['input_workbook_sha256']==protocol['implementation_contract']['workbook_sha256']
        assert published['sheets']==7 and len(published['summaries'])==len(published['read_checks'])==7
        artifacts=published['private_artifacts']
        assert len(artifacts)==7 and len({a['private_relative_file'] for a in artifacts})==7
        compare('manifest_roster','private_filenames',
                [f'sheet-{i:02d}.json' for i in range(7)],sorted(a['private_relative_file'] for a in artifacts))
        compare('manifest_roster','sheet_roster',
                [(s['file'],s['sheet']) for s in protocol['source_inputs']['sheet_roster']],
                [(a['file'],a['sheet']) for a in artifacts])
        for artifact in artifacts:
            target=args.production_directory/artifact['private_relative_file']
            compare('manifest_hashes',artifact['private_relative_file'],artifact['sha256'],digest(target))
        actual_sheets={}
        for path in sorted(args.production_directory.glob('sheet-*.json')):
            p=json.loads(path.read_text()); finite_check(p)
            assert p['status']=='ASSERTION_GRAPH_NOT_ANALYSIS_READY' and p['protocol_sha256']==PROTOCOL_SHA
            assert p['schema_sha256']==protocol['implementation_contract']['schema_sha256']
            assert p['code_sha256']==published['code_sha256']
            identity=(p['summary']['file'],p['summary']['sheet'])
            assert identity not in actual_sheets,'duplicate production sheet'
            actual_sheets[identity]=p
            producer_hashes.append(dict(path=portable(path),sha256=digest(path),code_sha256=p['code_sha256']))
        compare('sheet_roster','sheets',sorted((s['file'],s['sheet']) for s in reference['sheets']),sorted(actual_sheets))
        expected_roster=sorted((s['file'],s['sheet']) for s in protocol['source_inputs']['sheet_roster'])
        compare('frozen_sheet_roster','reference',expected_roster,sorted((s['file'],s['sheet']) for s in reference['sheets']))
        compare('frozen_sheet_roster','production',expected_roster,sorted(actual_sheets))
        assert len(reference['sheets'])==len(actual_sheets)==7
        for refsheet in reference['sheets']:
            label=refsheet['file']+'/'+refsheet['sheet']; r=refsheet['graph']
            p=actual_sheets[(refsheet['file'],refsheet['sheet'])]; g=p['graph']
            published_sheet=[x for x in published['summaries'] if (x['file'],x['sheet'])==(refsheet['file'],refsheet['sheet'])]
            assert len(published_sheet)==1,'non-unique public sheet summary'
            compare('public_private_summary',label,p['summary'],published_sheet[0])
            readcheck=[x for x in published['read_checks'] if (x['file'],x['sheet'])==(refsheet['file'],refsheet['sheet'])]
            assert len(readcheck)==1,'non-unique source read check'
            expected_readcheck=dict(file=refsheet['file'],sheet=refsheet['sheet'],xml_path=r['xml_path'],
                header_excel_row=1,pair_rows=refsheet['summary']['pair_rows'],xml_sha256=r['xml_sha256'],xml_bytes=r['xml_bytes'])
            compare('source_read_checks',label,expected_readcheck,readcheck[0])
            compare('worksheet_provenance',label,dict(xml_sha256=r['xml_sha256'],xml_bytes=r['xml_bytes']),p['worksheet_provenance'])
            compare('namespace',label,r['namespace'],[g['namespace']['workbook_sha256'],g['namespace']['sheet']])
            p_pairs={x['pair_id']:x for x in g['pair_records']}
            p_obs={x['observation_id']:x for x in g['recorded_observations']}
            compare('pair_roster',label,sorted(r['pairs']),sorted(p_pairs))
            compare('observation_roster',label,sorted(r['observations']),sorted(p_obs))
            compare('unique_serialized_records',label,len(p_pairs),len(g['pair_records']))
            compare('unique_serialized_records',label,len(p_obs),len(g['recorded_observations']))
            for pid,pair in r['pairs'].items():
                q=p_pairs[pid]
                for own,prod in [('row','excel_row'),('mother','mother_token'),('grandmother','grandmother_token'),('lineage','source_lineage_label')]:
                    compare('pair_fields',pid+'/'+prod,pair[own],q[prod])
                numeric_compare(pid+'/generation',pair['generation'],q['generation'])
                compare('pair_fields',pid+'/observations',pair['observations'],q['observation_ids'])
                compare('field_roster',pid,sorted(pair['fields']),sorted(q['fields']))
                unmapped={re.match(r'[A-Z]+',coordinate).group():cell for coordinate,cell in pair['unmapped_cells'].items()}
                compare('unmapped_field_roster',pid,sorted(unmapped),sorted(q['unmapped_xml_fields']))
                for column,cell in unmapped.items():
                    target=q['unmapped_xml_fields'][column]
                    for own,prod in [('coordinate','excel_cell'),('storage_type','xml_cell_type'),('raw','raw_storage_token'),('text','resolved_text')]:
                        compare('unmapped_cell_provenance',pid+'/'+column+'/'+prod,cell[own],target[prod])
                    declarations=' '.join(('xmlns'+(':'+prefix if prefix else '')+'='+quoteattr(uri))
                                          for prefix,uri in r['xml_namespaces'].items())
                    fragment=ET.fromstring('<independent-wrapper '+declarations+'>'+target['raw_xml_cell']+'</independent-wrapper>')
                    assert len(fragment)==1
                    compare('unmapped_cell_xml_structure',pid+'/'+column,cell['xml_structure'],json.loads(json.dumps(xml_structure(fragment[0]))))
                for header,cell in pair['fields'].items():
                    target=q['fields'][header]
                    expected={'workbook_sha256':r['namespace'][0],'sheet':r['namespace'][1],
                              'workbook_file':refsheet['file'],'excel_row':pair['row'],
                              'xml_sheet_path':r['xml_path'],'row_xml_ordinal':pair['ordinal'],
                              'excel_cell':cell['coordinate'],'raw_storage_token':cell['raw'],
                              'resolved_text':cell['text'],'xml_cell_type':cell['storage_type'],
                              'shared_string_index':cell['shared_string_index'],
                              'formula_text':cell['formula'] or None}
                    for field,value in expected.items():
                        compare('cell_provenance',pid+'/'+header+'/'+field,value,target[field])
                    if cell['formula'] is not None:
                        compare('formula_quarantine',pid+'/'+header,'formula_unresolved',target['field_status'])
                    if not cell['absent']:
                        declarations=' '.join(('xmlns'+(':'+prefix if prefix else '')+'='+quoteattr(uri))
                                              for prefix,uri in r['xml_namespaces'].items())
                        fragment=ET.fromstring('<independent-wrapper '+declarations+'>'+target['raw_xml_cell']+'</independent-wrapper>')
                        assert len(fragment)==1,'raw cell fragment must contain exactly one cell'
                        source_tree=xml_structure(fragment[0])
                        # JSON reconstitution changes tuple attributes to lists.
                        source_tree=json.loads(json.dumps(source_tree))
                        compare('cell_xml_structure',pid+'/'+header,cell.get('xml_structure'),source_tree)
            for oid,obs in r['observations'].items():
                q=p_obs[oid]
                for own,prod in [('pair','pair_id'),('side','sibling_side'),('token','cell_token')]:
                    compare('observation_fields',oid+'/'+prod,obs[own],q[prod])
                event=q['event_annotation']; fate=obs['fate']
                numeric_compare(oid+'/birth',fate['birth'],event['birth_value'])
                numeric_compare(oid+'/terminal',fate['terminal'],event['candidate_terminal_time'])
                compare('fate_semantics',oid+'/usable',fate['usable'],event['usable_nonnegative_fate'])
                for kind,(status,value) in fate['durations'].items():
                    numeric_compare(oid+'/duration/'+kind,value,event['duration_fields'][kind]['value'])
                for field,value in NO_MASK_CONTRACT.items():
                    compare('no_mask_claim',oid+'/'+field,value,event[field])
            p_edges={x['child_observation_id']:x for x in g['mother_assertion_edges']}
            compare('edge_roster',label,sorted(r['observations']),sorted(p_edges))
            compare('edge_roster',label+'/no_duplicate',len(p_edges),len(g['mother_assertion_edges']))
            prod_raw=set();prod_consistent=set()
            refkind={'missing':'missing_reference','external':'external_reference','ambiguous':'ambiguous_recorded_reference','unique':'unique_recorded_reference'}
            for edge in r['edges']:
                oid=edge['child'];q=p_edges[oid]
                for own,prod in [('parent','parent_observation_id'),('parent_token','parent_token'),('raw','raw_unique_identity_join'),('consistent','consistent_recorded_parent_edge')]:
                    compare('edges',oid+'/'+prod,edge[own],q[prod])
                compare('edges',oid+'/candidates',edge['parent_candidates'],sorted(q['candidate_parent_observation_ids']))
                compare('edges',oid+'/refkind',refkind[edge['reference_kind']],q['parent_reference_kind'])
                if q['raw_unique_identity_join']:
                    prod_raw.add((q['parent_observation_id'],oid))
                if q['consistent_recorded_parent_edge']:
                    prod_consistent.add((q['parent_observation_id'],oid))
                own=edge['checks'];actual=q['checks']
                compare('check_roster',oid,sorted(own),sorted(actual))
                for k in ('lineage','generation','grandmother_reference'):
                    compare('edge_checks',oid+'/'+k,own[k],actual[k])
                expected_identity='unique' if edge['raw'] else refkind[edge['reference_kind']]+'_or_ambiguous_child'
                compare('edge_checks',oid+'/identity',expected_identity,actual['identity'])
                expected_successor='unique' if own['successor_pair_uniqueness']=='consistent' else 'missing_or_multiple'
                compare('edge_checks',oid+'/successor',expected_successor,actual['successor_pair_uniqueness'])
                expected_cycle='cyclic_edge' if own['cycle']=='mismatch' else 'not_in_raw_directed_cycle'
                compare('edge_checks',oid+'/cycle',expected_cycle,actual['cycle'])
                expected_division={'consistent':'usable_division','mismatch':'not_one_usable_division','unavailable':'unavailable'}[own['parent_division']]
                compare('edge_checks',oid+'/parent_division',expected_division,actual['parent_division'])
                compare('edge_checks',oid+'/time_status',own['parent_child_time']['status'],actual['parent_child_time']['status'])
                numeric_compare(oid+'/time_residual',own['parent_child_time']['residual'],actual['parent_child_time']['residual_in_source_time_units'])
            compare('raw_edge_set',label,r['raw_edges'],sorted(map(list,prod_raw)))
            compare('consistent_edge_set',label,r['consistent_edges'],sorted(map(list,prod_consistent)))
            compare('cyclic_scc_membership',label,r['cyclic_sccs'],normalized_groups(g['cyclic_strong_components']))
            for k,prod in [('raw','raw_recorded_components'),('consistent','consistent_recorded_components'),('related','conservative_related_groups')]:
                compare('component_membership',label+'/'+k,r['groups'][k],normalized_groups(g[prod]))
                cover=[v for group in g[prod] for v in group['observation_ids']]
                compare('component_partition',label+'/'+k,sorted(r['observations']),sorted(cover))
            p_repeats={(x['child_observation_id'],x['kind']):x for x in g['repeated_cycle_checks']}
            compare('repeated_roster',label,len(p_repeats),len(r['repeated']))
            compare('repeated_roster',label+'/duplicates',len(p_repeats),len(g['repeated_cycle_checks']))
            for check in r['repeated']:
                oid=check['child'];q=p_repeats[(oid,check['kind'])]
                compare('repeated_checks',oid+'/'+check['kind']+'/reference',check['reference'],q['reference_observation_id'])
                compare('repeated_checks',oid+'/'+check['kind']+'/status',check['status'],q['status'])
                compare('repeated_checks',oid+'/'+check['kind']+'/header',check['header'],q['source_header'])
                for own,prod in [('supplied','supplied_value'),('recorded','recorded_value'),('residual','residual_in_source_time_units')]:
                    numeric_compare(oid+'/'+check['kind']+'/'+own,check[own],q[prod])
            consistent_children={b for a,b in r['consistent_edges']}
            for oid,own in r['successors'].items():
                q=p_obs[oid]['successor_state'];pids=own['pair_ids']
                if own['usable_fate']!='division':
                    expected='not_one_usable_division'
                elif not pids:
                    expected='missing_successor_pair_unknown_descendants'
                elif len(pids)>1:
                    expected='multiple_successor_pair_assertions_unresolved'
                elif all(x in consistent_children for x in r['pairs'][pids[0]]['observations']):
                    expected='unique_consistent_successor_pair'
                else:
                    expected='successor_pair_assertions_unresolved'
                compare('successor_states',oid+'/status',expected,q['status'])
                compare('successor_states',oid+'/pairs',pids,sorted(q['asserted_pair_ids']))
                compare('successor_states',oid+'/child_count',2*len(pids),q['recorded_child_observation_count'])
                compare('successor_uncertainty',oid+'/cardinality',None,q['unknown_descendant_cardinality'])
                compare('successor_uncertainty',oid+'/binary',False,q['binary_offspring_assumption'])
                compare('successor_uncertainty',oid+'/missing_count',0 if expected=='unique_consistent_successor_pair' else None,q['missing_successor_record_assertion_count'])
            aliases=sorted(sorted(x['tokens']) for x in g['numeric_alias_groups'])
            compare('numeric_aliases',label,r['aliases'],aliases)
            entities={x['token']:sorted(x['observation_ids']) for x in g['recorded_entities']}
            compare('entity_membership',label,{k:sorted(v) for k,v in r['entities'].items()},entities)
            for entity in g['recorded_entities']:
                compare('entity_metadata',entity['entity_id']+'/id',key('entity',*r['namespace'],entity['token']),entity['entity_id'])
                compare('entity_metadata',entity['entity_id']+'/status','unique' if len(entity['observation_ids'])==1 else 'ambiguous_multiple_observations',entity['identity_status'])
            ext={x['token']:x for x in g['external_references']}
            compare('external_roster',label,sorted(r['external_references']),sorted(ext))
            for token,uses in r['external_references'].items():
                q=ext[token]
                compare('external_references',q['reference_id']+'/id',key('external_reference',*r['namespace'],token),q['reference_id'])
                compare('external_references',q['reference_id']+'/users',sorted({v for k,v in uses}),sorted(q['referenced_by_observation_ids']))
                compare('external_references',q['reference_id']+'/roles',sorted({k for k,v in uses}),q['roles'])
                for field,value in [('observed_episode',False),('birth',None),('terminal_event',None),('original_founder_status','not_identified')]:
                    compare('external_uncertainty',q['reference_id']+'/'+field,value,q[field])
            lineages=defaultdict(list)
            for oid,obs in r['observations'].items():
                if obs['lineage'] is not None:
                    lineages[obs['lineage']].append(oid)
            compare('lineage_label_groups',label,{k:sorted(v) for k,v in lineages.items()},
                    {q['label']:sorted(q['observation_ids']) for q in g['source_lineage_label_groups']})
            # Public summaries derive independently where names share semantics.
            for k,value in refsheet['summary'].items():
                if k in ('group_counts','group_size_histograms','directed_cyclic_sccs'):
                    continue
                compare('summary',label+'/'+k,value,p['summary'][k])
            compare('summary',label+'/cyclic_raw_scc_count',refsheet['summary']['directed_cyclic_sccs'],p['summary']['cyclic_raw_scc_count'])
            compare('summary',label+'/cyclic_scc_size_histogram',
                    {str(k):v for k,v in Counter(map(len,r['cyclic_sccs'])).items()},p['summary']['cyclic_scc_size_histogram'])
            time_residuals=[abs(Decimal(e['checks']['parent_child_time']['residual'])) for e in r['edges']
                            if e['checks']['parent_child_time']['residual'] is not None]
            numeric_compare(label+'/maximum_absolute_parent_child_residual',
                str(max(time_residuals)) if time_residuals else None,p['summary']['maximum_absolute_parent_child_residual_source_units'])
            compare('summary',label+'/mother_assertions',len(r['observations']),p['summary']['mother_assertions'])
            for kind,prod in [('raw','raw_recorded_components'),('consistent','consistent_recorded_components'),('related','conservative_related_groups')]:
                compare('summary',label+'/group_counts/'+prod,len(r['groups'][kind]),p['summary']['group_counts'][prod])
                compare('summary',label+'/group_size_histogram/'+kind,
                        refsheet['summary']['group_size_histograms'][kind],p['summary']['group_size_histograms'][kind])
            # Issue serialization is an internal cross-check, not a second
            # independent issue-name ontology; source semantics are above.
            issues=g['issues'];issue_by_obs=defaultdict(set)
            for issue in issues:
                for oid in issue['observation_ids']:
                    assert oid in r['observations'],'issue references an absent observation'
                    issue_by_obs[oid].add(issue['code'])
            compare('internal_issue_bookkeeping',label+'/counts',dict(Counter(x['code'] for x in issues)),p['summary']['issue_record_counts'])
            compare('internal_issue_bookkeeping',label+'/affected_observations',
                    {code:sum(code in codes for codes in issue_by_obs.values()) for code in sorted({x['code'] for x in issues})},
                    p['summary']['affected_observation_counts'])
            for kind,prod in [('raw','raw_recorded_components'),('consistent','consistent_recorded_components'),('related','conservative_related_groups')]:
                for group in g[prod]:
                    expected=sorted(set().union(*(issue_by_obs[v] for v in group['observation_ids'])))
                    compare('internal_issue_bookkeeping',group['group_id'],expected,group['issue_codes'])
                compare('internal_issue_bookkeeping',label+'/no_issue/'+kind,
                        sum(not group['issue_codes'] for group in g[prod]),p['summary']['groups_with_no_recorded_issue'][kind])
            compare('internal_status_bookkeeping',label+'/blocking_reasons',
                dict(Counter(reason for edge in g['mother_assertion_edges'] for reason in set(edge['blocking_reasons']))),
                p['summary']['consistent_edge_blocking_reasons'])
            compare('internal_status_bookkeeping',label+'/reference_kinds',dict(Counter(e['parent_reference_kind'] for e in g['mother_assertion_edges'])),p['summary']['edge_parent_reference_kinds'])
            compare('internal_status_bookkeeping',label+'/fate_states',dict(Counter(o['event_annotation']['terminal_state'] for o in g['recorded_observations'])),p['summary']['fate_annotation_states'])
            compare('internal_status_bookkeeping',label+'/successor_states',dict(Counter(o['successor_state']['status'] for o in g['recorded_observations'])),p['summary']['successor_states'])
        assert digest(args.reference)==reference_hash,'reference artifact changed during comparison'
        assert digest(args.production_summary)==production_summary_hash,'production summary changed during comparison'
        for artifact in artifacts:
            assert digest(args.production_directory/artifact['private_relative_file'])==artifact['sha256'],'private source artifact changed during comparison'
        result=dict(status='PASS' if not mismatches else 'FAIL',created_utc=now(),protocol_sha256=PROTOCOL_SHA,
            code_sha256=digest(__file__),reference_sha256=reference_hash,production_summary_sha256=production_summary_hash,
            immutable_reference_code_sha256=reference['code_sha256'],reference_code_pin_sha256=digest(reference_pin_path),
            producer_artifacts=producer_hashes,
            comparisons_by_category=dict(counts),comparison_count=sum(counts.values()),mismatch_count=len(mismatches),
            mismatches_by_category=dict(Counter(x['category'] for x in mismatches)),
            residual_absolute_tolerance=RESIDUAL_COMPARE_TOL,
            maximum_absolute_numeric_difference=max(numeric_differences,default=0.0),
            additional_post_first_comparison_checks=['continuous_tracking_support','death_is_absorbing_mask'],
            independent_scope='Original XML/source fields, Decimal times, identities, raw and consistent edges, repeated annotations, cycles, components, related groups, successors and common aggregate fields.',
            internal_only_scope='Producer issue-code naming and issue-count/group issue-code serialization checked for self-consistency, not independently recoded.',
            no_outcome_grid=True)
        write_new(args.private_output,dict(report=result,mismatches=mismatches))
        result['private_comparison']=dict(path=portable(args.private_output),sha256=digest(args.private_output))
        write_new(args.output,result)
        return result
    except BaseException as exc:
        failure=dict(status='FAIL',created_utc=now(),protocol_sha256=PROTOCOL_SHA,code_sha256=digest(__file__),
                     error_type=type(exc).__name__,comparisons_by_category=dict(counts),
                     mismatch_count=len(mismatches))
        write_new(Path(str(args.private_output)+'.failure.json'),dict(report=failure,message=str(exc),mismatches=mismatches,traceback=traceback.format_exc()))
        write_new(Path(str(args.output)+'.failure.json'),failure)
        raise


def source_reference(args):
    protocol=frozen_protocol(args.protocol)
    guard_private(args.private_output,protocol)
    pin=json.loads(args.pin.read_text())
    assert pin['code_sha256']==digest(__file__), 'source execution requires matching independent code pin'
    assert pin['protocol_sha256']==PROTOCOL_SHA
    assert not args.output.exists() and not args.private_output.exists(), 'first outputs already exist'
    schema_path=ROOT/protocol['source_inputs']['schema']
    assert digest(schema_path)==protocol['implementation_contract']['schema_sha256']
    schema=json.loads(schema_path.read_text())
    public=dict(status='RUNNING',created_utc=now(),protocol_sha256=PROTOCOL_SHA,
                code_sha256=digest(__file__),schema_sha256=digest(schema_path),sheets=[])
    private=dict(status='RUNNING',protocol_sha256=PROTOCOL_SHA,code_sha256=digest(__file__),sheets=[])
    current=None
    try:
        for filename,sha in protocol['implementation_contract']['workbook_sha256'].items():
            path=ROOT/protocol['source_inputs']['directory']/filename
            for sheet in read_xlsx(path,sha,[s for s in schema if s['file']==filename]):
                current=dict(file=filename,sheet=sheet['sheet'])
                summary,graph=reconstruct(sheet)
                public['sheets'].append(summary)
                private['sheets'].append(dict(file=filename,sheet=sheet['sheet'],summary=summary,graph=graph))
        assert digest(schema_path)==public['schema_sha256']
        public['status']=private['status']='PASS'
        public['counts']=dict(sheets=len(public['sheets']),pair_rows=sum(s['pair_rows'] for s in public['sheets']),
                              observations=sum(s['observations'] for s in public['sheets']))
        assert public['counts']==dict(sheets=7,pair_rows=4678,observations=9356)
        write_new(args.private_output,private)
        public['private_artifact']=dict(path=portable(args.private_output),sha256=digest(args.private_output))
        write_new(args.output,public)
        return public
    except BaseException as exc:
        failure=dict(status='FAIL',created_utc=now(),protocol_sha256=PROTOCOL_SHA,code_sha256=digest(__file__),
                     current_sheet=current,error_type=type(exc).__name__,completed_summaries=public['sheets'])
        # Private partial results retained in their own unused failure path.
        write_new(Path(str(args.private_output)+'.failure.json'),dict(failure=failure,partial=private,message=str(exc),traceback=traceback.format_exc()))
        write_new(Path(str(args.output)+'.failure.json'),failure)
        raise


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mode',choices=['fixtures','pin','reference','compare'])
    ap.add_argument('--protocol',type=Path,default=ROOT/G/'protocol.json')
    ap.add_argument('--pin',type=Path,default=ROOT/G/'independent-code-pin.json')
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--private-output',type=Path)
    ap.add_argument('--reference',type=Path)
    ap.add_argument('--production-directory',type=Path)
    ap.add_argument('--production-summary',type=Path)
    ap.add_argument('--prior-source-failure',type=Path)
    ap.add_argument('--reference-code-pin',type=Path)
    ap.add_argument('--prior-comparison',type=Path)
    args=ap.parse_args()
    if args.mode=='fixtures':
        assert not args.output.exists()
        try:
            result=run_fixtures()
            result.update(created_utc=now(),code_sha256=digest(__file__),scope='synthetic_only_no_original_workbook_access')
            write_new(args.output,result)
        except BaseException as exc:
            write_new(Path(str(args.output)+'.failure.json'),dict(status='FAIL',code_sha256=digest(__file__),
                error_type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc()))
            raise
    elif args.mode=='pin':
        frozen_protocol(args.protocol)
        result=dict(status='PINNED_BEFORE_THIS_COMPARISON' if args.prior_comparison else 'PINNED_BEFORE_THIS_SOURCE_RUN',created_utc=now(),code_sha256=digest(__file__),
                    protocol_sha256=PROTOCOL_SHA,implementation=portable(__file__),
                    production_access='schema-only lines516–545 and schema descriptions; no production algorithm imports',
                    source_inputs_read=bool(args.prior_source_failure or args.prior_comparison),production_outputs_read=bool(args.prior_comparison),
                    arithmetic='Decimal source arithmetic; logical residual tolerance1e−6',
                    later_residual_comparison_absolute_tolerance=RESIDUAL_COMPARE_TOL)
        if args.prior_source_failure:
            result['preserved_prior_source_failure']=dict(path=portable(args.prior_source_failure),sha256=digest(args.prior_source_failure))
        if args.prior_comparison:
            result['preserved_prior_comparison']=dict(path=portable(args.prior_comparison),sha256=digest(args.prior_comparison))
            result['revision_scope']='Comparison-only boundary token correction, explicit tracking/absorbing-mask assertions, numeric-difference diagnostic, separate immutable-reference pin and FAIL exit status; no source reconstruction changes or rerun.'
        write_new(args.output,result)
    elif args.mode=='reference':
        assert args.private_output is not None,'reference requires excluded private output path'
        result=source_reference(args)
    else:
        result=compare_reference(args)
    print(json.dumps({k:v for k,v in result.items() if k in ('status','counts','fixture_count','code_sha256')},sort_keys=True))
    if result.get('status')=='FAIL':
        raise SystemExit(1)


if __name__=='__main__':
    main()
