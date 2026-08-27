# `ExecConfig` schema

`harbor exec --config FILE` accepts YAML, JSON, or TOML. The top-level model is
strict: unknown fields are rejected. The canonical shape is:

```yaml
schema_version: "1.0"
map:
  compile: ...
  job: ...
reduce:                 # optional
  task: ...
  job: ...
```

`map` is required. `reduce` is optional. If `reduce` is present,
`map.compile.artifacts` must be non-empty because the executor needs those
artifacts as the reducer's implicit input set.

## Top-level and phase models

| Model | Fields |
| --- | --- |
| `ExecConfig` | `schema_version` (default `"1.0"`), `map`, `reduce` (`null` by default) |
| `ExecMapConfig` | `compile`, `job` (default `ExecJobConfig`) |
| `ExecReduceConfig` | `task`, `job` (default `ExecJobConfig`) |
| `ExecReduceTaskConfig` | `task_name` (default `reduce`), `output_dir` (required), `task_template`, `instruction` (required), `artifacts`, `environment`, `verifier` |
| `ExecReduceEnvironment` | `docker_image` (default `ubuntu:latest`), `workdir` (default `/app`) |

The `Exec*` models use `extra="forbid"`. Do not put ordinary `JobConfig`
source fields such as `tasks`, `datasets`, or `artifacts` under `map.job` or
`reduce.job`; artifacts belong to the compile/task sections. Do not add a
workflow-level `name` or `output_dir`.

## `map.compile`

`map.compile` is a `CompileConfig`:

| Field | Meaning |
| --- | --- |
| `schema_version` | Compile schema version, default `"1.0"`. |
| `dataset_name` | Optional compiled dataset/task-set name. |
| `task_name_prefix` | Optional prefix for generated task directories. |
| `output_dir` | Directory where compiled tasks are written. The executor/compiler requires this to be available by execution time. |
| `instructions` | List of instruction variants. Each item is `{text: "..."}` or `{path: "prompt.md"}`; strings are coerced to text items. `text` and `path` are mutually exclusive per item. |
| `task_template` | Optional task-template directory copied into each compiled task. |
| `artifacts` | List of container paths or `ArtifactConfig` objects to collect. |
| `environments` | List of environment variants; each can use `path` **or** `paths`, not both. Empty means the default environment. |
| `verifiers` | List of verifier variants; each uses `path` **or** `auto_verifier`, not both. Empty means no compile-generated verifier. |

The compiler takes the cross-product of instruction, environment, and verifier
variants. Thus two instructions and three environments can create six tasks.
An environment with `paths` copies files/directories/glob matches into the
task's environment. A `path` copies an existing environment directory instead;
it cannot be combined with `paths`.

Example map section:

```yaml
map:
  compile:
    task_name_prefix: label
    output_dir: exec/label/tasks
    instructions:
      - path: prompts/label.md
    artifacts:
      - /app/result.json
      - source: /app/report.json
        destination: report.json
        exclude: []
    environments:
      - docker_image: python:3.12
        workdir: /app
        paths:
          - inputs/*.json
    verifiers:
      - auto_verifier:
          required_artifacts:
            - /app/result.json
    # task_template: templates/base-task
```

### Artifacts and explicit destinations

A string artifact is a container source path. Use an object when collection
needs host-side placement or other artifact behavior:

```yaml
artifacts:
  - /app/result.json
  - source: /app/reports
    destination: reports
    exclude:
      - "*.tmp"
  - source: /app/compose-report.json
    destination: compose/report.json
    service: worker
```

`ArtifactConfig` fields are `source` (required), `destination` (optional),
`exclude` (list, default empty), and `service` (optional). The source must not
contain `..`. A destination is relative to the trial's artifact directory; it
must use forward slashes, cannot be absolute, cannot contain `..`, and cannot
be the reserved `manifest.json`. A non-`main` service requires a compose-capable
environment and an absolute source path. These are collection semantics, not
paths for the agent to write: the agent should still write to the container
`source` path.

### Compile verifiers

A verifier item has exactly one source:

