# Validation contracts

This reference turns ClawBio's report, benchmark, action, and replay behavior
into observable gates. The source project has many independent skills, so a
field is a contract only when the selected skill documents and emits it; do not
invent a universal output schema from a single example.

## Evidence and replay

For a completed skill run, inspect the skill's declared outputs first. Where the
workflow supports them, the useful evidence bundle is:

- a human-readable `report.md` (or the skill's documented report name);
- a structured `result.json`, with a documented `status`/`ok` field when that
  skill uses the shared envelope;
- the input checksum and method/version metadata;
- `reproducibility/commands.sh` for replay, plus `environment.yml` or a stricter
  lock artifact when emitted; and
- `reproducibility/checksums.sha256` for the selected output files.

The shared reproducibility helpers deliberately do not promise identical output
for every skill. Replay still needs the original inputs and external tools,
and a replay into a non-empty directory can create suffixed artifacts. A
checksum mismatch is evidence to investigate tool versions, inputs, and output
contamination; it is not permission to ignore the mismatch.

`sha256_file` produces a full 64-character SHA-256 digest. `sha256_hex` is a
short display digest and is not interchangeable with a full verification
record. `write_checksums` writes `sha256  relative-or-file-label` lines and
silently omits paths that do not exist. Therefore, before claiming that a
bundle is complete, independently confirm every required artifact exists; an
empty or partial checksum file proves only what it lists.

The shared report footer must contain this exact boundary:

> ClawBio is a research and educational tool. It is not a medical device and does not provide clinical diagnoses. Consult a healthcare professional before making any medical decisions.

A report missing the required disclaimer fails the report-safety check even if
its computation completed.

## Audit and discrepancy evidence

The local audit helper writes JSONL records for point events, `skill_run` spans,
and child `execute_tool ...` spans. A successful span has an OK status; an
exception or non-zero subprocess records an error status and is re-raised. Audit
writes are best-effort and may be ignored on an operating-system error, so an
absent audit file is a missing observability artifact, not proof that nothing
ran. Callers must scrub patient identifiers, sample IDs, raw inputs, secrets,
and sensitive paths before passing attributes or command tokens to the logger.

Contract alerts are sanitized, schema-tagged records about route, input, state,
policy, or version discrepancies—not biomedical findings. The preferred local
JSONL locations are the run output directory's `contract_alerts.jsonl` or the
local fallback log for pre-run alerts. The logger must not make a run fail.
Never store raw file contents, genomic values, tokens, API keys, or unredacted
request payloads in an alert. `blocking: true` is information for the emitting
component; adapters render the alert but do not enforce the block themselves.
The skill or planner must withhold actions, wait, or expire the state.

## PASS, SKIP, and FAIL

Classify each case explicitly:

| Status | Meaning | Required evidence |
|---|---|---|
| `PASS` | Required work was attempted and completed with the declared outputs, schema, and acceptance checks. | Exit/status success, required artifacts present, and no unresolved required condition. |
| `SKIP` | Work was intentionally not attempted because it is optional or ineligible here (for example unavailable GPU, network, heavy dependency, or credential). | A named reason, scope, and recovery or alternate environment. |
| `FAIL` | Required work was attempted but errored, timed out, regressed, produced malformed/missing required evidence, or violated a safety gate. | Error, non-zero exit, missing artifact, regression, or violated policy recorded. |

A top-level report may be green only when every required case is PASS. It may
list optional SKIP cases, but each skipped case remains SKIP and must never be
counted as a pass or silently folded into a rate. A required unavailable GPU or
external service is a verification block, not a CPU pass. A timeout of attempted
required work is FAIL; only a pre-declared optional capability may be SKIP.
"Not tested", "unknown", and "no report" are not synonyms for normal,
negative, or PASS.

A correctly rejected stale action is an expected safety behavior, not an
analysis PASS: report it as a handled `expired` outcome in the contract-test
record and keep scientific result status separate.

## Baseline comparison

`scripts/check_bench_baseline.py` is a regression gate, not a claim that the
current benchmark is perfect. It uses the committed harness rates and a 0.05
point tolerance. It fails when a baseline harness disappears, has no
`pass_rate`, drops beyond tolerance, or (when baseline errors are tracked) its
harness errors increase. A missing report, malformed report, or malformed
baseline returns a distinct fatal status. Existing below-100% debt can remain in
the baseline, so "no regression" must not be reported as "all scientific cases
passed".

When parsing a baseline report, preserve per-harness status, pass rate, and
error counts. Do not discard error entries merely because another harness
passed. If an intentional baseline change is made, require a reviewable update
and explanation rather than weakening the gate in code.

## AD gene and variant scorer

The benchmark fixture groups positive genes into tier 1 causal, tier 2
GWAS-replicated, and tier 3 novel-Bellenguez sets, and separately defines
negative controls. Its scorer:

- de-duplicates submitted genes through a set;
- reports true positives by tier, false positives only from the negative set,
  and unknown genes separately (unknown genes are tracked but do not count as
  false positives in this fixture);
- computes recovery/recall, precision, F1, false discovery rate, and a weighted
  score with tier weights 3, 2, and 1;
- compares minimums of 0.5 recovery, 0.7 precision, and 0.6 F1 for its
  `passes_minimum` field; and
- can score lead-variant recovery by `rsid` independently of gene recovery.

A scorer PASS means only that the submitted identifiers met this fixture's
configured thresholds. It does not prove a pipeline's biological validity,
clinical utility, or current literature truth, and it must not be used to make a
patient-level claim. Always preserve the tier breakdown, unknown list, and
false-positive list with the score.

## Fine-mapping and swappable methods

The synthetic fine-mapping benchmark generates one seeded locus with injected
causal indices, runs selected registered methods, scores causal capture,
PIP concentration, credible-set precision/recall/F1, rank, and a composite,
and chooses the highest-scoring valid method. A method exception is recorded as
an error and does not qualify as a winner; no valid winner is a failed run.
An unknown method may be reported as skipped by the runner, but that method's
absence must remain visible and cannot be counted as passing. Preserve the seed,
method list, errors, and winner when comparing runs.

Synthetic benchmark success checks algorithm plumbing against known injected
signals. It is not a substitute for validation on appropriately documented
real data, and it supplies no clinical conclusion.

## Mock and offline API testing

`tests/benchmark/mock_api_server.py` supplies deterministic loopback responses
for Ensembl variation/VEP, GWAS Catalog associations, ClinPGx gene/drug calls,
and a health/404 route. Its context-manager and unit tests are useful for
request construction, response-shape, routing, and offline error handling.
A mock response proves only that a client handles the declared fixture shape; it
does not prove live-service availability, current database content, credentials,
or scientific correctness. Use synthetic or fixture identifiers only, bind to a
local interface, and keep real network jobs and benchmark-scale downloads out
of this validation route.

## Action and contract lifecycle

`workflow_state.lifecycle` is a UI vocabulary: `ready`, `busy`, `waiting`,
`disabled`, `error`, and `expired`. The skill owns the meaning of
`state_schema`, `state_id`, and `state_label`; the runner does not invent
transitions. A state-aware action request must carry its schema and expected
`state_id`, plus enough compact data, artifact references, or durable resource
identifiers for revalidation without hidden chat memory.

Each offered action requires a stable `action_id`, label, and nested structured
`request`. A `shell_line` or prose-only suggestion is not executable and must
not be offered. Action selection is dispatched through the normal runner input
path. On state mismatch, the skill should return a normal result with
`lifecycle: expired`, a safe explanation, no unsafe follow-up, and exit 0; the
contract check should still record that it was a stale rejection rather than a
scientific success.

Normalize alerts against `clawbio.contract_alert.v1`; keep severity, kind,
message, sanitized evidence, remedies, and blocking state. Valid alert kinds
include input/route mismatch, missing required slots, unregistered skill,
security skip, runner mismatch, state mismatch, version drift, missing input,
and remote-execution consent. Unknown or malformed alerts are dropped, not
trusted as instructions.
