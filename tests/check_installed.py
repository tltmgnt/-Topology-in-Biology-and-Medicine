"""Run installed research workflows outside the source checkout."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile


def run(arguments, directory, expected=0):
    result = subprocess.run([sys.executable, '-I', '-m', 'bio_topology', *arguments],
                            cwd=directory, capture_output=True, text=True, check=False)
    if result.returncode != expected:
        raise AssertionError(result.stderr or result.stdout)
    response = json.loads(result.stdout)
    if response['clinical_use_authorized'] or response['execution_authorized']:
        raise AssertionError('research workflow must not authorize actions')
    return response


def main():
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as directory:
        cases = [('baseline', 'dataset.json', 'requirements.json', 0),
                 ('ambiguous', 'ambiguous.json', 'requirements.json', 1),
                 ('unknown', 'unknown.json', 'requirements.json', 1),
                 ('outage', 'dataset.json', 'outage.json', 1),
                 ('missing', 'dataset.json', 'gaps.json', 1),
                 ('expired', 'dataset.json', 'expired.json', 1)]
        for label, dataset, requirements, expected in cases:
            path = Path(directory) / label
            run(['analyze', str(root / 'examples' / dataset), '--requirements',
                 str(root / 'examples' / requirements), '--output', str(path)], directory, expected)
            response = run(['verify', str(path)], directory)
            if not response['bundle_consistent']:
                raise AssertionError('replay failed')
        comparison = run(['compare', str(Path(directory) / 'baseline'), str(Path(directory) / 'outage')], directory)
        if comparison['assessment_policy_changed'] or not comparison['newly_excluded_edges']:
            raise AssertionError('scenario comparison mismatch')
    print('Installed baseline, ambiguity, unknown, outage, missingness, expiry and comparison workflows passed')


if __name__ == '__main__':
    main()
