# CLI command map

## Purpose

Use this map to select the correct RL Baselines3 Zoo entry point and sub-skill before building a command. Prefer installed-package module commands for core train/evaluate paths and console subcommands when optional imports are available.

## Main command surfaces

| Task intent | Preferred command form | Console form | Owning sub-skill |
| --- | --- | --- | --- |
| Train a model | `python -m rl_zoo3.train ...` | `rl_zoo3 train ...` | `sub-skills/training-cli/SKILL.md` |
| Resume training from a zip | `python -m rl_zoo3.train --trained-agent model.zip ...` | `rl_zoo3 train ... -i model.zip` | `sub-skills/training-cli/SKILL.md` |
| Evaluate/enjoy a model without rendering | `python -m rl_zoo3.enjoy --no-render ...` | `rl_zoo3 enjoy --no-render ...` | `sub-skills/evaluation-and-artifacts/SKILL.md` |
| Record one model video | `python -m rl_zoo3.record_video ...` | none in console router | `sub-skills/integrations-hub-tracking/SKILL.md` |
| Record checkpoints/best/final into one training video | `python -m rl_zoo3.record_training ...` | none in console router | `sub-skills/integrations-hub-tracking/SKILL.md` |
| Download a Hub model into RL Zoo layout | `python -m rl_zoo3.load_from_hub ...` | none in console router | `sub-skills/integrations-hub-tracking/SKILL.md` |
| Upload/package a trained model to Hub | `python -m rl_zoo3.push_to_hub ...` | none in console router | `sub-skills/integrations-hub-tracking/SKILL.md` |
| Plot monitor training curves | console `rl_zoo3 plot_train ...` | `rl_zoo3 plot_train ...` | `sub-skills/plotting-benchmarking/SKILL.md` |
| Aggregate evaluation curves/tables | console `rl_zoo3 all_plots ...` | `rl_zoo3 all_plots ...` | `sub-skills/plotting-benchmarking/SKILL.md` |
| Plot a saved all-plots pickle | console `rl_zoo3 plot_from_file ...` | `rl_zoo3 plot_from_file ...` | `sub-skills/plotting-benchmarking/SKILL.md` |
| Benchmark local/pretrained agents | `python -m rl_zoo3.benchmark ...` | none in console router | `sub-skills/plotting-benchmarking/SKILL.md` |

## Shared train parser routes

The training parser has a broad surface. Route detailed questions as follows:

| Flag family | Examples | Route |
| --- | --- | --- |
| Run identity and safety | `--algo`, `--env`, `--n-timesteps`, `--log-folder`, `--seed`, `--uuid`, `--device`, `--num-threads`, `--progress` | `training-cli` |
| Evaluation/checkpoints/replay | `--eval-freq`, `--eval-episodes`, `--n-eval-envs`, `--save-freq`, `--trained-agent`, `--save-replay-buffer` | `training-cli`, then `evaluation-and-artifacts` to inspect outputs |
| Config values | `--conf-file`, `--hyperparams`, `--env-kwargs`, `--eval-env-kwargs`, `n_envs`, wrappers, callbacks | `config-hyperparams`; component imports route further to `custom-components` |
| Custom registration | `--gym-packages` | `custom-components` plus `training-cli` launch guidance |
| Optuna HPO | `-optimize`, `--n-trials`, `--max-total-trials`, `--sampler`, `--pruner`, `--storage`, `--study-name`, `--trial-id` | `tuning-optimization` |
| W&B | `--track`, `--wandb-project-name`, `--wandb-entity`, `--wandb-group`, `--wandb-tags` | `integrations-hub-tracking` |

## Command style guidance

- Use `python -m rl_zoo3.train` and `python -m rl_zoo3.enjoy` for portable base installs and headless smoke checks.
- Use `rl_zoo3 <subcommand>` when the console router imports cleanly. Console train/enjoy imports plot modules as part of the router, so plotting extras may be required even when the subcommand itself is not plotting.
- Use bundled command-builder scripts only to construct or validate commands. They intentionally do not train, evaluate, upload, download, render, or mutate files unless a helper explicitly says it only reads a local tree.

## Safe first checks

```bash
python -m rl_zoo3.train --help
python -m rl_zoo3.enjoy --help
python scripts/check_rl_zoo3_install.py --check-plots
```

Then route to the owning sub-skill for the exact command family.
