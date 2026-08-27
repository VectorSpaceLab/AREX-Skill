# Map/reduce recipes

Use these as safe templates for constructing a workflow. They describe config
and preflight only; substitute an authorized agent/model, provider, and local
paths before execution.

## Recipe A: map only with explicit artifact

Prefer explicit artifacts whenever a later check or consumer depends on a
file:

```bash
harbor exec \
  --path inputs/topic.md \
  --no-scan \
  --instruction "Read topic.md and write a concise answer to /app/answer.md." \
  --artifact /app/answer.md \
  --tasks-dir exec/tasks \
  --jobs-dir exec/jobs \
  --agent AGENT_NAME \
  --model MODEL_NAME \
  --print-config
```

Inspect the printed JSON before removing `--print-config`. The path is copied
into the task environment, while `/app/answer.md` is a container-side output
path. `--no-scan` is intentional here: a single file is already non-scanning by
default, but the explicit choice protects the task cardinality if the input is
later changed to a directory.

## Recipe B: one map task per match

```bash
harbor exec \
  --scan \
  --path 'inputs/cases/*.json' \
  --limit 10 \
  --instruction "Read the JSON case and write /app/result.json." \
  --artifact /app/result.json \
  --workdir /app \
  --print-config
```

The CLI creates one compile environment per sorted match, de-duplicates
resolved paths across inputs, then applies the limit. A single glob also scans
by default, but explicit `--scan` makes the intended fan-out visible. A
 directory scan means immediate child directories, not all files recursively.

For multiple separate inputs, omission of `--scan` groups all paths into one
compile environment. Use explicit `--scan` when each discovered case must be a
separate map task.

## Recipe C: map plus reducer with output contracts

```bash
harbor exec \
  --path inputs/topic.md \
  --instruction "Read topic.md and write structured notes to /app/notes.json." \
  --artifact /app/notes.json \
  --reduce-instruction "Read the map artifacts under /app/artifacts and write /app/summary.md." \
  --reduce-artifact /app/summary.md \
  --tasks-dir exec/tasks \
  --jobs-dir exec/jobs \
  --agent AGENT_NAME \
  --model MODEL_NAME \
  --reduce-model REDUCER_MODEL_NAME \
  --n-attempts 2 \
  --n-reduce-attempts 1 \
  --print-config
```

The explicit map artifact is required for reducer configuration. When the map
job finishes, each map trial's collected artifacts are copied to the reducer
task's environment as:

```text
/app/artifacts/0001-<slugified-trial-name>/...
/app/artifacts/0002-<slugified-trial-name>/...
```

The ordinal is the position in the returned trial-result list, not a source
filename. Trials with no artifacts are omitted; if none have artifacts, the
reduce phase stops before its job. The reducer itself is compiled exactly once.

With flags mode, map and reducer share the jobs directory and inherit the map
provider, concurrency, quiet, retry, metrics, and map agent settings unless
specific reducer flags override them. `--n-attempts` applies to map tasks;
`--n-reduce-attempts` applies to the one reducer task.

## Recipe D: structured rewards

Map reward artifact:

```bash
harbor exec \
  --instruction "Score the input and write /app/scores.json." \
  --artifact /app/scores.json \
  --reward-artifact /app/scores.json \
  --print-config
```

Reducer reward artifact:

```bash
harbor exec \
  --instruction "Write /app/notes.json." \
  --artifact /app/notes.json \
  --reduce-instruction "Aggregate scores and write /app/reduce-scores.json." \
  --reduce-artifact /app/reduce-scores.json \
  --reduce-reward-artifact /app/reduce-scores.json \
  --print-config
```

The source file must contain a non-empty JSON object, for example:

```json
{
  "quality": 0.82,
  "coverage": 1,
  "error_count": 0
}
```

Keys must be strings and values must be numeric; booleans are rejected even
though JSON parsers treat them as a primitive type. The auto-verifier first
checks existence, then promotes the source to `/logs/verifier/reward.json`.
Malformed JSON, an empty object, a missing source, or a non-numeric value makes
verification fail. The reward artifact is collected as well as promoted.

Do not pass `--disable-verification` with either reward flag. If verification
is intentionally disabled, use ordinary artifacts and understand that no
existence-only or reward promotion check is generated.

## Recipe E: explicit reusable config

For a repeatable map/reduce workflow, put both phases in a file rather than
attempting to layer flags over it:

```yaml
schema_version: "1.0"
map:
  compile:
    task_name_prefix: topic-map
    output_dir: exec/tasks
    instructions:
      - text: "Read the input and write /app/notes.json."
    artifacts:
      - /app/notes.json
    environments:
      - paths: [inputs/topic.md]
    verifiers:
      - auto_verifier:
          required_artifacts: [/app/notes.json]
  job:
    job_name: topic-map-job
    jobs_dir: exec/jobs
    n_attempts: 2
    n_concurrent_trials: 4
    agents:
      - name: AGENT_NAME
        model_name: MODEL_NAME
    environment:
      type: docker
reduce:
  task:
    task_name: topic-reduce
    output_dir: exec/tasks
    instruction:
      text: "Read /app/artifacts/*/notes.json and write /app/summary.json."
    artifacts:
      - /app/summary.json
    verifier:
      auto_verifier:
        required_artifacts: [/app/summary.json]
  job:
    job_name: topic-reduce-job
    jobs_dir: exec/jobs
    n_attempts: 1
    agents:
      - name: AGENT_NAME
        model_name: MODEL_NAME
    environment:
      type: docker
```

Validate without execution:

```bash
harbor exec --config exec.yaml --print-config
```

Config mode does not apply map defaults or reducer inheritance through CLI
flags. Express the intended settings in both phase sections; the executor still
injects the compiled task path and reducer artifact inputs at runtime.
