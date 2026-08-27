# Job and trial configuration

This reference is the execution-side contract for Harbor's two primary
configuration models. Use it before starting a costly or credentialed run.
The task, dataset, adapter, and verifier must already be valid; authoring them
belongs to `author-benchmarks`.

## Concepts and expansion

- A **task** is one instruction, environment, and verifier.
- A **dataset** resolves to an ordered collection of task configurations.
- A **trial** is one agent attempt on one task and produces a trial result.
- A **job** is a planned collection of trials. A normal job expands
  `tasks/datasets × agents × n_attempts` into `TrialConfig` objects and runs
  the pending trials through bounded concurrency.
- A job normally writes `config.json`, `lock.json`, `result.json`, and one
  child directory per trial under `jobs_dir/job_name`. A trial writes its own
  config/lock/result plus agent, verifier, log, trajectory, and artifact data
  as available.

Do not confuse `n_attempts` with retries. `n_attempts` deliberately creates
independent attempts in the evaluation matrix. `retry.max_retries` retries a
failed trial execution according to exception policy and backoff.

## Job input modes

Choose exactly one primary job source at the CLI boundary:

```bash
# one local task or a directory containing local tasks
harbor run --path ./tasks/hello-world --agent <agent> --model <model>

# one registry/package task
harbor run --task <org>/<task>[@ref] --agent <agent> --model <model>

# a registry/package or local dataset
harbor run --dataset <dataset-or-package>[@version-or-ref] \
  --agent <agent> --model <model>
```

`--path` accepts a task directory or dataset directory. `--task` selects one
registry/package task. `--dataset` resolves a dataset and can be narrowed with
`--include-task-name` (glob patterns), `--exclude-task-name`, and
`--n-tasks`. Do not combine `--path`, `--task`, and `--dataset`. A job config
may contain multiple `tasks` and/or `datasets` when using a config file, but
there must still be a coherent resolved plan.

A local `DatasetConfig` uses `path`. A package task or dataset uses `name` and
optional `ref`; a registry dataset uses `name` and optional `version`, with
optional `registry_url` or `registry_path`. Git-backed tasks use `path` plus
`git_url` and optional `git_commit_id`. Keep package refs/commits pinned when
reproducibility matters.

## `JobConfig` essentials

A YAML/JSON config consumed by `harbor job start --config FILE` (or
`harbor run --config FILE`) follows `JobConfig`. The high-value fields are:

```yaml
job_name: smoke
jobs_dir: jobs
n_attempts: 2
n_concurrent_trials: 4
agents:
  - name: claude-code
    model_name: anthropic/<model>
    n_concurrent: 2
tasks:
  - path: ./tasks/hello-world
environment:
  type: docker
retry:
  max_retries: 1
  min_wait_sec: 2
  max_wait_sec: 30
artifacts:
  - /logs/artifacts
extra_instruction_paths: [./run-notes.md]
extra_instructions: ["Use the provided test command."]
```

Important job fields:

- `job_name`, `jobs_dir`: result identity and parent storage directory.
- `agents`: repeatable `AgentConfig` entries. A separate `--model` flag is
  repeatable and creates one agent configuration per model for an ad hoc job.
- `tasks`, `datasets`: resolved task sources.
- `n_attempts`: independent attempts per expanded trial.
- `n_concurrent_trials`: global trial concurrency; it must be at least one.
- `AgentConfig.n_concurrent`: optional per-agent execution cap, no higher than
  the global cap. Agents in one `concurrency_group` must use the same cap.
- `retry`: `max_retries`, optional `include_exceptions`, optional
  `exclude_exceptions`, and exponential-backoff bounds. Exclusions take
  precedence over inclusions.
- `timeout_multiplier` and phase-specific multipliers: defaults for task
  timeouts; phase-specific values override the general multiplier.
- `environment`, `verifier`, `artifacts`, extra instructions, metrics, and
  optional simulated-user configuration.
- `install_only`: perform agent setup/install and skip agent execution and
  verification. This is a compatibility/preparation check, not an evaluation
  and has no score.

