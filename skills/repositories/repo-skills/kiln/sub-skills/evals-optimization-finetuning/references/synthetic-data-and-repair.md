# Synthetic Data and Repair Workflows

Use this reference when operating Kiln's synthetic data generation, task Data Guides, Q&A generation, generated sample saving, and repair task construction. For provider/model/run-config primitives, route to task-execution-providers-tools. For RAG indexing and document ingestion before Q&A generation, route to rag-documents-data.

## Synthetic data stages

Kiln separates synthetic data into distinct stages:

1. Topic/category generation: produce a tree of short topic labels.
2. Input generation: produce candidate inputs to the target task.
3. Output generation: run the target task on those inputs to produce task runs.
4. Save/curate: persist selected generated runs, usually tagged as synthetic.
5. Optional Data Guide preview/refine: author or refine a reusable input guide.
6. Optional Q&A generation from a document part: produce query/reference-answer pairs for RAG-style datasets.

The stage boundary is important: a Task Data Guide describes realistic inputs only. It is used for topic and input generation, but not for output generation. Output behavior belongs to the target task's system prompt, output schema, run config, tools, and skills.

## Data generation task classes

### `DataGenCategoriesTaskInput`

Fields:

- `kiln_data_gen_topic_path`: list of strings from root to the current topic node.
- `kiln_data_gen_system_prompt`: target task prompt built without JSON instructions.
- `kiln_data_gen_num_subtopics`: number of subtopics to generate.
- `kiln_data_gen_existing_topics`: optional list of already-existing subtopics to avoid.

`from_task(task, node_path=[], num_subtopics=6, existing_topics=None)` builds this input from a target task using a simple prompt builder.

### `DataGenCategoriesTask`

Constructed with:

- `gen_type`: `training` or `eval`.
- `parent_project`: temporary/generated task parent project.
- `guidance`: optional combined guidance.

It produces structured output with a `subtopics` list.

### `DataGenSampleTaskInput`

Fields:

- `kiln_data_gen_topic_path`
- `kiln_data_gen_system_prompt`
- `kiln_data_gen_num_samples`

`from_task(task, topic=[], num_samples=8)` builds the input from a target task.

### `DataGenSampleTask`

Constructed with:

- `target_task`: the task whose input shape is being generated.
- `gen_type`: `training` or `eval`.
- `parent_project`
- `guidance`

Its output schema is always an object with `generated_samples`. If the target task has an input JSON schema, each generated item follows that closed object schema; otherwise each generated item is a string.

### `DataGenSingleInputTaskInput`

Fields:

- `kiln_data_gen_system_prompt`: target task prompt.
- `kiln_data_gen_input_guidance`: optional guidance for exactly this one generated input.

### `DataGenSingleInputTask`

Used by batch input generation. It creates exactly one generated input under a `generated_input` field and keeps per-input guidance in the user message so that LLM-generated guidance is treated as data, not system instruction.

### `wrap_task_with_guidance`

Use `wrap_task_with_guidance(original_instruction, guidance)` when output generation needs one-off extra instructions. It appends a `# Special Instructions` section to the target task instruction. Do not use this to inject Data Guide content into output generation.

## Task Data Guide datamodel

`DataGuide` is a child of `Task` and has:

- `guide`: markdown body.
- `source`: `manual` or `kiln_pro`.

Canonical guide shapes:

### Manual flow

Manual/user-authored guides usually include:

1. `# Reference Inputs`
2. `# Semantics`
3. `# Style`
4. `# Presentation Defaults`

`# Reference Inputs` examples are user-owned ground truth. Refine flows preserve them verbatim by default unless user feedback explicitly asks to add, edit, or remove an example.

### Kiln Pro / Copilot flow

Kiln Pro-derived guides usually include only:

1. `# Semantics`
2. `# Style`
3. `# Presentation Defaults`

Refine for this source is surgical: feedback-only targeted edits, with untouched sections preserved.

### Section semantics

- `# Semantics`: what information exists in inputs, fields, domain values, relationships, critical constraints, plausible ranges, and variability.
- `# Style`: how inputs read and look, including length, layout, formatting, tone, casing, list/value conventions, and quantitative ceilings.
- `# Presentation Defaults`: overridable conventions such as units, date formats, number formats, section ordering, terminology style, and defaults.

The Data Guide must not contain output policy, output schema rules, classification decision rules, or correctness criteria for generated outputs.

## Guidance composition and authority

When generating topics or inputs, Kiln composes guidance in this order:

1. Task Data Guide section, if one is resolved.
2. Template/per-run guidance, if supplied.

Authority cascade when sources conflict:

1. The specific generation guidance or batch prompt.
2. The Data Guide.
3. Model defaults.

Invariants always remain hard requirements: logical relationships between fields, domain plausibility and accuracy, and truthfulness to the task's actual purpose.

### Stage-specific Data Guide use

Topic stage:

