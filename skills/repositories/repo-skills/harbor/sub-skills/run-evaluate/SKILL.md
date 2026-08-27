---
name: run-evaluate
description: "Operate Harbor jobs and trials: resolve tasks, select
  agents/models/environments, configure execution, run locally or on hosted
  infrastructure, preserve artifacts and trajectories, and resume or hand off
  sessions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Run and evaluate Harbor workloads

Use this skill when the user wants to **execute** an existing Harbor task or
dataset, evaluate one or more agents/models, run a single trial, or recover an
interrupted execution. The task definition, dataset manifest, adapter, and
verifier must already exist or be resolvable. This skill operates the
evaluation; it does not author benchmark inputs and it does not perform
result analysis or framework extension work.

## Routing gate

Choose the smallest workflow before touching a command:

- **Create or repair a task, dataset, adapter, verifier, RewardKit check, or
  registry package:** route to `author-benchmarks`.
- **Compile arbitrary files into tasks or run map/reduce:** route to
  `exec-map-reduce`, not ordinary `run` flags.
- **Inspect, compare, view, export, upload, publish, or explain completed
  results/trajectories:** route to `analyze-publish`.
- **Implement or register a custom agent/environment/plugin/bridge/MCP
  integration:** route to `integrations`. Passing an already-implemented
  custom import path to a run is still covered here.

When a request mixes these surfaces, finish the smallest safe prerequisite
first and hand off the resulting path or config; do not duplicate the sibling
workflow. A task-side MCP server or skill directory belongs to the benchmark
configuration, while run-time `--mcp-config` and `--skill` injection is
execution configuration.

## First checks and safety gates

1. Confirm the installed command surface without assuming that the inspected
   source snapshot and installed distribution are identical:

   ```bash
   harbor --version
   harbor run --help
   harbor trial start --help
   ```

   If `harbor` is not on `PATH`, ask how it was installed rather than inventing
   an invocation. Older installs may omit newer commands or expose older
   trajectory semantics; prefer the live help and config-model validation.
2. Identify exactly one input mode for a job: `--path` for a local task or
   dataset, `--task` for one registry/package task, or `--dataset` for a
   dataset. Do not combine task and dataset flags. For a trial, use `--path`
   or a complete `--config`.
3. Before a costly or credentialed run, show the resolved agent, model,
   environment, task count, attempts, concurrency, timeout policy, output
   directory, network policy, and artifact plan. Use `--print-config` for a
   job config; it validates and prints without starting a job. A `--launch`
   dry run validates a hosted launch without queuing it.
4. Treat model keys, provider credentials, registry access, Docker/cloud
   daemons, network access, private images, and hosted quota as explicit gates.
   Never claim that a provider or model was executed merely because it appears
   in a factory enum or help panel. Do not expose secret values in YAML, logs,
   or a handoff.
5. Prefer a tiny local/CPU or install-only preflight when the user wants a
   compatibility check. `--install-only` performs agent setup/install, skips
   the agent run and verification, and is not a score-producing evaluation.

## Choose the execution shape

### One job: `run` / `job start`

Use a job for a task or dataset × agent/model × attempt matrix. The canonical
aliases are equivalent:

```bash
harbor run -p ./tasks/hello -a claude-code -m <model>
harbor run -d <org/dataset>@<ref> -a <agent> -m <model> -n 8
harbor job start --config ./job.yaml --print-config
```

`harbor run` is the public shortcut for `harbor job start`; a config file must
conform to `JobConfig` for a local run and to the installed hosted config model
when `--launch` is used. CLI flags are applied after a loaded config, so a
flagged value overrides the corresponding config value. `-m/--model` is
repeatable for jobs; each configured model becomes an agent configuration.

A job resolves datasets and task packages before creating trials. In the
ordinary (non-regrade) case it creates one `TrialConfig` for every task, agent
configuration, and attempt (`n_attempts`), then submits the remaining trials
through a bounded queue. Job results are written under `jobs_dir/job_name` and
trial directories are children of that job directory. The job and each trial
persist `config.json`, a resolved `lock.json`, logs, results, agent/verifier
outputs, and artifacts as applicable.

Useful job flags are grouped in the references:

- matrix and output: `--job-name`, `--jobs-dir`, `-k/--n-attempts`,
  `-n/--n-concurrent`, `--n-concurrent-agents`, `--quiet`, `--debug`;
- input: `-p/--path`, `-t/--task`, `-d/--dataset`, `--repo`, registry options,
  include/exclude task names, and `--n-tasks`;
- execution: `-a/--agent`, repeatable `-m/--model`, `-e/--env`, config files,
  timeout multipliers, resource overrides, `--artifact`, extra instructions,
  and verification controls;
- hosted/share gates: `--launch`, `--dry-run`, `--credential-mode`, secret
  grants, `--upload`, visibility, organization/user sharing.

Do not use `--launch` and `--upload` together. `--launch` moves execution to
Harbor-managed infrastructure; `--upload` runs locally and uploads the result
afterward. `--n-concurrent-agents` is a local-only per-agent cap and is
rejected for a hosted launch.

### One trial: `trial start`

Use a trial when isolating one task/agent/model configuration or debugging a
single rollout:

```bash
harbor trial start -p ./tasks/hello -a <agent> -m <model> \
  --trials-dir ./trials --trial-name smoke
harbor trial start --config ./trial.yaml
```

A trial requires `--path` or a YAML/JSON config. Its `TrialConfig.task` is a
`TaskConfig` identifying a local path, Git task (`path` plus `git_url` and
optional commit), or package task (`name: org/name` plus optional `ref`). A
trial's generated name is task-based plus a short unique suffix when no name
is supplied. Trial CLI flags modify the loaded model, including explicit
seconds for agent/verifier/setup timeouts and run-time trajectory loading.

