# Eval and Statistics Workflows

Use this reference when creating or operating Kiln evaluators, judge configurations, run-config comparisons, calibration runs, score summaries, and significance/statistics requests. For model/provider setup details, route to task-execution-providers-tools; for persisted project/task mechanics, route to project-datamodel.

## Core eval datamodel

### `EvalTemplateId`

Kiln's built-in eval template IDs are:

- `kiln_requirements`
- `desired_behaviour`
- `kiln_issue`
- `tool_call`
- `toxicity`
- `bias`
- `maliciousness`
- `factual_correctness`
- `jailbreak`
- `rag`

Templates help prefill eval steps, output scores, and template-specific properties. The datamodel still permits non-template evals when `template=None`.

### `EvalConfigType`

- `g_eval`: G-Eval style scoring. It asks a judge model for discrete rating tokens and computes weighted scores from output logprobs.
- `llm_as_judge`: direct LLM-as-judge scoring. It uses the same `GEval` implementation but returns mapped scores from the discrete output, without logprob weighting.

Both config types require `properties["eval_steps"]` as a list. `properties["task_description"]` is optional but must be a string when present.

### `EvalOutputScore`

Each output score has:

- `name`: user-facing score name. Kiln derives the JSON key by normalizing the name, for example `Overall Rating` -> `overall_rating`.
- `instruction`: optional rubric text shown to judge models.
- `type`: one of `five_star`, `pass_fail`, or `pass_fail_critical`.

Do not use `custom` in evaluator output scores. The datamodel rejects custom scores for evals.

Score value ranges in saved `EvalRun.scores` are:

| Rating type | Saved score range |
|---|---:|
| `five_star` | float from `1.0` to `5.0` inclusive |
| `pass_fail` | float from `0.0` to `1.0` inclusive |
| `pass_fail_critical` | float from `-1.0` to `1.0` inclusive |

Saved `EvalRun.scores` must contain exactly the normalized score keys defined by the parent `Eval.output_scores`.

### `EvalDataType`

`Eval.evaluation_data_type` determines what the judge receives:

- `final_answer`: evaluate the final task output. A saved `EvalRun` for this type must not set `task_run_trace`.
- `full_trace`: evaluate the conversation/tool trace. Task-run eval mode must provide a trace; the `tool_call` template requires this type.
- `reference_answer`: evaluate an output against a reference answer. Task-run eval mode stores the dataset item's original output as `reference_answer`.

### `Eval`

Important fields:

- `eval_set_filter_id`: dataset filter for run-config comparisons. This filter selects dataset items whose inputs will be rerun through one or more task run configs and then scored.
- `eval_configs_filter_id`: dataset filter for judge calibration. This filter should select golden/reference items with human ratings for comparing judge configs.
- `train_set_filter_id`: dataset filter for training/prompt-optimization data. Legacy evals may not have it; the update API lets it be set once when missing. Loaded legacy reference-answer evals and name-based migrations may derive tag filters such as `tag::train_<eval-name>`.
- `output_scores`: non-empty score list with unique normalized JSON keys.
- `current_config_id`: default judge config used by summary APIs and prompt optimization readiness checks.
- `template_properties`: template-specific data for legacy evals. Spec-backed evals usually carry template information in the associated spec instead.

Template validation notes:

- Non-RAG templates require `eval_configs_filter_id`.
- `kiln_issue` legacy template properties require `issue_prompt`; optional `failure_example` and `pass_example` must be strings if present.
- `tool_call` legacy template properties require `tool`, `tool_function_name`, and non-empty `appropriate_tool_use_guidelines`; `inappropriate_tool_use_guidelines` is optional but must be a string when present; `evaluation_data_type` must be `full_trace`.

### `EvalConfig`

Important fields:

- `name`
- `model_name`
- `model_provider`
- `config_type`
- `properties`

`model_provider` must match a valid provider enum name before `GEval` can run. `properties` must be JSON-serializable. For `g_eval` and `llm_as_judge`, include at least:

```json
{
  "eval_steps": ["Check factual correctness", "Check completeness"],
  "task_description": "Optional short description of the target task"
}
```

### `EvalRun`

Saved eval results are children of an `EvalConfig`. Important fields:

- `dataset_id`: dataset item used by the eval.
- `task_run_config_id`: set for `task_run_eval`, absent for `eval_config_eval`.
- `eval_config_eval`: true when calibrating judge configs against existing dataset items.
- `input`, `output`: denormalized strings used by the run.
- `reference_answer`: only valid for `reference_answer` evals.
- `intermediate_outputs`: judge thinking/intermediate data.
- `task_run_trace`: JSON string for full-trace task-run evals.
- `scores`: exact score-key map.
- `task_run_usage`: usage of the task run that produced the evaluated output, not judge usage.

## Creating evals and configs through the desktop server API

The desktop server exposes eval endpoints under a task:

