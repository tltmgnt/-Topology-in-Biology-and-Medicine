"""Structural graph, provenance, time, integrity and end-to-end research tests."""
import ast
import base64
import contextlib
import copy
import hashlib
import io
import itertools
from pathlib import Path
import tempfile
import unittest
from bio_topology import build_report, compare_bundles, create_bundle, parse_dataset, parse_requirements, verify_bundle
from bio_topology.analysis import canonical
from bio_topology.io import MAX_BYTES, decode, read_json
from bio_topology.__main__ import main

ROOT = Path(__file__).resolve().parents[1]


def sample():
    return read_json(ROOT / 'examples/dataset.json'), read_json(ROOT / 'examples/requirements.json')


def evidence(identifier, scope, payload=None, group='declared-lab-1'):
    payload = payload if payload is not None else ('synthetic:' + identifier).encode()
    return {'id': identifier, 'source': 'synthetic:' + identifier, 'kind': 'synthetic', 'provenance_group': group,
            'context': dict(scope), 'observed_at': '2026-11-01T00:00:00Z', 'expires_at': '2026-12-01T00:00:00Z',
            'sha256': hashlib.sha256(payload).hexdigest(), 'content_base64': base64.b64encode(payload).decode()}


class TopologyTests(unittest.TestCase):
    def setUp(self):
        self.data, self.policy = sample()

    def test_baseline_is_scoped_graph_result(self):
        report = build_report(self.data, self.policy)
        self.assertEqual(report['status'], 'DECLARED_CHECKS_SATISFIED')
        self.assertEqual(report['qualified_topology']['weak_components'], [['A', 'B', 'C', 'D']])
        self.assertEqual(report['qualified_topology']['regulatory_sccs'], [['A'], ['B'], ['C'], ['D']])
        self.assertEqual(report['path_checks'][0]['qualified_signs'], ['negative'])
        self.assertEqual(report['path_checks'][0]['witnesses']['negative']['edges'], ['AC'])
        self.assertFalse(report['clinical_use_authorized'])
        self.assertFalse(report['execution_authorized'])

    def test_association_is_not_regulatory_reachability(self):
        policy = read_json(ROOT / 'examples/gaps.json')
        report = build_report(self.data, policy)
        self.assertEqual(report['required_node_coverage'], 0.5)
        self.assertIn({'code': 'MISSING_REQUIRED_NODE', 'subject': 'missing'}, report['gaps'])
        self.assertEqual(report['path_checks'][0]['qualified_signs'], [])
        self.assertEqual(report['path_checks'][0]['reasons'], ['NO_DECLARED_REGULATORY_WALK'])

    def test_sign_ambiguity_is_visible(self):
        report = build_report(read_json(ROOT / 'examples/ambiguous.json'), self.policy)
        self.assertEqual(report['path_checks'][0]['qualified_signs'], ['positive', 'negative'])
        self.assertEqual(report['path_checks'][0]['reasons'], ['AMBIGUOUS_SIGN'])

    def test_unknown_does_not_become_negative(self):
        report = build_report(read_json(ROOT / 'examples/unknown.json'), self.policy)
        self.assertEqual(report['path_checks'][0]['qualified_signs'], ['negative', 'unknown'])
        self.assertEqual(report['path_checks'][0]['reasons'], ['UNKNOWN_SIGN'])

    def test_exclusions_are_recorded_and_do_not_mutate_data(self):
        before = copy.deepcopy(self.data)
        report = build_report(self.data, read_json(ROOT / 'examples/outage.json'))
        self.assertEqual(report['summary']['excluded_edges'], 2)
        self.assertEqual(report['path_checks'][0]['qualified_signs'], [])
        self.assertEqual(before, self.data)

    def test_negative_feedback_cycle_can_generate_both_walk_parities(self):
        self.data['edges'].append({'id': 'CA', 'source': 'C', 'target': 'A', 'kind': 'regulatory',
                                   'sign': 'positive', 'evidence_ids': ['ev-CA']})
        self.data['evidence'].append(evidence('ev-CA', self.data['context']))
        report = build_report(self.data, self.policy)
        self.assertIn(['A', 'B', 'C'], report['qualified_topology']['regulatory_cycles'])
        self.assertEqual(report['path_checks'][0]['qualified_signs'], ['positive', 'negative'])
        positive = report['path_checks'][0]['witnesses']['positive']['nodes']
        self.assertLess(len(set(positive)), len(positive))

    def test_missing_endpoint_is_not_disconnected(self):
        self.policy['required_paths'][0]['target'] = 'absent'
        report = build_report(self.data, self.policy)
        self.assertEqual(report['path_checks'][0]['reasons'], ['MISSING_ENDPOINT'])

    def test_opposite_expected_sign_is_not_supported(self):
        self.policy['required_paths'][0]['expected_sign'] = 'positive'
        report = build_report(self.data, self.policy)
        self.assertEqual(report['path_checks'][0]['reasons'], ['EXPECTED_SIGN_NOT_SUPPORTED'])

    def test_any_sign_requirement_allows_explicit_unknown(self):
        self.policy['required_paths'][0]['expected_sign'] = 'any'
        report = build_report(read_json(ROOT / 'examples/unknown.json'), self.policy)
        self.assertEqual(report['path_checks'][0]['status'], 'PASS')
        self.assertIn('unknown', report['path_checks'][0]['qualified_signs'])

    def test_all_two_node_signed_graphs_against_bounded_walk_oracle(self):
        scope = self.data['context']
        positions = list(itertools.product(['A', 'B'], repeat=2))
        signs = {1: 'positive', -1: 'negative', 0: 'unknown'}
        for assignment in itertools.product([None, 1, -1, 0], repeat=4):
            data = {'schema_version': 1, 'context': scope,
                    'nodes': [{'id': n, 'kind': 'gene', 'label': 'Fictional ' + n} for n in ('A', 'B')],
                    'edges': [], 'evidence': []}
            outgoing = {'A': [], 'B': []}
            for index, ((source, target), sign) in enumerate(zip(positions, assignment)):
                if sign is None:
                    continue
                identifier = str(index)
                data['edges'].append({'id': identifier, 'source': source, 'target': target,
                                      'kind': 'regulatory', 'sign': signs[sign], 'evidence_ids': [identifier]})
                data['evidence'].append(evidence(identifier, scope))
                outgoing[source].append((target, sign))
            policy = {**self.policy, 'required_nodes': [], 'required_paths': [
                {'id': a + b, 'source': a, 'target': b, 'expected_sign': 'any'} for a, b in [('A', 'B'), ('B', 'A')]]}
            results = build_report(data, policy)['path_checks']
            for result in results:
                source, target = result['requirement']['source'], result['requirement']['target']
                frontier, observed = {(source, 1)}, set()
                # Product graph has six states; six transitions cover every minimal witness.
                for _ in range(6):
                    frontier = {(end, product * edge_sign) for start, product in frontier
                                for end, edge_sign in outgoing[start]}
                    observed |= {signs[product] for end, product in frontier if end == target}
                self.assertEqual(set(result['qualified_signs']), observed, assignment)


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.data, self.policy = sample()

    def test_expiry_boundary_blocks_edges(self):
        report = build_report(self.data, read_json(ROOT / 'examples/expired.json'))
        self.assertEqual(report['summary']['qualified_edges'], 0)
        self.assertEqual(report['summary']['blocked_edges'], 4)
        self.assertEqual(report['path_checks'][0]['reasons'], ['NO_EVIDENCE_QUALIFIED_WALK'])
        self.assertTrue(all('EXPIRED' in item['reasons'] for item in report['evidence_checks']))

    def test_hash_context_and_future_checks_are_distinct(self):
        cases = [('sha256', '0' * 64, 'CONTENT_MISMATCH'),
                 ('context', {**self.data['context'], 'system': 'other'}, 'CONTEXT_MISMATCH'),
                 ('observed_at', '2026-11-09T00:00:00Z', 'FUTURE_OBSERVATION')]
        for key, value, reason in cases:
            with self.subTest(reason=reason):
                data = copy.deepcopy(self.data)
                data['evidence'][0][key] = value
                report = build_report(data, self.policy)
                check = next(item for item in report['evidence_checks'] if item['id'] == 'ev-AB')
                self.assertIn(reason, check['reasons'])
                edge = next(item for item in report['edge_checks'] if item['id'] == 'AB')
                self.assertEqual(edge['status'], 'BLOCKED')

    def test_unknown_evidence_reference_is_a_visible_gap(self):
        self.data['edges'][0]['evidence_ids'] = ['absent']
        report = build_report(self.data, self.policy)
        edge = next(item for item in report['edge_checks'] if item['id'] == 'AB')
        self.assertIn('MISSING_EVIDENCE:absent', edge['reasons'])
        self.assertIn({'code': 'EDGE_EVIDENCE_GAP', 'subject': 'AB'}, report['gaps'])

    def test_duplicate_groups_do_not_satisfy_threshold(self):
        self.policy['minimum_provenance_groups'] = 2
        for edge in self.data['edges']:
            identifier = 'duplicate-' + edge['id']
            self.data['evidence'].append(evidence(identifier, self.data['context']))
            edge['evidence_ids'].append(identifier)
        report = build_report(self.data, self.policy)
        self.assertTrue(all(item['declared_group_count'] == 1 for item in report['edge_checks']))
        self.assertEqual(report['summary']['qualified_edges'], 0)

    def test_duplicate_bytes_do_not_satisfy_distinct_content_threshold(self):
        self.policy['minimum_provenance_groups'] = 2
        records = {item['id']: item for item in self.data['evidence']}
        for edge in self.data['edges']:
            original = records[edge['evidence_ids'][0]]
            duplicate = {**original, 'id': 'copy-' + edge['id'], 'provenance_group': 'declared-lab-2'}
            self.data['evidence'].append(duplicate)
            edge['evidence_ids'].append(duplicate['id'])
        report = build_report(self.data, self.policy)
        self.assertTrue(all(item['declared_group_count'] == 2 for item in report['edge_checks']))
        self.assertTrue(all(item['distinct_content_count'] == 1 for item in report['edge_checks']))
        self.assertEqual(report['summary']['qualified_edges'], 0)

    def test_distinct_declared_groups_and_bytes_pass_only_input_checks(self):
        self.policy['minimum_provenance_groups'] = 2
        for edge in self.data['edges']:
            identifier = 'second-' + edge['id']
            self.data['evidence'].append(evidence(identifier, self.data['context'], group='declared-lab-2'))
            edge['evidence_ids'].append(identifier)
        report = build_report(self.data, self.policy)
        self.assertEqual(report['status'], 'DECLARED_CHECKS_SATISFIED')
        self.assertFalse(report['clinical_use_authorized'])

    def test_unreferenced_invalid_evidence_is_reported_without_supporting_edges(self):
        record = evidence('unused', self.data['context'])
        record['sha256'] = '0' * 64
        self.data['evidence'].append(record)
        report = build_report(self.data, self.policy)
        self.assertEqual(report['status'], 'DECLARED_CHECKS_SATISFIED')
        self.assertEqual(next(item for item in report['evidence_checks'] if item['id'] == 'unused')['status'], 'NOT_CURRENT')


