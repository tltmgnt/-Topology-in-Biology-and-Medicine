# Research contracts and implementation boundaries

## Accepted domain

A dataset is one explicit context and a finite typed network. Node kinds are gene,
protein, process and phenotype; these are descriptive categories, not a clinical
ontology. Context consists of exact organism, system and condition strings. The
software does not reconcile aliases, determine species, infer tissue compatibility
or validate biological meaning.

Regulatory edges are directed with supplied positive, negative or unknown signs.
Association edges must be unknown-sign and contribute undirected adjacency only to
weak-component analysis. Regulatory reachability never traverses associations.
Parallel regulatory edges and self-feedback are valid. Node and edge IDs are unique
within their own namespaces; evidence IDs are unique in theirs. All endpoints must
exist, but absent evidence references are assessed as gaps.

## Evidence checks and assessment time

Every evidence record contains actual nonempty inline base64 bytes with a declared
lowercase SHA256, source, declared kind/group, exact context and aware observation /
expiry timestamps. Allowed kinds are synthetic, experimental, computational and
literature; they are not verified evidence codes or scientific quality scores.

At requirements.as_of, each artifact is checked for content agreement, exact
context agreement, observation <= as_of, and as_of < expiry. These checks yield
CHECKED or NOT_CURRENT with CONTENT_MISMATCH, CONTEXT_MISMATCH, FUTURE_OBSERVATION
and/or EXPIRED. A CHECKED record may still contain false or irrelevant content.
The explicit cutoff is used for deterministic replay; no claim of present-day
currency is made. Change as_of and rerun to assess another time.

Every selected edge evidence reference must exist and be CHECKED. Distinct declared
provenance-group strings and distinct checked content hashes must each meet the
minimum (integer 1–16). Duplicate bytes do not become independent content merely
because their IDs or group names differ; two files with different bytes still may
share data or methods. These are two separate count requirements, not statistical
independence estimation or authenticated replication.

An edge that passes is EVIDENCE_QUALIFIED; it means only these software checks
passed. BLOCKED edges generate EDGE_EVIDENCE_GAP unless explicitly EXCLUDED by
scenario policy. Exclusion does not verify evidence, erase diagnostics or simulate
an experiment. Invalid unreferenced records remain visible but are not used as
support and do not independently create gaps.

## Topology and walk semantics

Two topology views are computed: declared non-excluded edges and qualified edges.
Both retain the full node inventory so isolated entities do not disappear when
support is lost. Weak components use both kinds; SCCs and cycles use only directed
regulatory edges. Analysis is deterministic by ID order.

A product state is `(entity, accumulated sign)` with positive as the initial identity.
Known signs multiply algebraically; unknown absorbs any subsequent sign. A breadth-
first search explores at most three product states per entity and returns one
minimum-hop witness for each reached target sign. Witnesses can revisit entity IDs
with different accumulated signs. No continuous dynamics, reaction kinetics, time
course, expression magnitude, causal effect or biological mechanism is estimated.

A specific expected sign passes only if present with neither unknown nor the opposite
known sign. `any` accepts any nonempty qualified-sign set, including ambiguity.
Association-only connectivity cannot satisfy a regulatory-walk requirement.
SCC membership or a signed cycle does not establish biological feedback behavior.

## Gap semantics

| Code | Meaning in supplied inputs |
|---|---|
| MISSING_REQUIRED_NODE | Required ID absent from the entity inventory |
| EDGE_EVIDENCE_GAP | Non-excluded edge fails the declared evidence-input policy |
| MISSING_ENDPOINT | Required regulatory walk endpoint absent |
| NO_DECLARED_REGULATORY_WALK | No regulatory walk after explicit exclusions |
| NO_EVIDENCE_QUALIFIED_WALK | Declared regulatory connection exists but qualified edges cannot establish it |
| EXPECTED_SIGN_NOT_SUPPORTED | A qualified walk exists but none has the expected sign |
| AMBIGUOUS_SIGN | Both known parities reach the target for a specific-sign requirement |
| UNKNOWN_SIGN | An unknown-parity walk reaches the target for a specific-sign requirement |

Required-node coverage measures presence only and is null for a path-only requirement
set. It does not measure evidence coverage. Overall DECLARED_CHECKS_SATISFIED requires
no listed requirement or non-excluded edge-evidence gaps. It is not a statement of
scientific correctness, source completeness, readiness for clinical decisions or
regulatory approval. Neither missingness nor a failed walk establishes biological
absence. Requirements never authorize actions.

## Exact validation and bounds

Root and nested objects require exact documented fields. Unknown fields are rejected.
Schema versions are integer 1, not booleans. Names are trimmed 1–160 character strings.
Identifier arrays are unique and bounded. Missing required node IDs are legal; unknown
excluded edge IDs are malformed scenario configuration. At least one required node
or walk is mandatory. Required walks have distinct endpoints and unique IDs.

Limits: 128 nodes, 512 edges, 256 evidence records, 32 required walks. Evidence is
bounded to 64 KiB per decoded artifact and 1 MiB total. Input/output files are at
most 4 MiB each. Regular UTF8 files with optional BOM are accepted; duplicate JSON
keys, nonfinite numbers and nesting beyond 64 levels are rejected. Read metadata is
compared before and after bounded reads. No network or source retrieval occurs.
These checks are not an authentication boundary against a privileged file writer.

The product-graph walk search has O(V+E) work up to its fixed three-sign expansion.
SCC analysis uses bounded mutual reachability, approximately O(V*(V+E)). It is a
transparent regional research-scale implementation, not a large omics pipeline.
Output-size checks can reject reports with unusually long witness/label combinations
even when individual input limits pass.

## Reproducibility and reporting

Reports include engine/schema versions, source fingerprints, cutoff/policy, all
artifact and edge checks, both topology views, witnesses and explicit limitations.
Canonical JSON sorts object keys but retains array order and numeric representation;
input whitespace is not retained. No current clock, randomness or model API affects
a report. Future output-changing versions may require replay with the original
software version; no migration or cross-version compatibility is promised.

A bundle has exactly five files. Verification requires bounded regular files,
rejects bundle-directory and file symlinks, regenerates all expected content from
captured inputs, and compares bytes. Edited analysis cannot be hidden by updating
its checksum manifest. A complete replacement/regeneration of inputs creates a
new consistent study; use externally trusted fingerprints or signatures if source
authenticity is required.

Existing output directories are preserved. New directory creation is exclusive;
handled write failures remove the new partial directory. Abrupt termination can
leave an incomplete directory, which verification rejects. Parent directories must
exist. Concurrent hostile modifications are not a supported operating model.

The HTML is self-contained, escaped and script-free. All captured evidence and
context remain in the dataset; report metadata includes source/group identifiers.
Do not put patient data, private biomedical records or confidential network details
in public repositories, issues or public CI artifacts. Only fictional fixtures ship
with this repository. No clinical-use approval, biological experiment, treatment
recommendation or consequential execution is implemented.

## Scenario comparisons

Comparison verifies both bundles and requires the same captured dataset. It reports
new/restored exclusions, changed qualifications and gap deltas. `assessment_policy_changed`
flags changes to cutoff, provenance threshold or requirements separately from edge
exclusions. A change in graph support is not evidence of an intervention's real-world
effect. Excluding weakly supported edges can remove an edge-quality gap while losing
coverage; inspect the complete report rather than counting gaps as a benefit score.
