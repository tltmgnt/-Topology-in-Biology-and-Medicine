"""Offline curriculum answer key. Synthetic checks, never operational approval."""
import ast
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
for base in (ROOT, ROOT / "src", ROOT / "layer-b"):
    sys.path.insert(0, str(base))
CASES = []

def check(name, actual, expected):
    passed = actual == expected
    CASES.append({"case": name, "actual": actual, "expected": expected, "passed": passed})
    if not passed:
        raise AssertionError(f"{name}: expected {expected!r}, got {actual!r}")

def rejects(name, call, error=ValueError):
    try:
        call()
    except error:
        check(name, error.__name__, error.__name__)
    else:
        raise AssertionError(f"{name}: expected {error.__name__}")

def sample(path):
    return json.loads((ROOT / path).read_text())



def run():
    from bio_topology.analysis import build_report, multiply
    data, policy = sample("examples/dataset.json"), sample("examples/requirements.json")
    r = build_report(data,policy)
    check("two inhibitions have positive parity", multiply("negative","negative"), "positive")
    check("unknown sign remains unknown", multiply("unknown","negative"), "unknown")
    check("qualified synthetic reference", r["status"], "DECLARED_CHECKS_SATISFIED")
    bad = copy.deepcopy(data)
    bad["evidence"][0]["sha256"] = "0"*64
    q = build_report(bad,policy)
    check("altered evidence creates a gap", q["status"], "GAPS_FOUND")
    check("digest failure remains visible", any("CONTENT_MISMATCH" in e["reasons"] for e in q["evidence_checks"]), True)
    check("no clinical authority", r["clinical_use_authorized"], False)
    check("no execution authority", r["execution_authorized"], False)

if __name__ == "__main__":
    if sys.argv[1:] not in ([], ["--verify"]):
        raise SystemExit("Usage: python curriculum/lab.py [--verify]")
    run()
    report = {"schema_version": 1, "status": "PASS", "case_count": len(CASES),
              "cases": CASES, "scope": "Synthetic curriculum checks only"}
    if sys.argv[1:] == ["--verify"]:
        expected = json.loads((Path(__file__).parent / "expected.json").read_text())
        if report != expected:
            raise AssertionError("Observed answers differ from curriculum/expected.json")
    print(json.dumps(report, sort_keys=True, indent=2, allow_nan=False))
