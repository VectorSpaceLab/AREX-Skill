# Troubleshooting Evals, Synthetic Data, Optimization, and Fine-Tuning

Use this reference when Kiln evals, statistics, synthetic data, repair, prompt optimization, dataset export, or fine-tune workflows fail. For model registry/provider credential primitives, route to task-execution-providers-tools; for RAG ingestion/vector store failures, route to rag-documents-data; for route wiring or UI implementation, route to server-desktop-web-api.

## Fast triage checklist

1. Classify the workflow: eval, statistics, synthetic data, Data Guide, repair, prompt optimization, dataset split/export, or fine-tune provider job.
2. Identify whether the failing step is local-only, local model/provider invocation, remote Copilot service, or provider fine-tune/cloud service.
3. Confirm task/project parents and IDs exist before resolving child models.
4. Confirm all dataset filters select the intended task runs.
5. Confirm required run configs and eval configs belong to the same task as the target eval.
6. For any live model, Copilot, Ollama, cloud, or provider job call, verify credentials/service readiness and obtain approval when the route policy requires it.
7. For fine-tune dataset files, run:

   ```bash
   python scripts/validate_finetune_dataset.py path/to/file.jsonl
   ```

8. Treat paid/provider/Ollama/cloud/Copilot flows as optional unless the user's task explicitly requires that live service.

## Environment import gotchas

These are verified environment issues for Kiln 1.0.4 and current source behavior.

| Symptom | Likely cause | Recovery |
|---|---|---|
| `kiln_ai.tools` imports fail after installing current unconstrained MCP packages | `mcp` package version is not lock-compatible with the current tool imports | Use a lock-compatible `mcp[cli]==1.10.1` in the environment used for Kiln tools/MCP inspection. |
| `kiln_server` import fails around Starlette internals such as `collapse_excgroups` | Starlette version mismatch; Starlette `1.6.0` was incompatible while `0.52.1` worked for this evidence set | Use the project lock or a Starlette version compatible with Kiln's server code, verified at `0.52.1` for this package evidence. |
| RAG LanceDB/vector store import fails with missing `pandas` | LanceDB/llama-index vector-store import path needs pandas | Install `pandas` for LanceDB-backed RAG inspection/runs, then route RAG details to rag-documents-data. |
| Provider, Ollama, Copilot, cloud, or fine-tune smoke fails due to missing service/credentials | External flow is optional by default | Do not treat this as core local skill failure unless the task requires the live service. Ask for credentials/service readiness before live calls. |

## Eval datamodel validation failures

### `output_scores are required`

Cause: `Eval.output_scores` is empty or missing.

Recovery:

1. Define at least one `EvalOutputScore`.
2. Use supported rating types: `five_star`, `pass_fail`, `pass_fail_critical`.
3. Do not use `custom` for eval output scores.

### Duplicate output score keys

Cause: two score names normalize to the same JSON key.

Recovery:

1. Normalize score names mentally before saving, for example `Overall Rating` -> `overall_rating`.
2. Rename one score so every normalized key is unique.
3. Keep score names aligned to task requirement names only when calibration against human requirement ratings is intended.

### `eval_configs_filter_id is required`

Cause: non-RAG template eval lacks the golden/calibration filter.

Recovery:

1. Choose a dataset filter containing human-rated calibration items.
2. Set `eval_configs_filter_id` when creating the eval.
3. If the eval is RAG-specific and genuinely does not need calibration, confirm the template is `rag`.

### Tool-call template rejects final-answer data

Cause: `tool_call` template requires `evaluation_data_type="full_trace"`.

Recovery:

1. Set `evaluation_data_type` to `full_trace`.
2. Ensure target task runs save traces.
3. Use full-trace eval only for run configs whose execution can produce traces.

### `reference_answer is only valid for reference answer evals`

Cause: saved `EvalRun.reference_answer` is set under a final-answer or full-trace eval.

Recovery:

1. Only set `reference_answer` when `Eval.evaluation_data_type == reference_answer`.
2. For final-answer and full-trace evals, leave it null.

## Eval config and G-Eval failures

