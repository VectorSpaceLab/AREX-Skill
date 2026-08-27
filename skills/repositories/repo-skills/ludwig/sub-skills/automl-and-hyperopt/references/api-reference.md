# AutoML and Hyperopt API Reference

## AutoML APIs

- `auto_train(dataset, target, time_limit_s, output_directory="results", tune_for_memory=False, user_config=None, random_seed=..., use_reference_config=False, **kwargs)` creates/selects config candidates and trains within a budget.
- `create_auto_config(dataset, target, time_limit_s, tune_for_memory=False, user_config=None, random_seed=..., imbalance_threshold=0.9, use_reference_config=False, backend=None)` produces an AutoML config without necessarily running full training.
- `init_config(dataset, target, time_limit_s, tune_for_memory=False, suggested=False, hyperopt=False, output=None, random_seed=..., use_reference_config=False, **kwargs)` initializes a user config from data and target.

These APIs may import optional backend code. Diagnose dependencies before use.

## Hyperopt CLI/API

`ludwig hyperopt` accepts the normal training dataset/config/output flags plus hyperopt-specific save/log verbosity flags. It reads its search plan from the config `hyperopt` section.

## Result artifacts

Hyperopt runs can write hyperopt statistics, individual trial artifacts, trained models, and selected configs. Use explicit output directories and budgets.