- Use `# Semantics` to inform scenario coverage.
- Ignore style and presentation details because topic labels are not final inputs.
- Keep topic strings short and topic-like; do not reproduce the input format in labels.

Input stage:

- Apply the full Data Guide.
- Treat `# Semantics` and `# Style` as hard constraints.
- Treat `# Presentation Defaults` as defaults the per-run template can override.
- If manual `# Reference Inputs` are present, mirror their structure and value patterns.
- Treat quantitative `# Style` constraints as ceilings.

Output stage:

- Do not pass the Data Guide.
- Use target task instruction, output schema, selected run config, tools, and any explicit output-generation guidance.

## Synthetic data desktop API routes

| Purpose | Method and path | Notes |
|---|---|---|
| Generate topic categories | `POST /api/projects/{project_id}/tasks/{task_id}/generate_categories` | Uses `DataGenCategoriesApiInput`; requires approval because it calls a model. |
| Generate input samples | `POST /api/projects/{project_id}/tasks/{task_id}/generate_inputs` | Uses `DataGenSampleApiInput`; requires approval because it calls a model. |
| Generate one output sample | `POST /api/projects/{project_id}/tasks/{task_id}/generate_sample` | Runs target task with a generated input; returned run is unsaved and gets a temporary ID. |
| Save generated sample | `POST /api/projects/{project_id}/tasks/{task_id}/save_sample` | Persists a `TaskRun` under the task. |
| Start batch input job | `POST /api/projects/{project_id}/tasks/{task_id}/generate_inputs_batch` | Starts in-process job, one input per prompt. |
| Poll batch input job | `GET /api/projects/{project_id}/tasks/{task_id}/generate_inputs_batch/{job_id}` | Returns status, progress, model info, per-index results/errors. |
| Start batch output job | `POST /api/projects/{project_id}/tasks/{task_id}/generate_outputs_batch` | Starts in-process task-output generation for provided inputs. |
| Poll batch output job | `GET /api/projects/{project_id}/tasks/{task_id}/generate_outputs_batch/{job_id}` | Returns status and unsaved `TaskRun` results. |
| Generate Q&A pairs | `POST /api/projects/{project_id}/tasks/{task_id}/generate_qna` | Uses a project document and part text; requires approval because it calls a model. |
| Save Q&A pair | `POST /api/projects/{project_id}/tasks/{task_id}/save_qna_pair` | Saves a query/answer as a `TaskRun` with a simple system/user/assistant trace. |
| Get Data Guide | `GET /api/projects/{project_id}/tasks/{task_id}/data_gen_guide` | Returns current task DataGuide or null. |
| Save Data Guide | `PUT /api/projects/{project_id}/tasks/{task_id}/data_gen_guide` | Reuses existing guide when present; empty guide is rejected. |
| Delete Data Guide | `DELETE /api/projects/{project_id}/tasks/{task_id}/data_gen_guide` | Requires approval. |
| Preview Data Guide | `POST /api/projects/{project_id}/tasks/{task_id}/data_gen_guide_preview` | Generates preview input samples; requires approval. |
| Refine Data Guide | `POST /api/projects/{project_id}/tasks/{task_id}/data_gen_guide_refine` | Calls the metaprompter; requires approval. |

### `DataGenCategoriesApiInput`

Fields:

- `node_path`: default `[]`.
- `num_subtopics`: default `6`.
- `gen_type`: `eval` or `training`.
- `guidance`: optional template guidance.
- `data_guide`: optional per-run guide override.
- `existing_topics`: optional duplicate-avoidance list.
- `run_config_properties`: `KilnAgentRunConfigProperties` for the generation model.

The endpoint clones `run_config_properties` and forces `prompt_id` to `simple`.

### `DataGenSampleApiInput`

Fields:

- `topic`: default `[]`.
- `num_samples`: default `8`.
- `gen_type`: `training` or `eval`.
- `guidance`: optional template guidance.
- `data_guide`: optional override replacing the task's saved guide for this call.
- `run_config_properties`: `KilnAgentRunConfigProperties` for the input-generation model.

The endpoint clones `run_config_properties` and forces `prompt_id` to `simple`.

### `DataGenSaveSamplesApiInput`

Used by `generate_sample`:

- `input`: generated input string or dict.
- `topic_path`: topic path used for metadata.
- `input_model_name`, `input_provider`: model/provider that generated the input.
- `run_config_properties`: target task run config for output generation.
- `guidance`: optional output-generation guidance.
- `tags`: optional extra tags.

Generated output runs get tags:

- `synthetic`
- `synthetic_session_{session_id}` when `session_id` query param is present
- any caller-provided tags

Data source properties include input model name/provider and `adapter_name="kiln_data_gen"`; topic path is stored as a `>>>>>`-joined string when present.

## Batch generation details

Batch input generation creates an in-memory `_BatchJob` with `kind="inputs"`. It stores one result per prompt index and runs up to 20 simultaneous LLM calls. Each prompt becomes `kiln_data_gen_input_guidance` for a `DataGenSingleInputTask`. For batch flow, `data_guide=None` means "do not use a guide" rather than "fall back to saved guide".