### `eval_steps is required and must be a list`

Cause: `EvalConfig.properties` missing `eval_steps` or using a string/dict.

Recovery:

```json
{
  "eval_steps": ["Check correctness", "Check completeness"],
  "task_description": "Optional task summary"
}
```

### Model/provider invalid in judge config

Cause: `EvalConfig.model_name` or `model_provider` missing or `model_provider` not a valid provider enum.

Recovery:

1. Check provider/model registry through task-execution-providers-tools.
2. Use a provider model that supports the structured-output mode selected for judging.
3. Confirm credentials before running a live judge call.

### `No logprobs found for output - can not calculate g-eval`

Cause: `g_eval` requires output logprobs, but the selected judge provider/model did not return them.

Recovery:

1. Switch to a judge model/provider that supports top logprobs.
2. Or use `llm_as_judge` if direct discrete scoring is acceptable.
3. Do not treat missing logprobs as a dataset issue.

### `No score found for metric`

Cause: judge output did not include a valid rating token for a score key.

Recovery:

1. Simplify eval steps and score instructions.
2. Use stronger structured output support.
3. Check the score schema has only supported rating types.
4. Retry transient structured-output failures; `EvalRunner` already retries known retryable structured-output errors.

### Full-trace eval missing trace

Cause: `EvalDataType.full_trace` requires `task_run.trace` in run/eval data.

Recovery:

1. Re-run the target task with tracing enabled/saved.
2. Use a final-answer eval if trace information is not available.
3. For repair/fine-tune datasets, do not assume all historical runs have traces.

## EvalRunner alignment failures

### `All eval configs must have the same parent eval`

Cause: mixed configs from different evals passed into one `EvalRunner`.

Recovery: group runner calls by one eval at a time.

### `Run config is not for the same task as the eval configs`

Cause: comparing a run config from another task.

Recovery:

1. Resolve run configs from the same `project_id` and `task_id`.
2. Use `GET /api/projects/{project_id}/tasks/{task_id}/run_configs` to include completed fine-tune virtual configs.

### No run config IDs provided

Cause: `run_comparison` called without `run_config_ids` and without `all_run_configs=true`.

Recovery: provide at least one `run_config_ids` query parameter or set `all_run_configs=true`.

### Empty eval set filter

Cause: `eval_set_filter_id` selects no dataset items.

Recovery:

1. Inspect task run tags/ratings.
2. Adjust dataset filter or add/save qualifying runs.
3. For prompt optimization/fine-tuning, use separate train filters as needed.

## Score summary/statistics issues

### Run config appears with no scores

Common causes:

- No `EvalRun` exists for that run config and expected dataset filter.
- Saved `EvalRun` IDs do not match current dataset IDs.
- Eval run exists but is missing required score keys.
- The eval has multiple judge configs and no `current_config_id` for default summaries.

Recovery:

1. Check `dataset_size` and percent complete.
2. Run the comparison for the missing run config/config pair.
3. Set default judge config when using whole-task or run-config eval scores.

### Calibration summary has no correlations

Common causes:

- Golden filter has no items.
- Items lack human ratings.
- Eval score keys do not align to human rating keys.
- Eval config runs are incomplete.

Recovery:

1. Check fully/partially/not-rated counts.
2. Align `EvalOutputScore.name` to task requirement names or `overall_rating` when appropriate.
3. Run calibration for all eval configs.

### Statistics endpoint rejects paired arrays

Cause: array lengths differ, arrays are empty, or binary arrays contain values other than 0/1.

Recovery:

1. Join per-item results by `dataset_id`.
2. Drop or report unpaired/missing items.
3. Pass aligned arrays of equal length.
4. For pass/fail, use `mcnemar_paired`; for numeric metrics, use `compare_paired`.

### User tries to pool paired eval data

Cause: treating repeated scores for the same dataset items as independent samples.

Recovery:

1. Do not pool across run configs/formats.
2. Run one paired test per condition pair.
3. Report the number of paired items used.

## Synthetic data and Data Guide failures

### Generated inputs do not follow the target task schema

