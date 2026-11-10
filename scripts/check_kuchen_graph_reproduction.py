#!/usr/bin/env python3
"""Exact structural graph reproduction; no graph builder/model imports.

Compare saved full private assertion graphs and public summaries after removing
only their top-level creation timestamps and comparing private artifact hashes
against their own manifests. Recheck all pinned original source/evidence bytes.
"""
import argparse
from datetime import datetime,timezone
import hashlib,json,os
from pathlib import Path
import tempfile

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'research/treatment-discovery/lineage-audit-2026-11-10/kuchen-source-audit/graph-audit'
PRIVATE=ROOT/'research/treatment-discovery/sources/lineage-2026-11-10/kuchen-graph-2026-11-10/derived'
SOURCE=ROOT/'research/treatment-discovery/sources/lineage-2026-11-10/alternative-lineage-2026-11-10'
CODE='be80f025ba7137b27cda1c6a755763eef0d9f938243e49be3f943f06881708c6'
PROTOCOL='6e0c73303c34a970d5fc17f6ffd7d0dfe478c0854435b7be20f085a8288bceae'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def canonical(obj):return json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def omit(obj,keys):return {k:v for k,v in obj.items() if k not in keys}


def validate_roster(artifacts,roster):
    expected=[(r['file'],r['sheet'],f'sheet-{i:02d}.json') for i,r in enumerate(roster)]
    actual=[(r['file'],r['sheet'],r['private_relative_file']) for r in artifacts]
    if len(set(actual))!=len(actual) or len({r[2] for r in actual})!=len(actual):
        raise ValueError('Duplicate private artifact or sheet mapping')
    if actual!=expected:raise ValueError('Private artifact roster differs from exact frozen source roster')


def validate_private_counts(payload,expected):
    summary=payload['summary'];graph=payload['graph']
    if (summary['file'],summary['sheet'])!=(expected['file'],expected['sheet']):
        raise ValueError('Private summary mapped to wrong source sheet')
    n=expected['expected_pair_rows']
    if (summary['pair_rows'],summary['observations'],len(graph['pair_records']),len(graph['recorded_observations']))!=(n,2*n,n,2*n):
        raise ValueError('Private source rows/observations do not reconcile with frozen roster')


