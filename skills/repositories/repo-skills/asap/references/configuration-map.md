# ASAP configuration map

This is the quickest reference for choosing Hydra groups in the ASAP skill tree.

## Core selection pattern

```bash
python humanoidverse/train_agent.py +simulator=<backend> +exp=<bundle> +robot=<choice> +terrain=<choice> +obs=<choice> [overrides...]
```

## Common experiment bundles

| `+exp` | Selects | Use case |
| --- | --- | --- |
| `motion_tracking` | `+algo=ppo`, `+env=motion_tracking` | Phase-based motion tracking from a robot motion file. |
| `locomotion` | `+algo=ppo`, `+env=locomotion` | Command-following locomotion. |
| `train_delta_a_open_loop` | `+algo=ppo`, `+env=delta_a_open_loop` | Open-loop delta-action training. |
| `train_delta_a_closed_loop` | `+algo=ppo_train_delta_a`, `+env=delta_a_closed_loop` | Closed-loop delta-action finetuning. |

## Common Hydra groups

| Group | Examples |
| --- | --- |
| `simulator` | `isaacgym`, `isaacsim`, `genesis`, `mujoco` |
| `robot/g1` | `g1_29dof_anneal_23dof` |
| `terrain` | `terrain_locomotion_plane`, `terrain_locomotion` |
| `domain_rand` | `NO_domain_rand`, `NO_domain_rand_finetune_with_deltaA` |
| `rewards/motion_tracking` | `reward_motion_tracking_dm_2real`, `reward_motion_tracking_dm_simfinetuning` |
| `rewards/motion_tracking/delta_a` | `reward_delta_a_openloop`, `reward_motion_tracking_use_deltaA_to_train_2real` |
| `obs/motion_tracking` | `deepmimic_a2c_nolinvel_LARGEnoise_history`, `motion_tracking` |
| `obs/loco` | `leggedloco_obs_singlestep_withlinvel`, `leggedloco_obs_history_wolinvel` |
| `obs/delta_a` | `open_loop`, `train_policy_with_delta_a` |
| `opt` | `wandb`, `record`, `eval_analysis_plot_motion_tracking`, `eval_analysis_plot_locomotion` |

## Scalar overrides that commonly matter

- `num_envs=1` for smoke tests and eval debugging.
- `project_name=...` and `experiment_name=...` for output directory naming.
- `headless=True` or `headless=False` for training.
- `+headless=True` for eval when the base eval config needs the key added.
- `+device=cuda:0` to force CUDA.
- `checkpoint=<path>` to resume or finetune from a saved policy.
- `algo.config.policy_checkpoint=<path>` to load the frozen policy inside `PPODeltaA`.

## Cross-links

- Root router: [`../SKILL.md`](../SKILL.md)
- Install and backends: [`install-and-backends.md`](install-and-backends.md)
- Troubleshooting: [`troubleshooting.md`](troubleshooting.md)
- Training and evaluation: [`../sub-skills/training-and-evaluation/SKILL.md`](../sub-skills/training-and-evaluation/SKILL.md)