class InputTests(unittest.TestCase):
    def setUp(self):
        self.data, self.policy = sample()

    def test_invalid_root_nodes_edges_and_context(self):
        mutations = [lambda d: d.update(schema_version=True), lambda d: d.update(unknown=1),
                     lambda d: d['nodes'].append(d['nodes'][0]),
                     lambda d: d['edges'][0].update(target='absent'),
                     lambda d: d['edges'][-1].update(sign='positive'),
                     lambda d: d['context'].pop('system')]
        for mutation in mutations:
            data = copy.deepcopy(self.data)
            mutation(data)
            with self.assertRaises(ValueError):
                parse_dataset(data)

    def test_invalid_evidence_shapes_and_timestamps(self):
        for key, value in [('content_base64', '!invalid'), ('content_base64', ''), ('kind', 'clinical-certification'),
                           ('sha256', 'bad'), ('observed_at', '2026-11-01T00:00:00'),
                           ('expires_at', '2026-10-01T00:00:00Z')]:
            data = copy.deepcopy(self.data)
            data['evidence'][0][key] = value
            with self.assertRaises(ValueError):
                parse_dataset(data)

    def test_invalid_requirements(self):
        dataset = parse_dataset(self.data)
        for changes in ({'excluded_edges': ['missing']}, {'minimum_provenance_groups': True},
                        {'minimum_provenance_groups': 0}, {'required_nodes': [], 'required_paths': []},
                        {'as_of': 'invalid'}):
            with self.assertRaises(ValueError):
                parse_requirements({**self.policy, **changes}, dataset)

    def test_strict_json_and_resource_limits(self):
        for raw in (b'{"x":1,"x":1}', b'{"x":NaN}', b'{"x":1e999}', b'\xff',
                    ('[' * 70 + '0' + ']' * 70).encode()):
            with self.assertRaises(ValueError):
                decode(raw)
        self.data['nodes'] += [{'id': str(i), 'kind': 'gene', 'label': 'Fictional'} for i in range(128)]
        with self.assertRaises(ValueError):
            parse_dataset(self.data)

    def test_decoded_evidence_byte_budgets(self):
        data = copy.deepcopy(self.data)
        data['evidence'][0] = evidence('oversize', data['context'], b'x' * 65537)
        with self.assertRaises(ValueError):
            parse_dataset(data)
        data = copy.deepcopy(self.data)
        data['evidence'] = [evidence(str(i), data['context'], b'x' * 65536) for i in range(17)]
        with self.assertRaises(ValueError):
            parse_dataset(data)

    def test_python_310_syntax(self):
        for path in (ROOT / 'bio_topology').glob('*.py'):
            ast.parse(path.read_text(), filename=str(path), feature_version=(3, 10))