| Purpose | Method and path | Notes |
|---|---|---|
| List evals | `GET /api/projects/{project_id}/tasks/{task_id}/evals` | Safe read. |
| Get eval | `GET /api/projects/{project_id}/tasks/{task_id}/evals/{eval_id}` | Raises 404 if missing. |
| Create eval | `POST /api/projects/{project_id}/tasks/{task_id}/create_evaluator` | Saves an `Eval`. |
| Update eval | `PATCH /api/projects/{project_id}/tasks/{task_id}/evals/{eval_id}` | Can edit name/description and set missing `train_set_filter_id` once. Requires approval in agent policy. |
| Delete eval | `DELETE /api/projects/{project_id}/tasks/{task_id}/evals/{eval_id}` | Denied to agents by policy. |
| List eval configs | `GET /api/projects/{project_id}/tasks/{task_id}/evals/{eval_id}/eval_configs` | Safe read. |
| Get eval config | `GET /api/projects/{project_id}/tasks/{task_id}/evals/{eval_id}/eval_config/{eval_config_id}` | Safe read. |
| Create eval config | `POST /api/projects/{project_id}/tasks/{task_id}/evals/{eval_id}/create_eval_config` | Saves an `EvalConfig`. |
| Set default config | `POST /api/projects/{project_id}/tasks/{task_id}/evals/{eval_id}/set_current_eval_config/{eval_config_id}` | Use literal `None` to clear. |
| Eval progress | `GET /api/projects/{project_id}/tasks/{task_id}/evals/{eval_id}/progress` | Returns eval/golden/train dataset sizes and human-rating coverage. |

When creating run configs for eval comparison, use:

`POST /api/projects/{project_id}/tasks/{task_id}/run_configs`

For Kiln-agent configs, the API freezes dynamic prompt-builder output into the run config unless an identical frozen prompt already exists. This prevents later task/prompt edits from silently changing historical eval comparisons. Fine-tuned models that have completed and have `fine_tune_model_id` appear as virtual run configs with IDs like `finetune_run_config::{project_id}::{task_id}::{finetune_id}`.

## Running evals

### Two runner modes

`EvalRunner` supports two modes:

1. `task_run_eval`
   - Uses `Eval.eval_set_filter_id`.
   - Requires one or more `TaskRunConfig` objects for the same task as the eval.
   - For each selected dataset item and run config, invokes the task with `adapter_for_task`, then invokes the judge.
   - Skips combinations already present in existing `EvalRun` children for the same eval config, run config, and dataset item.

2. `eval_config_eval`
   - Uses `Eval.eval_configs_filter_id`.
   - Does not accept run configs.
   - Runs judge configs against existing dataset item input/output pairs.
   - Skips eval-config/dataset pairs already present.

Both modes require all eval configs to share the same parent eval and target task. `EvalRunner.run()` uses async workers with default concurrency 25 and retries known transient LiteLLM/structured-output failures up to two times.

### API execution routes

| Purpose | Method and path | Behavior |
|---|---|---|
| Run run-config comparison | `GET /api/projects/{project_id}/tasks/{task_id}/evals/{eval_id}/eval_config/{eval_config_id}/run_comparison` | SSE progress; query `run_config_ids=...` or `all_run_configs=true`; executes task runs and judge calls. |
| Run judge calibration | `GET /api/projects/{project_id}/tasks/{task_id}/evals/{eval_id}/run_calibration` | SSE progress; runs all eval configs against golden dataset items. |

SSE messages are `data: {"progress": <complete>, "total": <total>, "errors": <errors>}` followed by `data: complete`.

## G-Eval and LLM-as-judge behavior

`GEval` wraps a temporary Kiln task named `GEval Task` with:

- a system instruction describing the judge job,
- optional `task_description`,
- chain-of-thought evaluation steps from `properties["eval_steps"]`,
- an output JSON schema built from the parent eval's scores.

For `g_eval`, Kiln requests top logprobs and computes each metric as a weighted average over valid rating tokens. For `llm_as_judge`, Kiln maps the returned discrete value directly to a float score.

Token-to-score mapping:

| Token | Score |
|---|---:|
| `1` to `5` | `1.0` to `5.0` |
| `pass` | `1.0` |
| `fail` | `0.0` |
| `critical` | `-1.0` |

Token cleanup tolerates quotes, whitespace, case changes, and integer-like numeric strings such as `1.0`.

For structured output mode, `GEval` asks the model registry for a default mode, disallowing function-calling modes because G-Eval expects JSON scoring output.

## Score summaries and calibration

### Run-config score summary

`GET /api/projects/{project_id}/tasks/{task_id}/evals/{eval_id}/eval_config/{eval_config_id}/score_summary`

Returns:

- `results`: run-config ID -> score key -> mean score.
- `run_config_percent_complete`: run-config ID -> fraction complete.
- `dataset_size`: number of dataset items selected by `eval_set_filter_id`.

Completion drops when an expected dataset item has no eval run or when an eval run is missing a required score key.

### Whole-task eval results summary

`GET /api/projects/{project_id}/tasks/{task_id}/eval_results_summary`

Returns all eval metadata, all run config names, and cells keyed by run config then eval. Only evals with a valid `current_config_id` contribute score cells. Dataset IDs are cached per filter while building the response.

