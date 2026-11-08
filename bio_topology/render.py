"""Self-contained, script-free research review; no medical recommendations."""
from html import escape
import json
from .model import parse_dataset


def render_html(data, report):
    dataset = parse_dataset(data)
    nodes = ''.join('<tr><td>' + escape(item.id) + '</td><td>' + escape(item.kind) + '</td><td>'
                    + escape(item.label) + '</td></tr>' for item in sorted(dataset.nodes.values(), key=lambda n: n.id))
    evidence = ''.join('<tr><td>' + escape(item['id']) + '</td><td>' + item['status'] + '</td><td>'
                       + escape(', '.join(item['reasons']) or 'Byte, context and time checks passed') + '</td></tr>'
                       for item in report['evidence_checks'])
    edges = ''.join('<tr><td>' + escape(item['id']) + '</td><td>' + item['status'] + '</td><td>'
                    + escape(', '.join(item['reasons']) or 'Declared input checks passed') + '</td></tr>'
                    for item in report['edge_checks'])
    paths = ''.join('<h3>' + escape(item['requirement']['id']) + ' — ' + item['status'] + '</h3><pre>'
                    + escape(json.dumps(item, sort_keys=True, indent=2)) + '</pre>' for item in report['path_checks'])
    def table(heading, titles, rows):
        return '<h2>' + heading + '</h2><table><thead><tr>' + ''.join('<th>' + t + '</th>' for t in titles) + '</tr></thead><tbody>' + rows + '</tbody></table>'
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'">'
            '<title>Biology topology research review</title><style>'
            'body{font:16px system-ui,sans-serif;max-width:1100px;margin:32px auto;padding:0 20px;color:#172033}'
            'table{width:100%;border-collapse:collapse;table-layout:fixed}'
            'th,td{border:1px solid #cbd5e1;padding:10px;text-align:left;overflow-wrap:anywhere}'
            'pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f1f5f9;padding:16px}'
            '</style></head><body><h1>Topology in biology and medicine</h1>'
            '<p><strong>Research software only. Not for diagnosis, treatment, patient triage or clinical decisions.</strong></p>'
            '<p>Signed walks describe supplied graph algebra, not predicted biological effects. '
            'Matching evidence bytes does not establish scientific validity.</p>'
            '<h2>' + report['status'] + '</h2><p>Assessment time: ' + escape(report['requirements']['as_of']) + '</p>'
            + table('Entity inventory', ['ID', 'Kind', 'Label'], nodes)
            + table('Evidence byte context and time checks', ['ID', 'Status', 'Finding'], evidence)
            + table('Declared edge qualification', ['ID', 'Status', 'Finding'], edges)
            + '<h2>Structural regulatory walk checks</h2>' + paths
            + '<h2>Complete analysis and limitations</h2><pre>'
            + escape(json.dumps(report, sort_keys=True, indent=2)) + '</pre></body></html>\n')
