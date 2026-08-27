---
name: evaluation
description: "Routes Promptify dataset loading, metric selection, ROUGE
  evaluation, and score aggregation for task outputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Evaluation

Use this sub-skill when the user wants to score Promptify task outputs against labeled data, load an evaluation dataset, or understand the metric and dataset formats supported by `promptify.eval`.

## Covered workflows

- Loading datasets from in-memory lists, JSON files, or CSV files.
- Running `evaluate()` against a Promptify task object or a compatible mock.
- Selecting metrics such as precision, recall, F1, accuracy, exact match, and ROUGE.
- Interpreting warnings, zero scores, and task failures during evaluation.

## Read first

- `references/api-reference.md` for the evaluation function signatures and metric registry.
- `references/data-formats.md` for dataset shapes and validation rules.
- `references/workflows.md` for small evaluation recipes and progress callback examples.
- `references/troubleshooting.md` for missing keys, unsupported formats, unknown metrics, and ROUGE dependency issues.
- `../../scripts/check_promptify.py --mode evaluation` for a no-network smoke test.

## Route boundaries

### Include here
- Turning a list, JSON file, or CSV file into a Promptify evaluation dataset.
- Choosing metrics and interpreting their outputs.
- Understanding how task exceptions are converted into zero scores for a sample.
- Reading the ROUGE dependency note and the exact dataset key requirements.

### Exclude or route elsewhere
- Task construction, prompt templates, parser behavior, and provider auth belong to structured-tasks.
- Repository maintenance, package release work, or notebook conversion do not belong here.
- Archived notebook or tutorial API names are not the current evaluation API.

## Mental model

Evaluation is a thin wrapper around the same Promptify task objects used at runtime:

1. `load_dataset()` normalizes the data source.
2. `evaluate()` iterates through the samples.
3. The task is called for each input.
4. Metric functions compare predicted and expected outputs.
5. The final result is the average score per metric.

## Use this route when the user asks for

- "Load a CSV dataset and score a task"
- "Compute exact match, F1, or ROUGE for Promptify outputs"
- "Figure out why evaluation returned 0.0"
- "Add progress reporting to evaluation"
- "Understand the dataset schema for Promptify evaluation"

## When to switch back to structured tasks

If the conversation moves from scoring outputs to building the task object or fixing its prompt, switch back to the structured-tasks sub-skill.
