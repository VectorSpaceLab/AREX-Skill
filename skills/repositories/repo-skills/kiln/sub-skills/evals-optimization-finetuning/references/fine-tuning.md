# Fine-Tuning and Dataset Formatting

Use this reference when creating Kiln dataset splits, exporting JSONL, selecting fine-tune providers/models, starting fine-tune jobs, polling status, or using completed fine-tunes as run configs. For generic provider configuration and model registry primitives, route to task-execution-providers-tools.

## Dataset split datamodel

### `DatasetSplitDefinition`

Fields:

- `name`: split name, for example `train`, `test`, `val`, or `all`.
- `description`: optional human description.
- `percentage`: float from `0.0` to `1.0`.

The split percentages in a `DatasetSplit` must sum to `1.0`.

Built-in split presets:

| Preset | Definitions |
|---|---|
| `AllSplitDefinition` | `all=1.0` |
| `Train80Test20SplitDefinition` | `train=0.8`, `test=0.2` |
| `Train80Val20SplitDefinition` | `train=0.8`, `val=0.2` |
| `Train60Test20Val20SplitDefinition` | `train=0.6`, `test=0.2`, `val=0.2` |
| `Train80Test10Val10SplitDefinition` | `train=0.8`, `test=0.1`, `val=0.1` |

The desktop fine-tune API exposes these as `DatasetSplitType` values:

- `train_val`
- `train_test`
- `train_test_val`
- `train_test_val_80`
- `all`

### `DatasetSplit`

Fields:

- `name`
- `description`
- `splits`: list of `DatasetSplitDefinition`.
- `split_contents`: mapping from split name to task-run IDs.
- `filter`: dataset filter ID used to build the split.

`DatasetSplit.from_task(name, task, splits, filter_id="all", description=None)` applies a dataset filter to `task.runs()`, shuffles valid IDs, and assigns IDs by rounded percentages. The last split receives remaining items to absorb rounding.

`missing_count()` counts IDs referenced by the split that no longer exist in the parent task's runs.

`tool_info()` inspects task runs referenced by the split and returns:

- `has_tool_mismatch`: true when runs do not all share the same tool/skill set.
- `tools`: sorted common tool IDs, empty list when all runs use no tools, or null when mismatched.

Tool consistency matters because fine-tune dataset export and provider support can depend on whether every example has the same tool schema.

## Fine-tune datamodel

`Finetune` is a child of `Task` and tracks a provider training job plus the runnable tuned model when complete.

Fields:

- `name`
- `description`
- `provider`: provider enum string, for example `fireworks_ai`, `together_ai`, or `vertex`.
- `base_model_id`: provider-native base model ID.
- `provider_id`: provider-side fine-tune job ID.
- `fine_tune_model_id`: provider-side tuned model ID or deployed endpoint ID.
- `dataset_split_id`: local `DatasetSplit` ID.
- `train_split_name`: default `train`.
- `validation_split_name`: optional.
- `parameters`: provider-specific hyperparameters.
- `system_message`: exact system message saved for training.
- `thinking_instructions`: only allowed/required for two-message CoT data strategies.
- `latest_status`: `unknown`, `pending`, `running`, `completed`, or `failed`.
- `properties`: provider-specific metadata.
- `data_strategy`: chat/training data strategy.
- `run_config`: runtime config that will call the tuned model after creation.

`nested_id()` returns:

```text
{project_id}::{task_id}::{finetune_id}
```

During `BaseFinetuneAdapter.create_and_start`, the supplied run config is mutated for tuned-model runtime use:

- `model_provider_name = kiln_fine_tune`
- `model_name = datamodel.nested_id()`
- `prompt_id = fine_tune_prompt::{datamodel.nested_id()}`

Completed fine-tunes with `fine_tune_model_id` and `run_config` appear in eval run-config lists as virtual `TaskRunConfig` objects with IDs:

```text
finetune_run_config::{project_id}::{task_id}::{finetune_id}
```

Unfinished, failed, unknown, or missing-model fine-tunes are not returned as runnable eval configs.

## Data strategies

`ChatStrategy` values used for fine-tuning:

| Strategy | Wire value | Use |
|---|---|---|
| `single_turn` | `final_only` | One assistant final answer. |
| `two_message_cot` | `two_message_cot` | Assistant thinking message then final answer; preferred new CoT strategy. |
| `two_message_cot_legacy` | `final_and_intermediate` | Legacy two-message CoT; supported for old data but not preferred for new tunes. |
| `single_turn_r1_thinking` | `final_and_intermediate_r1_compatible` | One assistant message containing `<think>...</think>` plus final answer for R1/QwQ-style thinking models. |

Thinking-data rules:

