# Topology compatibility and curriculum v2 — -Topology-in-Biology-and-Medicine

Version 2 adapts the explicit-molecular-graph teaching pattern to this repository's actual role. This is documentation and a learning/decision framework; it introduces no mathematical engine, runtime dependency or operational permission.

## Repository decision

| Question | Repository-specific answer |
| --- | --- |
| Architectural role | specialized network tool |
| Minimum useful mathematics | Directed signed graphs with scoped evidence qualification |
| Relationships to preserve | Association/regulatory distinction, unknown signs, context and evidence validity |
| Concrete operation / capstone | Trace positive, negative and unknown-parity walks; expire one evidence item and recompute eligible structure |
| Necessity and scope boundary | A signed walk is not a causal effect; declared provenance groups do not prove independent replication or clinical validity |

The decision is a source-based recommendation, not measured proof that a new specialty improves this repository. Start with the existing implementation and compare any proposed abstraction against a simpler alternative.

## Six-criterion compatibility scorecard

Complete one scorecard per proposed candidate and per concrete operation. Leave unmeasured entries unknown. Scores are human judgments from 0 (no fit) to 5 (strong evidenced fit); unknown is not zero. Do not sum an incomplete card. A total out of 30 is a heuristic, not adoption approval, and feasibility or necessity can veto a high total.

| Criterion | Score | Required evidence |
| --- | --- | --- |
| Structural compatibility | Not yet scored | Map the repository objects and the relationships above without losing direction, labels, units or missingness. |
| Transformation support | Not yet scored | Demonstrate the capstone operation on accepted and rejected inputs. |
| Invariant preservation | Not yet scored | State the property preserved and supply a counterexample or perturbation. |
| Computational feasibility | Not yet scored | Measure size, time and memory on bounded fixtures; record limits. |
| Integration compatibility | Not yet scored | Verify existing schemas, APIs and neighboring contracts remain compatible. |
| Mathematical necessity | Not yet scored | Compare with directed signed graphs with scoped evidence qualification and explain the additional capability, if any. |

## Curriculum

Prerequisites: basic programming, sets, functions and graph vocabulary. Work in six competency-gated sessions, approximately 60–90 minutes each; empirical evaluation is a separate research activity.

| Session | Learning objective | Exercise | Completion evidence |
| --- | --- | --- | --- |
| 1. Model | Identify association/regulatory distinction, unknown signs, context and evidence validity. | Draw a minimal valid example and one excluded relationship. | Annotated object/relation inventory with explicit assumptions. |
| 2. Contract | Distinguish schema validity from substantive correctness. | Trace validation and propose malformed, missing and boundary inputs. | Input-to-rejection table grounded in current source. |
| 3. Operation | Explain directed signed graphs with scoped evidence qualification. | Trace positive, negative and unknown-parity walks; expire one evidence item and recompute eligible structure. | Hand trace compared with existing software, or a clearly labeled specification when no runtime exists. |
| 4. Preservation | State what a transformation must preserve. | Rename identifiers, reorder records, then alter one meaningful relation; predict each effect under the actual contract. | Separate invariant, expected change and unsupported transformation. |
| 5. Comparison | Justify mathematical necessity and cost. | Complete the six-criterion card for the existing approach and one proposed alternative; record unknowns honestly. | Evidence-backed recommendation with baseline and explicit veto conditions. |
| 6. Reproduction | Communicate the bounded result. | Reproduce the capstone using existing offline fixtures and record software version, inputs, outputs and limitations. | Reviewable notebook or report distinguishing computation, replay, independent evaluation and authorization. |

## Source-linked reading laboratory

The table is a guided selection of source lines, not an assertion that the whole repository is covered. Line numbers refer to the inspected source blob `e95b84a1661c967ae98e01a6d35dbd9aca63db9d` in [bio_topology/analysis.py](../../bio_topology/analysis.py). Recheck anchors after source changes.

