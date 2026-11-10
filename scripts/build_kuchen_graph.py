#!/usr/bin/env python3
"""Conservative observation/ancestry graph for pinned Kuchen source workbooks.

Default executes synthetic fixtures only. No real workbook is opened unless
--run supplies a frozen protocol and its exact hash. Per-observation, edge and
reference outputs are restricted to the ignored lineage source directory.
No outcome grid, survival, covariance, rate, fit or treatment comparison.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict, deque
from datetime import datetime,timezone
from decimal import Decimal,InvalidOperation
import hashlib
import io
import json
import math
import os
from pathlib import Path,PurePosixPath
import posixpath
import re
import tempfile
import xml.etree.ElementTree as ET
from xml.parsers import expat
import zipfile

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'research/treatment-discovery/lineage-audit-2026-11-10/kuchen-source-audit'
EXCLUDED=ROOT/'research/treatment-discovery/sources/lineage-2026-11-10'
SOURCE=EXCLUDED/'alternative-lineage-2026-11-10'
NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
REL_NS='http://schemas.openxmlformats.org/package/2006/relationships'
RID_NS='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PARSER_VERSION='kuchen-xml-graph-1'
CONTRACT={
 'version':'kuchen-graph-v1',
 'schema_sha256':'c0b676bd16c3a1eeac12dadf061498e7f7830fdfeded69f6d7d042396768f3db',
 'workbook_sha256':{'kuchen-control.xlsx':'8ecdd5c66a466b71b5ee4790c79c2b9ce38fd1ec6daf59f88347d67e4fa1b86e',
                    'kuchen-perturbation.xlsx':'0065797f9d1cb12dc695bf9baa516f68afea1d6c6077b75c2a9830389806a6f3'},
 'identity':'exact_resolved_text_no_numeric_merge_namespaced_workbook_sha_sheet',
 'duplicates':'retain_each_row_side_observation_ambiguous_entity_no_preferred_record',
 'time_residual_tolerance':1e-6,
 'time_tolerance_role':'arithmetic_consistency_not_imaging_precision',
 'component_vertices':'all_recorded_row_side_observations_external_references_separate',
 'component_edges':['unique_recorded_identity_joins','consistent_recorded_parent_edges'],
 'consistent_edge_requirements':['unique_parent_and_child_identity','unique_successor_pair_assertion_for_parent',
   'not_self_or_inside_directed_cycle','one_finite_nonnegative_parent_division_other_fates_recognized_source_missing_no_invalid_or_formula_fate',
   'finite_child_birth_and_time_residual_within_tolerance',
   'no_present_lineage_generation_grandmother_reference_conflict'],
 'missing_annotations':'retain_unavailable_check_status_not_a_positive_match',
 'repeat_cycle_annotation_mismatch':'retain_residual_and_issue_do_not_replace_or_block_edge_alone',
 'cycle_quarantine':'only_edges_inside_cyclic_scc_no_blanket_descendant_exclusion',
 'missing_successor_cardinality':None,'recording_end':None,
 'continuous_tracking_support':'unresolved','event_boundary_convention':'unresolved','outcome_grid':None,
 'source_ascertainment':'unresolved_export_selection','source_condition_labels':'preserve_no_reassignment',
 'related_groups':'shared_nonmissing_recorded_or_ancestor_identity_assertions_including_ambiguous_identities_plus_same_nonmissing_source_lineage_label_within_namespace',
 'formula_cells':'preserve_formula_and_cached_token_unverified_no_execution',
 'scc_basis':'raw_unique_recorded_identity_directed_graph_before_other_edge_filtering'
}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def sha_bytes(data):return hashlib.sha256(data).hexdigest()
def utc():return datetime.now(timezone.utc).isoformat()
def key(kind,*parts):return kind+':'+sha_bytes(json.dumps([kind,*parts],ensure_ascii=False,separators=(',',':')).encode())


def write_new(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.partial-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f'))
    with tmp.open('x') as f:json.dump(data,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
    os.link(tmp,path);tmp.unlink()


def exact_xml_cells(data):
    """Extract original cell element bytes using Expat byte offsets.

    ET subsequently supplies namespace-aware values. Raw markup remains a
    separate provenance field; neither shared-string indices nor numeric ID
    lexemes are converted through floating point.
    """
    def tag_end(begin):
        quote=None
        for i in range(begin,len(data)):
            char=data[i]
            if quote is not None:
                if char==quote:quote=None
            elif char in (34,39):quote=char
            elif char==62:return i+1
        raise ValueError('Unterminated XML tag')
    parser=expat.ParserCreate(namespace_separator='}')
    spans=[];active=None
    def start(name,attrs):
        nonlocal active
        if name.rsplit('}',1)[-1]=='c':
            if active is not None:raise ValueError('Nested worksheet cell')
            begin=parser.CurrentByteIndex
            finish=tag_end(begin)
            active=(begin,finish,data[begin:finish].rstrip().endswith(b'/>'))
    def end(name):
        nonlocal active
        if name.rsplit('}',1)[-1]=='c':
            if active is None:raise ValueError('Missing XML cell start')
            begin,start_end,self_closing=active
            finish=start_end if self_closing else tag_end(parser.CurrentByteIndex)
            if finish<=begin:raise ValueError('Unterminated XML cell end tag')
            spans.append(data[begin:finish].decode('utf-8'))
            active=None
    parser.StartElementHandler=start;parser.EndElementHandler=end
    parser.Parse(data,True)
    return spans


def rich_text(element):
    parts=[]
    for child in element:
        local=child.tag.rsplit('}',1)[-1]
        if local=='t':parts.append(child.text or '')
        elif local=='r':
            t=child.find('m:t',NS)
            if t is not None:parts.append(t.text or '')
    return ''.join(parts)


def workbook_mapping(archive):
    workbook=ET.fromstring(archive.read('xl/workbook.xml'))
    relroot=ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
    relations={}
    for r in relroot:
        rid=r.attrib['Id']
        if rid in relations:raise ValueError('Duplicate workbook relationship ID')
        target=r.attrib.get('Target','')
        if r.attrib.get('TargetMode')=='External':
            relations[rid]=None
        else:
            normalized=posixpath.normpath(target.lstrip('/') if target.startswith('/') else posixpath.join('xl',target))
            if normalized.startswith('../') or normalized.startswith('/'):
                raise ValueError('Worksheet target escapes archive')
            relations[rid]=normalized
    result=[]
    for s in workbook.findall('m:sheets/m:sheet',NS):
        rid=s.attrib.get('{'+RID_NS+'}id')
        if rid not in relations or relations[rid] is None:raise ValueError('Worksheet has no internal relationship')
        result.append(dict(sheet=s.attrib['name'],sheet_id=s.attrib.get('sheetId'),relationship_id=rid,
                           xml_path=relations[rid],sheet_state=s.attrib.get('state','visible')))
    if len({x['sheet'] for x in result})!=len(result):raise ValueError('Duplicate worksheet names')
    return result


def read_worksheet(archive,mapping,filename,workbook_hash):
    shared=[]
    if 'xl/sharedStrings.xml' in archive.namelist():
        for si in ET.fromstring(archive.read('xl/sharedStrings.xml')).findall('m:si',NS):
            shared.append(dict(text=rich_text(si),parsed_xml=ET.tostring(si,encoding='unicode')))
    raw=archive.read(mapping['xml_path'])
    root=ET.fromstring(raw)
    raw_cells=iter(exact_xml_cells(raw))
    rows=[]
    for ordinal,row in enumerate(root.findall('m:sheetData/m:row',NS)):
        rownum=int(row.attrib['r'])
        cells={}
        for c in row.findall('m:c',NS):
            raw_xml=next(raw_cells)
            address=c.attrib['r']
            match=re.fullmatch(r'([A-Z]+)([1-9][0-9]*)',address)
            if not match or int(match.group(2))!=rownum:raise ValueError('Worksheet row/cell address mismatch')
            col=match.group(1)
            if col in cells:raise ValueError('Duplicate XML cell address; no preferred value')
            t=c.attrib.get('t');v=c.find('m:v',NS);formula=c.find('m:f',NS)
            storage=v.text if v is not None else None
            resolved=storage;shared_index=None;shared_xml=None
            if t=='s':
                if storage is None or not re.fullmatch(r'[0-9]+',storage):raise ValueError('Invalid shared-string index')
                shared_index=int(storage)
                if shared_index>=len(shared):raise ValueError('Shared-string index out of bounds')
                resolved=shared[shared_index]['text'];shared_xml=shared[shared_index]['parsed_xml']
            elif t=='inlineStr':
                inline=c.find('m:is',NS);resolved=rich_text(inline) if inline is not None else None
            if formula is not None:status='formula_unresolved'
            elif t=='e':status='xml_error'
            elif resolved is None or resolved=='':status='present_empty'
            elif resolved=='NaN':status='literal_NaN'
            else:status='present'
            cells[col]=dict(workbook_sha256=workbook_hash,workbook_file=filename,sheet=mapping['sheet'],
                xml_sheet_path=mapping['xml_path'],excel_row=rownum,row_xml_ordinal=ordinal,
                excel_column=col,excel_cell=address,xml_cell_type=t,raw_storage_token=storage,
                resolved_text=resolved,raw_xml_cell=raw_xml,shared_string_index=shared_index,
                shared_string_parsed_xml=shared_xml,formula_text=formula.text if formula is not None else None,
                field_status=status,parser_rule=PARSER_VERSION)
        rows.append(dict(excel_row=rownum,row_xml_ordinal=ordinal,cells=cells))
    try:next(raw_cells);raise ValueError('Unmatched worksheet cell outside recognized data rows')
    except StopIteration:pass
    if len({r['excel_row'] for r in rows})!=len(rows):raise ValueError('Duplicate source Excel row numbers')
    return rows,dict(xml_sha256=sha_bytes(raw),xml_bytes=len(raw))


def absent_field(meta,row,col):
    return dict(workbook_sha256=meta['workbook_sha256'],workbook_file=meta['file'],sheet=meta['sheet'],
        xml_sheet_path=meta['xml_path'],excel_row=row['excel_row'],row_xml_ordinal=row['row_xml_ordinal'],
        excel_column=col,excel_cell=f'{col}{row["excel_row"]}',xml_cell_type=None,raw_storage_token=None,
        resolved_text=None,raw_xml_cell=None,shared_string_index=None,shared_string_parsed_xml=None,
        formula_text=None,field_status='absent_xml_cell',parser_rule=PARSER_VERSION)


def numeric(field):
    if field['field_status']!='present':return None,field['field_status']
    text=field['resolved_text']
    try:d=Decimal(text)
    except (InvalidOperation,TypeError):return None,'invalid_numeric'
    if not d.is_finite():return None,'nonfinite_numeric'
    try:value=float(d)
    except (OverflowError,ValueError):return None,'nonfinite_float_representation'
    if not math.isfinite(value):return None,'nonfinite_float_representation'
    return value,'finite_numeric'


def identifier(field):
    if field['field_status']!='present':return None,field['field_status']
    text=field['resolved_text']
    if not isinstance(text,str) or not text.strip():return None,'empty_or_whitespace_identity'
    try:
        if not Decimal(text).is_finite():return None,'nonfinite_identity'
    except InvalidOperation:pass
    return text,'present_exact_text'


def source_fields(meta,row,side):
    fields={}
    for col,header in meta['columns'].items():
        f=dict(row['cells'].get(col,absent_field(meta,row,col)))
        match=re.search(r'sibling\s+([12])',header,re.I)
        f['source_header']=header;f['sibling_side']=int(match.group(1)) if match else side
        fields[header.strip()]=f
    if len(fields)!=len(meta['columns']):raise ValueError('Stripped header names collide')
    return fields


def event_annotation(fields,side):
    birth,birth_status=numeric(fields['Birth time'])
    durations={}
    for fate,name in [('division','cycle length'),('death','time to death'),('loss','time to cell loss')]:
        value,status=numeric(fields[f'Sibling {side} {name}'])
        durations[fate]=dict(value=value,status=status)
    finite=[k for k,v in durations.items() if v['status']=='finite_numeric']
    bad=[k for k,v in durations.items() if v['status'] not in ('finite_numeric','literal_NaN','absent_xml_cell','present_empty')]
    negative=[k for k in finite if durations[k]['value']<0]
    issues=[]
    if birth is None:issues.append('invalid_or_missing_birth')
    if birth is not None and birth<0:issues.append('negative_absolute_birth_origin_unresolved')
    if not finite:issues.append('no_finite_fate')
    if len(finite)>1:issues.append('multiple_finite_fates')
    if bad:issues.append('invalid_fate_annotation')
    if negative:issues.append('negative_fate_duration')
    usable=len(finite)==1 and not bad and not negative
    fate=finite[0] if usable else None
    terminal=birth+durations[fate]['value'] if fate is not None and birth is not None else None
    if terminal is not None and not math.isfinite(terminal):
        terminal=None;issues.append('nonfinite_derived_terminal_time')
    if usable and durations[fate]['value']==0:issues.append('zero_duration_event_boundary_unresolved')
    return dict(birth_value=birth,birth_status=birth_status,duration_fields=durations,
                usable_nonnegative_fate=fate,candidate_terminal_time=terminal,
                terminal_state='candidate_'+fate if fate and terminal is not None else 'unresolved',
                continuous_tracking_support='unresolved',recording_end=None,event_boundary_convention='unresolved',
                death_is_absorbing_mask=False),issues


def connected_groups(nodes,edges,kind):
    adjacency={n:set() for n in nodes}
    for a,b in edges:
        adjacency[a].add(b);adjacency[b].add(a)
    seen=set();groups=[]
    for initial in sorted(nodes):
        if initial in seen:continue
        todo=[initial];seen.add(initial);group=[]
        while todo:
            current=todo.pop();group.append(current)
            for neighbor in sorted(adjacency[current]):
                if neighbor not in seen:seen.add(neighbor);todo.append(neighbor)
        members=sorted(group)
        groups.append(dict(group_id=key(kind,CONTRACT['version'],members),observation_ids=members,
                           interpretation='retained_record_structure_not_original_founder_or_independence'))
    return groups


def cyclic_edges(nodes,edges):
    """Iterative Kosaraju avoids recursion limits on long synthetic ancestry."""
    adj={n:[] for n in nodes};rev={n:[] for n in nodes}
    for a,b in edges:adj[a].append(b);rev[b].append(a)
    order=[];seen=set()
    for start in sorted(nodes):
        if start in seen:continue
        stack=[(start,False)]
        while stack:
            node,finish=stack.pop()
            if finish:order.append(node);continue
            if node in seen:continue
            seen.add(node);stack.append((node,True))
            for nxt in adj[node]:
                if nxt not in seen:stack.append((nxt,False))
    component={};sizes=[]
    for start in reversed(order):
        if start in component:continue
        number=len(sizes);todo=[start];component[start]=number;count=0
        while todo:
            node=todo.pop();count+=1
            for nxt in rev[node]:
                if nxt not in component:component[nxt]=number;todo.append(nxt)
        sizes.append(count)
    return {(a,b) for a,b in edges if component[a]==component[b] and (sizes[component[a]]>1 or a==b)}

def build_sheet(meta,rows):
    """Construct only record assertions and graph structure, never outcomes."""
    namespace=[meta['workbook_sha256'],meta['sheet']]
    pairs=[];observations=[];entities=defaultdict(list);mothers=defaultdict(list)
    issues=[];issue_keys=set();pairs_by_id={};obs_by_id={}
    def issue(code,obs=(),pair=(),edge=(),detail=None):
        payload=dict(code=code,observation_ids=sorted(set(obs)),pair_ids=sorted(set(pair)),
                     edge_ids=sorted(set(edge)),detail=detail or {})
        identifier_key=key('issue',namespace,payload)
        if identifier_key not in issue_keys:
            issues.append(dict(issue_id=identifier_key,**payload));issue_keys.add(identifier_key)
    for row in rows:
        pair_id=key('pair',*namespace,row['excel_row'])
        if pair_id in pairs_by_id:raise ValueError('Duplicate source row provenance')
        fields=source_fields(meta,row,None)
        label,label_status=identifier(fields['Lineage ID'])
        mother,mother_status=identifier(fields['Mother ID'])
        grandmother,gm_status=identifier(fields['Grandmother ID'])
        generation,generation_status=numeric(fields['Generation'])
        if generation is not None and (generation<0 or generation!=math.floor(generation)):
            generation_status='invalid_generation';generation=None
        pair=dict(pair_id=pair_id,workbook_sha256=meta['workbook_sha256'],sheet=meta['sheet'],
            excel_row=row['excel_row'],fields=fields,source_lineage_label=label,lineage_status=label_status,
            mother_token=mother,mother_status=mother_status,grandmother_token=grandmother,
            grandmother_status=gm_status,generation=generation,generation_status=generation_status,
            observation_ids=[],unmapped_xml_fields={c:v for c,v in row['cells'].items() if c not in meta['columns']})
        pairs.append(pair);pairs_by_id[pair_id]=pair
        if mother is not None:mothers[mother].append(pair_id)
        for side in (1,2):
            obs_id=key('observation',*namespace,row['excel_row'],side)
            cell_id,id_status=identifier(fields[f'Sibling {side} ID'])
            event,event_issues=event_annotation(fields,side)
            obs=dict(observation_id=obs_id,pair_id=pair_id,sibling_side=side,cell_token=cell_id,
                cell_identity_status=id_status,entity_id=key('entity',*namespace,cell_id) if cell_id is not None else None,
                source_field_reference=dict(pair_id=pair_id,id_header=f'Sibling {side} ID',birth_header='Birth time',
                    duration_headers={name:f'Sibling {side} {suffix}' for name,suffix in
                                      [('division','cycle length'),('death','time to death'),('loss','time to cell loss')]}),
                event_annotation=event,source_ascertainment='unresolved_export_selection',
                observed_episode=True,original_founder_status='not_identified')
            observations.append(obs);obs_by_id[obs_id]=obs;pair['observation_ids'].append(obs_id)
            if cell_id is not None:entities[cell_id].append(obs_id)
            else:issue('missing_or_invalid_child_identity',obs=[obs_id],pair=[pair_id],detail={'status':id_status})
            if cell_id is not None and cell_id==mother:
                issue('self_parent_reference_assertion',obs=[obs_id],pair=[pair_id])
            for code in event_issues:issue(code,obs=[obs_id],pair=[pair_id])
            if generation_status!='finite_numeric':issue('unavailable_generation_annotation',obs=[obs_id],pair=[pair_id],detail={'status':generation_status})
        left,right=[obs_by_id[x] for x in pair['observation_ids']]
        if left['cell_token'] is not None and left['cell_token']==right['cell_token']:
            issue('same_child_identity_both_siblings',obs=pair['observation_ids'],pair=[pair_id])
        if mother is None:issue('missing_or_invalid_mother_reference',obs=pair['observation_ids'],pair=[pair_id],detail={'status':mother_status})
    for token,ids in sorted(entities.items()):
        if len(ids)>1:issue('duplicate_recorded_child_identity',obs=ids,pair=[obs_by_id[i]['pair_id'] for i in ids],detail={'entity_id':key('entity',*namespace,token)})
    for token,pids in sorted(mothers.items()):
        if len(pids)>1:
            children=[o for pid in pids for o in pairs_by_id[pid]['observation_ids']]
            issue('multiple_successor_pair_assertions',obs=children+entities.get(token,[]),pair=pids)
    # Lexical numeric aliases are diagnostics only, never identity joins.
    token_users=defaultdict(set)
    for obs in observations:
        pair=pairs_by_id[obs['pair_id']]
        for token in (obs['cell_token'],pair['mother_token'],pair['grandmother_token']):
            if token is not None:token_users[token].add(obs['observation_id'])
    numeric_groups=defaultdict(list)
    for token in token_users:
        try:value=Decimal(token)
        except InvalidOperation:continue
        if value.is_finite():numeric_groups[value].append(token)
    aliases=[]
    for tokens in numeric_groups.values():
        if len(tokens)>1:
            members=sorted(set().union(*(token_users[x] for x in tokens)))
            aliases.append(dict(tokens=sorted(tokens),observation_ids=members,merged=False))
            issue('numeric_equivalent_lexical_id_alias',obs=members,detail={'tokens':sorted(tokens),'merged':False})
    aliases.sort(key=lambda x:x['tokens'])
    edges=[];raw=[];edge_for_obs={}
    for obs in observations:
        oid=obs['observation_id'];pair=pairs_by_id[obs['pair_id']];token=pair['mother_token']
        parent_ids=entities.get(token,[]) if token is not None else []
        own_ids=entities.get(obs['cell_token'],[]) if obs['cell_token'] is not None else []
        unique=len(parent_ids)==1 and len(own_ids)==1
        if token is None:parent_kind='missing_reference'
        elif not parent_ids:parent_kind='external_reference'
        elif len(parent_ids)>1:parent_kind='ambiguous_recorded_reference'
        else:parent_kind='unique_recorded_reference'
        edge=dict(edge_id=key('mother_assertion',oid),child_observation_id=oid,
            parent_token=token,parent_reference_kind=parent_kind,candidate_parent_observation_ids=list(parent_ids),
            parent_observation_id=parent_ids[0] if len(parent_ids)==1 else None,
            raw_unique_identity_join=unique,consistent_recorded_parent_edge=False,checks={},blocking_reasons=[])
        if unique:raw.append((parent_ids[0],oid))
        edges.append(edge);edge_for_obs[oid]=edge
    cycles=cyclic_edges(obs_by_id,raw)
    tol=CONTRACT['time_residual_tolerance']
    repeated=[]
    def repeat_check(child,parent,kind,source_header,recorded_field):
        pair=pairs_by_id[child['pair_id']]
        supplied,supplied_status=numeric(pair['fields'][source_header])
        actual=recorded_field
        record=dict(child_observation_id=child['observation_id'],reference_observation_id=parent['observation_id'] if parent else None,
                    kind=kind,source_pair_id=pair['pair_id'],source_header=source_header,
                    supplied_value=supplied,supplied_status=supplied_status,recorded_value=actual,
                    residual_in_source_time_units=None,status='unavailable')
        if supplied is not None and actual is not None:
            residual=supplied-actual
            if math.isfinite(residual):
                record['residual_in_source_time_units']=residual
                record['status']='consistent' if abs(residual)<=tol else 'mismatch'
            else:
                record['status']='nonfinite_derived_residual'
                issue('nonfinite_repeated_'+kind+'_residual',obs=[child['observation_id']],pair=[pair['pair_id']])
            if record['status']=='mismatch':issue('repeated_'+kind+'_mismatch',obs=[child['observation_id']],pair=[pair['pair_id']],detail={'residual_in_source_time_units':residual})
        if supplied is not None and supplied<0:issue('negative_'+kind+'_annotation',obs=[child['observation_id']],pair=[pair['pair_id']])
        repeated.append(record)
    for edge in edges:
        oid=edge['child_observation_id'];child=obs_by_id[oid];pair=pairs_by_id[child['pair_id']]
        parent=obs_by_id.get(edge['parent_observation_id']);checks=edge['checks'];blocks=edge['blocking_reasons']
        checks['identity']='unique' if edge['raw_unique_identity_join'] else edge['parent_reference_kind']+'_or_ambiguous_child'
        if not edge['raw_unique_identity_join']:blocks.append('nonunique_or_external_identity')
        checks['successor_pair_uniqueness']='unique' if pair['mother_token'] is not None and len(mothers[pair['mother_token']])==1 else 'missing_or_multiple'
        if checks['successor_pair_uniqueness']!='unique':blocks.append('nonunique_successor_pair_assertion')
        checks['cycle']='cyclic_edge' if parent and (parent['observation_id'],oid) in cycles else 'not_in_raw_directed_cycle'
        if checks['cycle']=='cyclic_edge':
            blocks.append('self_or_directed_cycle');issue('self_parent' if parent['observation_id']==oid else 'directed_cycle_edge',obs=[oid,parent['observation_id']],edge=[edge['edge_id']])
        checks['parent_division']='unavailable'
        checks['parent_child_time']=dict(status='unavailable',residual_in_source_time_units=None)
        checks['lineage']='unavailable';checks['generation']='unavailable';checks['grandmother_reference']='unavailable'
        if parent is not None:
            pp=pairs_by_id[parent['pair_id']];pe=parent['event_annotation'];ce=child['event_annotation']
            usable=pe['usable_nonnegative_fate']=='division' and pe['candidate_terminal_time'] is not None
            checks['parent_division']='usable_division' if usable else 'not_one_usable_division'
            if not usable:
                blocks.append('parent_without_usable_division');issue('parent_without_usable_division',obs=[oid,parent['observation_id']],edge=[edge['edge_id']])
            if pe['usable_nonnegative_fate']=='death':issue('death_with_descendant_assertion',obs=[parent['observation_id'],oid],edge=[edge['edge_id']])
            if pe['usable_nonnegative_fate']=='loss':issue('loss_with_later_ancestry_assertion_support_unresolved',obs=[parent['observation_id'],oid],edge=[edge['edge_id']])
            if usable and ce['birth_value'] is not None:
                residual=ce['birth_value']-pe['candidate_terminal_time']
                if math.isfinite(residual):
                    checks['parent_child_time']=dict(status='consistent' if abs(residual)<=tol else 'mismatch',residual_in_source_time_units=residual)
                    if abs(residual)>tol:issue('parent_child_time_mismatch',obs=[oid,parent['observation_id']],edge=[edge['edge_id']],detail={'residual_in_source_time_units':residual})
                else:
                    checks['parent_child_time']=dict(status='nonfinite_derived_residual',residual_in_source_time_units=None)
                    issue('nonfinite_parent_child_time_residual',obs=[oid,parent['observation_id']],edge=[edge['edge_id']])
            if checks['parent_child_time']['status']!='consistent':blocks.append('unresolved_or_conflicting_parent_child_time')
            for name,left,right in [('lineage',pair['source_lineage_label'],pp['source_lineage_label']),
                                   ('grandmother_reference',pair['grandmother_token'],pp['mother_token'])]:
                if left is not None and right is not None:
                    checks[name]='consistent' if left==right else 'mismatch'
                    if left!=right:
                        blocks.append(name+'_conflict');issue(name+'_conflict',obs=[oid,parent['observation_id']],edge=[edge['edge_id']])
            if pair['generation'] is not None and pp['generation'] is not None:
                checks['generation']='consistent' if pair['generation']==pp['generation']+1 else 'mismatch'
                if checks['generation']=='mismatch':
                    blocks.append('generation_conflict');issue('generation_conflict',obs=[oid,parent['observation_id']],edge=[edge['edge_id']])
            repeat_check(child,parent,'mother_cycle','Mother cycle length',pe['duration_fields']['division']['value'])
            # The child's grandmother-cycle field may also be repeated in the
            # recorded mother's mother-cycle field. Preserve both assertions.
            mother_repeat,_=numeric(pp['fields']['Mother cycle length'])
            repeat_check(child,parent,'grandmother_cycle_vs_mother_annotation','Grandmother cycle length',mother_repeat)
        else:
            blocks.append('parent_without_usable_division');blocks.append('unresolved_or_conflicting_parent_child_time')
            repeat_check(child,None,'mother_cycle','Mother cycle length',None)
            repeat_check(child,None,'grandmother_cycle_vs_mother_annotation','Grandmother cycle length',None)
            if edge['parent_reference_kind']=='external_reference' and pair['generation'] is not None and pair['generation']!=2:
                issue('external_parent_after_generation_2',obs=[oid],edge=[edge['edge_id']])
        gm_ids=entities.get(pair['grandmother_token'],[]) if pair['grandmother_token'] is not None else []
        gm=obs_by_id[gm_ids[0]] if len(gm_ids)==1 else None
        repeat_check(child,gm,'grandmother_cycle','Grandmother cycle length',gm['event_annotation']['duration_fields']['division']['value'] if gm else None)
        edge['consistent_recorded_parent_edge']=not blocks
    # Every recorded division keeps its successor ambiguity; no unknown branch
    # is relabeled death, reduced to one daughter or assigned a fabricated ID.
    for obs in observations:
        token=obs['cell_token'];successors=mothers.get(token,[]) if token is not None else []
        if obs['event_annotation']['usable_nonnegative_fate']=='division':
            if not successors:
                state='missing_successor_pair_unknown_descendants'
                issue('division_without_successor_pair',obs=[obs['observation_id']],pair=[obs['pair_id']])
            elif len(successors)>1:state='multiple_successor_pair_assertions_unresolved'
            else:
                children=pairs_by_id[successors[0]]['observation_ids']
                state=('unique_consistent_successor_pair' if all(edge_for_obs[c]['consistent_recorded_parent_edge']
                      and edge_for_obs[c]['parent_observation_id']==obs['observation_id'] for c in children)
                       else 'successor_pair_assertions_unresolved')
            obs['successor_state']=dict(status=state,asserted_pair_ids=successors,
                unknown_descendant_cardinality=None,
                missing_successor_record_assertion_count=0 if state=='unique_consistent_successor_pair' else None,
                recorded_child_observation_count=sum(len(pairs_by_id[p]['observation_ids']) for p in successors),
                binary_offspring_assumption=False)
        else:
            obs['successor_state']=dict(status='not_one_usable_division',asserted_pair_ids=successors,
                unknown_descendant_cardinality=None,missing_successor_record_assertion_count=None,
                recorded_child_observation_count=sum(len(pairs_by_id[p]['observation_ids']) for p in successors),binary_offspring_assumption=False)
    consistent=[(e['parent_observation_id'],e['child_observation_id']) for e in edges if e['consistent_recorded_parent_edge']]
    if cyclic_edges(obs_by_id,consistent):raise AssertionError('Consistent-edge subset must be acyclic')
    external_users=defaultdict(set);external_roles=defaultdict(set);lineage_users=defaultdict(set)
    for obs in observations:
        oid=obs['observation_id'];pair=pairs_by_id[obs['pair_id']]
        for role,token in [('mother',pair['mother_token']),('grandmother',pair['grandmother_token'])]:
            if token is not None and token not in entities:
                external_users[token].add(oid);external_roles[token].add(role)
        if pair['source_lineage_label'] is not None:lineage_users[pair['source_lineage_label']].add(oid)
    related_edges=list(raw)
    for members in [*token_users.values(),*lineage_users.values()]:
        ordered=sorted(members)
        related_edges.extend((ordered[0],other) for other in ordered[1:])
    raw_groups=connected_groups(obs_by_id,raw,'raw_component')
    cycle_groups=connected_groups({n for edge in cycles for n in edge},sorted(cycles),'cyclic_strong_component')
    consistent_groups=connected_groups(obs_by_id,consistent,'consistent_component')
    related_groups=connected_groups(obs_by_id,related_edges,'conservative_related_group')
    issues_by_obs=defaultdict(set)
    for i in issues:
        for oid in i['observation_ids']:issues_by_obs[oid].add(i['code'])
    for groups in (raw_groups,consistent_groups,related_groups):
        for group in groups:
            group['issue_codes']=sorted(set().union(*(issues_by_obs.get(oid,set()) for oid in group['observation_ids'])))
    external=[dict(reference_id=key('external_reference',*namespace,token),token=token,
                   roles=sorted(external_roles[token]),referenced_by_observation_ids=sorted(ids),observed_episode=False,
                   birth=None,terminal_event=None,original_founder_status='not_identified')
              for token,ids in sorted(external_users.items())]
    summary=dict(file=meta['file'],sheet=meta['sheet'],workbook_sha256=meta['workbook_sha256'],
        pair_rows=len(pairs),observations=len(observations),unique_nonmissing_cell_tokens=len(entities),
        uniquely_recorded_entities=sum(len(v)==1 for v in entities.values()),
        duplicate_identity_entities=sum(len(v)>1 for v in entities.values()),
        observations_missing_usable_identity=sum(o['cell_token'] is None for o in observations),
        lexical_numeric_alias_groups=len(aliases),source_lineage_label_groups=len(lineage_users),
        mother_assertions=len(edges),raw_unique_recorded_edges=len(raw),consistent_recorded_edges=len(consistent),
        cyclic_raw_edges=len(cycles),self_raw_edges=sum(a==b for a,b in raw),
        cyclic_raw_scc_count=len(cycle_groups),cyclic_scc_size_histogram=dict(sorted(Counter(len(g['observation_ids']) for g in cycle_groups).items())),
        external_reference_entities=len(external),external_mother_assertions=sum(e['parent_reference_kind']=='external_reference' for e in edges),
        edge_parent_reference_kinds=dict(Counter(e['parent_reference_kind'] for e in edges)),
        consistent_edge_blocking_reasons=dict(Counter(reason for e in edges for reason in set(e['blocking_reasons']))),
        edge_check_status_counts={name:dict(Counter((e['checks'][name]['status'] if isinstance(e['checks'][name],dict) else e['checks'][name]) for e in edges)) for name in edges[0]['checks']} if edges else {},
        maximum_absolute_parent_child_residual_source_units=max((abs(e['checks']['parent_child_time']['residual_in_source_time_units']) for e in edges if e['checks']['parent_child_time']['residual_in_source_time_units'] is not None),default=None),
        fate_annotation_states=dict(Counter(o['event_annotation']['terminal_state'] for o in observations)),
        usable_fate_labels=dict(Counter(o['event_annotation']['usable_nonnegative_fate'] or 'unresolved' for o in observations)),
        successor_states=dict(Counter(o['successor_state']['status'] for o in observations)),
        issue_record_counts=dict(Counter(i['code'] for i in issues)),
        affected_observation_counts={code:sum(code in codes for codes in issues_by_obs.values()) for code in sorted({i['code'] for i in issues})},
        repeated_cycle_check_statuses={kind:dict(Counter(r['status'] for r in repeated if r['kind']==kind)) for kind in ('mother_cycle','grandmother_cycle_vs_mother_annotation','grandmother_cycle')},
        group_counts=dict(raw_recorded_components=len(raw_groups),consistent_recorded_components=len(consistent_groups),conservative_related_groups=len(related_groups)),
        group_size_histograms={name:dict(sorted(Counter(len(g['observation_ids']) for g in groups).items())) for name,groups in [('raw',raw_groups),('consistent',consistent_groups),('related',related_groups)]},
        groups_with_no_recorded_issue={name:sum(not g['issue_codes'] for g in groups) for name,groups in [('raw',raw_groups),('consistent',consistent_groups),('related',related_groups)]},
        raw_root_observations=len(observations)-len({b for a,b in raw}),consistent_root_observations=len(observations)-len({b for a,b in consistent}),
        source_units='numeric_source_time_units_hour_interpretation_from_separate_dictionary',
        no_outcome_grid=True,no_original_founder_assignment=True,no_continuous_observation_mask=True)
    private=dict(namespace=dict(workbook_sha256=meta['workbook_sha256'],sheet=meta['sheet']),
        pair_records=pairs,recorded_observations=observations,
        recorded_entities=[dict(entity_id=key('entity',*namespace,token),token=token,observation_ids=ids,identity_status='unique' if len(ids)==1 else 'ambiguous_multiple_observations') for token,ids in sorted(entities.items())],
        external_references=external,mother_assertion_edges=edges,numeric_alias_groups=aliases,
        repeated_cycle_checks=repeated,issues=issues,raw_recorded_components=raw_groups,
        cyclic_strong_components=cycle_groups,
        consistent_recorded_components=consistent_groups,conservative_related_groups=related_groups,
        source_lineage_label_groups=[dict(label=label,observation_ids=sorted(ids)) for label,ids in sorted(lineage_users.items())])
    return private,summary

def validate_plan(path,expected_hash):
    if not expected_hash or sha(path)!=expected_hash:raise ValueError('Protocol SHA does not match explicit frozen hash')
    plan=json.loads(Path(path).read_text())
    if not str(plan.get('status','')).startswith('FROZEN'):raise ValueError('Protocol is not frozen')
    if plan.get('implementation_contract')!=CONTRACT:raise ValueError('Frozen protocol contract differs from code')
    return plan


def run_graph(plan_path,expected_plan_hash,source_dir,schema_path,private_dir,public_out):
    plan=validate_plan(plan_path,expected_plan_hash)
    source_dir,schema_path,private_dir,public_out=map(Path,(source_dir,schema_path,private_dir,public_out))
    required_prefix=(ROOT/plan['publication']['private_output_prefix']).resolve()
    if not private_dir.resolve().is_relative_to(required_prefix):raise ValueError('Per-cell graph output must remain under excluded derived-source prefix')
    if private_dir.exists() or public_out.exists():raise FileExistsError('Use fresh graph output paths; first outputs are immutable')
    if public_out.resolve().is_relative_to(private_dir.resolve()):raise ValueError('Public aggregate path must be separate from private graph output')
    inputs={str(schema_path):CONTRACT['schema_sha256'],str(plan_path):expected_plan_hash}
    inputs.update({str(source_dir/name):digest for name,digest in CONTRACT['workbook_sha256'].items()})
    inputs.update({str(ROOT/name):digest for name,digest in plan.get('source_evidence',{}).items()})
    if any(sha(Path(path))!=digest for path,digest in inputs.items()):raise ValueError('Pinned input/source-evidence hash mismatch')
    schemas=json.loads(schema_path.read_text())
    roster=[dict(file=m['file'],sheet=m['sheet'],xml_path=m['xml_path'],expected_pair_rows=m['data_rows']) for m in schemas]
    if roster!=plan['source_inputs']['sheet_roster']:raise ValueError('Frozen schema/roster mismatch')
    private_dir.mkdir(parents=True,exist_ok=False)
    summaries=[];artifacts=[];read_checks=[]
    try:
        for filename in CONTRACT['workbook_sha256']:
            with zipfile.ZipFile(source_dir/filename) as archive:
                mappings=workbook_mapping(archive)
                expected=[m for m in schemas if m['file']==filename]
                if [(m['sheet'],m['xml_path']) for m in mappings]!=[(m['sheet'],m['xml_path']) for m in expected]:
                    raise ValueError('Actual workbook sheet/relationship mapping differs from schema')
                for mapping,meta0 in zip(mappings,expected):
                    meta={**meta0,'workbook_sha256':CONTRACT['workbook_sha256'][filename]}
                    rows,xml_info=read_worksheet(archive,mapping,filename,meta['workbook_sha256'])
                    if not rows:raise ValueError('Missing source header row')
                    header=rows[0]['cells']
                    actual_headers={c:f['resolved_text'] for c,f in header.items() if f['field_status']=='present'}
                    if actual_headers!=meta['columns']:raise ValueError('Exact source headers differ from saved schema')
                    if len(rows)-1!=meta['data_rows']:raise ValueError('Source pair row count differs from frozen schema')
                    graph,summary=build_sheet(meta,rows[1:])
                    ordinal=len(summaries)
                    out=private_dir/f'sheet-{ordinal:02d}.json'
                    payload=dict(status='ASSERTION_GRAPH_NOT_ANALYSIS_READY',created_utc=utc(),
                        protocol_sha256=expected_plan_hash,code_sha256=sha(__file__),schema_sha256=CONTRACT['schema_sha256'],
                        workbook_mapping=mapping,worksheet_provenance=xml_info,summary=summary,graph=graph)
                    write_new(out,payload)
                    artifacts.append(dict(file=filename,sheet=meta['sheet'],private_relative_file=out.name,sha256=sha(out)))
                    summaries.append(summary)
                    read_checks.append(dict(file=filename,sheet=meta['sheet'],xml_path=mapping['xml_path'],
                        header_excel_row=rows[0]['excel_row'],pair_rows=len(rows)-1,**xml_info))
        if any(sha(Path(path))!=digest for path,digest in inputs.items()):raise ValueError('Pinned source changed during read')
        if len(summaries)!=7 or sum(x['pair_rows'] for x in summaries)!=4678 or sum(x['observations'] for x in summaries)!=9356:
            raise ValueError('Frozen complete source roster did not reconcile')
        result=dict(status='STRUCTURAL_GRAPH_ONLY_NOT_ANALYSIS_READY',created_utc=utc(),
            protocol_sha256=expected_plan_hash,code_sha256=sha(__file__),schema_sha256=CONTRACT['schema_sha256'],
            input_workbook_sha256=CONTRACT['workbook_sha256'],implementation_contract=CONTRACT,
            source_preservation='All pinned source/schema/evidence hashes verified before and after; originals unchanged.',
            sheets=len(summaries),pair_rows=sum(x['pair_rows'] for x in summaries),observations=sum(x['observations'] for x in summaries),
            summaries=summaries,read_checks=read_checks,private_artifacts=artifacts,
            per_cell_output_public=False,outcome_calculations=False,
            interpretation='Recorded components and conservative related groups are not original founders or proof of independence; no continuous observation or outcome masks assigned.')
        write_new(public_out,result)
        return dict(status=result['status'],sheets=7,pair_rows=4678,observations=9356,
                    public_report_sha256=sha(public_out),private_artifact_count=len(artifacts))
    except Exception as exc:
        # Detailed source-bearing failures stay excluded. The public failure
        # reports provenance and completion, never raw records or exception text.
        private_failure=dict(status='INCOMPLETE',created_utc=utc(),protocol_sha256=expected_plan_hash,
            code_sha256=sha(__file__),completed_sheet_summaries=summaries,private_artifacts=artifacts,
            error_class=type(exc).__name__,error=str(exc))
        write_new(private_dir/'failure.json',private_failure)
        if not public_out.exists():write_new(public_out,dict(status='INCOMPLETE_STRUCTURAL_GRAPH',created_utc=utc(),
            protocol_sha256=expected_plan_hash,code_sha256=sha(__file__),completed_sheets=len(summaries),
            private_failure_sha256=sha(private_dir/'failure.json'),error_class=type(exc).__name__,outcome_calculations=False))
        raise


FIXTURE_COLUMNS=dict(zip('ABCDEFGHIJKLMNOPQRS',[
 'Lineage ID','Sibling 1 cycle length','Sibling 1 time to death','Sibling 1 time to cell loss ',
 'Sibling 2 cycle length','Sibling 2 time to death','Sibling 2 time to cell loss','Birth time ',
 'Sibling 1 ID','Sibling 2 ID ','Mother ID','Birth x position sibling 1','Birth y position sibling 1',
 'Birth x position sibling 2','Birth y position sibling 2','Generation','Mother cycle length',
 'Grandmother cycle length','Grandmother ID']))


def fixture_meta(sheet='synthetic',workbook_hash='a'*64):
    return dict(file='synthetic.xlsx',sheet=sheet,xml_path='xl/worksheets/custom.xml',
                workbook_sha256=workbook_hash,columns=FIXTURE_COLUMNS)


def fixture_row(number,ids=('A','B'),mother='M',birth='0',generation='2',lineage='L',grandmother='G',
                fate1=('division','1'),fate2=('death','2'),mother_cycle='NaN',grandmother_cycle='NaN',overrides=None):
    from xml.sax.saxutils import escape
    meta=fixture_meta()
    values={c:'NaN' for c in FIXTURE_COLUMNS}
    values.update(A=lineage,H=birth,I=ids[0],J=ids[1],K=mother,P=generation,Q=mother_cycle,R=grandmother_cycle,S=grandmother)
    for side,fate in ((1,fate1),(2,fate2)):
        if fate:
            col={1:{'division':'B','death':'C','loss':'D'},2:{'division':'E','death':'F','loss':'G'}}[side][fate[0]]
            values[col]=fate[1]
    values.update(overrides or {})
    row=dict(excel_row=number,row_xml_ordinal=number-1,cells={})
    for col,text in values.items():
        if text is None:continue
        field=absent_field(meta,row,col)
        formula=None
        if isinstance(text,tuple):text,formula=text
        field.update(xml_cell_type=None,raw_storage_token=text,resolved_text=text,
            raw_xml_cell=f'<c r="{col}{number}"><v>{escape(text)}</v></c>',
            field_status='formula_unresolved' if formula is not None else 'literal_NaN' if text=='NaN' else 'present_empty' if text=='' else 'present',
            formula_text=formula)
        row['cells'][col]=field
    return row


def fixtures():
    passed=[]
    def check(ok,name):
        if not ok:raise AssertionError(name)
        passed.append(name)
    def build(rows,meta=None):return build_sheet(meta or fixture_meta(),rows)
    base=fixture_row(2)
    child=fixture_row(3,ids=('C','D'),mother='A',birth='1',generation='3',grandmother='M',
                      fate1=('loss','3'),fate2=('loss','3'),mother_cycle='1')
    graph,s=build([base,child])
    check(s['observations']==4 and s['raw_unique_recorded_edges']==2 and s['consistent_recorded_edges']==2,'valid observed parent pair has two retained ancestry edges')
    check(s['group_counts']==dict(raw_recorded_components=2,consistent_recorded_components=2,conservative_related_groups=1),'external siblings remain separate recorded components but conservatively related')
    check(all(not x['observed_episode'] and x['birth'] is None for x in graph['external_references']),'external ancestor references never become observed episodes')
    check(s['groups_with_no_recorded_issue']['raw']==2 and not graph['issues'],'reading empty issue lists does not taint clean components')
    parent_a=next(o for o in graph['recorded_observations'] if o['cell_token']=='A')
    check(parent_a['successor_state']['missing_successor_record_assertion_count']==0
          and parent_a['successor_state']['unknown_descendant_cardinality'] is None,
          'complete recorded successor pair does not certify biological offspring cardinality')
    other,_=build([base,child],fixture_meta(sheet='second'))
    third,_=build([base,child],fixture_meta(workbook_hash='b'*64))
    ids={o['observation_id'] for o in graph['recorded_observations']}
    check(ids.isdisjoint(o['observation_id'] for o in other['recorded_observations']) and ids.isdisjoint(o['observation_id'] for o in third['recorded_observations']),'identical ID tokens across sheets or workbooks never join')
    dup=fixture_row(4,ids=('A','Z'),mother='OTHER',lineage='DIFFERENT',grandmother='GM2',fate1=('loss','2'),fate2=('loss','2'))
    dg,ds=build([base,child,dup])
    check(ds['observations']==6 and ds['duplicate_identity_entities']==1 and ds['raw_unique_recorded_edges']==0,'duplicate ID observations all retained without a preferred parent')
    check(ds['group_counts']['conservative_related_groups']==1,'ambiguous recorded identities and references cannot cross related-group splits')
    duplicate_successor=fixture_row(4,ids=('E','F'),mother='A',birth='1',generation='3',grandmother='M',fate1=('loss','1'),fate2=('loss','1'))
    _,dss=build([base,child,duplicate_successor])
    check(dss['raw_unique_recorded_edges']==4 and dss['consistent_recorded_edges']==0 and dss['issue_record_counts']['multiple_successor_pair_assertions']==1,'multiple successor pair assertions never select a convenient pair')
    cyc1=fixture_row(2,ids=('A','S1'),mother='B',birth='0',generation='2',grandmother='A',fate1=('division','1'),fate2=('loss','5'))
    cyc2=fixture_row(3,ids=('B','S2'),mother='A',birth='1',generation='3',grandmother='B',fate1=('division','1'),fate2=('loss','5'))
    cg,cs=build([cyc1,cyc2])
    check(cs['cyclic_raw_edges']==2 and cs['cyclic_raw_scc_count']==1 and cs['consistent_recorded_edges']==1,'raw SCC quarantine does not erase a valid downstream edge')
    _,ss=build([fixture_row(2,mother='A',fate1=('division','0'),grandmother='A')])
    check(ss['self_raw_edges']==1 and ss['issue_record_counts']['self_parent_reference_assertion']==1,'source self-parent assertion and raw self edge retained as conflict')
    conflict=fixture_row(3,ids=('C','D'),mother='A',birth='1',generation='8',lineage='X',grandmother='WRONG',fate1=('loss','1'),fate2=('loss','1'))
    _,co=build([base,conflict])
    check(co['consistent_recorded_edges']==0 and all(co['issue_record_counts'][k]==2 for k in ('generation_conflict','lineage_conflict','grandmother_reference_conflict')),'lineage generation and grandmother conflicts quarantine affected edges')
    repeat=fixture_row(3,ids=('C','D'),mother='A',birth='1',generation='3',grandmother='M',fate1=('loss','1'),fate2=('loss','1'),mother_cycle='9')
    _,repeated=build([base,repeat])
    check(repeated['consistent_recorded_edges']==2 and repeated['issue_record_counts']['repeated_mother_cycle_mismatch']==2,'repeated cycle mismatch recorded separately without replacing event or blocking valid birth link')
    missing,ms=build([base])
    div=next(o for o in missing['recorded_observations'] if o['cell_token']=='A')
    check(div['successor_state']['status']=='missing_successor_pair_unknown_descendants' and div['successor_state']['unknown_descendant_cardinality'] is None,'missing successor preserves unknown descendants and no assumed daughter count')
    _,mi=build([fixture_row(2,ids=(None,'B')),fixture_row(3,ids=(None,'D'),mother='N',lineage='OTHER',grandmother='GN')])
    check(mi['observations']==4 and mi['observations_missing_usable_identity']==2 and mi['unique_nonmissing_cell_tokens']==2,'missing identities get separate observation slots rather than a shared dummy cell')
    invalid_child=fixture_row(3,ids=('C','D'),mother='A',birth='1',generation='3',grandmother='M',fate1=('loss','-1'),fate2=('loss','3'))
    ig,iv=build([base,invalid_child])
    check(iv['consistent_recorded_edges']==2 and iv['issue_record_counts']['negative_fate_duration']==1,'invalid child terminal annotation alone does not erase its coherent birth edge')
    for label,overrides in [('multiple',{'C':'2'}),('nonfinite',{'C':'Inf'}),('formula',{'C':('NaN','1+1')})]:
        _,bad=build([fixture_row(2,overrides=overrides),child])
        check(bad['consistent_recorded_edges']==0 and bad['consistent_edge_blocking_reasons']['parent_without_usable_division']>=2,f'parent division exclusivity rejects {label} competing fate')
    missing_fate=fixture_row(2,fate1=None)
    _,mf=build([missing_fate])
    check(mf['issue_record_counts']['no_finite_fate']==1,'all missing fate fields remain unresolved')
    for fate in ('death','loss'):
        _,fs=build([fixture_row(2,fate1=(fate,'1')),child])
        code='death_with_descendant_assertion' if fate=='death' else 'loss_with_later_ancestry_assertion_support_unresolved'
        check(fs['consistent_recorded_edges']==0 and fs['issue_record_counts'][code]==2,f'{fate} with descendant assertion preserved without continuous-support repair')
    clean=fixture_row(4,ids=('X','Y'),mother='MX',lineage='LX',grandmother='GX',fate1=('loss','-1'),fate2=('death','2'))
    _,mixed=build([base,child,clean])
    check(mixed['groups_with_no_recorded_issue']['raw']==3 and mixed['group_counts']['raw_recorded_components']==4,'unrelated anomaly does not taint a clean component or sibling')
    unavail=fixture_row(3,ids=('C','D'),mother='A',birth='1',generation=None,lineage=None,grandmother=None,fate1=('loss','2'),fate2=('loss','2'))
    ug,us=build([base,unavail])
    relevant=[e for e in ug['mother_assertion_edges'] if e['raw_unique_identity_join']]
    check(us['consistent_recorded_edges']==2 and all(e['checks']['lineage']=='unavailable' and e['checks']['generation']=='unavailable' for e in relevant),'missing annotation check remains unavailable rather than a certified match')
    ag,aas=build([fixture_row(2,ids=('1','1.0'),fate1=('loss','2'),fate2=('loss','2'))])
    check(aas['unique_nonmissing_cell_tokens']==2 and aas['lexical_numeric_alias_groups']==1 and all(not a['merged'] for a in ag['numeric_alias_groups']),'numeric-equivalent lexical IDs are flagged without merging')
    _,large=build([fixture_row(2,ids=('9007199254740992','9007199254740993'),fate1=('loss','2'),fate2=('loss','2'))])
    check(large['unique_nonmissing_cell_tokens']==2 and large['lexical_numeric_alias_groups']==0,'large integer identifiers never pass through lossy float conversion')
    fid=fixture_row(2,overrides={'I':('A','CONCAT("A","")')})
    fg,ff=build([fid])
    check(ff['observations_missing_usable_identity']==1 and fg['pair_records'][0]['fields']['Sibling 1 ID']['raw_storage_token']=='A','formula identity cached token preserved but not used in joins')
    prov=graph['pair_records'][0]['fields']['Sibling 1 ID']
    check(prov['excel_cell']=='I2' and prov['raw_storage_token']=='A' and prov['sibling_side']==1 and prov['raw_xml_cell'].endswith('</c>'),'source field provenance resolves to original row column side and token')
    # ZIP/XML fixture exercises actual relationship resolution and storage types.
    xml=b'<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="7"><c r="A7" t="s"><v>0</v></c><c r="B7" t="inlineStr"><is><t xml:space="preserve"> 01 </t></is></c><c r="C7"><f>1+1</f><v>2</v></c><c r="D7" s="1" custom="x&gt;y"/><c r="E7"><v>9007199254740993</v></c></row></sheetData></worksheet>'
    raw=io.BytesIO()
    with zipfile.ZipFile(raw,'w') as z:
        z.writestr('xl/workbook.xml','<workbook xmlns="'+NS['m']+'" xmlns:r="'+RID_NS+'"><sheets><sheet name="actual" sheetId="9" r:id="rId9"/></sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels','<Relationships xmlns="'+REL_NS+'"><Relationship Id="rId9" Target="worksheets/unusual.xml" Type="worksheet"/></Relationships>')
        z.writestr('xl/sharedStrings.xml','<sst xmlns="'+NS['m']+'"><si><r><t>Na</t></r><r><t>N</t></r></si></sst>')
        z.writestr('xl/worksheets/unusual.xml',xml)
    with zipfile.ZipFile(io.BytesIO(raw.getvalue())) as z:
        mapping=workbook_mapping(z)[0];rows,info=read_worksheet(z,mapping,'fixture.xlsx','c'*64)
    f=rows[0]['cells']
    check(mapping['sheet']=='actual' and mapping['xml_path']=='xl/worksheets/unusual.xml' and rows[0]['excel_row']==7,'actual workbook relationship and original Excel row retained')
    check(f['A']['raw_storage_token']=='0' and f['A']['resolved_text']=='NaN' and f['A']['field_status']=='literal_NaN','shared-string index and missing marker separately preserved')
    check(f['B']['resolved_text']==' 01 ' and f['E']['resolved_text']=='9007199254740993','inline whitespace and large numeric XML token unmodified')
    check(f['C']['formula_text']=='1+1' and numeric(f['C'])[0] is None and identifier(f['C'])[0] is None,'XML formula never evaluated or trusted for numeric/identity evidence')
    check(f['D']['raw_xml_cell']=='<c r="D7" s="1" custom="x&gt;y"/>' and f['D']['field_status']=='present_empty','self-closing empty XML cell raw markup retained')
    check(len(exact_xml_cells(b'<r><c a="x>y"/><c><v>1</v></c></r>'))==2,'raw token extractor respects greater-than character inside quoted attributes')
    check(all(not o['event_annotation']['death_is_absorbing_mask'] and o['event_annotation']['event_boundary_convention']=='unresolved' for o in graph['recorded_observations']),'no synthetic half-open convention or absorbing mask imposed on source assertions')
    extreme_parent=fixture_row(2,birth='1e308',fate1=('division','0'))
    extreme_child=fixture_row(3,ids=('C','D'),mother='A',birth='-1e308',generation='3',grandmother='M',fate1=('loss','0'),fate2=('loss','0'))
    eg,es=build([extreme_parent,extreme_child])
    check(es['consistent_recorded_edges']==0 and es['edge_check_status_counts']['parent_child_time']['nonfinite_derived_residual']==2,
          'finite source inputs with overflowed time residual stay unresolved and serializable')
    extreme_parent=fixture_row(2,birth='0',fate1=('division','1e308'))
    extreme_child=fixture_row(3,ids=('C','D'),mother='A',birth='1e308',generation='3',grandmother='M',fate1=('loss','0'),fate2=('loss','0'),mother_cycle='-1e308')
    eg,es=build([extreme_parent,extreme_child])
    check(es['repeated_cycle_check_statuses']['mother_cycle']['nonfinite_derived_residual']==2
          and es['consistent_recorded_edges']==2,
          'overflowed repeated annotation residual is flagged separately from coherent birth links')
    json.dumps(eg,allow_nan=False)
    with tempfile.TemporaryDirectory(prefix='kuchen-graph-fixture-') as tmp:
        p=Path(tmp)/'graph.json';write_new(p,{'fixture':True});before=sha(p)
        try:write_new(p,{'replacement':True});raise AssertionError('output overwritten')
        except FileExistsError:check(sha(p)==before,'first graph artifact cannot be overwritten')
    return dict(status='PASS',created_utc=utc(),code_sha256=sha(__file__),count=len(passed),fixtures=passed,
                real_source_workbooks_parsed=False,source_graph_outputs_generated=False,outcome_calculations=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',action='store_true')
    p.add_argument('--protocol',type=Path,default=BASE/'graph-audit/protocol.json')
    p.add_argument('--expected-protocol-sha')
    p.add_argument('--source-dir',type=Path,default=SOURCE)
    p.add_argument('--schema',type=Path,default=BASE/'kuchen-schema.json')
    p.add_argument('--private-output',type=Path,default=EXCLUDED/'kuchen-graph-2026-11-10/derived/first')
    p.add_argument('--out',type=Path,default=BASE/'graph-audit/results.json')
    p.add_argument('--fixture-report',type=Path)
    args=p.parse_args();report=fixtures()
    if args.fixture_report:write_new(args.fixture_report,report)
    print(json.dumps(report,indent=2),flush=True)
    if args.run:
        if not args.expected_protocol_sha:p.error('--run requires the frozen --expected-protocol-sha')
        print(json.dumps(run_graph(args.protocol,args.expected_protocol_sha,args.source_dir,args.schema,args.private_output,args.out),indent=2),flush=True)


if __name__=='__main__':main()