- `two_message_cot` and `two_message_cot_legacy` require `thinking_instructions` on `Finetune`.
- `single_turn_r1_thinking` must not pass `thinking_instructions`; the formatter requires thinking data and serializes it into `<think>` tags.
- Non-thinking strategies ignore `custom_thinking_instructions` and use `None`.
- Dataset examples must contain reasoning/intermediate training data for thinking strategies. Missing thinking data raises before export/upload.

Model strategy inference:

- Built-in providers infer from provider parser metadata.
- Fireworks fine-tune model IDs infer R1/QwQ/Qwen3 strategy support by model ID.
- Default strategy list is `single_turn` and `two_message_cot`.

## Dataset formatter

`DatasetFormatter(dataset, system_message, thinking_instructions=None)` formats a frozen split into provider JSONL. It does not call providers. It reads task runs from the parent task, prefers `task_run.repaired_output.output` over the original output when present, and writes UTF-8 JSONL with `ensure_ascii=False`.

### Supported formats

| `DatasetFormat` | Output shape |
|---|---|
| `openai_chat_jsonl` | `{"messages": [...]}` with plaintext assistant final response. |
| `openai_chat_json_schema_jsonl` | `{"messages": [...]}` with the final assistant message normalized to one-line JSON dict. |
| `openai_chat_toolcall_jsonl` | `{"messages": [...]}` where the final structured output is converted to an assistant `tool_calls` entry named `task_response`. |
| `huggingface_chat_template_jsonl` | `{"conversations": [...]}` using OpenAI-like messages under `conversations`. |
| `huggingface_chat_template_toolcall_jsonl` | `{"conversations": [...]}` where the final structured output is converted to a tool call. |
| `vertex_gemini` | `{"systemInstruction": ..., "contents": [...]}` plus optional Vertex tool declarations. |

Use `scripts/validate_finetune_dataset.py` to check small exported files before upload or handoff.

### Chat construction

`build_training_chat(task_run, system_message, data_strategy, thinking_instructions=None)` builds messages in this order:

1. System message.
2. User input.
3. Tool call/response messages extracted from the saved trace, when present.
4. Strategy-specific assistant messages:
   - `single_turn`: final output.
   - `two_message_cot` / legacy: thinking, then final output.
   - `single_turn_r1_thinking`: one assistant message containing `<think>` block and final output.

The formatter uses repaired output when present:

```text
final_output = task_run.repaired_output.output if repaired_output exists else task_run.output.output
```

### Structured final output

Structured formats parse the last assistant message as JSON and require a JSON object. If the final output is not valid JSON or parses to a non-dict, export raises. For tool-call formats, that dict becomes `task_response` arguments.

### Tool definitions

When a task run's source run config has `tools_config`, the formatter resolves tool definitions and attaches them to examples. It caches tool definitions by tool ID to avoid repeated MCP/tool calls. Skill tool IDs are combined into one `SkillTool` definition.

Tool consistency and export constraints:

- Datasets with mixed tool/skill selections cannot be downloaded through the desktop API.
- Some providers or models do not support function calling. Use provider metadata before choosing tool-call formats or tool-enabled training.
- Together models are marked as not supporting tools even when the base model entry supports function calling.

## Fine-tune provider adapter base class

`BaseFinetuneAdapter.create_and_start(...)` validates and starts provider jobs.

Required inputs:

- `dataset`: `DatasetSplit` with ID and parent task path.
- `provider_id`: provider enum string.
- `provider_base_model_id`: provider-native model ID.
- `train_split_name`: must exist in `dataset.split_contents`.
- `system_message`: non-empty training system message.
- `thinking_instructions`: required/forbidden depending on data strategy.
- `data_strategy`: chat strategy.
- `parameters`: provider-specific hyperparameters.
- `run_config`: required `KilnAgentRunConfigProperties` that will be rewritten to use the fine-tuned model.

Validation:

- Dataset must have an ID.
- Train split must exist.
- Validation split must exist if provided.
- Run config is required.
- Parent task and task path are required.
- Hyperparameters must match available parameter names and types; unknown parameters are rejected. Int-to-float conversion is allowed for expected float parameters.

Provider adapters implement:

- `_start(dataset)`: upload/launch provider job.
- `status()`: refresh provider status and update local datamodel.
- `available_parameters()`: provider hyperparameter catalog.
- `augment_system_message(system_message, task)`: provider-specific training prompt adjustments.

## Provider adapters

### Registry

Fine-tune registry maps:

- `fireworks_ai` -> `FireworksFinetune`
- `together_ai` -> `TogetherFinetune`
- `vertex` -> `VertexFinetune`

Other model providers may run tasks but are not fine-tune providers unless in this registry.

### Together.ai

Requirements:

- Together API key configured.
- Provider model ID selected from supported built-in provider entries.

Dataset format:

