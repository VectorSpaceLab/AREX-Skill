---
name: training-evaluation-and-tuning
description: "Run, evaluate, tune, reload, compare, and troubleshoot RecBole
  experiments with safe CPU-first workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# RecBole training, evaluation, and tuning

Use this sub-skill when the user asks how to run or troubleshoot RecBole experiments after the model and dataset/config choices are known. It covers one-model train/evaluate jobs, API smoke tests, grouped model comparisons, checkpoints and save/load, case-study scoring, HyperTuning/Hyperopt/Ray, statistical significance, and CPU/GPU/distributed runtime choices.

## Route here for

- "run BPR on ml-100k", "write a `run_recbole` config", or "make a one-epoch CPU smoke test".
- "load a saved RecBole checkpoint", "save dataset/dataloaders", or "get top-k items for a user".
- "tune RecBole hyperparameters", "write a `hyper.test` file", "why did Ray tuning fail?".
- "compare two RecBole models statistically", "run repeated seeds", or "interpret valid/test metrics".
- "use GPU", "avoid GPU", "use distributed training", or "what do `nproc/world_size/ip/port/group_offset` mean?".

## Do not handle here

- Atomic file schema, field names, `load_col`, dataset acquisition, or `data_path` layout details: route to `../configuration-and-data/`.
- Model-family choice, custom recommender classes, custom trainers, or model registration: route to `../models-and-customization/`.
- Long benchmark campaigns without an explicit budget. Give a bounded plan first; significance tests, grouped runs, Ray tuning, and full HPO can multiply training cost.

## Core public APIs

RecBole exposes these stable routes for this skill:

```python
from recbole.quick_start import run, run_recbole, objective_function, load_data_and_model

run(model, dataset, config_file_list=None, config_dict=None, saved=True,
    nproc=1, world_size=-1, ip='localhost', port='5678', group_offset=0)
run_recbole(model=None, dataset=None, config_file_list=None, config_dict=None,
            saved=True, queue=None)
objective_function(config_dict=None, config_file_list=None, saved=True)
load_data_and_model(model_file)
```

At trainer level, the reference methods are:

```python
Trainer.fit(train_data, valid_data=None, verbose=True, saved=True,
            show_progress=False, callback_fn=None)
Trainer.evaluate(eval_data, load_best_model=True, model_file=None,
                 show_progress=False)
```

## Safe default pattern

For a bounded CPU smoke test, prefer:

- `use_gpu: False`
- one or a few `epochs`
- `show_progress: False`
- `saved=False` when no checkpoint is needed
- an explicit `checkpoint_dir` when `saved=True`
- a dedicated working directory so logs/checkpoints are not written into a source checkout by accident

Use the bundled wrapper first when the user wants an executable safe starting point:

```bash
python scripts/recbole_train_eval_smoke.py --dry-run-config
python scripts/recbole_train_eval_smoke.py --run --model BPR --dataset ml-100k --epochs 1 --work-dir ./recbole-runs/bpr-smoke
```

The wrapper imports installed RecBole from the active Python environment and does not rely on a repository checkout.

## References and helpers

- [Training, evaluation, save/load, case-study, and significance reference](references/training-and-evaluation.md)
- [Hyperparameter tuning, Hyperopt, and Ray reference](references/hyperparameter-tuning.md)
- [Troubleshooting reference](references/troubleshooting.md)
- [`scripts/recbole_train_eval_smoke.py`](scripts/recbole_train_eval_smoke.py): CPU-first one-model wrapper around `run` / `run_recbole`; no training side effects unless `--run` is passed.
- [`scripts/recbole_hyperopt_template.py`](scripts/recbole_hyperopt_template.py): writes and validates HyperTuning parameter files; optional tiny Hyperopt run only with `--run`.
- [`scripts/recbole_save_load_recipe.py`](scripts/recbole_save_load_recipe.py): validates a checkpoint path, prints the load/case-study API sequence, and can execute top-k scoring for supplied users.

## Workflow outline

1. Confirm model, dataset, data path/config file, and budget. If dataset/config details are missing, route to the configuration/data sibling first.
2. For smoke runs, use CPU, small epochs, `show_progress=False`, `saved=False`, and a non-checkout `--work-dir`.
3. Inspect the result dictionary keys: `best_valid_score`, `valid_score_bigger`, `best_valid_result`, and `test_result`. `objective_function` additionally returns `model`.
4. For saved models, set `saved=True` plus `checkpoint_dir`, optionally `save_dataset=True` and `save_dataloaders=True`, then reload with `load_data_and_model(model_file)`.
5. For case studies, convert external user/item tokens with `dataset.token2id`, run `full_sort_scores` or `full_sort_topk`, and convert item ids back with `dataset.id2token`.
6. For HPO, start with a small validated parameter file and `algo='random'`/low `max_evals` unless the user explicitly wants exhaustive search.
7. For Ray, require absolute `data_path` and absolute fixed config file paths because Ray changes worker working directories.
8. For significance, run both models on matched seeds and apply a paired t-test to each common metric; warn that repeated training is expensive.

## Verification focus cases

Future verification should include at least these synthetic usability cases:

1. Create a no-checkpoint one-epoch CPU BPR run that returns valid/test metrics and writes only under a user-chosen run directory.
2. Explain and fix a Ray tuning failure caused by relative `data_path` after Ray changes the working directory to `local_dir`.