### Eval-config calibration summary

`GET /api/projects/{project_id}/tasks/{task_id}/evals/{eval_id}/eval_configs_score_summary`

Compares judge configs against human ratings in `eval_configs_filter_id`. It normalizes human and judge scores by score type, feeds pairs to the correlation calculator, and reports:

- correlation results by eval config and score key,
- percent complete per eval config,
- dataset size,
- fully/partially/not-rated counts for human ratings.

The endpoint returns an empty summary for an empty golden dataset. It returns 400 when `eval_configs_filter_id` is missing.

### Run-config eval scores

`GET /api/projects/{project_id}/tasks/{task_id}/run_configs/{run_config_id}/eval_scores`

Summarizes default eval-config scores for one run config across all non-archived spec-backed and legacy evals. It also returns mean usage metrics when at least half of included eval runs have that metric. Usage fields include input tokens, output tokens, total tokens, cost, and total LLM latency.

If an eval has more than one config and no default `current_config_id`, the response includes the eval with `missing_default_eval_config=true` and no scores.

## Human score alignment

Human ratings are matched to output score keys in this order:

1. `overall_rating` uses `task_run.output.rating.value`.
2. Requirement ratings match the normalized task requirement name to a task requirement ID.
3. Named ratings fall back to IDs of the form `named::{score.name}`.

This matters when designing evaluator scores: choose score names that normalize to existing task requirement names if you want calibration against those ratings.

## Statistics endpoint

Use `POST /api/statistics` for confidence intervals and significance instead of hand-computing standard errors.

### Operations

| Operation | Input shape | Best use |
|---|---|---|
| `proportion_ci` | `proportion`, `n`, optional `confidence` | One pass-rate/proportion cell. |
| `compare_proportions` | `proportion_a`, `n_a`, `proportion_b`, `n_b`, optional `confidence` | Independent or unpaired proportions. Conservative when items are actually paired. |
| `mcnemar_paired` | aligned `outcomes_a`, `outcomes_b` arrays of 0/1 values | Same eval items scored pass/fail under two run configs or methods. Prefer this for paired eval comparisons. |
| `compare_paired` | aligned numeric `values_a`, `values_b` arrays; nulls allowed and skipped | Same cases with continuous/count metrics such as latency, token count, cost, or scalar score differences. |

The response includes statistic fields, a `significant` verdict when meaningful, and an `interpretation` sentence.

### Method details

- `proportion_ci`: Wilson interval and normal-approximation standard error.
- `compare_proportions`: Newcombe/Wilson difference interval, z-score, deterministic percentile-bootstrap side block.
- `mcnemar_paired`: exact two-sided McNemar p-value from discordant counts, continuity-corrected chi-square sanity check, and Newcombe paired CI.
- `compare_paired`: paired bootstrap CI over mean paired differences plus Wilcoxon signed-rank p-value when at least five non-zero differences remain.

Never pool the same items across multiple run configs or formats for one test. Pair by `dataset_id` and run one paired test per condition pair.

## Common operating patterns

### Create a robust eval for run-config comparison

1. Choose an eval template or define `output_scores` directly.
2. Select `eval_set_filter_id` for items to rerun.
3. Select `eval_configs_filter_id` for golden/human-rated calibration items unless the template is `rag` or the workflow truly lacks calibration data.
4. Set `train_set_filter_id` if prompt optimization or fine-tune training will reuse the eval's training slice.
5. Create at least one judge config with valid `eval_steps`, model, and provider.
6. Set `current_config_id` after choosing the default judge config.
7. Run calibration first when human-rated items exist; then run run-config comparison.
8. Use score summaries plus `/api/statistics` for significance.

### Compare two run configs on a pass/fail eval

1. Fetch per-item eval run results for both run configs.
2. Join by `dataset_id`; do not compare by row order unless already aligned.
3. Convert the relevant score to 0/1 using the threshold appropriate to the score type.
4. Call `/api/statistics` with `operation="mcnemar_paired"` and the aligned arrays.
5. Report the eval dataset size, number of paired items actually used, raw means, delta, confidence interval, exact p-value, and any missing pairs.

### Evaluate a tool-calling task

1. Use a `tool_call` template or explicit `evaluation_data_type="full_trace"`.
2. Ensure the task run config records tools through task-execution-provider primitives.
3. Confirm the task run traces are saved; final-answer-only outputs cannot support full-trace evals.
4. In calibration, ensure golden dataset items include human ratings for the same score keys.

## Evidence notes

Source evidence: `libs/core/kiln_ai/datamodel/eval.py`, `libs/core/kiln_ai/adapters/eval/base_eval.py`, `libs/core/kiln_ai/adapters/eval/g_eval.py`, `libs/core/kiln_ai/adapters/eval/eval_runner.py`, `libs/core/kiln_ai/adapters/eval/registry.py`, `app/desktop/studio_server/eval_api.py`, `libs/server/kiln_server/statistics_api.py`, `libs/server/kiln_server/statistics_lib.py`, and associated eval/statistics tests.
