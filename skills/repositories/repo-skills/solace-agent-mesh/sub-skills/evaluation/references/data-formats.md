# Evaluation data formats

This reference summarizes the suite, test case, scorer, and result shapes used by `sam eval`.

## Configuration conventions

- The live loader currently parses suite files as JSON.
- Keys ending in `_VAR` mean "read the referenced environment variable value".
- Direct values are passed through as-is.
- Relative paths in a suite are resolved from the suite file directory.
- Relative artifact paths in a test case are resolved from the test case file directory.
- `results_dir_name` should be provided explicitly; the current loader treats it as required.

## Suite configuration

### Common fields

| Field | Required | Notes |
| --- | --- | --- |
| `broker` | yes | Solace broker connection object. The live loader resolves `_VAR` keys to environment values. |
| `test_cases` | yes | List of test case file paths. At least one. |
| `results_dir_name` | yes | Output directory name under `results/`. |
| `runs` | no | Defaults to `1`. Each test case is repeated this many times. |
| `workers` | no | Defaults to `4`. Capped by the runtime maximum. |
| `evaluation_settings` | no | Scoring controls. Missing keys fall back to defaults. |

### Local-only fields

| Field | Required | Notes |
| --- | --- | --- |
| `agents` | yes | List of local agent config files. At least one. |
| `llm_models` | yes | List of model configurations. At least one. |
| `remote` | no | Must not be present in local mode. |

### Remote-only fields

| Field | Required | Notes |
| --- | --- | --- |
| `remote` | yes | Remote REST gateway settings and namespace. |
| `agents` | no | Must not be present in remote mode. |
| `llm_models` | no | Must not be present in remote mode. |

## Local broker and model environment blocks

### Broker object

The broker object is resolved into these required runtime fields:

- `SOLACE_BROKER_URL`
- `SOLACE_BROKER_VPN`
- `SOLACE_BROKER_USERNAME`
- `SOLACE_BROKER_PASSWORD`

The usual authoring pattern is:

```json
{
  "SOLACE_BROKER_URL_VAR": "SOLACE_BROKER_URL",
  "SOLACE_BROKER_USERNAME_VAR": "SOLACE_BROKER_USERNAME",
  "SOLACE_BROKER_PASSWORD_VAR": "SOLACE_BROKER_PASSWORD",
  "SOLACE_BROKER_VPN_VAR": "SOLACE_BROKER_VPN"
}
```

### `llm_models` items

Each item has:

- `name`: display label for the model run directory.
- `env`: map of direct values and/or `_VAR` references.

The runtime validates that each model resolves `LLM_SERVICE_PLANNING_MODEL_NAME`.

## Remote connection block

The remote object resolves these runtime fields:

- `EVAL_REMOTE_URL`
- `EVAL_NAMESPACE`
- `EVAL_AUTH_TOKEN` is optional.

A typical authoring shape is:

```json
{
  "EVAL_REMOTE_URL_VAR": "EVAL_REMOTE_URL",
  "EVAL_AUTH_TOKEN_VAR": "EVAL_AUTH_TOKEN",
  "EVAL_NAMESPACE_VAR": "EVAL_NAMESPACE"
}
```

The auth token is only sent when present.

## `evaluation_settings`

`evaluation_settings` is an object with these nested controls:

- `tool_match.enabled`
- `response_match.enabled`
- `llm_evaluator.enabled`
- `llm_evaluator.env`

Default behavior when the block is absent:

- `tool_match.enabled = true`
- `response_match.enabled = true`
- `llm_evaluator.enabled = false`

If `llm_evaluator.enabled` is true, the evaluator needs all of these resolved values:

- `LLM_SERVICE_PLANNING_MODEL_NAME`
- `LLM_SERVICE_ENDPOINT`
- `LLM_SERVICE_API_KEY`

## Test case format

### Required fields

| Field | Required | Notes |
| --- | --- | --- |
| `test_case_id` | yes | Unique identifier for the test case. |
| `query` | yes | Prompt sent to the target agent. |
| `target_agent` | yes | Agent name to invoke. |

### Optional fields and defaults

| Field | Default | Notes |
| --- | --- | --- |
| `category` | `Other` | Human-readable grouping label. |
| `description` | `No description provided.` | Short intent summary. |
| `artifacts` | `[]` | Attachments sent with the query. |
| `wait_time` | `60` | Maximum wait time in seconds; current loader caps this at 300. |
| `evaluation` | empty criteria object | Scoring hints. |

### Artifact items

| Field | Required | Notes |
| --- | --- | --- |
| `type` | yes | Supported values: `file`, `url`, `text`. |
| `path` | yes | Path or content reference, depending on type. |

For `file` artifacts:

- Use a path relative to the test case file.
- Do not use absolute paths.
- Do not traverse upward with `..`.
- The file should exist before live evaluation.

### Evaluation object

| Field | Default | Notes |
| --- | --- | --- |
| `expected_tools` | `[]` | Tool names the agent should use. |
| `expected_response` | empty string | Canonical or expected final answer. |
| `criterion` | empty string | LLM judge rubric text. |

## Scorers

### `tool_match`

- Compares expected tool names against tool names extracted from the run summary.
- Uses set intersection on names.
- If `expected_tools` is empty, the score is `1.0`.

### `response_match`

- Compares the final message against `expected_response`.
- Uses weighted ROUGE F-scores.
- Weights: ROUGE-1 `0.2`, ROUGE-2 `0.3`, ROUGE-L `0.5`.
- This scorer is sensitive to wording and does not reason about synonyms.

### `llm_evaluator`

- Builds a judge prompt from the query, expected response, actual response, criterion, input artifacts, and output artifacts.
- Calls an LLM through `litellm`.
- Reads a score from `Score: <number>` or another 0-to-1 number in the response.
- Captures free-form reasoning text after `Reasoning:` when present.

## Result data

### `summary.json`

Per-run summary data includes:

- `test_case_id`
- `run_id`
- `query`
- `target_agent`
- `namespace`
- `context_id`
- `final_status`
- `final_message`
- `start_time`
- `end_time`
- `duration_seconds`
- `tool_calls`
- `input_artifacts`
- `output_artifacts`
- `errors`

### `results.json`

Per-model or remote aggregate data includes:

- `model_name`
- `total_execution_time`
- `test_cases` list

Each test case entry includes:

- `test_case_id`
- `category`
- `runs`
- `average_duration`
- `tool_match_scores`
- `response_match_scores`
- `llm_eval_scores`

Each run entry includes:

- `run`
- `test_case_id`
- `test_case_path`
- `duration_seconds`
- `tool_match` when enabled
- `response_match` when enabled
- `llm_eval.score` and `llm_eval.reasoning` when enabled
- `errors` when present

### `stats.json`

The top-level stats file stores the overall execution time and a per-model score summary.

## Practical authoring checklist

1. Pick local or remote mode, not both.
2. Keep `results_dir_name` unique.
3. Resolve suite-relative and test-case-relative paths before live runs.
4. Make every `_VAR` reference traceable to an environment variable name.
5. Keep file artifacts local and present before evaluation.
6. Keep scorer settings aligned with the kind of behavior you want to measure.