- Unstructured outputs: `openai_chat_jsonl`.
- Structured outputs: `openai_chat_json_schema_jsonl`; run config structured output mode becomes `json_custom_instructions` because Together fine-tunes do not use JSON-mode for training and receive shorter JSON-only instructions in the system message.

Start behavior:

1. Export and upload train JSONL with purpose FineTune.
2. Optionally export and upload validation JSONL.
3. Create a Together fine-tuning job with LoRA forced on.
4. Pass W&B config if available.
5. Save provider job ID and output model name when returned.

Status mapping:

- pending: Together pending/queued.
- running: running/compressing/uploading.
- completed: completed.
- failed: cancelled/cancel requested/error/user error.
- unknown: missing job ID, unknown state, status-fetch exception.

Together-specific parameters include `epochs`, `learning_rate`, `batch_size`, `num_checkpoints`, `min_lr_ratio`, `warmup_ratio`, `max_grad_norm`, `weight_decay`, `lora_rank`, `lora_dropout`, and `lora_alpha`.

### Fireworks

Requirements:

- Fireworks API key and account ID configured.
- Base model ID in Fireworks supported fine-tune model allowlist.
- Optional W&B API key/entity only when no custom W&B base URL is configured.

Dataset format:

- Unstructured outputs: `openai_chat_jsonl`.
- Structured outputs: `openai_chat_json_schema_jsonl`; run config structured output mode becomes `json_mode` because Fireworks does not support function calls or JSON schema for these fine-tune runtime calls.

Start behavior:

1. Create Fireworks dataset record.
2. Upload JSONL file.
3. Check dataset state is `READY`.
4. Create supervised fine-tuning job.
5. Save provider job ID and `properties["endpoint_version"]="v2"`.

Status and deploy behavior:

- Status uses Fireworks job endpoint and maps failed/running/completed states.
- On completed status, Kiln attempts to deploy the model.
- Serverless-supported base models use serverless PEFT deployment and treat already-deployed error code 9 as success.
- Other models deploy to a scale-to-zero server with H100 accelerator configuration.
- `fine_tune_model_id` is updated from the provider model ID or deployment base model when available.

Fireworks-specific parameters include `epochs`, `learning_rate`, `batch_size`, and `lora_rank`.

### Vertex AI

Requirements:

- Vertex project ID and location configured.
- Google Cloud credentials usable by Vertex AI and Cloud Storage.
- Bucket name derived from project ID must be valid and available.

Dataset format:

- `vertex_gemini`.
- Structured outputs set runtime structured output mode to `json_mode` when applicable.

Start behavior:

1. Export split to Vertex Gemini JSONL.
2. Create or reuse a GCS bucket named from the project ID.
3. Upload train and optional validation JSONL.
4. Initialize Vertex AI with configured project/location.
5. Start supervised tuning with source model, dataset URIs, display name, optional `epochs`, `adapter_size`, and `learning_rate_multiplier`.
6. Save provider job resource name.

Status mapping:

- pending: pending/queued.
- running: running.
- completed: succeeded/partially succeeded.
- failed: failed/expired/cancelled/cancelling or explicit job error.
- unknown: updating/unspecified/paused or unexpected state.

Vertex-specific parameters include `learning_rate_multiplier`, `epochs`, and `adapter_size`.

## Fine-tune desktop API routes

| Purpose | Method and path | Notes |
|---|---|---|
| List dataset splits | `GET /api/projects/{project_id}/tasks/{task_id}/dataset_splits` | Safe read. |
| Create dataset split | `POST /api/projects/{project_id}/tasks/{task_id}/dataset_splits` | Applies selected filter and split preset. |
| List fine-tunes | `GET /api/projects/{project_id}/tasks/{task_id}/finetunes?update_status=false` | Optional status refresh for non-final jobs. |
| Get fine-tune | `GET /api/projects/{project_id}/tasks/{task_id}/finetunes/{finetune_id}` | Returns finetune plus current status. |
| Update fine-tune | `PATCH /api/projects/{project_id}/tasks/{task_id}/finetunes/{finetune_id}` | Edits name/description; requires approval. |
| List fine-tune providers | `GET /api/finetune_providers` | Includes provider enabled state, model IDs, data strategies, function-calling support. |
| List hyperparameters | `GET /api/finetune/hyperparameters/{provider_id}` | Reads provider adapter parameter catalog. |
| Get dataset info | `GET /api/projects/{project_id}/tasks/{task_id}/finetune_dataset_info` | Returns existing datasets/fine-tunes, tag counts, and tool-filtered eligibility. |
| Create fine-tune | `POST /api/projects/{project_id}/tasks/{task_id}/finetunes` | Launches provider job; requires approval because it incurs cost. |
| Download dataset JSONL | `GET /api/download_dataset_jsonl` | Denied to agents by policy, but useful evidence for export behavior. |

