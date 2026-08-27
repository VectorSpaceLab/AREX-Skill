# Evaluation workflows

Use these workflows after reading [task-schemas.md](task-schemas.md) for task rows and metric compatibility. Run the static linter before launching any job:

```bash
python scripts/llmfoundry_eval_config_lint.py path/to/eval.yaml
```

The linter is safe: it parses YAML and optional local JSONL samples only; it does not import LLM Foundry, load models, call APIs, download datasets, or allocate accelerators.

## Workflow 1: offline ICL evaluation with the public CLI

1. Prepare an eval YAML with at least:

   ```yaml
   max_seq_len: 1024
   precision: fp32
   device_eval_batch_size: 4
   models:
   - model_name: tiny-or-cached-model
     model:
       name: hf_causal_lm
       pretrained_model_name_or_path: EleutherAI/gpt-neo-125m
       pretrained: true
       init_device: cpu
     tokenizer:
       name: EleutherAI/gpt-neo-125m
       kwargs:
         model_max_length: 1024
   icl_tasks:
   - label: lambada_smoke
     dataset_uri: local/path/to/lambada.jsonl
     num_fewshot: [0]
     icl_task_type: language_modeling
   icl_subset_num_batches: 1
   ```

2. Lint the file:

   ```bash
   python scripts/llmfoundry_eval_config_lint.py eval.yaml
   ```

3. Confirm model and tokenizer behavior before launch:

   - Hugging Face names can download model/tokenizer files unless already cached.
   - Private models need authentication handled outside YAML.
   - `mpt_causal_lm` offline eval requires a checkpoint `load_path`; use `hf_causal_lm` for ordinary Hugging Face pretrained eval.
   - `device_eval_batch_size` must be an integer for ICL tasks.

4. Launch with the installed CLI:

   ```bash
   llmfoundry eval eval.yaml
   ```

5. Apply quick overrides with key-value arguments:

   ```bash
   llmfoundry eval eval.yaml \
     max_seq_len=2048 \
     device_eval_batch_size=2 \
     models.0.model.pretrained_model_name_or_path=local-or-cached-model
   ```

6. Watch stdout for the complete-results table and, if configured, the Gauntlet-results table. See “Interpreting results” below.

## Workflow 2: custom JSONL task plus optional Eval Gauntlet category

1. Pick one task family from [task-schemas.md](task-schemas.md):

   - `generation_task_with_answers` for free-response exact match.
   - `language_modeling` for exact continuation prediction.
   - `multiple_choice` for choice scoring with `query`/`choices`/`gold`.
   - `schema` for `context_options`/`continuation`/`gold`.

2. Create a small local JSONL first. Include 2-10 rows that exercise edge cases such as spaces, categories, aliases, and nonzero gold indices.

3. Add a task block:

   ```yaml
   icl_tasks:
   - label: custom_mc
     dataset_uri: data/custom_mc.jsonl
     num_fewshot: [0, 3]
     icl_task_type: multiple_choice
     metric_names:
     - InContextLearningMultipleChoiceAccuracy
     prompt_string: "Answer the following multiple-choice questions.\n"
     continuation_delimiter: "\nAnswer: "
     example_delimiter: "\n"
     batch_size: 4
   ```

4. If the dataset has subject groups, add `category` to every JSONL row and set `has_categories: true`.

5. If aggregating with Eval Gauntlet, ensure each benchmark entry exactly matches the task `label` and one of its `num_fewshot` values:

   ```yaml
   eval_gauntlet:
     weighting: EQUAL
     subtract_random_baseline: true
     rescale_accuracy: true
     categories:
     - name: custom_reasoning
       benchmarks:
       - name: custom_mc
         num_fewshot: 3
         random_baseline: 0.25
   ```

6. Lint, then launch. For first runs, keep `icl_subset_num_batches: 1` until formatting and metrics are correct.

## Workflow 3: in-training ICL evaluation hooks

This sub-skill only owns the eval hook fields. Route optimizer, dataloader, checkpointing, and schedule design to `../training-finetuning/`.

Add these fields to an otherwise valid training YAML:

```yaml
icl_tasks: path/or/inline/tasks.yaml
eval_gauntlet: path/or/inline/eval_gauntlet.yaml
icl_seq_len: 1024
icl_subset_num_batches: 100
```

Operational guidance:

