"""Evidence-qualified network topology and structural signed-walk diagnostics."""
from collections import deque
import hashlib
import json
from .model import parse_dataset, parse_requirements, timestamp

ENGINE_VERSION = '0.1.0'
SIGNS = ('positive', 'negative', 'unknown')


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def fingerprint(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def evidence_assessment(dataset, policy):
    instant = timestamp(policy['as_of'])
    results = {}
    for item in sorted(dataset.evidence.values(), key=lambda e: e.id):
        reasons = []
        if hashlib.sha256(item.payload).hexdigest() != item.sha256:
            reasons.append('CONTENT_MISMATCH')
        if item.context != dataset.context:
            reasons.append('CONTEXT_MISMATCH')
        if instant < item.observed_at:
            reasons.append('FUTURE_OBSERVATION')
        if instant >= item.expires_at:
            reasons.append('EXPIRED')
        results[item.id] = {'id': item.id, 'status': 'CHECKED' if not reasons else 'NOT_CURRENT',
                            'reasons': reasons, 'source': item.source, 'declared_evidence_kind': item.kind,
                            'declared_provenance_group': item.provenance_group}
    return results


def edge_assessment(dataset, policy, evidence):
    results = {}
    minimum = policy['minimum_provenance_groups']
    for edge in sorted(dataset.edges.values(), key=lambda e: e.id):
        reasons, groups, hashes = [], set(), set()
        if not edge.evidence_ids:
            reasons.append('MISSING_EVIDENCE')
        for identifier in edge.evidence_ids:
            if identifier not in evidence:
                reasons.append('MISSING_EVIDENCE:' + identifier)
            elif evidence[identifier]['status'] != 'CHECKED':
                reasons.append('INVALID_EVIDENCE:' + identifier)
            else:
                groups.add(dataset.evidence[identifier].provenance_group)
                hashes.add(dataset.evidence[identifier].sha256)
        if len(groups) < minimum:
            reasons.append('INSUFFICIENT_DECLARED_GROUPS')
        if len(hashes) < minimum:
            reasons.append('INSUFFICIENT_DISTINCT_CONTENT')
        excluded = edge.id in policy['excluded_edges']
        results[edge.id] = {'id': edge.id, 'status': 'EXCLUDED' if excluded else 'EVIDENCE_QUALIFIED' if not reasons else 'BLOCKED',
                           'reasons': sorted(set(reasons)), 'declared_group_count': len(groups),
                           'distinct_content_count': len(hashes), 'evidence_ids': list(edge.evidence_ids)}
    return results


def regulatory_graph(dataset, edge_ids):
    graph = {node: [] for node in sorted(dataset.nodes)}
    for identifier in sorted(edge_ids):
        edge = dataset.edges[identifier]
        if edge.kind == 'regulatory':
            graph[edge.source].append(edge)
    return graph


def multiply(left, right):
    if 'unknown' in (left, right):
        return 'unknown'
    return 'positive' if left == right else 'negative'


def signed_walks(graph, source, target):
    """Reachability in (node, sign) product space; walks can revisit biological nodes."""
    if source not in graph or target not in graph:
        return {}
    initial = (source, 'positive')
    parents, queue = {initial: None}, deque([initial])
    while queue:
        state = queue.popleft()
        for edge in graph[state[0]]:
            successor = (edge.target, multiply(state[1], edge.sign))
            if successor not in parents:
                parents[successor] = (state, edge.id)
                queue.append(successor)
    results = {}
    for sign in SIGNS:
        state = (target, sign)
        if state not in parents:
            continue
        nodes, edges = [target], []
        while parents[state] is not None:
            previous, identifier = parents[state]
            nodes.append(previous[0])
            edges.append(identifier)
            state = previous
        results[sign] = {'nodes': list(reversed(nodes)), 'edges': list(reversed(edges)), 'sign': sign}
    return results


def topology(dataset, edge_ids):
    weak = {node: set() for node in dataset.nodes}
    graph = regulatory_graph(dataset, edge_ids)
    for identifier in edge_ids:
        edge = dataset.edges[identifier]
        weak[edge.source].add(edge.target)
        weak[edge.target].add(edge.source)
    remaining, components = set(weak), []
    while remaining:
        start = min(remaining)
        found, pending = {start}, [start]
        remaining.remove(start)
        while pending:
            for other in sorted(weak[pending.pop()]):
                if other in remaining:
                    remaining.remove(other)
                    found.add(other)
                    pending.append(other)
        components.append(sorted(found))
    reach = {}
    for start in sorted(graph):
        found, pending = {start}, [start]
        while pending:
            for edge in graph[pending.pop()]:
                if edge.target not in found:
                    found.add(edge.target)
                    pending.append(edge.target)
        reach[start] = found
    remaining, sccs = set(graph), []
    while remaining:
        start = min(remaining)
        group = {other for other in remaining if other in reach[start] and start in reach[other]}
        sccs.append(sorted(group))
        remaining -= group
    return {'weak_components': components, 'isolated_nodes': sorted(node for node in weak if not weak[node]),
            'regulatory_sccs': sccs,
            'regulatory_cycles': [group for group in sccs if len(group) > 1 or any(edge.target == group[0] for edge in graph[group[0]])]}


def build_report(data, requirements):
    dataset = parse_dataset(data)
    policy = parse_requirements(requirements, dataset)
    evidence = evidence_assessment(dataset, policy)
    edges = edge_assessment(dataset, policy, evidence)
    declared_ids = sorted(set(dataset.edges) - set(policy['excluded_edges']))
    qualified_ids = sorted(identifier for identifier, result in edges.items() if result['status'] == 'EVIDENCE_QUALIFIED')
    declared, qualified = regulatory_graph(dataset, declared_ids), regulatory_graph(dataset, qualified_ids)
    gaps, checks = [], []
    for node in policy['required_nodes']:
        if node not in dataset.nodes:
            gaps.append({'code': 'MISSING_REQUIRED_NODE', 'subject': node})
    for edge in edges.values():
        if edge['status'] == 'BLOCKED':
            gaps.append({'code': 'EDGE_EVIDENCE_GAP', 'subject': edge['id']})
    for requirement in policy['required_paths']:
        source, target = requirement['source'], requirement['target']
        observed = signed_walks(qualified, source, target)
        proposed = signed_walks(declared, source, target)
        reasons = []
        if source not in dataset.nodes or target not in dataset.nodes:
            reasons.append('MISSING_ENDPOINT')
        elif not proposed:
            reasons.append('NO_DECLARED_REGULATORY_WALK')
        elif not observed:
            reasons.append('NO_EVIDENCE_QUALIFIED_WALK')
        elif requirement['expected_sign'] != 'any':
            if requirement['expected_sign'] not in observed:
                reasons.append('EXPECTED_SIGN_NOT_SUPPORTED')
            if 'positive' in observed and 'negative' in observed:
                reasons.append('AMBIGUOUS_SIGN')
            if 'unknown' in observed:
                reasons.append('UNKNOWN_SIGN')
        checks.append({'requirement': requirement, 'status': 'FAIL' if reasons else 'PASS',
                       'reasons': reasons, 'declared_signs': [sign for sign in SIGNS if sign in proposed],
                       'qualified_signs': [sign for sign in SIGNS if sign in observed], 'witnesses': observed})
        gaps.extend({'code': reason, 'subject': requirement['id']} for reason in reasons)
    missing = sum(node not in dataset.nodes for node in policy['required_nodes'])
    return {'schema_version': 1, 'engine_version': ENGINE_VERSION,
            'dataset_sha256': fingerprint(data), 'requirements_sha256': fingerprint(requirements),
            'status': 'GAPS_FOUND' if gaps else 'DECLARED_CHECKS_SATISFIED',
            'context': data['context'], 'requirements': policy,
            'summary': {'nodes': len(dataset.nodes), 'edges': len(dataset.edges), 'evidence_records': len(dataset.evidence),
                        'qualified_edges': len(qualified_ids), 'blocked_edges': sum(edge['status'] == 'BLOCKED' for edge in edges.values()),
                        'excluded_edges': len(policy['excluded_edges']), 'gap_count': len(gaps)},
            'required_node_coverage': 1 - missing / len(policy['required_nodes']) if policy['required_nodes'] else None,
            'declared_topology': topology(dataset, declared_ids), 'qualified_topology': topology(dataset, qualified_ids),
            'evidence_checks': list(evidence.values()), 'edge_checks': list(edges.values()), 'path_checks': checks, 'gaps': gaps,
            'clinical_use_authorized': False, 'execution_authorized': False,
            'limitations': ['Research data-quality and structural graph checks only; no diagnosis or treatment guidance',
                            'Hashes verify bytes, not biological truth, source authenticity or experimental reproducibility',
                            'Provenance groups are declarations, not independently authenticated sources',
                            'Signed walks are algebra over supplied regulatory edges, not causal or clinical predictions',
                            'Missing nodes or links indicate dataset gaps, not biological absence',
                            'Evidence validity is assessed at the explicit as_of time, not necessarily now']}
