---
name: setup-and-configuration
description: "Install Habitat-Lab, compose Habitat/Habitat-Baselines Hydra
  configs, validate data paths, and diagnose setup failures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Setup And Configuration

Use this sub-skill when a user needs Habitat-Lab installed or imported, needs to choose a compatible Python/Habitat-Sim path, needs to compose or override Habitat or Habitat-Baselines configs, or needs to diagnose config/data/import failures before running environments or training.

## Fast Routing

- For installation, Python/Habitat-Sim compatibility, package order, and data directory layout, read [references/install-and-data.md](references/install-and-data.md).
- For `habitat.get_config`, `habitat_baselines.config.default.get_config`, Hydra config groups, override syntax, `read_write`, and config validation patterns, read [references/configuration.md](references/configuration.md).
- For concrete failure symptoms such as missing `magnum`, missing `habitat_sim`, Hydra errors, invalid override keys, missing datasets/assets, Gym warnings, and graphics/EGL warnings, read [references/troubleshooting.md](references/troubleshooting.md).
- To test imports and config composition without starting simulation or training, run [scripts/config_probe.py](scripts/config_probe.py).

## Workflow

1. Confirm the environment goal: lightweight config inspection, environment stepping, baselines training, or HITL use. Prefer a Python 3.9 conda environment when Habitat-Sim wheels/conda packages are needed.
2. Install Habitat-Sim with compatible physics support before relying on `habitat` imports that transitively need `habitat_sim`/`magnum`; then install `habitat-lab`, and install `habitat-baselines` only when training/evaluation configs are needed.
3. Use `scripts/config_probe.py` to verify package imports and compose a known config with any requested overrides before launching expensive simulation or training.
4. Resolve data and asset paths from composed config keys such as `habitat.dataset.data_path`, `habitat.dataset.scenes_dir`, `habitat.simulator.scene`, and robot/physics asset paths.
5. Route runtime behavior questions to sibling sub-skills: environment stepping and task/dataset use to [tasks-datasets-and-envs](../tasks-datasets-and-envs/SKILL.md), baselines training/evaluation to [baselines-training-and-evaluation](../baselines-training-and-evaluation/SKILL.md), HITL launch or interaction to [hitl-apps-and-interaction](../hitl-apps-and-interaction/SKILL.md), and custom registry/config authoring to [extension-patterns](../extension-patterns/SKILL.md).

## Safe Probe Examples

```bash
python path/to/skills/habitat-lab/sub-skills/setup-and-configuration/scripts/config_probe.py \
  --kind habitat \
  --config benchmark/nav/pointnav/pointnav_habitat_test.yaml \
  --override habitat.environment.max_episode_steps=5
```

```bash
python path/to/skills/habitat-lab/sub-skills/setup-and-configuration/scripts/config_probe.py \
  --kind baselines \
  --config pointnav/ppo_pointnav_example.yaml \
  --override habitat_baselines.total_num_steps=10 \
  --key habitat_baselines.trainer_name \
  --key habitat.environment.max_episode_steps
```

## Boundaries

- This sub-skill covers installation/imports, config composition, config mutation, data/asset path validation, and setup/config troubleshooting.
- It does not explain stepping `Env`, Gym wrappers, episode semantics, task behavior, or dataset generation; use [tasks-datasets-and-envs](../tasks-datasets-and-envs/SKILL.md).
- It does not run training/evaluation loops, tune PPO/DDPPO, or interpret checkpoints; use [baselines-training-and-evaluation](../baselines-training-and-evaluation/SKILL.md).
- It does not launch HITL applications; use [hitl-apps-and-interaction](../hitl-apps-and-interaction/SKILL.md).
- It does not define new registries, sensors, measures, actions, or structured config classes; use [extension-patterns](../extension-patterns/SKILL.md).
