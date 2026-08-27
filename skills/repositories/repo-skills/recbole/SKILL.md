---
name: recbole
description: "Use RecBole for recommender-system data preparation, model
  selection, training, evaluation, tuning, and customization workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# RecBole

Use this repo skill when the task is about RecBole, the `recbole` Python
package, or recommender-system experiments that need RecBole-style atomic data,
configuration, models, training/evaluation, hyperparameter tuning, or extension
points.

RecBole is a PyTorch-based recommendation library covering general,
sequential, context-aware/CTR, and knowledge-aware recommendation. This skill is
self-contained operating guidance for using the installed package; do not rely
on the original repository checkout at runtime.

## Start here

1. Confirm the active environment can import RecBole and PyTorch:

   ```bash
   python -c "import recbole, torch; print(recbole.__version__); print(torch.__version__)"
   ```

2. For a richer smoke check, run the bundled helper from this skill:

   ```bash
   python scripts/check_recbole_env.py --models BPR SASRec --check-optional
   ```

3. Route the task to the narrowest sub-skill below. Read
   [references/repo-provenance.md](references/repo-provenance.md) before
   deciding whether this skill is current for a different RecBole checkout.

## Sub-skill routes

### Configuration and data

Read [configuration-and-data](sub-skills/configuration-and-data/SKILL.md) when
the user needs to:

- create or debug `Config(model, dataset, config_file_list, config_dict)`;
- understand YAML/dict/CLI priority;
- prepare RecBole atomic files such as `.inter`, `.user`, `.item`, `.kg`,
  `.link`, or `.net`;
- fix `load_col`, `data_path`, field-type headers, dataset filtering/splitting,
  saved dataset, or saved dataloader issues;
- validate a dataset with the bundled atomic-file checker.

### Training, evaluation, and tuning

Read [training-evaluation-and-tuning](sub-skills/training-evaluation-and-tuning/SKILL.md)
when the user needs to:

- run `BPR`, `SASRec`, `FM`, `KGAT`, or another model with `run` or
  `run_recbole`;
- build a no-checkpoint CPU smoke run or a saved experiment run;
- interpret valid/test metrics, grouped model results, or significance tests;
- use `load_data_and_model`, `full_sort_topk`, or `full_sort_scores`;
- run HyperTuning/Hyperopt/Ray or diagnose HPO/GPU/distributed failures.

### Models and customization

Read [models-and-customization](sub-skills/models-and-customization/SKILL.md)
when the user needs to:

- choose among general, sequential, context-aware/CTR, knowledge-aware, or
  external-library model families;
- resolve model class names with `get_model`/`get_trainer`;
- understand model-property defaults and task-specific data prerequisites;
- implement or diagnose custom recommenders, trainers, dataloaders, samplers,
  or metrics.

## Shared references and helpers

- [references/api-surface.md](references/api-surface.md) lists verified public
  API signatures and how root/sub-skill guidance uses them.
- [references/troubleshooting.md](references/troubleshooting.md) covers
  cross-cutting install/import, optional dependency, backend, and route-choice
  failures.
- [scripts/check_recbole_env.py](scripts/check_recbole_env.py) is a safe
  import/model/backend diagnostic helper.

## Default operating stance

- Prefer CPU-safe examples first: set `use_gpu: False`, small `epochs`,
  `show_progress: False`, and `saved=False` unless the user explicitly wants
  checkpoints.
- Treat CUDA, multi-GPU/distributed training, Ray GPU trials, W&B, and long HPO
  as optional/budget-sensitive paths. Verify hardware, credentials, and output
  directories before enabling them.
- Put complex data layout and `load_col` work in the configuration/data route
  before training.
- Put model-family decisions before experiment execution. CTR/side-feature
  requests usually belong to context-aware models; knowledge-graph requests
  require KG/link data; sequence/session requests belong to sequential models.
- If a workflow spans multiple areas, handle it in this order: data/config →
  model selection/customization → training/evaluation/tuning.

## Do not use this skill for

- Generic PyTorch training not using RecBole.
- Editing RecBole source internals as a maintainer task; use a repository
  maintenance route if the user asks to modify the repo itself.
- Recommendation frameworks outside RecBole unless the user is translating a
  workflow into RecBole terms.
