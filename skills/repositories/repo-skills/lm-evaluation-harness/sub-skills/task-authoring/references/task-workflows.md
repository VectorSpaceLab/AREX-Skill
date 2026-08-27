# Task Authoring Workflows

This reference gives practical workflows for creating, validating, and handing off lm-evaluation-harness tasks.

## Create a New External Task Directory

1. Generate a starter package:

   ```bash
   python scripts/create_task_skeleton.py my_task --output-dir ./external_tasks --with-json-fixture
   ```

2. Edit `external_tasks/my_task/my_task.yaml` and `external_tasks/my_task/utils.py`.
3. Run static lint:

   ```bash
   python scripts/lint_task_yaml.py external_tasks/my_task/my_task.yaml
   ```

4. List or validate discovery:

   ```bash
   lm-eval ls tasks --include_path ./external_tasks
   lm-eval validate --tasks my_task --include_path ./external_tasks
   ```

5. For actual scoring, route to the evaluation-runs sub-skill and choose a model/backend deliberately.

## Adapt an Existing Task Pattern

- Match the user's benchmark to an existing pattern: multiple-choice, free generation, perplexity, or grouped suite.
- Copy only the ideas, not a full catalog or unrelated benchmark definitions.
- Preserve a unique `task` name and use `task_alias` for nicer result display.
- Keep `metadata.version` in every public task variant.
- If using `include`, keep the base YAML in the same external task package and avoid absolute paths.

## Validate Without Surprises

Use three levels of validation:

1. Static, no downloads: `lint_task_yaml.py` parses YAML with `!function` preserved as strings, detects include cycles/missing includes, checks required fields, inspects filter/metric names, and warns about YAML newline pitfalls.
2. Discovery: `lm-eval validate --tasks TASK --include_path DIR` checks that `TaskManager` can find requested tasks/groups/tags for the installed package. Although the command help describes syntax, dataset, metric, filter, and template checks, version `0.4.13.dev0` primarily confirms task existence.
3. Runtime smoke: after user confirmation for dataset access and model/backend cost, run a tiny limited evaluation or write-out style prompt preview through the evaluation-runs workflow.

## External Task Directory Layout

Recommended layout:

```text
external_tasks/
  my_task/
    README.md
    my_task.yaml
    utils.py
    data/
      validation.jsonl
```

Use `--include_path external_tasks` rather than placing user experiments inside the installed package. `TaskManager` scans YAML files recursively and later include paths override earlier defaults, so unique names matter.

## Local JSON Dataset Pattern

For local JSONL data:

```yaml
task: my_local_qa
dataset_path: json
dataset_name: null
dataset_kwargs:
  data_files:
    validation: data/validation.jsonl
validation_split: validation
output_type: generate_until
doc_to_text: "Question: {{question}}\nAnswer:"
doc_to_target: "{{answer}}"
generation_kwargs:
  until: ["\n"]
metric_list:
  - metric: exact_match
metadata:
  version: 1
```

Keep data files small for tests. For private or large data, document expected relative paths and avoid bundling secrets.

## Python Helper Pattern

Use `utils.py` for preprocessing and nontrivial rendering:

```python
def process_docs(dataset):
    def normalize(doc):
        return {
            "question": doc["question"].strip(),
            "answer": doc["answer"].strip(),
        }
    return dataset.map(normalize)
```

YAML:

```yaml
process_docs: !function utils.process_docs
```

Task-local `!function` references resolve relative to the YAML directory first. Runtime import executes Python, so inspect helper code and ask before running unfamiliar task packages.

## Group Authoring Workflow

1. Define and statically lint all leaf task YAMLs.
2. Create a group YAML with `group`, `task`, optional `group_alias`, `aggregate_metric_list`, and `metadata`.
3. Use `lm-eval validate --tasks GROUP --include_path DIR` to check discovery.
4. For aggregate metrics, verify all subtasks emit the same metric/filter key names.

Example:

```yaml
group: my_suite
task:
  - my_task_easy
  - task: my_task_hard
    num_fewshot: 5
aggregate_metric_list:
  - metric: exact_match
    aggregation: mean
    weight_by_size: true
metadata:
  version: 1
```

## Few-Shot Workflow

- If examples come from the dataset, set `fewshot_split` and runtime `num_fewshot`.
- If examples need different formatting, use `fewshot_config` with override templates.
- If examples are fixed and tiny, use `fewshot_config.samples` or `utils.list_fewshot_samples`.
- Validate that every sample includes keys used by few-shot `doc_to_text`, `doc_to_target`, and `doc_to_choice`.

## Handoff to Evaluation Runs

When the YAML passes static lint and discovery validation, hand off with:

- Task name(s) and external `--include_path`.
- Dataset access requirements and any local files.
- Whether `!function`, custom dataset, Python task class, or `unsafe_code` is present.
- Suggested smoke-test limit, model, and backend constraints.
- Known non-default filters, metrics, repeats, and generation kwargs.
