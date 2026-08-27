# Evaluation troubleshooting

Start every debug pass with the safe linter:

```bash
python scripts/llmfoundry_eval_config_lint.py path/to/eval.yaml
```

It catches many YAML, task-schema, path, and Gauntlet matching issues before a model or API is touched.

## Malformed task rows

Symptoms:

- JSON decode errors.
- Assertion errors while building ICL evaluators.
- Key errors such as `context`, `continuation`, `query`, `choices`, `context_options`, `answer`, `aliases`, or `gold`.
- Empty or nonsensical prompts after formatting.

Likely causes and fixes:

- Wrong schema for task type. Use [task-schemas.md](task-schemas.md) and validate each JSONL row.
- `gold` is one-based or a string. It must be a zero-based integer index.
- `choices` or `context_options` is a string instead of a list of strings.
- `aliases` missing for `generation_task_with_answers`. Include a list, even if it only repeats the canonical answer.
- `num_fewshot` is an integer. Use a list, for example `num_fewshot: [0]`.
- `has_categories: true` but some rows lack `category`.
- `question_prelimiter` and `prelimiter` both set. Use only one.

## Wrong metric/task pairing

Symptoms:

- Evaluator construction fails.
- Metrics never update or result tables omit expected values.
- Gauntlet scores are empty even though evaluation ran.

Correct pairings:

- `generation_task_with_answers` → `InContextLearningGenerationExactMatchAccuracy`.
- `language_modeling` → `InContextLearningLMAccuracy`; optional `InContextLearningLMExpectedCalibrationError`.
- `multiple_choice` → `InContextLearningMultipleChoiceAccuracy`; optional `InContextLearningMCExpectedCalibrationError`.
- `schema` → `InContextLearningMultipleChoiceAccuracy`; optional `InContextLearningMCExpectedCalibrationError`.

Use class-style metric names in `metric_names`. Lower-case registry aliases such as `mc_accuracy` are useful for package APIs but are not the documented ICL task YAML style.

## Model/tokenizer downloads and local cache problems

Symptoms:

- Hugging Face authentication or network errors.
- Tokenizer/model download starts unexpectedly.
- Model loads on CPU/GPU longer than expected before eval begins.
- `MPT causal LMs require a load_path` error.

Fixes:

- Use local model/tokenizer paths or ensure cache and network permissions are intentional.
- For private models, configure authentication outside YAML.
- For `hf_causal_lm`, set `pretrained_model_name_or_path` and tokenizer `name` deliberately.
- For `mpt_causal_lm`, provide `load_path` for offline evaluation or use a suitable HF wrapper for pretrained HF models.
- Match tokenizer `model_max_length` with eval `max_seq_len` where possible.

## API credentials and endpoint failures

Symptoms:

- `No OpenAI API Key found`.
- Import error for optional OpenAI dependency.
- API rate limit, timeout, quota, or endpoint readiness errors.
- FMAPI endpoint cannot be reached.

Fixes:

- Export `OPENAI_API_KEY` for default OpenAI endpoints.
- Use `base_url` for OpenAI-compatible custom endpoints when appropriate.
- For FMAPI, configure `base_url` or `local: true`; local mode can use `MOSAICML_MODEL_ENDPOINT`.
- Keep secrets out of YAML and logs.
- Smoke-test with a tiny task and low `icl_subset_num_batches` before large API evals.
- Expect API wrappers to retry some timeouts/rate limits but not quota exhaustion.

## Too-long context or `max_seq_len` issues

Symptoms:

- Poor results from truncated prompts.
- Warnings about answer length versus sequence length.
- Long-context tasks fail or silently under-test the intended length.

Fixes:

- Increase top-level `max_seq_len` or task-level `max_seq_len` only if the model and tokenizer support it.
- Reduce `num_fewshot` when prompts exceed context length.
- For generation tasks, bound `generation_kwargs.max_new_tokens` and align it with expected answer lengths.
- For long-context Gauntlet variants, verify context length support before launching; do not assume a model supports 8K+ just because the eval task does.
- Inspect custom task prompts manually after applying `prompt_string`, `example_delimiter`, `continuation_delimiter`, and `prelimiter`.

## Batch size, OOM, and performance

Symptoms:

- CUDA OOM or process killed.
- Eval hangs at dataloader/model forward.
- API eval is slow or expensive.

Fixes:

- Lower `device_eval_batch_size` first.
- Set per-task `batch_size` for expensive tasks.
- Remember MC/schema rows expand to one input per choice/context option.
- Lower `num_fewshot`, `max_seq_len`, or `generation_kwargs.max_new_tokens`.
- Use `icl_subset_num_batches` for smoke tests.
- Avoid combining FSDP with 8-bit HF loading; that combination is rejected.
- For API eval, tiny batches and short tasks reduce rate-limit and cost exposure.

## Local data path confusion

Symptoms:

- `dataset_uri` or task/Gauntlet YAML path not found.
- A path works from one directory but not another.
- Linter finds a path but the actual eval command does not, or vice versa.

Fixes:

- Prefer explicit absolute/user-expanded paths for custom local datasets when running from changing directories.
- If using relative paths, run the actual `llmfoundry eval` command from the directory the paths expect.
- Keep task YAML and JSONL files together when possible.
- The bundled linter tries several safe relative resolutions for convenience, but LLM Foundry itself resolves runtime paths according to the launch process and config value.
- Remote/object-store/Hugging Face URIs are not downloaded by the linter; validate credentials separately.

## Eval Gauntlet missing or empty scores

Symptoms:

- Gauntlet table missing categories.
- Warnings about missing benchmarks.
- Composite average is 0 or absent.

Fixes:

- Ensure every Gauntlet benchmark `name` exactly matches a task `label`.
- Ensure every benchmark `num_fewshot` appears in that task's `num_fewshot` list.
- Ensure the underlying metric is an accuracy metric; non-accuracy metrics are ignored by Gauntlet extraction.
- If a category has one missing benchmark, the whole category is removed from composite scores.
- Avoid duplicate category and average names.
- Use [eval-gauntlet.md](eval-gauntlet.md) to check random baseline, weighting, and rescaling rules.

## Subset confusion

Symptoms:

- User expects only ICL tasks to be subsetted but base eval loader is subsetted, or vice versa.
- A YAML uses `subsets:` and the config parser rejects or ignores it.
- Training eval uses `max_seq_len` but ICL hooks do not reflect it.

Fixes:

- Offline ICL subset: `icl_subset_num_batches`.
- Offline base eval-loader subset: `eval_subset_num_batches`.
- In-training ICL eval length: `icl_seq_len`, not offline `max_seq_len`.
- In-training ICL subset: `icl_subset_num_batches`.
- Do not use a generic `subsets` key for this installed config version.

## Prompt formatting surprises

Symptoms:

- Accuracy is much lower than expected.
- Generated answers include repeated questions or chain-of-thought text.
- MC choices appear glued to questions or separated oddly.

Fixes:

- Check spaces in `continuation_delimiter` and answer strings.
- Add explicit `\nAnswer: ` or task-appropriate delimiters.
- For generation tasks, set `early_stopping_criteria` to stop at repeated question separators.
- For chain-of-thought data, set `cot_delimiter` and `do_normalization` deliberately.
- Use `prelimiter` or `question_prelimiter` for per-question prefixes, but not both.
- If exact matching should be strict, set `do_normalization: false`; otherwise leave normalization enabled for free-response aliases.