```yaml
verifiers:
  - path: templates/tests
  - auto_verifier:
      required_artifacts:
        - /app/result.json
      reward_artifact: /app/scores.json
      artifact_json_schemas:
        /app/result.json: schemas/result.schema.json
```

`auto_verifier.required_artifacts` is optional. If omitted, the compiler uses
the configured artifact sources (and adds `reward_artifact` if needed). In the
common flags-generated form it is an existence-only check. `reward_artifact`
is validated and promoted only after required-artifact checks succeed.
`artifact_json_schemas` is a map from artifact path to schema file and is
available in config mode when richer generated checks are wanted.

## `map.job` and `reduce.job`

Both are `ExecJobConfig` instances:

| Field | Default / constraint |
| --- | --- |
| `job_name` | Optional; flags mode supplies timestamped phase names when omitted. |
| `jobs_dir` | Optional; flags mode resolves to `jobs`. |
| `n_attempts` | `1`, minimum `1`. Attempts per task in that phase. |
| `n_concurrent_trials` | `4`, minimum `1`. |
| `quiet` | `false`. |
| `retry` | `RetryConfig`; use the normal Harbor retry fields. |
| `environment` | `EnvironmentConfig`; provider/type and provider kwargs. |
| `verifier` | `VerifierConfig`; execution-time verifier controls. |
| `metrics` | List of `MetricConfig`. |
| `agents` | List of `AgentConfig`, defaulting to one default agent. Harbor's job validation checks agent concurrency against `n_concurrent_trials`. |

A job section configures execution only. It does not own `tasks`, datasets, or
compile artifacts; the executor supplies the compiled task paths internally.
Config mode does not merge CLI flags into the file: make each phase's values
complete in the file.

## `reduce.task` and implicit map inputs

A reducer is one `ExecReduceTaskConfig`, not a second scanned task set. Its
`instruction` is one `{text: ...}` or `{path: ...}` object. Its `environment`
contains only image and workdir because the executor injects map artifacts.
`reduce.task.artifacts` and `reduce.task.verifier` describe outputs produced by
the reducer itself.

At execution time:

1. The map job runs and returns trial results.
2. For every map trial with an `artifacts` directory, the executor copies that
   directory into a temporary staging tree named with a 1-based ordinal and a
   slugified trial name, such as `0001-map-trial`.
3. It compiles exactly one reducer task and copies the staging tree into that
   task's environment as `artifacts/`.
4. With the default `/app` workdir, the reducer reads inputs below
   `/app/artifacts/0001-map-trial/` (and subsequent ordinal directories).
5. Missing per-trial artifact directories are skipped. If all map trials lack
   artifacts, reduction fails with `Cannot reduce a map job with no trial
   artifacts.` A map job with no trial results fails earlier.

The map artifact list is the eligibility gate, not a guarantee that every trial
produced an artifact. Keep reducer instructions explicit about the staged
layout and output a reducer artifact under the reducer workdir.

## Minimal complete config

```yaml
schema_version: "1.0"
map:
  compile:
    output_dir: exec/tasks
    instructions:
      - text: "Read the supplied input and write /app/notes.json."
    artifacts:
      - /app/notes.json
    environments:
      - paths:
          - inputs/topic.md
    verifiers:
      - auto_verifier:
          required_artifacts:
            - /app/notes.json
  job:
    jobs_dir: exec/jobs
    agents:
      - name: claude-code
        model_name: anthropic/claude-sonnet-4-5
    environment:
      type: docker
reduce:
  task:
    output_dir: exec/tasks
    instruction:
      text: "Read /app/artifacts/*/notes.json and write /app/summary.json."
    artifacts:
      - /app/summary.json
    verifier:
      auto_verifier:
        required_artifacts:
          - /app/summary.json
  job:
    jobs_dir: exec/jobs
    agents:
      - name: claude-code
        model_name: anthropic/claude-sonnet-4-5
    environment:
      type: docker
```

Use the bundled recipes in [`map-reduce-recipes.md`](map-reduce-recipes.md) as
shape examples; replace their model, paths, and instructions for the caller's
run. Always validate with `harbor exec --config FILE --print-config` first.
