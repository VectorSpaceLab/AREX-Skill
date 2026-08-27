# Task schemas and eval configuration

This reference is for static reasoning and safe configuration of LLM Foundry evaluation. It is intentionally self-contained; do not depend on source-checkout paths at runtime.

## Offline EvalConfig shape

Use the public CLI:

```bash
llmfoundry eval YAML_PATH [overrides...]
```

Canonical offline eval YAMLs use these required top-level keys:

```yaml
max_seq_len: 1024
device_eval_batch_size: 4
models:
- model_name: my-model-label
  model:
    name: hf_causal_lm
    pretrained_model_name_or_path: EleutherAI/gpt-neo-125m
    pretrained: true
    init_device: cpu
  tokenizer:
    name: EleutherAI/gpt-neo-125m
    kwargs:
      model_max_length: 1024
```

Required fields:

- `models`: list of model entries. Each entry should include `model_name`, `model`, and `tokenizer`; `load_path` is needed for some local checkpoint-backed model classes.
- `max_seq_len`: default ICL sequence length used when a task does not override `max_seq_len`.
- `device_eval_batch_size`: per-device eval batch size. It must be an integer when `icl_tasks` are present.

Frequently used optional fields:

- `icl_tasks`: inline list or local YAML path containing an `icl_tasks:` list.
- `eval_gauntlet`: inline dict or local YAML path containing an `eval_gauntlet:` dict.
- `loggers`, `callbacks`, `fsdp_config`, `precision`, `seed`, `run_name`, `metadata`, `python_log_level`, `dist_timeout`, `code_paths`.
- Subset controls: `eval_subset_num_batches` limits base eval loaders; `icl_subset_num_batches` limits ICL evaluators. In this version, do not use a generic top-level `subsets` key.

The utility also tolerates a single top-level `model`/`tokenizer` shorthand and transforms it into `models`, but the list form is easier to lint and safer for multi-model comparisons.

## ICL task YAML skeleton

`icl_tasks` can be inline or placed in a separate YAML file:

```yaml
icl_tasks:
- label: lambada_smoke
  dataset_uri: local/path/to/lambada.jsonl
  num_fewshot: [0]
  icl_task_type: language_modeling
  metric_names:
  - InContextLearningLMAccuracy
  prompt_string: ''
  example_delimiter: "\n"
  continuation_delimiter: ' '
```

Required task keys for all four task families:

- `label`: benchmark label; this must match Eval Gauntlet benchmark `name` when aggregated.
- `dataset_uri`: local JSONL path, object-store URI, or `hf://...` Hugging Face dataset URI.
- `num_fewshot`: list of few-shot counts. Use `[0]`, not `0`, because the evaluator iterates this field.
- `icl_task_type`: one of `generation_task_with_answers`, `language_modeling`, `multiple_choice`, `schema`.

Common optional task keys:

- `batch_size`: overrides `device_eval_batch_size` for this task.
- `max_seq_len`: overrides top-level `max_seq_len` for this task.
- `metric_names`: list of metric class names. Defaults are inferred for the four supported task types if omitted.
- `prompt_string`: text prepended once before few-shot examples and the evaluated sample. Default: empty string.
- `example_delimiter`: separator between few-shot examples. Default: newline.
- `continuation_delimiter`: separator between context/query and answer/continuation. Default: single space.
- `prelimiter`: text inserted before each question/context. `question_prelimiter` is a backward-compatible alias. Do not set both.
- `has_categories`: when `true`, the dataset is partitioned by each row's `category` field.
- `hf_loading_vars`, `hf_parsing_map`: used for Hugging Face datasets; the parsing map maps final ICL keys to source columns.
- Generation-only options include `generation_kwargs`, `cot_delimiter`, `early_stopping_criteria`, and `do_normalization`.

Do not use top-level `num_beams` inside a task. Put generation settings under `generation_kwargs`, for example:

```yaml
generation_kwargs:
  num_beams: 4
  max_new_tokens: 32
```