Cause: input-generation model drift or an underspecified Data Guide.

Recovery:

1. Check the target task input JSON schema.
2. Refine the Data Guide with schema-derived input constraints.
3. Generate fewer samples per call or use batch single-input generation for more controlled diversity.
4. Inspect parse errors before saving generated runs.

### Data Guide contains output policy

Cause: guide authoring/refine conflated inputs with outputs.

Recovery:

1. Move output policy back to task instruction, output schema, or eval rubric.
2. Keep Data Guide sections input-only.
3. Re-refine and explicitly state feedback such as "remove output rules; describe only realistic inputs".

### Data guide preview produces no samples

Common causes:

- Provider credential/rate-limit error.
- Model returns malformed output.
- Guide constraints are contradictory or too narrow.
- Target task input schema is too restrictive for the selected model.

Recovery:

1. Read the preview failure detail; provider errors are surfaced when available.
2. Verify the generation run config/provider.
3. Simplify guide constraints and retry.
4. Reduce `num_samples` or switch to a stronger model.

### Batch job status disappears or never completes

Cause: batch jobs are in-memory process state; process restart loses them. Long provider calls can also fail per item.

Recovery:

1. Poll status soon after starting.
2. Inspect per-index errors.
3. Restart the batch for missing items rather than assuming job IDs persist.
4. Save curated results promptly.

### Generated output incorrectly includes Data Guide constraints

Cause: Data Guide was injected into output generation guidance.

Recovery:

1. Do not pass Data Guide to `generate_sample` or output batch guidance.
2. Use Data Guide only for topics and inputs.
3. Put output requirements into the target task instruction or output schema.

## Repair failures

### Repair input lacks evaluator feedback

Cause: `RepairTaskInput.evaluator_feedback` is empty.

Recovery: provide concise, actionable non-empty feedback explaining what should change.

### Repair uses wrong original prompt

Cause: original run source lacks a valid `prompt_id` or uses an unknown legacy prompt builder name.

Recovery:

1. Expect fallback to simple prompt builder.
2. If exact prompt provenance matters, inspect the original run config through project-datamodel and task-execution-providers-tools.
3. Do not mutate the original run; save repaired output separately.

## Prompt optimization failures

### `Kiln Copilot API key not configured`

Cause: prompt optimization requires remote Kiln Copilot authentication.

Recovery:

1. Ask the user to configure the Copilot API key/service.
2. Treat prompt optimization as optional unless required by the task.
3. Continue with local eval/prompt iteration if acceptable.

### Run config unsupported

Common causes:

- Not `KilnAgentRunConfigProperties`.
- Tools are enabled.
- Missing model name/provider.
- Remote service does not support the model.

Recovery:

1. Choose a plain Kiln-agent run config with no tools.
2. Verify model support with `check_run_config`.
3. If tools are required, prompt optimization is not the right workflow.

### Eval unsupported for prompt optimization

Common causes:

- No default eval config.
- Stale `current_config_id`.
- No train filter.
- Default judge model unsupported.

Recovery:

1. Create and set a default eval config.
2. Set a missing `train_set_filter_id` once on legacy evals.
3. Use `check_eval` before starting the job.

### Success job did not create prompt/run config

Common causes:

- Remote result has no `optimized_prompt`.
- Artifact creation failed.
- Local prompt or run-config cleanup ran after a partial failure.

Recovery:

1. Get the local job again; status update can retry artifact creation.
2. Check `optimized_prompt`, `created_prompt_id`, and `created_run_config_id`.
3. Do not manually create duplicates until the locked creation path has clearly failed and the user approves a manual recovery.

## Fine-tune dataset split/export failures

### Split percentages do not sum to 1.0

Cause: custom split definitions invalid.

Recovery: use built-in presets or adjust percentages so they sum exactly to 1.0 within tolerance.

### Train or validation split missing

Cause: `train_split_name` or `validation_split_name` is not a key in `dataset.split_contents`.

Recovery: inspect dataset split names and update the fine-tune request.

### Dataset has missing task runs

Cause: task runs referenced in `split_contents` were deleted or moved.

Recovery:

