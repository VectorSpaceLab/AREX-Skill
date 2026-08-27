# RecBole API Surface

Use this reference when a task needs exact public API entry points before going
to a deeper sub-skill. The signatures below were verified against `recbole`
version `1.2.1`.

## Quick-start experiment APIs

```python
from recbole.quick_start import run, run_recbole, objective_function, load_data_and_model

run(model, dataset, config_file_list=None, config_dict=None, saved=True,
    nproc=1, world_size=-1, ip='localhost', port='5678', group_offset=0)
run_recbole(model=None, dataset=None, config_file_list=None, config_dict=None,
            saved=True, queue=None)
objective_function(config_dict=None, config_file_list=None, saved=True)
load_data_and_model(model_file)
```

Notes:

- `run` is the script-facing route and accepts distributed arguments.
- `run_recbole` is the compact single-process API.
- `objective_function` is the HyperTuning-compatible route.
- `load_data_and_model(model_file)` reloads a saved checkpoint and its packaged
  config/data objects for case-study or evaluation workflows.

For run/evaluation details, read
`sub-skills/training-evaluation-and-tuning/SKILL.md`.

## Config and data APIs

```python
from recbole.config import Config
from recbole.data import (
    create_dataset,
    data_preparation,
    save_split_dataloaders,
    load_split_dataloaders,
)

Config(model=None, dataset=None, config_file_list=None, config_dict=None)
create_dataset(config)
data_preparation(config, dataset)
save_split_dataloaders(config, dataloaders)
load_split_dataloaders(config)
```

Use these after validating `data_path`, atomic file headers, `load_col`, and
config priority. For schema and config details, read
`sub-skills/configuration-and-data/SKILL.md`.

## Trainer/evaluator APIs

```python
Trainer.fit(train_data, valid_data=None, verbose=True, saved=True,
            show_progress=False, callback_fn=None)
Trainer.evaluate(eval_data, load_best_model=True, model_file=None,
                 show_progress=False)
```

These are lower-level routes when the quick-start APIs are too coarse. If
`fit(..., saved=False)` is used and no checkpoint exists, call
`evaluate(..., load_best_model=False)` unless a `model_file` is supplied.

## Hyperparameter tuning APIs

```python
from recbole.trainer import HyperTuning

HyperTuning(objective_function, space=None, params_file=None, params_dict=None,
            fixed_config_file_list=None, display_file=None, algo='exhaustive',
            max_evals=100, early_stop=10)
HyperTuning.run()
HyperTuning.export_result(output_file=None)
```

Search ranges may come from `space`, `params_file`, or `params_dict`. For the
parameter-file grammar, Hyperopt/Ray differences, and budget caveats, read
`sub-skills/training-evaluation-and-tuning/references/hyperparameter-tuning.md`.

## Model registry and customization APIs

```python
from recbole.utils import get_model, get_trainer
from recbole.model.abstract_recommender import (
    GeneralRecommender,
    SequentialRecommender,
    ContextRecommender,
    KnowledgeRecommender,
)

get_model(model_name)
get_trainer(model_type, model_name)
GeneralRecommender(config, dataset)
SequentialRecommender(config, dataset)
ContextRecommender(config, dataset)
KnowledgeRecommender(config, dataset)
```

Use `get_model` and the bundled registry helper to verify spelling and package
availability before training. For model-family selection and custom component
contracts, read `sub-skills/models-and-customization/SKILL.md`.

## Case-study APIs

```python
from recbole.utils.case_study import full_sort_scores, full_sort_topk

full_sort_scores(uid_series, model, test_data, device=None)
full_sort_topk(uid_series, model, test_data, k, device=None)
```

Use `dataset.token2id(dataset.uid_field, external_user_tokens)` before calling
these helpers, then convert internal item ids back with `dataset.id2token`.
Case-study execution requires a trained model/checkpoint and can be expensive
on large item catalogs.
