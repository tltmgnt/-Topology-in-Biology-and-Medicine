# Topology in Biology and Medicine

A dependency-free **research-only network topology and evidence-integrity tool**.
Import a context-scoped biological network, check supplied evidence bytes and
validity intervals, separate associations from regulatory edges, inspect structural
signed walks, and create reproducible offline review bundles.

This implementation is complete for its documented offline contracts. It is not a
clinical system, biological simulator, diagnostic tool, treatment recommender or
validation of a real biological pathway. All supplied examples are fictional.

## Install and complete a study

Requires Python 3.10 or later. No API account, paid service or credentials are needed.

```sh
python -m pip install .
mkdir -p runs
bio-topology analyze examples/dataset.json --requirements examples/requirements.json --output runs/reference
bio-topology verify runs/reference
```

Open `runs/reference/review.html` for the offline report. Each output directory must
be new and its parent must exist. Without installation, use `python -m bio_topology`
from the repository root.

```sh
python -m unittest discover -s tests -v
python tests/check_installed.py
```

The installed-workflow check requires a normal package installation and runs with
isolated imports outside the checkout, so source files cannot hide missing package
contents.

## What the workflow checks

| Layer | Implemented check | What it does not establish |
|---|---|---|
| Entity inventory | Typed gene, protein, process and phenotype nodes; required-node coverage | Completeness of biological knowledge |
| Evidence bytes | Actual decoded bytes match declared SHA256 | Source authenticity or meaningful evidence content |
| Evidence scope | Organism, system and condition match exactly | Correctness of those supplied declarations |
| Evidence time | Observation is not future-dated and expiry has not passed at explicit `as_of` | Automatic currency at today's date |
| Support counts | Distinct declared provenance groups and distinct content hashes meet thresholds | Experimental independence or replication |
| Network topology | Weak components, isolated nodes, directed regulatory SCCs and cycles | Functional importance or therapeutic value |
| Signed walks | Positive, negative and unknown parity witnesses | Causal effects, expression dynamics or clinical predictions |
| Replay | Every bundle file matches recomputation | Independent scientific validation or certification |

An association is undirected for weak-component reporting and **never participates
in regulatory signed walks**. Regulatory edges are directed. Their signs are supplied
assertions. No biological relationships are inferred from source contents.

## Synthetic examples and expected outcomes

The baseline contains fictional A → B positive, B → C negative, direct A → C
negative, and a separate unsigned association C–D. Each edge references an inline
synthetic artifact with matching bytes, context and validity dates. The negative
A-to-C requirement passes its declared input and structural checks. C–D does not
establish a regulatory walk from A to D.

- `ambiguous.json` adds an opposite-sign A-to-C edge. Both parities are reported.
- `unknown.json` changes the direct A-to-C sign to unknown. Unknown stays explicit.
- `outage.json` excludes BC and AC in a graph scenario, removing declared A-to-C access.
- `gaps.json` requires an absent entity and a regulatory walk to D that is not declared.
- `expired.json` changes assessment time to the evidence expiry boundary.

```sh
bio-topology analyze examples/ambiguous.json --requirements examples/requirements.json --output runs/ambiguous
# Expected exit 1; a complete gap report is still created.
bio-topology verify runs/ambiguous
# Expected exit 0; consistency does not turn ambiguous signs into a passing requirement.
bio-topology analyze examples/dataset.json --requirements examples/outage.json --output runs/outage
# Expected exit 1.
bio-topology compare runs/reference runs/outage
```

Comparison verifies both bundles, requires the same captured dataset, separates
exclusion changes from policy/time changes, and reports changed qualifications and
gaps. An excluded edge is a software scenario assumption, not a simulated knockout,
biological intervention, or measured treatment effect.

## Exact input contracts

Dataset root: `schema_version`, `context`, `nodes`, `edges`, `evidence`.
Context has `organism`, `system`, `condition`, all explicit trimmed strings.

Node:

```json
{"id":"A", "kind":"gene", "label":"Fictional A"}
```

Edge:

```json
{"id":"AB", "source":"A", "target":"B", "kind":"regulatory",
 "sign":"positive", "evidence_ids":["ev-AB"]}
```

Edge kinds are `regulatory` and `association`; signs are `positive`, `negative` and
`unknown`. Association signs must be unknown. Directed regulatory self-loops and
parallel links are supported. Endpoints must exist. Evidence references may be
missing and become visible gaps instead of disappearing from the analysis.

Evidence contains exactly `id`, `source`, `kind`, `provenance_group`, `context`,
`observed_at`, `expires_at`, `sha256`, `content_base64`. Evidence kind is a supplied
category: synthetic, experimental, computational or literature. No category is
independently authenticated or automatically assigned scientific credibility.

The base64 contains the actual artifact bytes, not a path to a file that might be
missing. Dates must be timezone-aware, and expiry must follow observation. Source
references are retained but never retrieved. This is not a GO, GO-CAM, SBGN, clinical
record or standard ontology importer.

Requirements:

```json
{
  "schema_version":1,
  "as_of":"2026-11-08T00:00:00Z",
  "minimum_provenance_groups":1,
  "required_nodes":["A","C"],
  "required_paths":[
    {"id":"A-C","source":"A","target":"C","expected_sign":"negative"}
  ],
  "excluded_edges":[]
}
```

