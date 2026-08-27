# OpenPrompt Data And Config Troubleshooting

## Config YAML Does Not Load

Symptoms:

- YAML parser errors.
- Nested CLI flags missing or wrong type.
- `get_user_config` fails before training begins.

Checks:

1. Confirm the file is valid YAML. Quote template strings that contain `{}`, `:`, `#`, or leading spaces.
2. Keep booleans as YAML booleans (`true`/`false`) rather than strings unless the downstream code expects strings.
3. Lists such as seeds or `cuda_visible_devices` should be YAML lists, not comma-separated strings.
4. Run the bundled inspector with `--json` if a machine-readable summary is easier to audit.

## Selected Branch Is Missing

Symptoms:

- `template: some_branch` or `verbalizer: some_branch` is set, but the expected branch values are absent after config merging.
- A custom branch is present but not activated.

Cause:

OpenPrompt's `get_conditional_config` attaches top-level branches by matching scalar string selector values to branch names. User-supplied conditional branches should include `parent_config`.

Fix pattern:

```yaml
template: manual_template
manual_template:
  parent_config: template
  file_path: <ASSET_DIR>/manual_template.txt
```

For few-shot sampling:

```yaml
learning_setting: few_shot
few_shot:
  parent_config: learning_setting
  few_shot_sampling: sampling_from_train
sampling_from_train:
  parent_config: few_shot_sampling
  num_examples_per_label: 8
```

## Unknown Dataset Name

Symptoms:

- `KeyError` in `PROCESSORS[dataset_config.name.lower()]`.
- The config looks valid, but `load_dataset` cannot find a processor.

Checks:

1. Compare `dataset.name` to the catalog in `api-reference.md`.
2. Use lowercase names for normal YAML workflows.
3. For HuggingFace wrappers, include the namespace, e.g. `super_glue.boolq`, not just `boolq` if you want the HuggingFace processor.
4. Avoid YAML `dataset.name: LAMA` for `load_dataset`; the source map's uppercase key conflicts with lowercasing and the processor also needs constructor arguments.

## Dataset Path Exists But Splits Are Missing

Symptoms:

- Warnings such as no train/dev/test dataset in a path.
- `load_dataset` logs that the dataset is empty and exits.

Checks by family:

- Local FewGLUE uses `train.jsonl`, `dev32.jsonl`, and `val.jsonl`, not `dev.jsonl` and `test.jsonl`.
- SST-2 and SNLI use TSV split files with headers/expected columns.
- DBpedia/IMDB/Amazon need `<split>.txt` and matching `<split>_labels.txt` sidecar files.
- TACRED/TACREV/ReTACRED use JSON split files; SemEval uses JSONL.
- FewNERD expects `supervised/<split>.txt` under the dataset directory.
- CSQA uses `train_rand_split.jsonl`, `dev_rand_split.jsonl`, and `test_rand_split_no_answers.jsonl`.

The bundled inspector checks only existence and naming. It does not parse full benchmark data unless the user asks for a fixture-level read.

## Relative Paths Point To The Wrong Directory

Symptoms:

- `manual_template.file_path` exists when run from the project root but not from another cwd.
- Dataset paths copied from examples fail in a project.

Cause:

Repo examples were written to be launched from the checkout root with `python experiments/cli.py --config_yaml experiments/<name>.yaml`. Relative paths therefore often assume a particular process cwd, not the config file's directory.

Fixes:

- Prefer absolute paths for user projects.
- Or pass the intended root to the inspector and to any launcher wrapper.
- Replace example placeholders with project-owned paths, e.g. `<DATA_ROOT>/TextClassification/agnews` and `<ASSET_DIR>/manual_template.txt`.

## Prompt Asset Path Is Missing

Symptoms:

- Template/verbalizer loader cannot find `file_path`.
- Training begins but fails when prompt assets load.

Checks:

1. Validate all keys named `file_path` with the inspector.
2. Distinguish prompt assets from model identifiers: `plm.model_path: bert-large-cased` is a HuggingFace ID, not a local file requirement.
3. Route malformed prompt text, verbalizer label words, or template grammar errors to `../template-verbalizer-design/`.

## HuggingFace Dataset Or Model Downloads Unexpectedly Start

Symptoms:

- Runtime tries network access during dataset/model loading.
- Offline environment fails despite static config success.

Causes:

- `dataset.name` is a HuggingFace processor such as `super_glue.boolq`.
- `plm.model_path` is a HuggingFace model ID rather than a local cache path.

Fixes:

- Ask the user whether downloads are allowed.
- Provide local caches/paths and document cache environment variables.
- For purely static work, do not instantiate HuggingFace processors or PLMs.

## Few-Shot Sampling Fails Or Gives Odd Counts

Symptoms:

- `ValueError`: total and per-label strategies both missing or both set.
- Assertion failure because examples lack `label`.
- Some labels have fewer selected examples than requested.

Fixes:

- Set exactly one of `num_examples_total` or `num_examples_per_label`.
- For generation datasets, use total sampling or a custom labeled fixture; per-label sampling needs classification labels.
- Check class balance before promising exact per-label counts.
- Use deterministic `seed` values and record them in the config.

## GPU Flags Do Not Guarantee GPU Readiness

Symptoms:

- Config contains `environment.num_gpus: 1`, but runtime still uses CPU or fails on CUDA.
- `cuda_visible_devices` is empty, wrong type, or inconsistent with `local_rank`.

Notes:

- This sub-skill can report the requested flags only.
- Actual torch/CUDA installation, device placement, model parallelism, and runner behavior must be verified by the training/generation workflow.

## Source Bugs And Sharp Edges To Remember

- `RecordProcessor.get_examples` is declared static but references `data_dir`; verify before depending on it.
- `UltraChatProcessor.get_examples` accepts a single data file path rather than the base `(data_dir, split)` convention, so normal `load_dataset` routing is awkward.
- `LAMAProcessor` is not a normal YAML-config processor: the map key/lowercase behavior and required constructor arguments both need special handling.
- `classification_mixed_template_freeze.yaml` in repo examples uses a top-level `valid` block, while `experiments/cli.py` builds dev dataloaders from `config.dev`; check this if adapting that example.