1. Check `DatasetSplit.missing_count()`.
2. Rebuild the split from a current filter.
3. Do not upload a dataset that references missing runs.

### Dataset contains mixed tool/skill selections

Cause: referenced runs use different `tools_config.tools` sets.

Recovery:

1. Use `DatasetSplit.tool_info()`.
2. Rebuild the dataset with a filter that selects uniform tool/skill setup.
3. For no-tool training, explicitly filter for no tools (`tool_ids=[]` in dataset info semantics).
4. Avoid tool-call formats unless the selected provider/model supports tools.

### Final message is not JSON for structured format

Cause: `openai_chat_json_schema_jsonl`, tool-call formats, or Vertex structured path expects final output to parse as a JSON object.

Recovery:

1. Repair or exclude non-JSON examples.
2. Use an unstructured dataset format if the task is not structured.
3. Run `scripts/validate_finetune_dataset.py --expect-structured-output` before upload.

### Thinking data missing

Cause: chosen data strategy requires thinking/intermediate output but task runs lack it.

Recovery:

1. Use `single_turn` if reasoning training is not required.
2. Generate or select runs with reasoning/intermediate outputs.
3. For R1-style training, ensure the final assistant message can be serialized with a non-empty `<think>` block.

## Fine-tune provider failures

### Provider not in fine-tune registry

Cause: selected provider can run inference but lacks a fine-tune adapter.

Recovery: choose one of the fine-tune providers in [fine-tuning.md](fine-tuning.md): Fireworks, Together, or Vertex.

### Hyperparameter validation fails

Common causes:

- Required parameter omitted.
- Unknown parameter name.
- Float supplied as a string.
- Int supplied as a float/string.

Recovery:

1. Fetch `/api/finetune/hyperparameters/{provider_id}`.
2. Use exact parameter names and JSON scalar types.
3. Remove unknown keys.

### `Run config is required`

Cause: fine-tune creation did not include `run_config_properties`.

Recovery: provide the `KilnAgentRunConfigProperties` that should become the runtime config for the tuned model.

### Fireworks credentials or account missing

Cause: Fireworks fine-tune/status/deploy needs both API key and account ID.

Recovery:

1. Ask user to configure Fireworks provider settings.
2. Confirm selected model appears in `/api/finetune_providers`.
3. Treat Fireworks as optional unless explicitly required.

### Fireworks model completes but deploy fails

Common causes:

- Output model ID not returned by status.
- Account lacks deployment capacity/permissions.
- Model is not serverless and server deployment failed.

Recovery:

1. Refresh status again; status can update `fine_tune_model_id`.
2. Read `status.error_details`.
3. Confirm account permissions and deployment quota.
4. Do not expose the fine-tune as runnable until `fine_tune_model_id` is set.

### Together API key missing

Cause: Together adapter initialization requires API key.

Recovery: configure Together credentials or select another provider. Do not attempt upload without credentials.

### Vertex project/location or credentials missing

Cause: Vertex adapter needs project ID, location, and Google Cloud credentials; dataset upload uses Cloud Storage.

Recovery:

1. Configure Vertex project and location.
2. Ensure cloud credentials and bucket permissions are available.
3. Confirm bucket naming based on project ID is valid.
4. Treat Vertex as optional unless required.

## Evidence notes

Source evidence: `libs/core/kiln_ai/datamodel/eval.py`, `libs/core/kiln_ai/datamodel/data_guide.py`, `libs/core/kiln_ai/datamodel/dataset_split.py`, `libs/core/kiln_ai/datamodel/finetune.py`, `libs/core/kiln_ai/adapters/eval/`, `libs/core/kiln_ai/adapters/data_gen/`, `libs/core/kiln_ai/adapters/repair/`, `libs/core/kiln_ai/adapters/fine_tune/`, `libs/server/kiln_server/statistics_api.py`, `app/desktop/studio_server/eval_api.py`, `app/desktop/studio_server/data_gen_api.py`, `app/desktop/studio_server/prompt_optimization_job_api.py`, `app/desktop/studio_server/finetune_api.py`, and related tests.