The config model validates cross-field constraints before job creation. For
example, an agent concurrency cap cannot exceed `n_concurrent_trials`, and a
regrade source cannot be combined with `install_only`.

## Layering and dry validation

Use a config file for a reproducible baseline and CLI flags for an intentional
run-specific override. The CLI applies supplied flags **after** loading the
config. Do not assume a flag merges lists: flags such as `--agent`, repeated
`--model`, and `--artifact` can replace the corresponding ad hoc collection.
Inspect the resolved result rather than reasoning from the input files alone.

```bash
harbor job start --config ./job.yaml --print-config
# equivalent public shortcut for an actual local run:
harbor run --config ./job.yaml --print-config
```

`--print-config` validates and prints the resolved `JobConfig` without
starting a job. Use it to confirm task source, agent/model matrix,
concurrency, retries, timeouts, environment, verifier, artifacts, and
trajectory fields. Confirm host environment access and credentials only after
this stage. For a hosted launch, use `--launch --dry-run`; it resolves tasks,
owner/secret selections, and trial count without queueing or consuming quota.

Do not use `--launch` and `--upload` together. `--launch` runs on Harbor-managed
infrastructure; `--upload` runs locally and uploads the completed job.
Hosted launch also rejects the local-only `--n-concurrent-agents` option.

## Single-trial configuration

Use `harbor trial start` to isolate one task/configuration:

```bash
harbor trial start --path ./tasks/hello-world \
  --agent claude-code --model <model> \
  --trials-dir ./trials --trial-name smoke

harbor trial start --config ./trial.yaml
```

A trial needs `--path` or a complete YAML/JSON `TrialConfig`. `TrialConfig`
requires `task`, where `task` is one of:

```yaml
task:
  path: ./tasks/hello-world
# or a Git task:
# path: ./task-subdirectory
# git_url: <git-url>
# git_commit_id: <commit>
# or a package task:
# name: org/task
# ref: <tag-or-digest>
```

A trial's high-value fields are `trial_name`, `trials_dir`, `agent`,
`environment`, `verifier`, `artifacts`, extra instructions, phase timeout
multipliers, and optional `job_id`. If no name is provided Harbor generates a
name from the task plus a short unique suffix. `--agent-timeout` and
`--verifier-timeout` set explicit seconds; job/trial multipliers scale task
phase defaults, and max timeout fields cap the effective value.

CLI overrides mutate the loaded model. For example, `--agent-kwarg key=value`
updates `agent.kwargs`, `--environment-kwarg key=value` updates
`environment.kwargs`, and repeatable `--verifier-env KEY=VALUE` updates the
verifier environment. `--init` is a config-building operation and does not
run the trial.

## Retries, cancellation, and resume

Use retry settings for transient execution failures, not to conceal a bad
agent, verifier, credential, or provider setup. The default exclusion set
includes agent/verifier timeout, missing/empty reward, verifier parse errors,
API usage/authentication/model errors, and safety refusal classes; inspect the
installed model's defaults before changing it. Add explicit include/exclude
sets when the experiment requires a different policy and record that choice.

`harbor job resume --job-path ./jobs/<job-name>` resumes an interrupted job
from its persisted config and lock. It reconciles completed trial configs and
runs only remaining work. By default it removes child trials whose recorded
error type is `CancelledError` before rebuilding the plan; pass repeated
`--filter-error-type` options deliberately when changing that cleanup policy.
The config and resolved lock must still match. A completed job is not silently
restarted, and there is no generic `harbor trial resume` command.

For one trial, create a new trial with trajectory loading, or use
`harbor trial handoff` when the agent supports local handoff. Do not copy a
job directory over an existing result and call it resume; preserve the source
and let Harbor validate locks.

## Regrade is a derived config

`JobConfig.source_jobs` and `TrialConfig.source_trial` describe a regrade
rather than a normal execution matrix. Regrade creates fresh output and runs
only a replacement verifier against recorded artifacts; it never reruns the
agent. Use the dedicated commands and the constraints in
[`trajectory-lifecycle.md`](trajectory-lifecycle.md). For task/dataset
creation or verifier authoring, route to `author-benchmarks`.