## Task family contracts

### `generation_task_with_answers`

Use for free-response question answering evaluated by generation exact match.

Required JSONL fields per row:

```json
{"context": "What star sign is Jamie Lee Curtis?", "answer": "Scorpio", "aliases": ["Scorpio", "Skorpio"]}
```

- `context`: string prompt/question.
- `answer`: canonical correct answer string.
- `aliases`: list of accepted answer strings. Include the canonical answer here too if you want it listed explicitly.
- Optional `chain_of_thought`: string prepended before the answer when chain-of-thought handling is enabled.

Recommended metrics:

- Default/config metric: `InContextLearningGenerationExactMatchAccuracy`.
- Registry alias for API construction: `qa_accuracy`.

Behavior notes:

- Uses the model's generation path, not next-token likelihood scoring.
- Requires a tokenizer with a non-null EOS token.
- `do_normalization: true` lowercases, strips punctuation/articles/extra spaces, and handles underscores before exact-match comparison.
- `cot_delimiter` splits generated text and scores the final answer segment after the delimiter.
- `early_stopping_criteria` can stop scoring at repeated question separators or other delimiters.
- Long expected answers raise the effective generation length; ensure `max_seq_len` and generation kwargs are compatible.

### `language_modeling`

Use for exact continuation prediction by forward-pass logits.

Required JSONL fields per row:

```json
{"context": "He took another step, but he was still in the", "continuation": " glen"}
```

- `context`: preceding text string.
- `continuation`: exact continuation string to score.

Recommended metrics:

- Default/config metric: `InContextLearningLMAccuracy`.
- Optional calibration metric: `InContextLearningLMExpectedCalibrationError`.
- Registry aliases: `lm_accuracy`, `lm_expected_calibration_error`.

Behavior notes:

- The model is considered correct only when argmax logits exactly match continuation tokens.
- Space before the continuation is meaningful. If the tokenizer needs a prefix space and the continuation lacks one, the dataset code can prepend one.
- This is the right family for cloze-style datasets such as LAMBADA and exact short continuations.

### `multiple_choice`

Use when the model chooses the lowest-per-token-perplexity option among choices.

Required JSONL fields per row:

```json
{"query": "Question text and choices...\nAnswer: ", "choices": ["A", "B", "C", "D"], "gold": 2}
```

- `query`: question/context string.
- `choices`: list of answer strings.
- `gold`: zero-based integer index into `choices`.
- Optional `category`: string used only when `has_categories: true`.

Recommended metrics:

- Default/config metric: `InContextLearningMultipleChoiceAccuracy`.
- Optional calibration metric: `InContextLearningMCExpectedCalibrationError`.
- Registry aliases: `mc_accuracy`, `mc_expected_calibration_error`.

Behavior notes:

- Each logical row produces one model input per choice. Large choice counts multiply memory use.
- `gold` is an index, not the answer string and not one-based.
- The effective dataloader batch size is reduced so all choices for a question stay grouped.
- Use this family for exams, yes/no tasks, and tasks already converted into discrete choices.

### `schema`

Use when several possible contexts compete for a single continuation, such as Winograd-style schema tasks.

Required JSONL fields per row:

```json
{"context_options": ["Jim comforted Kevin because Jim", "Jim comforted Kevin because Kevin"], "continuation": " was upset.", "gold": 1}
```

- `context_options`: list of possible preceding contexts.
- `continuation`: shared continuation string.
- `gold`: zero-based integer index into `context_options`.
- Optional `category`: string used only when `has_categories: true`.

Recommended metrics:

- Default/config metric: `InContextLearningMultipleChoiceAccuracy`.
- Optional calibration metric: `InContextLearningMCExpectedCalibrationError`.
- Registry aliases: `mc_accuracy`, `mc_expected_calibration_error`.

Behavior notes:

- Although this is not ordinary multiple choice, it uses the multiple-choice accuracy metric because each context option is scored by continuation likelihood.
- Do not use `query`/`choices` for schema rows; use `context_options`/`continuation`/`gold`.

