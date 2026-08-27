# Task Schema

lm-evaluation-harness 0.4-style tasks are usually YAML files loaded into `TaskConfig`. Every task YAML must be a mapping and should define an explicit `task` name unless it is a pure group config.

## Leaf Task Shape

Common leaf task fields:

```yaml
task: my_task_name
task_alias: My Task
tag:
  - my_domain_tag
dataset_path: json
dataset_name: null
dataset_kwargs:
  data_files:
    validation: data/validation.jsonl
validation_split: validation
fewshot_split: validation
output_type: generate_until
doc_to_text: "Question: {{question}}\nAnswer:"
doc_to_target: "{{answer}}"
generation_kwargs:
  until: ["\n"]
metric_list:
  - metric: exact_match
    aggregation: mean
    higher_is_better: true
metadata:
  version: 1
```

Important fields from `TaskConfig`:

- Identity: `task`, `task_alias`, `tag`, `metadata`.
- Dataset loading: `dataset_path`, `dataset_name`, `dataset_kwargs`, `custom_dataset`.
- Splits: `training_split`, `validation_split`, `test_split`, `fewshot_split`.
- Prompt/data transforms: `process_docs`, `doc_to_text`, `doc_to_target`, `doc_to_choice`, `doc_to_image`, `doc_to_audio`, `description`, `target_delimiter`, `fewshot_delimiter`, `gen_prefix`, `use_prompt`.
- Few-shot formatting: `num_fewshot`, `fewshot_config`.
- Scoring/runtime: `output_type`, `generation_kwargs`, `repeats`, `filter_list`, `metric_list`, `process_results`, `should_decontaminate`, `doc_to_decontamination_query`.
- Code risk: `class` for Python-backed tasks and `unsafe_code` for tasks that intentionally execute untrusted/complex code.

## Output Types

- `generate_until`: model generates free text; usually pair with `doc_to_text`, `doc_to_target`, `generation_kwargs.until`, and generative metrics such as `exact_match`, `bleu`, `chrf`, or `ter`.
- `multiple_choice`: model scores choices; requires `doc_to_choice` and `doc_to_target` as an answer index or label that resolves to a choice.
- `loglikelihood`: scores a continuation; typically uses accuracy/perplexity-like metrics depending on task logic.
- `loglikelihood_rolling`: rolling language-modeling/perplexity style tasks.

For multiple-choice prompts, avoid trailing whitespace in `doc_to_text` when `target_delimiter` is whitespace. The harness forms choice requests by appending the delimiter and each choice.

## Prompt Fields

`doc_to_text`, `doc_to_target`, and `doc_to_choice` may be:

- A column name, such as `question` or `label`.
- A Jinja template, such as `"{{passage}}\nQuestion: {{question}}?\nAnswer:"`.
- A YAML list or dict for choices, such as `["no", "yes"]`.
- A Python helper via `!function utils.render_prompt` when string/Jinja is not enough.

Use double quotes for strings that need escape sequences like `"\n"`; single quotes preserve backslash characters literally.

## Python Helpers With `!function`

The YAML loader supports `!function module.function`. For task-local helpers, place `utils.py` beside the YAML and reference functions as:

```yaml
process_docs: !function utils.process_docs
doc_to_text: !function utils.doc_to_text
doc_to_target: !function utils.doc_to_target
```

Supported task fields for function use include `process_docs`, `doc_to_text`, `doc_to_target`, `doc_to_choice`, custom metric functions, aggregation functions, Python task `class`, custom datasets, and `process_results`. Validate the file/function exists statically before runtime import. Runtime resolution imports Python code, so get confirmation for unfamiliar or unsafe code.

## Local and Custom Datasets

For local JSON/CSV/Arrow fixtures, use Hugging Face `datasets` loaders through `dataset_path` and `dataset_kwargs`:

```yaml
dataset_path: json
dataset_name: null
dataset_kwargs:
  data_files:
    validation: data/validation.jsonl
validation_split: validation
```

Prefer relative paths inside an external task directory. If the user has a fully custom source, define `custom_dataset: !function utils.load_dataset`, returning a mapping like `{"validation": datasets.Dataset(...)}`. Keep custom loading deterministic and document required local files.

## Few-Shot Configuration

Basic few-shot selection uses `num_fewshot` and `fewshot_split`. For more control, use `fewshot_config`:

```yaml
fewshot_config:
  sampler: first_n
  split: train
  samples:
    - question: "2+2?"
      answer: "4"
  doc_to_text: "Question: {{question}}\nAnswer:"
  doc_to_target: "{{answer}}"
  fewshot_delimiter: "\n\n"
  target_delimiter: " "
```

`fewshot_config.split` takes precedence over hardcoded `samples` when both are present. Hardcoded samples must contain all fields referenced by the few-shot templates.

## Includes

`include` merges one or more YAML files before interpreting the config. Included keys load first; the child YAML overrides them. Relative includes resolve from the including YAML's directory.

```yaml
include: base.yaml
task: my_variant
doc_to_text: "{{question}}\nAnswer with one word:"
```

Include cycles are rejected by the loader. Avoid absolute include paths in portable task packages.

## Groups and Tags

Use `tag` on leaf tasks for lightweight selection sets:

```yaml
tag:
  - arithmetic_local
```

Use a group YAML when the collection needs hierarchy, aliases, aggregate metrics, or per-subtask overrides:

```yaml
group: local_reasoning_suite
group_alias: Local Reasoning
task:
  - my_task_a
  - task: my_task_b
    num_fewshot: 5
aggregate_metric_list:
  - metric: acc
    aggregation: mean
    weight_by_size: true
metadata:
  version: 1
```

The task index classifies configs with `group` as groups, configs with `class` as Python tasks, and configs with `task` as leaf tasks. Names must be unique within the scanned task directories.
