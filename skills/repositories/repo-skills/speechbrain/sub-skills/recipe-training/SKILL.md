---
name: recipe-training
description: "Guides SpeechBrain recipe and template training workflows,
  HyperPyYAML overrides, Brain loops, debug/test-only runs, recipe catalogs, and
  CPU/GPU/DDP launch choices."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# SpeechBrain recipe training

Use this sub-skill when the task is to run, adapt, debug, or create SpeechBrain recipes or templates. This includes `train.py`, `hparams.yaml`, HyperPyYAML, `Brain`, `RunOptions`, dataset preparation, debug flags, and distributed training.

## Core route

1. Read `references/recipe-workflows.md` to understand recipe layout, data prep, output folders, and command construction.
2. Read `references/hyperpyyaml-and-run-options.md` when editing hparams, placeholders, overrides, runtime options, or `Brain` code.
3. Read `references/native-examples.md` to map tiny integration examples and recipe CSV debug rows to verification ideas.
4. Read `references/distributed-and-debugging.md` for CPU/GPU debug, DDP, and multi-node launches.
5. Read `references/troubleshooting.md` for slow downloads, missing extras, bad overrides, and device failures.
6. Use `scripts/inspect_recipe_catalog.py` to inspect a `tests/recipes/*.csv` catalog and build a debug command without running the recipe.

## Common command shapes

Local recipe run:

```bash
cd recipes/<dataset>/<task>/<model>
python train.py hparams/train.yaml --data_folder /path/to/data --device cpu
```

Debug a cataloged recipe from repository root:

```bash
python sub-skills/recipe-training/scripts/inspect_recipe_catalog.py \
  --csv /path/to/recipe-catalog.csv --row 2 --print-command --device cpu
```

DDP single-node pattern:

```bash
cd recipes/<dataset>/<task>/<model>
torchrun --standalone --nproc_per_node=4 train.py hparams/train.yaml
```

## Safety rules

- Dataset preparation scripts can download or rewrite large datasets. Use `--skip_prep=True` when using pre-existing fixtures or when data prep is out of scope.
- Recipe-specific `extra_requirements.txt` files can install large or conflicting packages. Install only the selected recipe's extras.
- HyperPyYAML can construct Python objects. Treat untrusted recipe YAML as code.
- CPU debug runs prove control/data flow only; they do not verify full recipe performance or CUDA throughput.
