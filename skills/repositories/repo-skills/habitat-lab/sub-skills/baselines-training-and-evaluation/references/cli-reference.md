# Habitat-Baselines CLI Reference

Habitat-Baselines is Hydra-powered. The main executable is the `habitat-baselines` console script, and the equivalent module form is `python -m habitat_baselines.run`.

## Command Forms

Use these patterns as starting points:

```bash
habitat-baselines --help
python -m habitat_baselines.run --help
python -u -m habitat_baselines.run --config-name=pointnav/ppo_pointnav_example.yaml
python -u -m habitat_baselines.run --config-name=pointnav/ppo_pointnav_example.yaml habitat_baselines.evaluate=True
```

`--config-name` is a path inside the installed `habitat_baselines/config/` package. Do not pass a filesystem path to the source checkout unless you are intentionally using Hydra with a custom config search path.

## Train Versus Eval

Current Habitat-Baselines no longer uses `--run-type` for the CLI. Train/eval is selected by `habitat_baselines.evaluate`:

- Train: omit `habitat_baselines.evaluate` or set `habitat_baselines.evaluate=False`.
- Eval: set `habitat_baselines.evaluate=True`.
- Programmatic API: use `execute_exp(config, "train")` or `execute_exp(config, "eval")` after composing a config.

The CLI rejects legacy `--exp-config` and `--run-type` arguments with a conversion message.

## Legacy Command Conversion

Old style, shown only because Habitat-Baselines emits this conversion hint for legacy commands:

```bash
python -u -m habitat_baselines.run \
  --exp-config <installed-or-checkout-config-root>/pointnav/ppo_pointnav_example.yaml \
  --run-type eval
```

Current style:

```bash
python -u -m habitat_baselines.run \
  --config-name=pointnav/ppo_pointnav_example.yaml \
  habitat_baselines.evaluate=True
```

Conversion rules:

- Remove any installed-package or checkout config-root prefix from the old config path.
- Keep the remaining relative YAML path as the `--config-name` value.
- Replace `--run-type train` with `habitat_baselines.evaluate=False` or omit it.
- Replace `--run-type eval` with `habitat_baselines.evaluate=True`.
- Keep later command-line changes as Hydra overrides, for example `habitat_baselines.trainer_name=ver`.

## Common Config Names

The live Hydra help and config tree expose these primary baseline config groups:

| Group | Example configs | Typical use |
| --- | --- | --- |
| `pointnav` | `ppo_pointnav_example`, `ppo_pointnav`, `ddppo_pointnav`, `ppo_pointnav_habitat_iccv19` | PointGoal navigation training/eval |
| `objectnav` | `ddppo_objectnav`, `ddppo_objectnav_hm3d`, `ddppo_objectnav_hssd-hab`, `ddppo_objectnav_procthor-hab` | ObjectNav baselines |
| `imagenav` | `ppo_imagenav_example`, `ddppo_imagenav_example`, `ddppo_imagenav_gibson` | ImageGoal navigation |
| `instance_imagenav` | `ddppo_instance_imagenav` | Instance image-goal navigation |
| `rearrange` | `rl_skill`, `rl_rearrange`, `rl_rearrange_easy`, `rl_hierarchical`, `rl_hierarchical_oracle_nav` | Rearrangement and HRL workflows |
| `social_nav` | `social_nav` | Habitat 3 social navigation |
| `social_rearrange` | `pop_play`, `plan_pop` | Habitat 3 social rearrangement |
| `eqa` | `il_eqa_cnn_pretrain`, `il_vqa`, `il_pacman_nav` | Imitation/supervised EQA workflows |

Use the `.yaml` suffix in `--config-name` examples when following repository commands, for example `--config-name=rearrange/rl_hierarchical.yaml`. The config loader and tests also accept relative config strings such as `rearrange/rl_skill.yaml`.

## Hydra Override Examples

Trainer and run-control overrides:

```bash
python -u -m habitat_baselines.run \
  --config-name=pointnav/ppo_pointnav_example.yaml \
  habitat_baselines.trainer_name=ver \
  habitat_baselines.num_environments=4 \
  habitat_baselines.num_updates=2 \
  habitat_baselines.total_num_steps=-1
```

Checkpoint and output overrides:

```bash
python -u -m habitat_baselines.run \
  --config-name=pointnav/ddppo_pointnav.yaml \
  habitat_baselines.evaluate=True \
  habitat_baselines.eval_ckpt_path_dir=data/checkpoints/ckpt.0.pth \
  habitat_baselines.load_resume_state_config=False \
  habitat_baselines.eval.video_option='["disk"]' \
  habitat_baselines.video_dir=video_eval
```

Config group overrides:

```bash
python -u -m habitat_baselines.run \
  --config-name=pointnav/ddppo_pointnav.yaml \
  benchmark/nav/pointnav=pointnav_hm3d
```

Adding an optional config group usually needs Hydra's `+` prefix:

```bash
python -u -m habitat_baselines.run \
  --config-name=rearrange/rl_skill.yaml \
  +habitat_baselines/rl/policy/obs_transforms@habitat_baselines.rl.policy.main_agent.obs_transforms.center_cropper=center_cropper_base
```

## Programmatic Config Inspection

Use config composition before launching training:

```python
from habitat_baselines.config.default import get_config

cfg = get_config(
    "pointnav/ppo_pointnav_example.yaml",
    [
        "habitat_baselines.num_updates=2",
        "habitat_baselines.total_num_steps=-1",
    ],
)
print(cfg.habitat_baselines.trainer_name)
```

`get_config` registers the Habitat-Baselines Hydra plugin and returns an OmegaConf `DictConfig`. It composes configs without calling trainer `train()` or `eval()`.

## Help And Probe Script

Use the bundled probe script for safe, no-training checks:

```bash
python sub-skills/baselines-training-and-evaluation/scripts/baselines_cli_probe.py help
python sub-skills/baselines-training-and-evaluation/scripts/baselines_cli_probe.py groups
python sub-skills/baselines-training-and-evaluation/scripts/baselines_cli_probe.py load-config --config-name pointnav/ppo_pointnav_example.yaml --override habitat_baselines.num_updates=2 --summary
python sub-skills/baselines-training-and-evaluation/scripts/baselines_cli_probe.py convert-legacy --exp-config <config-root>/pointnav/ppo_pointnav_example.yaml --run-type eval
```

The probe imports Habitat-Baselines and composes configs, but it does not execute trainers.