Batch output generation reloads the task per item because output generation can temporarily mutate task instructions when guidance is applied. Output results are unsaved task runs with temporary IDs; save selected runs separately.

The in-memory registry evicts old finished jobs when it grows beyond its cap. Do not rely on batch job IDs as long-lived project state.

## Data Guide preview and refine

### Preview

Preview uses the same input-generation framing as runtime synthetic data. It wraps the draft guide through the guidance composer, creates a `DataGenSampleTask`, forces `prompt_id` to `simple`, and fans out independent `num_samples=1` calls in parallel. Independent draws better reveal guide quality than one multi-sample call.

If all preview calls fail or parse to no usable inputs, the endpoint surfaces the first provider error when available. This helps distinguish guide-quality issues from credential, rate-limit, or provider failures.

### Refine

Refine builds a temporary task named `guidance_refinement` whose output schema is `{ "guide": "..." }`. It chooses the metaprompt branch by `GuideRefineInput.source`, falling back to the persisted guide's source or `manual`.

Manual refine consumes:

- the target task runtime prompt,
- optional task input JSON schema,
- current guide,
- rated preview samples,
- user feedback.

Kiln Pro refine consumes:

- the target task runtime prompt,
- optional task input JSON schema,
- current guide,
- user feedback only.

If the refine model returns empty guide content, the endpoint returns the current guide unchanged.

## Q&A generation and saving

`DataGenQnaTask` generates Q&A pairs from a project document part. Use it for RAG-style datasets where the answer must be grounded strictly in supplied document text. Generated Q&A runs receive tags:

- `synthetic`
- `qna`
- `synthetic_qna_session_{session_id}` when present
- caller-provided tags

`save_qna_pair` persists a single query/reference answer as a `TaskRun`. It builds a simple OpenAI-style trace:

1. system: target task instruction
2. user: query
3. assistant: answer

The run input is the query; the run output is the answer; input/output data sources record `adapter_name="kiln_qna_manual_save"`, model name, and provider.

## Repair task workflow

Use repair when an evaluator or human feedback says a saved task run output should be improved.

### `RepairTaskInput`

Fields:

- `original_prompt`: prompt used for the original run, built from the saved source prompt ID when possible.
- `original_input`: original task input.
- `original_output`: original task output.
- `evaluator_feedback`: non-empty feedback explaining what to improve.

### `RepairTaskRun`

`RepairTaskRun(original_task)` creates a temporary task with:

- an instruction telling the model to improve another assistant's output,
- a P0 requirement named `Follow Eval Feedback`,
- input schema from `RepairTaskInput`,
- output schema copied from the original task.

Prompt recovery order for `original_prompt`:

1. Use `run.output.source.properties["prompt_id"]` when available.
2. Fall back to legacy `prompt_builder_name`.
3. If the prompt ID is unknown or missing, use `SimplePromptBuilder` for the original task.

Do not treat repair as editing the original task instruction or run config. It constructs a separate repair task input and should preserve the original task/run evidence.

## Safe operating patterns

### Generate and curate synthetic eval inputs

1. Confirm the target task input shape and whether a saved Data Guide exists.
2. If the task lacks enough examples, create or refine a Data Guide first.
3. Generate topics with `gen_type="eval"` only if a topic tree will improve coverage.
4. Generate inputs from topics or batch prompts.
5. Generate outputs with the target task run config only after inspecting inputs.
6. Save only curated runs and tag them for later filters, for example `synthetic`, `eval`, `fine_tune_*`, or task-specific tags.
7. Build eval, train, or calibration filters from tags after curation.

### Build training data with a Data Guide

1. Keep the guide input-only: no output policy.
2. Generate realistic and diverse inputs.
3. Generate outputs with the candidate target run config.
4. Rate or repair outputs before using high-quality filters for fine-tuning.
5. Use dataset splits from [fine-tuning.md](fine-tuning.md) to freeze selected IDs before export or training.

### Use repair before fine-tuning

1. Identify low-quality or evaluator-failed runs.
2. Run repair with concrete evaluator feedback.
3. Inspect repaired outputs and human ratings.
4. Prefer the dataset formatter's repaired-output preference over mutating the original output text.
5. Tag repaired/high-quality examples consistently so dataset filters can select them.

## Evidence notes

Source evidence: `libs/core/kiln_ai/datamodel/data_guide.py`, `libs/core/kiln_ai/datamodel/spec.py`, `libs/core/kiln_ai/adapters/data_gen/data_gen_task.py`, `libs/core/kiln_ai/adapters/data_gen/data_gen_prompts.py`, `libs/core/kiln_ai/adapters/data_gen/qna_gen_task.py`, `libs/core/kiln_ai/adapters/repair/repair_task.py`, `app/desktop/studio_server/data_gen_api.py`, and related data generation/repair API tests.
