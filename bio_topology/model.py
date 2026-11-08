"""Strict bounded research-network and evidence contracts; no clinical execution."""
import base64
from dataclasses import dataclass
from datetime import datetime, timezone
import re
from types import MappingProxyType
from typing import Mapping

MAX_NODES = 128
MAX_EDGES = 512
MAX_EVIDENCE = 256
MAX_PAYLOAD = 65536
MAX_TOTAL_PAYLOAD = 1048576


def fields(value, required):
    if not isinstance(value, dict) or set(value) != set(required):
        raise ValueError('exact contract fields required')


def name(value):
    if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > 160:
        raise ValueError('trimmed text of 1 to 160 characters required')
    return value


def version(value):
    if isinstance(value, bool) or not isinstance(value, int) or value != 1:
        raise ValueError('schema version 1 required')


def names(values, maximum):
    if not isinstance(values, list) or len(values) > maximum:
        raise ValueError('bounded identifier array required')
    result = [name(value) for value in values]
    if len(set(result)) != len(result):
        raise ValueError('duplicate identifier')
    return sorted(result)


def context(value):
    fields(value, {'organism', 'system', 'condition'})
    return tuple(name(value[key]) for key in ('organism', 'system', 'condition'))


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError('timestamp text required')
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('timezone-aware timestamp required')
    return result.astimezone(timezone.utc)


@dataclass(frozen=True)
class Node:
    id: str
    kind: str
    label: str


@dataclass(frozen=True)
class Edge:
    id: str
    source: str
    target: str
    kind: str
    sign: str
    evidence_ids: tuple


@dataclass(frozen=True)
class Evidence:
    id: str
    source: str
    kind: str
    provenance_group: str
    context: tuple
    observed_at: datetime
    expires_at: datetime
    sha256: str
    payload: bytes


@dataclass(frozen=True)
class Dataset:
    context: tuple
    nodes: Mapping[str, Node]
    edges: Mapping[str, Edge]
    evidence: Mapping[str, Evidence]


def parse_dataset(data):
    fields(data, {'schema_version', 'context', 'nodes', 'edges', 'evidence'})
    version(data['schema_version'])
    scope = context(data['context'])
    if not isinstance(data['nodes'], list) or not 1 <= len(data['nodes']) <= MAX_NODES:
        raise ValueError('between 1 and 128 nodes required')
    nodes, edges, evidence = {}, {}, {}
    for value in data['nodes']:
        fields(value, {'id', 'kind', 'label'})
        item = Node(*(name(value[key]) for key in ('id', 'kind', 'label')))
        if item.id in nodes or item.kind not in {'gene', 'protein', 'process', 'phenotype'}:
            raise ValueError('duplicate node or unsupported kind')
        nodes[item.id] = item
    if not isinstance(data['edges'], list) or len(data['edges']) > MAX_EDGES:
        raise ValueError('edge limit exceeded')
    for value in data['edges']:
        fields(value, {'id', 'source', 'target', 'kind', 'sign', 'evidence_ids'})
        item = Edge(*(name(value[key]) for key in ('id', 'source', 'target', 'kind', 'sign')),
                    tuple(names(value['evidence_ids'], MAX_EVIDENCE)))
        if item.id in edges or item.source not in nodes or item.target not in nodes:
            raise ValueError('duplicate edge or dangling endpoint')
        if item.kind not in {'regulatory', 'association'} or item.sign not in {'positive', 'negative', 'unknown'}:
            raise ValueError('unsupported edge semantics')
        if item.kind == 'association' and item.sign != 'unknown':
            raise ValueError('association must not assert a regulatory sign')
        edges[item.id] = item
    if not isinstance(data['evidence'], list) or len(data['evidence']) > MAX_EVIDENCE:
        raise ValueError('evidence limit exceeded')
    total = 0
    for value in data['evidence']:
        fields(value, {'id', 'source', 'kind', 'provenance_group', 'context', 'observed_at', 'expires_at', 'sha256', 'content_base64'})
        identifier = name(value['id'])
        if identifier in evidence:
            raise ValueError('duplicate evidence ID')
        source, kind, group = name(value['source']), name(value['kind']), name(value['provenance_group'])
        if kind not in {'synthetic', 'experimental', 'computational', 'literature'}:
            raise ValueError('unsupported evidence kind')
        scope_evidence = context(value['context'])
        observed, expires = timestamp(value['observed_at']), timestamp(value['expires_at'])
        if observed >= expires:
            raise ValueError('evidence expiry must follow observation')
        if not isinstance(value['sha256'], str) or not re.fullmatch('[0-9a-f]{64}', value['sha256']):
            raise ValueError('lowercase SHA256 required')
        encoded = value['content_base64']
        if not isinstance(encoded, str) or len(encoded) > 90000:
            raise ValueError('bounded base64 content required')
        try:
            payload = base64.b64decode(encoded, validate=True)
        except (ValueError, UnicodeError) as error:
            raise ValueError('invalid base64 evidence') from error
        total += len(payload)
        if not payload or len(payload) > MAX_PAYLOAD or total > MAX_TOTAL_PAYLOAD:
            raise ValueError('evidence byte budget exceeded')
        evidence[identifier] = Evidence(identifier, source, kind, group, scope_evidence, observed, expires, value['sha256'], payload)
    return Dataset(scope, MappingProxyType(nodes), MappingProxyType(edges), MappingProxyType(evidence))


def parse_requirements(data, dataset):
    fields(data, {'schema_version', 'as_of', 'minimum_provenance_groups', 'required_nodes', 'required_paths', 'excluded_edges'})
    version(data['schema_version'])
    timestamp(data['as_of'])
    minimum = data['minimum_provenance_groups']
    if isinstance(minimum, bool) or not isinstance(minimum, int) or not 1 <= minimum <= 16:
        raise ValueError('minimum provenance groups must be an integer from 1 to 16')
    required = names(data['required_nodes'], MAX_NODES)
    excluded = names(data['excluded_edges'], MAX_EDGES)
    if set(excluded) - set(dataset.edges):
        raise ValueError('cannot exclude unknown edges')
    if not isinstance(data['required_paths'], list) or len(data['required_paths']) > 32:
        raise ValueError('at most 32 required paths permitted')
    paths, seen = [], set()
    for path in data['required_paths']:
        fields(path, {'id', 'source', 'target', 'expected_sign'})
        identifier, source, target, sign = (name(path[key]) for key in ('id', 'source', 'target', 'expected_sign'))
        if identifier in seen or source == target or sign not in {'positive', 'negative', 'any'}:
            raise ValueError('duplicate path, identical endpoints or unsupported expected sign')
        seen.add(identifier)
        paths.append({'id': identifier, 'source': source, 'target': target, 'expected_sign': sign})
    if not required and not paths:
        raise ValueError('at least one explicit requirement required')
    return {'schema_version': 1, 'as_of': data['as_of'], 'minimum_provenance_groups': minimum,
            'required_nodes': required, 'excluded_edges': excluded, 'required_paths': sorted(paths, key=lambda p: p['id'])}
