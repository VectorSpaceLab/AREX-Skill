# Troubleshooting Task YAMLs

Use this checklist when a task does not load, validate, or score as expected.

## Literal `\n` Instead of Newlines

Symptom: generation never stops, regexes fail, or prompts show backslash-n characters.

Cause: YAML single quotes preserve backslashes. `['\n']` is a literal backslash plus `n`, not an actual newline.

Fix:

```yaml
generation_kwargs:
  until: ["\n"]
```

For prompt text, prefer block scalars for multiline strings:

```yaml
doc_to_text: |
  Passage: {{passage}}
  Question: {{question}}
  Answer:
```

## YAML Quoting and Regex Escapes

- Single quotes preserve most text literally; escape a single quote by doubling it.
- Double quotes interpret escapes, so regex backslashes often need doubling.
- Plain strings can be misread as booleans, numbers, mappings, or comments when they contain `:`, `#`, `{}`, `[]`, or leading special characters.
- Jinja templates are safest when quoted or written as block scalars.

## Include Failures

Symptoms: missing inherited fields, `Include cycle`, or file-not-found errors.

Checks:

- Relative includes resolve from the YAML file's directory.
- Child keys override included keys.
- `include` can be a string or list of strings.
- Avoid absolute paths in portable task packages.
- Break cycles such as `a.yaml -> b.yaml -> a.yaml`.

## Missing Task or Group

Symptoms: `lm-eval validate` says `Tasks not found` or `TaskManager` cannot load a name.

Checks:

- Leaf YAML has `task: exact_name`.
- Group YAML has `group: exact_group_name`.
- The parent directory is included with `--include_path`.
- Names are unique; later include paths override earlier indexed tasks.
- Filename does not matter as much as the YAML `task` or `group` value.

## Invalid `!function` Paths

Symptoms: import errors, missing function errors, or validation works statically but runtime load fails.

Checks:

- The referenced file is next to the YAML for local references like `!function utils.process_docs`.
- The final component is a function/class name that exists.
- Helper imports are installed in the runtime environment.
- The helper does not rely on local absolute paths.
- The helper signature matches the field: `process_docs(dataset)`, `custom_dataset(...)`, `doc_to_text(doc)`, `process_results(doc, results)`, or metric/aggregation expectations.

Do not runtime-import unfamiliar `!function` code until the user confirms that executing task-local Python is acceptable.

## Dataset Split Mismatch

Symptoms: `KeyError` for a split, no evaluation docs, or few-shot errors.

Checks:

- `validation_split`, `test_split`, `training_split`, and `fewshot_split` exactly match the loaded dataset's split names.
- If `num_fewshot > 0`, a usable `fewshot_split` or `fewshot_config` is available.
- For local JSON/CSV, `dataset_kwargs.data_files` maps split names to real files.
- If only `test_split` exists, avoid drawing few-shot examples from test unless explicitly intended and documented.

## Prompt Rendering Errors

Symptoms: missing Jinja variables, malformed prompts, or multiple-choice target errors.

Checks:

- All template variables exist in each processed document.
- `process_docs` returns the names expected by the templates.
- `doc_to_choice` returns a list of strings for `multiple_choice`.
- `doc_to_target` is an integer index or a label compatible with the choices for `multiple_choice`.
- Avoid trailing whitespace in `doc_to_text` when `target_delimiter` is a space.

## Filter Return Shape Bugs

Symptoms: metric receives lists, filter pipeline crashes, or result keys show unexpected values.

Checks:

- `regex`, `lowercase`, `uppercase`, and `map` preserve a list per document.
- `majority_vote` returns a one-item list per document; usually follow it with `take_first`.
- `take_first` unwraps each response list to a scalar.
- `take_first_k` requires at least `k` responses per document, so `repeats` must be high enough.
- `multi_choice_regex` expects `choices` in each doc.

## Metric and Aggregation Issues

Symptoms: undefined metric/aggregation, wrong directionality, or group aggregate missing.

Checks:

- The metric is registered or supplied with a valid `!function`.
- `aggregation` and `higher_is_better` are present for custom metrics.
- The metric supports the task `output_type`.
- For group aggregation, each child task emits the metric and filter key being aggregated.
- Exact match options like `ignore_case`, `ignore_punctuation`, and `regexes_to_ignore` belong under the metric entry.

## Unsafe Code Tasks

Treat these as requiring explicit confirmation before runtime execution:

- `unsafe_code: true`.
- Python task `class: !function ...`.
- `custom_dataset: !function ...`.
- `process_results`, custom metric, custom aggregation, or custom filter code from an untrusted task package.
- Local dataset loading scripts or helpers that read arbitrary paths.

Static lint is safe because it does not import helper code or download datasets.

## When to Escalate

Escalate to another sub-skill or ask the user when:

- A full evaluation or model selection is needed: use evaluation-runs.
- Backend/extras installation is needed: use model-backends.
- Score tables, JSON outputs, or leaderboard comparisons need interpretation: use result-logging.
- The task depends on private datasets, credentials, remote code, or local scripts with side effects.