- Use a lightweight task file or a small `icl_subset_num_batches` during training. Full Gauntlet evaluation can dominate wall time.
- `icl_seq_len` is the ICL eval sequence length for training-mode eval hooks; it is separate from offline `max_seq_len` naming.
- Reuse the same task row schemas and metric names as offline eval.
- If `has_categories: true`, category labels affect logged submetrics and Gauntlet aggregation the same way as offline eval.

## Workflow 4: API-wrapper model evaluation

LLM Foundry can evaluate API-backed causal LM and chat models through registered model names such as `openai_causal_lm`, `openai_chat`, `fmapi_causal_lm`, and `fmapi_chat`.

Minimal OpenAI chat-style shape:

```yaml
seed: 1
max_seq_len: 1024
device_eval_batch_size: 4
models:
- model_name: openai/gpt-3.5-turbo
  model:
    name: openai_chat
    version: gpt-3.5-turbo
  tokenizer:
    name: tiktoken
    kwargs:
      model_name: gpt-3.5-turbo
icl_tasks:
- label: api_lm_smoke
  dataset_uri: data/api_lm_smoke.jsonl
  num_fewshot: [0]
  icl_task_type: language_modeling
  metric_names:
  - InContextLearningLMAccuracy
```

Credential and endpoint rules:

- OpenAI default endpoint requires `OPENAI_API_KEY` in the environment.
- A custom OpenAI-compatible endpoint can use `base_url`; if the endpoint does not require a real key, the wrapper uses a placeholder internally, but avoid relying on that without confirming endpoint behavior.
- FMAPI wrappers require `base_url` or `local: true`. For local FMAPI mode, `MOSAICML_MODEL_ENDPOINT` can define the endpoint; otherwise a local default is attempted.
- API eval can be slow, costly, rate-limited, and non-deterministic. Use tiny task files and low subsets first.
- Do not commit secrets to YAML. Use environment variables, local secret injection, or platform secret managers.

## Workflow 5: multi-model comparison

Use multiple entries in `models:`:

```yaml
models:
- model_name: baseline
  model: {name: hf_causal_lm, pretrained_model_name_or_path: cached-baseline, pretrained: true, init_device: cpu}
  tokenizer: {name: cached-baseline, kwargs: {model_max_length: 1024}}
- model_name: candidate
  model: {name: hf_causal_lm, pretrained_model_name_or_path: cached-candidate, pretrained: true, init_device: cpu}
  tokenizer: {name: cached-candidate, kwargs: {model_max_length: 1024}}
```

The eval loop evaluates each model, prints complete results for all models seen so far, and closes each trainer. Use distinct `model_name` values because result tables use that label.

## Interpreting results

Offline eval prints two markdown tables when relevant.

### Complete results table

The complete table has columns like:

- `Category`: Eval Gauntlet category when a matching Gauntlet config is present; otherwise blank.
- `Benchmark`: task label. For categorized datasets, one row may show benchmark average and child rows show subtasks.
- `Subtask`: category subtask name for `has_categories: true`, `Average` for the aggregate row, or blank for uncategorized tasks.
- `Accuracy`: metric value. Higher is better for the accuracy metrics covered here.
- `Number few shot`: the few-shot count as configured.
- `Model`: the `model_name` label.

Only metrics whose class name contains `Accuracy` are included in this markdown summary. Calibration metrics may be logged but not shown in this table.

### Eval Gauntlet table

When `eval_gauntlet` is configured, a separate table includes:

- `model_name`.
- Named averages such as `core_average` or a default average.
- One column per configured Gauntlet category.

If a category's benchmark is missing, the category is removed from composite scoring and a warning is logged. The most common cause is a mismatch between Gauntlet benchmark `name`/`num_fewshot` and ICL task `label`/`num_fewshot`.

## Safe preflight checklist

Before any nontrivial eval run:

- Linter has no errors and no ignored path/metric warnings.
- Local JSONL files are reachable from the intended launch directory or use absolute/user-expanded paths.
- `num_fewshot` values are lists and match Gauntlet benchmark few-shot counts.
- `metric_names` match task families.
- `device_eval_batch_size` is an integer and small enough for the model plus MC/schema expansion.
- `max_seq_len` or per-task `max_seq_len` can fit prompt, few-shot examples, context, and continuation.
- Model/tokenizer files are cached or downloading is intentionally allowed.
- API credentials and rate limits are understood for API-wrapper models.
- Full Gauntlet runs are budgeted; otherwise use `icl_subset_num_batches` smoke runs.