| Line | Statement | Learning check |
| --- | --- | --- |
| [11](../../bio_topology/analysis.py#L11) | `def canonical(value):` | State the input/output contract and trace one normal and one failing case. |
| [12](../../bio_topology/analysis.py#L12) | `return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()` | Predict the returned value and distinguish a computed result from authorization. |
| [15](../../bio_topology/analysis.py#L15) | `def fingerprint(value):` | State the input/output contract and trace one normal and one failing case. |
| [16](../../bio_topology/analysis.py#L16) | `return hashlib.sha256(canonical(value)).hexdigest()` | Explain the exact bytes bound by the digest and why hashing does not authenticate the source. |
| [19](../../bio_topology/analysis.py#L19) | `def evidence_assessment(dataset, policy):` | State the input/output contract and trace one normal and one failing case. |
| [35](../../bio_topology/analysis.py#L35) | `return results` | Predict the returned value and distinguish a computed result from authorization. |
| [38](../../bio_topology/analysis.py#L38) | `def edge_assessment(dataset, policy, evidence):` | State the input/output contract and trace one normal and one failing case. |
| [61](../../bio_topology/analysis.py#L61) | `return results` | Predict the returned value and distinguish a computed result from authorization. |
| [64](../../bio_topology/analysis.py#L64) | `def regulatory_graph(dataset, edge_ids):` | State the input/output contract and trace one normal and one failing case. |
| [70](../../bio_topology/analysis.py#L70) | `return graph` | Predict the returned value and distinguish a computed result from authorization. |
| [73](../../bio_topology/analysis.py#L73) | `def multiply(left, right):` | State the input/output contract and trace one normal and one failing case. |
| [75](../../bio_topology/analysis.py#L75) | `return 'unknown'` | Predict the returned value and distinguish a computed result from authorization. |
| [76](../../bio_topology/analysis.py#L76) | `return 'positive' if left == right else 'negative'` | Predict the returned value and distinguish a computed result from authorization. |
| [79](../../bio_topology/analysis.py#L79) | `def signed_walks(graph, source, target):` | State the input/output contract and trace one normal and one failing case. |
| [82](../../bio_topology/analysis.py#L82) | `return {}` | Predict the returned value and distinguish a computed result from authorization. |
| [104](../../bio_topology/analysis.py#L104) | `return results` | Predict the returned value and distinguish a computed result from authorization. |
| [107](../../bio_topology/analysis.py#L107) | `def topology(dataset, edge_ids):` | State the input/output contract and trace one normal and one failing case. |
| [141](../../bio_topology/analysis.py#L141) | `return {'weak_components': components, 'isolated_nodes': sorted(node for node in weak if not weak[node]),` | Trace component bookkeeping on a disconnected example. |
| [146](../../bio_topology/analysis.py#L146) | `def build_report(data, requirements):` | State the input/output contract and trace one normal and one failing case. |
| [184](../../bio_topology/analysis.py#L184) | `return {'schema_version': 1, 'engine_version': ENGINE_VERSION,` | Separate type, shape and value checks; test a missing field and an invalid value. |
## Assessment and verification

A learner must explain the model, trace the capstone, identify a counterexample and state the scope boundary. Assess these four competencies equally; a numerical score cannot compensate for an unsupported scientific or operational claim.

Relevant existing checks:

- [tests/test_bio.py](../../tests/test_bio.py)
- [tests/test_researchos.py](../../tests/test_researchos.py)

Follow [README](../../README.md) for environment and installed-package instructions. Read scripts before execution; source-reading exercises do not authorize provider calls, model downloads, live orders, hardware actions or messages. Synthetic fixtures establish software behavior only. This documentation change does not report those exercises as already executed.

## Interoperability and adoption gate

Retain explicit domain contracts. Shared assurance records should refer to domain evidence and its assumptions rather than relabeling graph reachability, homology, statistical calibration and epistemic acceptance as interchangeable quantities. The canonical ResearchOs controller remains owned by ResearchOs; this curriculum does not create another controller fork.

Adopt additional mathematics only after a versioned experiment demonstrates a useful operation, the scorecard has evidence, the simpler baseline is inadequate and existing conformance checks remain satisfied. A signed walk is not a causal effect; declared provenance groups do not prove independent replication or clinical validity.
