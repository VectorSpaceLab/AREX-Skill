# Results, artifacts, and trajectories

## Result inventory

A local job is the aggregate directory; a trial is one task execution beneath
it. Confirm the directory type from its files rather than its name:

```text
job/
├── config.json                 # requested job configuration
├── lock.json                   # resolved task/agent/environment inputs
├── result.json                 # aggregate counts, rewards, costs, errors
├── job.log
└── <trial>/
    ├── config.json
    ├── lock.json
    ├── result.json             # TrialResult: identity, reward, exception, timing
    ├── trial.log
    ├── agent/                  # Harbor ATIF and agent logs/sessions
    ├── verifier/               # test stdout/stderr and reward files
    └── artifacts/
        ├── manifest.json
        └── ...
```

Multi-step trials place per-step `agent/`, `verifier/`, and `artifacts/` under
`steps/<step-name>/`; do not assume root-level artifacts exist after cleanup.
Use `result.json` as the structured source of truth. Inspect at least:

- `task_name`, task checksum/id, trial name/id, source, agent name/version,
  model/provider, requested and resolved config/lock;
- `verifier_result.rewards` (possibly several numeric keys),
  `verifier_environment_mode`, timing, and token/cost fields;
- `exception_info` including exception type/message and whether the attempt was
  cancelled, timed out, or failed before verification;
- `step_results` for multi-step rewards and exceptions; a missing verifier result
  is not the same as a zero reward.

At job level distinguish `n_total_trials`, completed/running/pending/errored/
cancelled counts, retry count, per-agent/dataset reward distributions, token
counts, and cost. Do not average retries as independent benchmark trials when
the question concerns final task performance: compare latest attempts and report
retry history separately.

## Artifact inspection

Read `artifacts/manifest.json` before opening artifact bytes. Each entry records
`source`, host-relative `destination`, `type`, `status`, and optional Compose
`service`. `ok` is usable; `failed`, `empty`, and `skipped` are evidence gaps.
The convention directory `/logs/artifacts/` is collected under
`artifacts/logs/artifacts/`. Configured absolute sources are mirrored below the
artifact root unless an explicit safe relative destination was requested.
`manifest.json` is reserved and must not be shadowed. When two services export
the same source-derived host path, the first claimant is kept and the other is
recorded as skipped; do not silently treat the collision as valid evidence.

Artifact collection is best effort and does not itself fail a trial. For a
verifier or regrade, check that every declared input has an `ok` manifest entry
and that the corresponding bytes still exist. Read verifier stdout/stderr and
reward files together with the manifest: a reward can be syntactically valid
while the test output reveals a setup or partial-evidence failure.

## ATIF trajectories

Harbor writes a portable ATIF trajectory at `agent/trajectory.json` when the
agent supports ATIF. Validate a copied file before loading or exporting it:

```bash
python -m harbor.utils.trajectory_validator path/to/trajectory.json
# add --no-validate-images only when missing image files are an intentional
# external dependency and the limitation is recorded
```

ATIF is portable but conversion to another agent loses agent-specific session
state. Check schema version, agent metadata, sequential `steps` starting at 1,
tool-call/observation references, continuation references, and any referenced
image files. Embedded subagent trajectories need unique `trajectory_id` values;
resolve a `subagent_trajectory_ref` by that ID or by its external path, never by
`session_id` alone. A `continued_trajectory_ref` creates an ordered chain; follow
and validate every file before interpreting the full conversation.

Use `harbor traces export --path <trial-or-root>` to turn ATIF conversations
into a local Hugging Face-style dataset (all episodes by default, or
`--episodes last`). `--filter success|failure|all`, `--subagents`,
`--instruction-metadata`, and `--verifier-metadata` control the export. The
exporter skips unsupported/malformed/multimodal cases with explicit messages;
keep those omissions in the report. Use `--format otel --output file.jsonl`
or a protobuf directory for local OpenTelemetry output; `--endpoint` is an
external upload and is gated separately.

## Native sessions and loading

Native sessions live under `agent/sessions/` and are lossless only for the same
agent. Preserve the original filename when copying one for loading. An ATIF
file can be loaded by a compatible agent through `--load-trajectory`; a native
file is agent-specific. Loading restores conversation context, not files created
by the earlier run. Run-level `--load-trajectory` overrides a task-level
`trajectory.json`; task-level loading is ATIF-only. `--resume-trajectory` is a
multi-step execution setting that resumes later step sessions and is not the
same operation as loading an initial trajectory.

A finished trial can be handed off with `harbor trial handoff <trial-dir>` (or a
Hub trial UUID). This resumes a supported agent's local CLI session; it does not
restore the container filesystem. Today the support claim is agent-dependent;
check the installed agent capability before promising handoff.

## Analysis, retry, and regrade distinctions

- `harbor analyze <trial-or-job>` runs a rubric-driven evaluator over copied
  trial data and writes a new analysis job plus `analysis.json`; `--passing` or
  `--failing` filters by the primary reward. It does not change the source.
- `harbor check <task-or-task-root>` evaluates task quality and writes a check
  report/job; it is not a verifier result for an already-run benchmark.
- A Hub retry requeues a finished hosted attempt with the same job configuration.
  It spends execution/model resources and changes hosted job state. Preview with
  `harbor hub job trials <job-id> --failed-only` (and filters), then require
  confirmation or `--yes`; inspect later attempts with `--include-retries`.
- `harbor job resume` continues a local incomplete job and may rerun trials.
  It is not read-only and is distinct from inspecting a result.
- `harbor job regrade` / `harbor trial regrade` create a new result using saved
  agent logs and artifacts plus a replacement verifier. They never modify the
  source or rerun the agent. Current regrade requires a completed single-step
  source, a readable result and artifact manifest/bytes, and a separate-mode
  replacement verifier; multi-step regrade is unsupported.

For every comparison label data as original attempt, retry attempt, analysis
job, or regrade-derived result. Never overwrite the original `result.json` to
make a regrade or corrected score look like the recorded run.