## Prompt and delimiter behavior

The rendered prompt is conceptually:

```text
prompt_string + few-shot examples joined by example_delimiter + current context/query + continuation_delimiter
```

Then the continuation, choice, or generated answer is tokenized/scored according to task type. Practical rules:

- Keep delimiter spaces intentional. A trailing space in `continuation_delimiter` and a leading space in continuations can change tokens.
- Use `prompt_string` for global instructions, `prelimiter`/`question_prelimiter` for per-question labels such as `Question: `, and `continuation_delimiter` for labels such as `\nAnswer: `.
- Few-shot examples are sampled from the same dataset using `num_fewshot`; the current example is excluded when possible.
- `strip_dataset` defaults to `true`; set it deliberately for code or whitespace-sensitive tasks.

## Category handling

When a task has `has_categories: true`:

1. Every row must include a `category` key.
2. The loader partitions the dataset into separate category-specific dataloaders.
3. Logged metric keys include the task label, few-shot count, category, and metric.
4. Result tables report category subtasks and an average for the benchmark.
5. Eval Gauntlet aggregation averages category subtasks into the benchmark score before category-level composite scoring.

Use categories for large multi-subject datasets such as MMLU or Jeopardy-style subject groups. Do not enable categories for mixed datasets unless the `category` labels are meaningful and present on every row.

## Installed public signatures to rely on

Use these signatures when writing helper code or explaining API usage:

```python
llmfoundry.command_utils.eval.eval_from_yaml(
    yaml_path: str,
    args_list: Optional[list[str]],
) -> tuple[list[composer.trainer.Trainer], pandas.DataFrame]

llmfoundry.eval.datasets.in_context_learning_evaluation.build_icl_dataloader(
    icl_task_type: str,
    dataset_uri: str,
    tokenizer: transformers.PreTrainedTokenizerBase,
    batch_size: int,
    hf_loading_vars: dict,
    hf_parsing_map: dict,
    destination_path: str = '',
    kwargs: Optional[dict[str, Any]] = None,
) -> composer.core.DataSpec

llmfoundry.eval.datasets.in_context_learning_evaluation.get_icl_task_dataloader(
    icl_task_type: str,
    dataset_uri: str,
    tokenizer: transformers.PreTrainedTokenizerBase,
    batch_size: int,
    has_categories: bool = False,
    hf_loading_vars: Optional[dict] = None,
    hf_parsing_map: Optional[dict] = None,
    destination_path: str = '',
    kwargs: Optional[dict[str, Any]] = None,
) -> Union[composer.core.DataSpec, dict[str, composer.core.DataSpec]]

llmfoundry.utils.builders.build_icl_evaluators(
    icl_tasks: Union[str, list[dict[str, Any]]],
    tokenizer: transformers.PreTrainedTokenizerBase,
    default_max_seq_len: int,
    default_batch_size: int,
    destination_dir: Optional[str] = None,
    icl_subset_num_batches: Optional[int] = None,
) -> tuple[list[composer.core.Evaluator], list[str]]
```

## Metric names

Use class-style names in ICL task `metric_names`:

- `InContextLearningGenerationExactMatchAccuracy`
- `InContextLearningLMAccuracy`
- `InContextLearningLMExpectedCalibrationError`
- `InContextLearningMultipleChoiceAccuracy`
- `InContextLearningMCExpectedCalibrationError`

Metric registry aliases available to package APIs include:

- ICL aliases: `qa_accuracy`, `lm_accuracy`, `lm_expected_calibration_error`, `mc_accuracy`, `mc_expected_calibration_error`.
- General LM aliases: `language_cross_entropy`, `language_perplexity`, `masked_accuracy`, `token_accuracy`.

If a YAML task uses lower-case aliases inside `metric_names`, check whether the active Composer/model path accepts them. For LLM Foundry's documented ICL task configs, prefer the class-style names above.
