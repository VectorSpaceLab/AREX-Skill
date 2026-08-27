# Recipe workflows

SpeechBrain recipes are usually organized as dataset/task/model directories. A typical recipe contains a Python script, a HyperPyYAML file, dataset preparation code, and a README. Template directories provide minimal starting points for new recipes.

## Recipe anatomy

Common files:

```text
recipes/<Dataset>/<Task>/<Model>/
  train.py                  # experiment script, often subclassing speechbrain.Brain
  hparams/*.yaml            # HyperPyYAML experiment configuration
  *_prepare.py              # dataset preparation helper, often downloads or writes manifests
  README.md                 # data, dependency, model, result, and run instructions
  extra_requirements.txt    # optional recipe-specific dependencies
```

Templates have the same idea under `templates/<task>/` and are better starting points than copying a large dataset-specific recipe.

## Launching a recipe

The canonical pattern is:

```bash
python train.py hparams/train.yaml --override_name override_value
```

The first positional argument is the hparams file. Known SpeechBrain runtime flags become `RunOptions`; other arguments become HyperPyYAML overrides.

Common runtime flags:

- `--device cpu` or `--device cuda:0`
- `--debug`, `--debug_batches`, `--debug_epochs`
- `--test_only`
- `--precision fp32|fp16|bf16`
- `--eval_precision fp32|fp16|bf16`
- `--compile`, `--jit` and module-key variants
- `--ckpt_interval_minutes`, `--ckpt_interval_steps`
- `--grad_accumulation_factor`

Common hparam overrides are recipe-defined, such as `--data_folder`, `--train_csv`, `--valid_csv`, `--test_csv`, `--output_folder`, `--skip_prep=True`, `--number_of_epochs=2`, or model-size knobs.

## Data preparation

Dataset preparation files build CSV/JSON manifests or folder layouts consumed by the training script. They may download datasets, unpack archives, normalize paths, or parallelize scans. Before running a preparation script, resolve:

- Where the raw dataset lives.
- Where generated CSV/JSON manifests should be written.
- Whether network downloads are acceptable.
- Whether preparation is deterministic and idempotent.
- Whether `--skip_prep=True` should be used.

Use `--skip_prep=True` when running a small already-prepared fixture or when verifying training code only.

## Output folders

Recipes usually write an `output_folder` containing:

- `env.log`
- `hyperparams.yaml`
- `log.txt`
- `train_log.txt` or task-specific logs
- checkpoints under `save/`
- task metrics such as WER/PER files, predictions, enhanced wavs, or label encoders

The output folder is often created through `speechbrain.core.create_experiment_directory`.

## Using `tests/recipes/*.csv`

The recipe CSV catalogs encode real debug flags and expected output files. They are valuable for constructing safe smoke runs without guessing. Typical fields:

- `Task`
- `Dataset`
- `Script_file`
- `Hparam_file`
- `Data_prep_file`
- `Readme_file`
- `Result_url`
- `HF_repo`
- `test_debug_flags`
- `test_debug_checks`
- `performance`

Use the bundled `inspect_recipe_catalog.py` helper to print candidate commands from CSV rows without running them.

## Creating or adapting a recipe

1. Start from the closest template or a tiny integration example rather than a large production recipe.
2. Define a `Brain` subclass and override at least `compute_forward` and `compute_objectives`.
3. Build `DynamicItemDataset` objects and add audio/text/label pipelines.
4. Keep HyperPyYAML responsible for modules, optimizers, schedulers, losses, loggers, and paths.
5. Provide a `--debug` or tiny fixture path before full training.
6. Add/update recipe CSV metadata if contributing to the repository.
7. Document recipe-specific `extra_requirements.txt` and data prep side effects.
