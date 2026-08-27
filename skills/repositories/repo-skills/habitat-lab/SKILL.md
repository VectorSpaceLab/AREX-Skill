---
name: habitat-lab
description: "Use Habitat-Lab, Habitat-Baselines, and Habitat-HITL for embodied
  AI configs, environments, datasets, training, HITL apps, and extensions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Habitat-Lab Repo Skill

Use this repo skill when the user asks about Habitat-Lab, Habitat-Baselines, Habitat-HITL, embodied AI tasks, Habitat configs, navigation or rearrangement environments, baseline training/evaluation, HITL viewers/apps, or Habitat extension registries.

## Start Here

- Read [references/installation.md](references/installation.md) before recommending installs, imports, or optional backend packages.
- Read [references/data-and-assets.md](references/data-and-assets.md) when a task mentions scenes, episode datasets, `data/`, dataset downloads, or missing assets.
- Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting import, Habitat-Sim, graphics, Gym, Hydra, data, and backend failures.
- Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is stale for a current checkout.
- Use [scripts/check_habitat_install.py](scripts/check_habitat_install.py) and [scripts/habitat_env_report.py](scripts/habitat_env_report.py) for safe import/config/backend diagnostics.

## Route By Task

| User task | Read |
| --- | --- |
| Install Habitat-Lab, choose Python/Habitat-Sim packages, compose Hydra configs, validate data paths | [setup-and-configuration](sub-skills/setup-and-configuration/SKILL.md) |
| Create `habitat.Env`, `RLEnv`, Gym wrappers, VectorEnv/ThreadedVectorEnv, task configs, datasets, episode flows | [tasks-datasets-and-envs](sub-skills/tasks-datasets-and-envs/SKILL.md) |
| Run or inspect Habitat-Baselines train/eval, Hydra CLI, checkpoints, metrics, PPO/DDPPO/VER/IL configs, benchmarks | [baselines-training-and-evaluation](sub-skills/baselines-training-and-evaluation/SKILL.md) |
| Work with Habitat-HITL realtime viewers, app states, GUI input, websockets, VR/web clients, policy-in-app loops | [hitl-apps-and-interaction](sub-skills/hitl-apps-and-interaction/SKILL.md) |
| Add or debug custom sensors, measures, actions, tasks, datasets, simulators, policies, trainers, obs transforms | [extension-patterns](sub-skills/extension-patterns/SKILL.md) |

## Public Package Facts

- Habitat-Lab is a Python embodied AI framework built on Habitat-Sim for task definition, environment construction, datasets, agents, and benchmarks.
- The source tree exposes three installable distributions: `habitat-lab`, `habitat-baselines`, and `habitat-hitl`; this skill was generated against version `0.3.3` for all three.
- Core imports include `habitat`, `habitat_baselines`, and `habitat_hitl`; simulator-backed imports also require `habitat_sim` and `magnum` from Habitat-Sim.
- The repository README documents Python 3.9 with conda and `habitat-sim withbullet` as the safest public install route for current Habitat-Sim compatibility.
- The `habitat-baselines` console script maps to `habitat_baselines.run:main` and is Hydra-powered.

## Minimal Public Install Shape

Use this as the starting point when the user has not provided an environment:

```bash
conda create -n habitat python=3.9 cmake=3.14.0
conda activate habitat
conda install habitat-sim withbullet -c conda-forge -c aihabitat
pip install -e habitat-lab
pip install -e habitat-baselines  # only when baseline training/eval is needed
pip install -e habitat-hitl       # only when HITL apps are needed
```

For package inspection or config-only help, do not run training, benchmarks, viewers, or dataset downloads unless the user asks and the data/graphics/hardware requirements are clear.

## Safe Diagnostics

```bash
python path/to/habitat-lab/scripts/check_habitat_install.py --include-baselines --include-hitl
python path/to/habitat-lab/scripts/habitat_env_report.py --json
```

Then use narrower sub-skill probes:

```bash
python path/to/habitat-lab/sub-skills/setup-and-configuration/scripts/config_probe.py --kind habitat --config benchmark/nav/pointnav/pointnav_habitat_test.yaml
python path/to/habitat-lab/sub-skills/baselines-training-and-evaluation/scripts/baselines_cli_probe.py groups
python path/to/habitat-lab/sub-skills/extension-patterns/scripts/inspect_registry_extensions.py --all
```

## Safety Defaults

- Treat full simulation, Gym environments, HITL apps, benchmarks, and baseline training as data/backend-dependent operations.
- Prefer config composition, import checks, CLI `--help`, and registry introspection before launching expensive or graphics-heavy workflows.
- Do not rely on the original repository docs, examples, tests, or scripts at runtime; this skill distills the necessary routes, references, and safe probes into its own files.
- If a current checkout has changed from [references/repo-provenance.md](references/repo-provenance.md), run `refresh-repo-skill` before trusting exact API/config coverage.
