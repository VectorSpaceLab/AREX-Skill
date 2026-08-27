---
name: configuration-and-data
description: "Build, validate, and troubleshoot RecBole Config objects, atomic
  datasets, load_col settings, and dataset/dataloader preparation flows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# RecBole Configuration and Data

Use this sub-skill when the user is working with RecBole configuration objects,
YAML/dict/CLI overrides, atomic data files, dataset preprocessing, or split
DataLoader creation. Keep the answer focused on creating or diagnosing the
configuration/data layer; route model internals and training loops to siblings.

## Trigger requests

- "prepare a RecBole dataset" or "convert my data to RecBole atomic files".
- "fix my `load_col` config", "why is my `.user` file ignored?", or "load an
  extra feature file".
- "explain RecBole atomic files", including `.inter`, `.user`, `.item`, `.kg`,
  `.link`, and `.net`.
- "create a YAML config for sequential recommendation" or context-aware,
  knowledge-aware, social, or general data preparation.
- "why does `Config` ignore my value?" or any conflict among YAML,
  `config_dict`, command-line arguments, and defaults.
- "split and save dataloaders" or "load saved dataloaders" without asking for a
  full training run.
- Data failures involving `data_path`, missing dataset directories, missing
  `field:type` header suffixes, delimiter mistakes, YAML/list quoting, GPU
  fallback, filtering/splitting knobs, or cache paths.

## Quick workflow

1. Identify the task family: general, context-aware, knowledge-aware,
   sequential, or social. Use this to decide mandatory atomic files and the
   model/dataset defaults likely to be injected by `Config`.
2. Determine the expected RecBole dataset name. The directory should contain
   files named like `<dataset>.inter`; for most non-bundled datasets,
   `data_path` is the parent directory and `Config` appends the dataset name.
3. Construct the configuration with:

   ```python
   from recbole.config import Config

   config = Config(
       model="BPR",
       dataset="my_dataset",
       config_file_list=["config.yaml"],
       config_dict={"load_col": None},
   )
   ```

4. Apply configuration priority exactly: command line `--key=value` overrides
   `config_dict`, which overrides later values merged from `config_file_list`,
   which overrides RecBole defaults. If `model` or `dataset` are passed directly
   to `Config`, those constructor arguments select the final model/dataset.
5. Validate atomic data before running RecBole. Use the bundled helper:

   ```bash
   python scripts/validate_atomic_dataset.py /path/to/dataset-root/my_dataset \
     --dataset my_dataset --task-family general
   ```

6. If the user asks to build runtime objects, use the documented data flow:

   ```python
   from recbole.data import (
       create_dataset,
       data_preparation,
       save_split_dataloaders,
       load_split_dataloaders,
   )

   dataset = create_dataset(config)
   train_data, valid_data, test_data = data_preparation(config, dataset)
   save_split_dataloaders(config, (train_data, valid_data, test_data))
   cached = load_split_dataloaders(config)
   ```

7. For errors, first inspect the resolved values (`config["data_path"]`,
   `config["load_col"]`, `config["eval_args"]`, `config["device"]`) rather than
   assuming the YAML file won.

## Config surfaces to cover here

- Five groups: environment, data, model, training, and evaluation. Discuss model
  settings only as they affect data defaults; send model choice/customization to
  `models-and-customization`.
- Environment/data keys: `use_gpu`, `gpu_id`, `data_path`, `checkpoint_dir`,
  `save_dataset`, `dataset_save_path`, `save_dataloaders`,
  `dataloaders_save_path`, `field_separator`, `seq_separator`, `load_col`,
  `unload_col`, `unused_col`, `additional_feat_suffix`, `alias_of_user_id`,
  `alias_of_item_id`, `alias_of_entity_id`, `alias_of_relation_id`, filtering
  knobs, benchmark/pre-split knobs, and the shape of `eval_args`.
- Training/evaluation keys only enough for routing and splits: `epochs`, batch
  sizes, `train_neg_sample_args`, `eval_args`, `metrics`, `topk`,
  `valid_metric`, `repeatable`, and evaluation modes. Route full training,
  checkpointing, metrics interpretation, HyperTuning, Ray, and significance
  tests to `training-evaluation-and-tuning`.

## Atomic data rules to enforce

- Headers must use `field_name:field_type`; valid types are `token`,
  `token_seq`, `float`, and `float_seq`.
- Default column delimiter is a tab. Sequence-valued cells use the sequence
  separator, usually a single space.
- Mandatory files by task family:
  - general: `.inter`
  - context-aware: `.inter`, `.user`, `.item`
  - knowledge-aware: `.inter`, `.kg`, `.link`
  - sequential: `.inter`
  - social: `.inter`, `.net`
- `load_col: null` loads all existing standard files used by the dataset class.
  If `load_col` is a dict and a suffix is absent, RecBole treats that file as
  not loaded. Include every required source and field explicitly, or use `"*"`
  for all fields in a source.
- Do not set `load_col` and `unload_col` for the same source in normal guidance.

## Key references and helper

- See [configuration-and-data.md](references/configuration-and-data.md) for
  config priority examples, atomic file tables, `load_col` patterns, dataset
  construction, saving, and loading.
- See [troubleshooting.md](references/troubleshooting.md) for symptom/cause/fix
  tables, including missing header type suffixes and override surprises.
- Use [scripts/validate_atomic_dataset.py](scripts/validate_atomic_dataset.py)
  to check local atomic files without importing RecBole.

## Boundaries and sibling routing

- Route actual model training/evaluation loops, checkpoint semantics, metric
  selection strategy, HyperTuning, Ray integration, and statistical tests to
  `../training-evaluation-and-tuning/SKILL.md`.
- Route model family selection, custom models, trainers, samplers, dataloaders,
  metrics, transforms, and extension APIs to
  `../models-and-customization/SKILL.md`.
- Do not ask a future agent to reopen RecBole source files for the topics in
  this sub-skill; the bundled references and script are the runtime evidence.

## Answer checklist

Before finalizing a configuration/data answer, include:

- Expected dataset directory and file names.
- Minimal YAML or `config_dict` with correctly quoted lists/dicts.
- Resolved priority explanation when values conflict.
- `load_col` or `unload_col` behavior for every required suffix.
- Atomic header remediation if a file does not use `name:type` columns.
- Whether saved dataset/dataloader caches are being created, loaded, or ignored.
- Clear routing note if the user is really asking for training, tuning, or model
  customization.