def write_new(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.partial-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f'))
    with temporary.open('x') as f:json.dump(obj,f,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
    os.link(temporary,path);temporary.unlink()


def compare(first,second,private_first,private_second,source_dir,out):
    if Path(out).exists():raise FileExistsError('Preserve first reproduction report')
    plan=read(BASE/'protocol.json')
    if sha(BASE/'protocol.json')!=PROTOCOL:raise ValueError('Frozen protocol changed')
    a,b=read(first),read(second)
    for report in (a,b):
        if report['status']!='STRUCTURAL_GRAPH_ONLY_NOT_ANALYSIS_READY' or report['code_sha256']!=CODE or report['protocol_sha256']!=PROTOCOL:
            raise ValueError('Unexpected producer status or version')
        if (report['sheets'],report['pair_rows'],report['observations'])!=(7,4678,9356):raise ValueError('Source roster differs')
        if report['outcome_calculations'] or report['per_cell_output_public']:raise ValueError('Scope/publication guard mismatch')
    excludes={'created_utc','private_artifacts'}
    ca,cb=canonical(omit(a,excludes)),canonical(omit(b,excludes))
    if ca!=cb:raise ValueError('Public structural scientific/provenance payload differs')
    roster=plan['source_inputs']['sheet_roster']
    if len(roster)!=7 or sum(r['expected_pair_rows'] for r in roster)!=4678:raise ValueError('Unexpected frozen roster cardinality')
    for report in (a,b):validate_roster(report['private_artifacts'],roster)
    records=[]
    for left,right,expected_sheet in zip(a['private_artifacts'],b['private_artifacts'],roster):
        if omit(left,{'sha256'})!=omit(right,{'sha256'}):raise ValueError('Graph artifact labels differ')
        p,q=Path(private_first)/left['private_relative_file'],Path(private_second)/right['private_relative_file']
        if sha(p)!=left['sha256'] or sha(q)!=right['sha256']:raise ValueError('Graph bytes differ from first manifests')
        x,y=read(p),read(q)
        for graph in (x,y):
            if graph['code_sha256']!=CODE or graph['protocol_sha256']!=PROTOCOL:raise ValueError('Private graph provenance mismatch')
            validate_private_counts(graph,expected_sheet)
        cx,cy=canonical(omit(x,{'created_utc'})),canonical(omit(y,{'created_utc'}))
        if cx!=cy:raise ValueError('Raw tokens, scalar types, graph assertions or record provenance differ')
        records.append(dict(file=left['file'],sheet=left['sheet'],first_artifact_sha256=left['sha256'],
            second_artifact_sha256=right['sha256'],canonical_payload_sha256=hashlib.sha256(cx).hexdigest(),
            all_graph_and_provenance_fields_identical=True,observation_count=x['summary']['observations']))
    if sum(r['observation_count'] for r in records)!=9356:raise ValueError('Complete observation roster does not reconcile')
    expected=plan['implementation_contract']
    originals=[]
    for name,digest in expected['workbook_sha256'].items():
        actual=sha(Path(source_dir)/name)
        if actual!=digest:raise ValueError('Original source workbook changed')
        originals.append(dict(file=name,sha256=actual,unchanged=True))
    schema=ROOT/plan['source_inputs']['schema']
    if sha(schema)!=expected['schema_sha256']:raise ValueError('Original schema changed')
    for name,digest in plan.get('source_evidence',{}).items():
        if sha(ROOT/name)!=digest:raise ValueError('Frozen source evidence changed')
    result=dict(status='EXACT_REPRODUCTION',created_utc=datetime.now(timezone.utc).isoformat(),
        checker_code_sha256=sha(__file__),producer_code_sha256=CODE,protocol_sha256=PROTOCOL,
        first_public_report_sha256=sha(first),second_public_report_sha256=sha(second),
        public_canonical_payload_sha256=hashlib.sha256(ca).hexdigest(),
        public_exclusions=['top-level created_utc','private_artifacts hashes (each independently verified and payload compared)'],
        private_exclusions=['top-level created_utc'],comparison='Exact canonical UTF-8 JSON bytes, including scalar number types and raw source tokens.',
        sheets=7,observations=sum(r['observation_count'] for r in records),private_graphs=records,
        exact_unique_frozen_artifact_roster=True,per_sheet_source_row_and_observation_counts_reconciled=True,
        original_workbooks=originals,original_schema_and_evidence_hashes_unchanged=True,
        new_outcome_calculations=False)
    write_new(out,result)
    return dict(status=result['status'],sheets=7,observations=result['observations'],original_bytes_unchanged=True)


def fixtures():
    a={'created_utc':'first','value':1,'raw':'01','nested':{'created_utc':'source'}}
    b={**a,'created_utc':'second'}
    assert canonical(omit(a,{'created_utc'}))==canonical(omit(b,{'created_utc'}))
    assert canonical(a)!=canonical({**a,'value':1.0})
    assert canonical(a)!=canonical({**a,'raw':'1'})
    assert canonical(omit(a,{'created_utc'}))!=canonical(omit({**a,'nested':{'created_utc':'changed'}},{'created_utc'}))
    with tempfile.TemporaryDirectory(prefix='kuchen-reproduction-fixture-') as temporary:
        p=Path(temporary)/'x.json';write_new(p,a);before=sha(p)
        try:write_new(p,b);raise AssertionError('first output overwritten')
        except FileExistsError:assert sha(p)==before
    roster=[dict(file='source.xlsx',sheet='a',expected_pair_rows=2),dict(file='source.xlsx',sheet='b',expected_pair_rows=1)]
    artifacts=[dict(file=r['file'],sheet=r['sheet'],private_relative_file=f'sheet-{i:02d}.json') for i,r in enumerate(roster)]
    validate_roster(artifacts,roster)
    bad_rosters=[artifacts[:1],[artifacts[0],artifacts[0]],artifacts[::-1],
        [artifacts[0],{**artifacts[1],'private_relative_file':'sheet-00.json'}]]
    for bad in bad_rosters:
        try:validate_roster(bad,roster);raise AssertionError('Bad roster accepted')
        except ValueError:pass
    payload=dict(summary=dict(file='source.xlsx',sheet='a',pair_rows=2,observations=4),
        graph=dict(pair_records=[{},{}],recorded_observations=[{},{},{},{}]))
    validate_private_counts(payload,roster[0])
    try:validate_private_counts(payload,roster[1]);raise AssertionError('Wrong source sheet accepted')
    except ValueError:pass
    payload['graph']['recorded_observations'].pop()
    try:validate_private_counts(payload,roster[0]);raise AssertionError('Missing observation accepted')
    except ValueError:pass
    return dict(status='PASS',count=13,code_sha256=sha(__file__),fixtures=['only top-level creation time excluded','integer versus float change detected','raw lexical token change detected','nested provenance retained','first reproduction output preserved','exact roster accepted','missing sheet rejected','duplicate sheet rejected','reordered source mapping rejected','duplicate private file rejected','exact private counts accepted','wrong source sheet rejected','missing observation rejected'],source_graphs_read=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',action='store_true');p.add_argument('--fixture-report',type=Path)
    p.add_argument('--first',type=Path,default=BASE/'results.json');p.add_argument('--second',type=Path,default=BASE/'reproduction-results.json')
    p.add_argument('--private-first',type=Path,default=PRIVATE/'first');p.add_argument('--private-second',type=Path,default=PRIVATE/'reproduction')
    p.add_argument('--source-dir',type=Path,default=SOURCE);p.add_argument('--out',type=Path,default=BASE/'reproduction.json')
    args=p.parse_args();f=fixtures()
    if args.fixture_report:write_new(args.fixture_report,f)
    print(json.dumps(f,indent=2),flush=True)
    if args.run:print(json.dumps(compare(args.first,args.second,args.private_first,args.private_second,args.source_dir,args.out),indent=2),flush=True)


if __name__=='__main__':main()