class BundleTests(unittest.TestCase):
    def setUp(self):
        self.data, self.policy = sample()
        self.temp = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'run'

    def test_complete_bundle_replays_and_preserves_existing(self):
        report = create_bundle(self.path, self.data, self.policy)
        self.assertEqual(report, verify_bundle(self.path))
        self.assertEqual({p.name for p in self.path.iterdir()}, {'dataset.json','requirements.json','report.json','review.html','manifest.json'})
        with self.assertRaises(FileExistsError):
            create_bundle(self.path, self.data, self.policy)
        self.assertEqual(report, verify_bundle(self.path))

    def test_rehashed_forged_report_is_rejected(self):
        create_bundle(self.path, self.data, self.policy)
        report = read_json(self.path / 'report.json')
        report['clinical_use_authorized'] = True
        payload = canonical(report)
        (self.path / 'report.json').write_bytes(payload)
        manifest = read_json(self.path / 'manifest.json')
        manifest['files']['report.json'] = {'sha256': hashlib.sha256(payload).hexdigest(), 'bytes': len(payload)}
        (self.path / 'manifest.json').write_bytes(canonical(manifest))
        with self.assertRaises(ValueError):
            verify_bundle(self.path)

    def test_each_file_tamper_is_rejected(self):
        create_bundle(self.path, self.data, self.policy)
        for path in self.path.iterdir():
            raw = path.read_bytes()
            path.write_bytes(raw + b' ')
            with self.assertRaises(ValueError):
                verify_bundle(self.path)
            path.write_bytes(raw)

    def test_invalid_file_inventory_and_symlinks(self):
        create_bundle(self.path, self.data, self.policy)
        extra = self.path / 'extra'
        extra.write_text('x')
        with self.assertRaises(ValueError):
            verify_bundle(self.path)
        extra.unlink()
        target = Path(self.temp.name) / 'external'
        source = self.path / 'report.json'
        target.write_bytes(source.read_bytes())
        source.unlink()
        try:
            source.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest('symlinks unavailable')
        with self.assertRaises(ValueError):
            verify_bundle(self.path)

    def test_assessment_policy_and_exclusion_comparisons(self):
        create_bundle(self.path, self.data, self.policy)
        outage = Path(self.temp.name) / 'outage'
        create_bundle(outage, self.data, read_json(ROOT / 'examples/outage.json'))
        result = compare_bundles(self.path, outage)
        self.assertFalse(result['assessment_policy_changed'])
        self.assertEqual(result['newly_excluded_edges'], ['AC', 'BC'])
        expired = Path(self.temp.name) / 'expired'
        create_bundle(expired, self.data, read_json(ROOT / 'examples/expired.json'))
        result = compare_bundles(self.path, expired)
        self.assertTrue(result['assessment_policy_changed'])
        self.assertEqual(len(result['lost_qualified_edges']), 4)

    def test_comparison_rejects_other_captured_dataset(self):
        create_bundle(self.path, self.data, self.policy)
        other = Path(self.temp.name) / 'other'
        self.data['nodes'][0]['label'] = 'Changed source record'
        create_bundle(other, self.data, self.policy)
        with self.assertRaises(ValueError):
            compare_bundles(self.path, other)

    def test_html_escapes_supplied_labels(self):
        self.data['nodes'][0]['label'] = '<script>alert(1)</script>'
        create_bundle(self.path, self.data, self.policy)
        html = (self.path / 'review.html').read_text()
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)
        self.assertIn('Not for diagnosis', html)

    def test_cli_and_failure_status(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(['analyze', str(ROOT / 'examples/dataset.json'), '--requirements',
                                   str(ROOT / 'examples/requirements.json'), '--output', str(self.path)]), 0)
            self.assertEqual(main(['verify', str(self.path)]), 0)
            outage = Path(self.temp.name) / 'outage'
            self.assertEqual(main(['analyze', str(ROOT / 'examples/dataset.json'), '--requirements',
                                   str(ROOT / 'examples/outage.json'), '--output', str(outage)]), 1)
            self.assertEqual(main(['compare', str(self.path), str(outage)]), 0)
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(['verify', str(Path(self.temp.name) / 'absent')]), 2)

    def test_oversize_file(self):
        path = Path(self.temp.name) / 'large'
        with path.open('wb') as stream:
            stream.truncate(MAX_BYTES + 1)
        with self.assertRaises(ValueError):
            read_json(path)


if __name__ == '__main__':
    unittest.main()