For a specific expected sign, that sign must be present with no opposite known sign
and no unknown-sign walk. `any` requires at least one qualified walk and explicitly
permits ambiguity and unknown signs; the report still displays them. At least one
required node or path is necessary to avoid vacuous acceptance.

## Evidence qualification and missingness

An edge is `EVIDENCE_QUALIFIED` only when every selected evidence reference exists
and passes byte, context and time checks, and both distinct declared-group count and
distinct content-hash count meet the minimum. A changed hash, expired record,
context mismatch or absent reference blocks the edge. Group strings and content
counts do not prove independence; differently encoded or rephrased versions of the
same underlying experiment can still appear distinct.

Qualification is a software-input label. It does not validate a biological claim.
All non-excluded blocked edges create an `EDGE_EVIDENCE_GAP`, even if an alternate
qualified route satisfies a particular requirement. Explicitly excluded edges
remain visible but do not create that edge gap. Unreferenced invalid artifacts are
reported but do not qualify any edge or by themselves block the study.

Missing entities and links indicate incomplete supplied data, not absence in
biology. This follows an open-world interpretation of research knowledge. The
[Gene Ontology annotation guide](https://geneontology.org/docs/go-annotations/)
also distinguishes missing annotations from negative biological findings and records
references, evidence types and context. This tool does not claim GO conformance.

## Signed walks and feedback

Sign multiplication is positive×positive = positive, negative×negative = positive,
positive×negative = negative, and any unknown factor yields unknown. Breadth-first
search explores the finite `(node, accumulated sign)` product graph and returns a
minimum-hop witness per reachable sign. Witnesses are **walks**, not necessarily
simple paths; feedback can revisit a biological node with a different accumulated
sign. This algebra cannot predict whether feedback creates oscillation, stability,
activation or inhibition in an actual system.

Weak components use all selected edge kinds. Regulatory SCCs/cycles use regulatory
edges only. No confidence probabilities, centrality-based treatment rankings,
causal identification, dosage, diagnosis or patient triage are produced.

## Bundle and CLI semantics

A new bundle contains exactly `dataset.json`, `requirements.json`, `report.json`,
`review.html`, and `manifest.json`. It captures inline evidence bytes and metadata,
not only their references. Reports expose contexts, sources and provenance labels;
keep real datasets and reports private. CI uploads only fictional fixtures.

| Command | Exit 0 | Exit 1 | Exit 2 |
|---|---|---|---|
| `analyze` | Declared input/structural checks pass | Gaps found; bundle still created | Invalid contract, size or I/O failure |
| `verify` | Complete bundle matches recomputation | Not used | Edited, incomplete or incompatible bundle |
| `compare` | Verified comparison completed | Not used | Invalid bundles or different captured datasets |

`verify` recomputes every file, so rewriting a forged report's manifest hash cannot
hide inconsistent analysis. Replacing the dataset and regenerating the complete
study creates another internally consistent bundle; no signature or authentic source
proof is supplied. `clinical_use_authorized` and `execution_authorized` are always
false in reports and CLI results.

## Validation and development

Tests cover context/time/hash failures, missingness, association/regulatory separation,
unknown and opposite signs, feedback, duplicate sources/content, malformed JSON,
limits, forged manifests, escaped HTML, Python 3.10 syntax and end-to-end commands.
An exhaustive test enumerates all 256 two-node signed directed graphs (absent,
positive, negative or unknown in each edge slot) and compares both directions with
a bounded-walk oracle: 512 source/target checks. This validates a finite regression
set, not biological truth or universal software correctness.

CI runs Python 3.10, 3.12 and 3.13, tests installed workflows, and publishes a
seven-day `synthetic-biology-review` artifact. Extract it, open `review.html`, and
run `bio-topology verify` on the extracted directory.

See [detailed contracts and limits](docs/CONTRACTS.md). Future extensions may add
version-pinned ontology importers, authenticated provenance and qualified real-data
research validation. Clinical deployment, biological experimentation and intervention
recommendations are outside this implementation.

## License

Apache License 2.0. The repository's original license is retained.

## ResearchOS / TECT concept integration

The [ResearchOS / Topological Epistemic Control Theory technical concept paper](docs/researchos/TECT_WHITE_PAPER.md) proposes an epistemic control and assurance infrastructure for AI-generated knowledge. Read the [repository integration status](docs/researchos/INTEGRATION.md) and [machine-readable scope](docs/researchos/integration.json) for the boundary between the concept and implemented capabilities. Performance targets are research objectives, not achieved results. This documentation addition does not implement the complete ResearchOS architecture or change operational authority.

## ResearchOS / TECT assurance layer

This repository includes the shared v0.1 research controller, a scoped executable domain pilot, replayable evidence/decision bundles, adversarial regression probes, and explicit unassured outcomes. See [the workflow](docs/RESEARCHOS.md), [versioned semantics](docs/TECT_SPEC.md), and [research-program traceability](docs/TECT_RESEARCH_PLAN.md). Existing domain results retain their documented limits. No claim state authorizes external or clinical execution.

## Portfolio implementation boundary

See [current implementation and shared-core integration](docs/portfolio/INTEGRATION.md) and [machine-readable status](docs/portfolio/STATUS.json). Independent empirical reproduction and real-provider acceptance remain separate from software checks.