`Trial.create()` resolves the task, selects `MultiStepTrial` when the task has
`[[steps]]`, otherwise `SingleStepTrial`, initializes the environment and
agent, then `run()` performs setup, agent execution, artifact recovery,
verification, final persistence, and teardown. A failed trial normally records
`exception_info` and returns a result; a cancellation is recorded and then
re-raised so the job can preserve cancellation state.

### Job/trial management commands

- `harbor job resume -p <job-dir>` continues a persisted local job; it does
  not restart completed trials.
- `harbor job download <job-uuid>` and `harbor trial download <trial-uuid>`
  materialize hosted archives locally and require platform authentication.
  `--overwrite` is an explicit replacement of an existing target.
- `harbor job share <job-uuid> --org <name>` or `--user <name>` mutates sharing
  on an already-uploaded job; require confirmation and Hub auth. General
  publishing, comparisons, and result browsing route to `analyze-publish`.
- `job summarize` and `trial summarize` are removed command shims in the
  current source surface; use `analyze-publish` for summaries rather than
  teaching a future agent a command that exits with an error.
- `trial handoff`, `job regrade`, and `trial regrade` are covered below and in
  [`trajectory-lifecycle.md`](references/trajectory-lifecycle.md).

## Job and trial lifecycle commands

Use the singular command groups exposed by the installed CLI:

- `harbor job start` is the config-oriented form of `harbor run`; use
  `--print-config` to validate without execution.
- `harbor job resume --job-path JOB_DIR` continues an interrupted job from
  its persisted config/lock. It is not an agent-session resume; see the
  trajectory reference.
- `harbor job download JOB_UUID --output-dir DIR` and
  `harbor trial download TRIAL_UUID --output-dir DIR` materialize credentialed
  Hub records locally. They do not execute an agent. Treat the downloaded
  directory as read-only until a deliberate derived operation is chosen.
- `harbor job share JOB_UUID --org ORG` or `--user USER` changes sharing on an
  already-uploaded job. It requires authentication and explicit sharing
  confirmation; never run it as part of a local evaluation.
- `harbor job regrade SOURCE ...` and `harbor trial regrade SOURCE ...` create
  new verifier-only derived outputs. They never rerun the agent and require
  the single-step/separate-verifier/artifact-manifest conditions described in
  [`trajectory-lifecycle.md`](references/trajectory-lifecycle.md).
- `harbor job summarize` and `harbor trial summarize` are removed compatibility
  shims in current Harbor. Use `harbor analyze` for completed-result
  inspection instead of relying on an old summarize command.
- `harbor trial start` runs one trial; there is no generic `trial resume`.
  Use `--load-trajectory` for a new seeded trial or `trial handoff` for a
  supported local CLI continuation.

Credentialed download/share operations and result inspection are normally
handed to `analyze-publish` after the execution choice is made. This skill
still records their execution gates so a run plan does not accidentally
relaunch or mutate a completed result.

## Configure, run, and hand off

Read the focused references progressively:

1. [`job-and-trial-config.md`](references/job-and-trial-config.md) for schemas,
   config layering, task expansion, retries, and resume.
2. [`agents-and-environments.md`](references/agents-and-environments.md) for
   factory selection, providers, agent options, and preflight.
3. [`resources-network-artifacts.md`](references/resources-network-artifacts.md)
   for resource policies, timeouts, network phases, artifacts, and logs.
4. [`trajectory-lifecycle.md`](references/trajectory-lifecycle.md) for
   multi-step sessions, loading, handoff, downloads, and regrade boundaries.
5. [`troubleshooting.md`](references/troubleshooting.md) for symptom-driven
   recovery before relaunching anything.

For multi-step execution, make the session policy explicit. By default each
step starts a fresh conversation. `resume_trajectory: true` changes the
sequence to `(fresh, resume, resume, ...)`, but only for agents that advertise
native resume support; a failure is intended to happen before environment
spend. `load_trajectory` seeds the first step, and can be combined with
resume. A native session is lossless but agent-specific; an ATIF JSON
trajectory is portable but converted and therefore not lossless. Only claim
handoff when the installed agent supports it and the trial has one session.

Use `harbor job resume --job-path <job-dir>` for an interrupted job. It reads
that job's `config.json`, reconciles completed trial configs, and continues the
remaining work. It rejects a changed config or mismatched lock and, by default,
removes trials whose recorded error type is `CancelledError`; pass repeated
`--filter-error-type` options deliberately if another cleanup policy is
wanted. A completed job is not restarted by accident. There is no generic
`trial resume` command: use trajectory loading, `trial handoff`, or a new
trial config.

Use regrade only when the intent is to recompute verification without rerunning
the agent. `harbor trial regrade` and `harbor job regrade` never modify the
source and require a completed single-step source with readable artifacts and
an artifact manifest; the replacement verifier must run in separate mode.
Multi-step regrade is unsupported. Route score inspection, comparisons, and
read-only result browsing to `analyze-publish` after the execution decision.

## Stop conditions

Stop before creating a job when the task/dataset cannot be resolved, the
resolved config is invalid, a required custom import cannot load, the selected
provider's preflight fails, a required model credential is absent, a required
backend is unsupported, or a network/resource policy cannot be enforced. Do
not paper over these with `--disable-verification`, a larger timeout, or a
provider fallback unless the user explicitly approves the changed experiment.

`--disable-verification` is an intentional no-score mode, not a fix for a bad
verifier. If the task itself, its tests, its registry metadata, or an adapter
must change, hand off to `author-benchmarks`.