### Create dataset split request

```json
{
  "dataset_split_type": "train_test",
  "filter_id": "all",
  "name": "Optional name",
  "description": "Optional description"
}
```

If name is omitted, Kiln generates a memorable two-word name.

### Create fine-tune request

Fields:

- `name`, `description`: optional.
- `dataset_id`: dataset split ID.
- `train_split_name`: split to train on.
- `validation_split_name`: optional split.
- `parameters`: provider hyperparameters.
- `provider`: provider enum string in fine-tune registry.
- `base_model_id`: provider-native tuneable model ID.
- `system_message_generator`: prompt builder ID, optional when custom system message provided.
- `custom_system_message`: direct system message, optional when generator provided.
- `custom_thinking_instructions`: optional for two-message CoT strategies.
- `data_strategy`: `ChatStrategy`.
- `run_config_properties`: required for actual `BaseFinetuneAdapter.create_and_start`.

The API rejects requests with unsupported provider/model data strategy before launching a job.

### System message selection

`system_message_from_request` prefers a non-empty custom system message. Otherwise it resolves `system_message_generator` with `prompt_builder_from_id` and builds a prompt without JSON instructions. If run config properties contain skills, it loads those skills and includes them when building the system message.

A custom system message ignores selected skills; this is intentional.

### Thinking instructions selection

`thinking_instructions_from_request`:

- returns `None` for non-thinking strategies,
- returns `None` for `single_turn_r1_thinking`,
- prefers custom thinking instructions when provided,
- otherwise uses the task's default chain-of-thought prompt.

## Dataset tags and filters

Fine-tune dataset info counts tags starting with `fine_tune`. For each tag it reports:

- total count,
- reasoning count via thinking-data filter,
- high-quality count via high-rating filter,
- reasoning-and-high-quality count.

Optional tool filters select only runs whose source run config has exactly the requested tool IDs. `tool_ids=[]` means match runs with no tools/skills; it is different from omitting `tool_ids`.

Existing datasets in `finetune_dataset_info` include only dataset splits already referenced by some fine-tune. Orphan splits are excluded from `existing_datasets` and eligibility lists.

## Safe operating patterns

### Freeze a high-quality training split

1. Tag curated task runs consistently, for example `fine_tune_baseline`, `fine_tune_tools`, or project-specific tags.
2. Ensure outputs are rated or repaired when high quality is required.
3. For tool-enabled data, verify all selected runs share exactly the same tool/skill set.
4. Create a `DatasetSplit` from the tag/filter.
5. Inspect `missing_count()` and `tool_info()` before training.
6. Keep train and validation split names aligned with the provider request.

### Validate JSONL before upload

1. Export with the intended format and data strategy.
2. Run [../scripts/validate_finetune_dataset.py](../scripts/validate_finetune_dataset.py) on a small sample or full exported file.
3. Add `--expect-structured-output` for `openai_chat_json_schema_jsonl` and tool-call formats.
4. Add `--require-thinking` for thinking data strategies.
5. Add `--require-tools` if tool training is expected.
6. Fix dataset/run issues before spending provider credits.

### Start a fine-tune safely

1. Read provider catalog and enabled state from `/api/finetune_providers`.
2. Read provider hyperparameters from `/api/finetune/hyperparameters/{provider_id}`.
3. Confirm provider credentials/service readiness.
4. Confirm dataset split exists and has enough examples in train/validation splits.
5. Confirm data strategy is supported by the selected provider model.
6. Confirm run config properties are available and will be rewritten to `kiln_fine_tune`.
7. Ask for approval before launching the job.
8. Poll status; do not treat missing `fine_tune_model_id` as runnable completion.
9. After completion, use the virtual fine-tune run config in eval comparisons before promoting.

## Evidence notes

Source evidence: `libs/core/kiln_ai/datamodel/dataset_split.py`, `libs/core/kiln_ai/datamodel/finetune.py`, `libs/core/kiln_ai/adapters/fine_tune/base_finetune.py`, `libs/core/kiln_ai/adapters/fine_tune/dataset_formatter.py`, `libs/core/kiln_ai/adapters/fine_tune/finetune_registry.py`, `libs/core/kiln_ai/adapters/fine_tune/finetune_run_config_id.py`, `libs/core/kiln_ai/adapters/fine_tune/fireworks_finetune.py`, `libs/core/kiln_ai/adapters/fine_tune/together_finetune.py`, `libs/core/kiln_ai/adapters/fine_tune/vertex_finetune.py`, `libs/core/kiln_ai/adapters/fine_tune/vertex_formatter.py`, `app/desktop/studio_server/finetune_api.py`, and fine-tune API/formatter tests.
