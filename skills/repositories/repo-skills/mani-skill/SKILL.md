---
name: mani-skill
description: "Use ManiSkill 3 for Gymnasium robot simulation, custom task
  authoring, trajectories, demos, and robot-learning baselines."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# ManiSkill

Use this repo skill when the task involves ManiSkill / `mani_skill`: robot manipulation environments, Gymnasium-compatible simulation, SAPIEN/PhysX CPU or GPU backends, custom tasks or robots, demonstration trajectories, motion planning, teleoperation, or ManiSkill RL/IL baselines.

Start by choosing the route that matches the user's goal:

| Goal | Read |
| --- | --- |
| Create, run, wrap, smoke-test, visualize, or benchmark existing environments | [sub-skills/environment-usage/](sub-skills/environment-usage/) |
| Build a custom task, robot, scene builder, reward, observation, or reset pipeline | [sub-skills/custom-environments/](sub-skills/custom-environments/) |
| Record, replay, inspect, download, or convert trajectory/dataset bundles | [sub-skills/trajectories-and-datasets/](sub-skills/trajectories-and-datasets/) |
| Understand or prepare RL/IL baseline families, benchmark tasks, and evaluation conventions | [sub-skills/learning-and-baselines/](sub-skills/learning-and-baselines/) |
| Diagnose cross-cutting install, asset, rendering, or workflow failures | [references/troubleshooting.md](references/troubleshooting.md) |
| Check whether this skill matches the source version | [references/repo-provenance.md](references/repo-provenance.md) |

## Install and import baseline

Public package install:

```bash
python -m pip install --upgrade mani_skill torch
```

Editable install when you are intentionally working in a ManiSkill checkout:

```bash
python -m pip install -e .
python -m pip install torch
```

Minimal import check:

```bash
python -c "import mani_skill, mani_skill.envs; print(mani_skill.__version__)"
```

Bundled safe install probe:

```bash
python scripts/check_install.py --json
```

Add `--env-smoke` only when a bounded no-render CPU reset/step is acceptable.

## Core runtime facts

- Import `mani_skill.envs` before the first `gym.make(...)` so environments register.
- `gym.make("PickCube-v1", num_envs=1, obs_mode="state")` is the common smallest environment check.
- `num_envs=1` with `sim_backend="auto"` uses PhysX CPU; `num_envs>1` selects PhysX CUDA.
- `render_backend="none"` and `render_mode=None` are the safest headless checks.
- Rendering, GUI, ray tracing, and point-cloud visualization require working SAPIEN/Vulkan/display support.
- Many asset-backed tasks and official demonstrations are not bundled with the package; plan downloads explicitly.
- The LeRobot converter imports `pandas` before help and may require additional parquet/LeRobot dependencies for real conversion.
- Baseline training and benchmark sweeps are expensive and should remain reference-only unless the user explicitly asks to run them.

## Route details

### Existing environment usage

Read [sub-skills/environment-usage/](sub-skills/environment-usage/) when the task asks for:

- Gymnasium environment creation or `BaseEnv` runtime kwargs
- observation modes such as `state`, `state_dict`, `rgbd`, `pointcloud`, or raw `sensor_data`
- controller/action-space selection such as `pd_joint_delta_pos` or `pd_ee_delta_pose`
- `CPUGymWrapper`, `ManiSkillVectorEnv`, `RecordEpisode`, or flatten wrappers
- `demo_random_action`, visual demos, reset-distribution demos, robot inspection, or GPU benchmark help
- no-render CPU smoke checks or CPU/GPU backend debugging

### Custom environments and robots

Read [sub-skills/custom-environments/](sub-skills/custom-environments/) when the task asks for:

- `BaseEnv` subclassing and `@register_env`
- actor/articulation building, scene builders, cameras, observations, rewards, or success/fail logic
- replay-safe state with `get_state_dict` / `set_state_dict`
- custom robots, controllers, mounted sensors, keyframes, or robot asset setup
- GPU-memory and partial-reset design for vectorized custom tasks

### Trajectories and datasets

Read [sub-skills/trajectories-and-datasets/](sub-skills/trajectories-and-datasets/) when the task asks for:

- `RecordEpisode` HDF5/JSON bundles
- official demo or asset download planning
- trajectory replay, reward/observation regeneration, or control-mode conversion
- LeRobot conversion command planning
- `ManiSkillTrajectoryDataset`
- motion-planning or teleoperation data collection workflows

### Learning and baselines

Read [sub-skills/learning-and-baselines/](sub-skills/learning-and-baselines/) when the task asks for:

- PPO, SAC, TD-MPC2, BC, ACT, Diffusion Policy, RFCL, or RLPD
- benchmark task selection and fair evaluation
- baseline dependency, WandB, checkpoint, or dataset setup questions
- benchmark data-generation and replay conventions

## Operating rules

1. Prefer safe help and planning commands before running demos, replays, downloads, converters, or training loops.
2. Never silently switch an asset-backed task to an easier built-in task; report the missing asset requirement.
3. Keep CPU/GPU/render claims separate. A no-render CUDA simulation smoke does not prove Vulkan rendering.
4. For non-interactive smoke runs, set `MS_SKIP_ASSET_DOWNLOAD_PROMPT=1` and keep rendering disabled.
5. When comparing baselines, preserve the evaluation contract: no partial resets, reconfigure on reset, record metrics, and aggregate complete episodes.
6. When authoring tasks, keep reset-time logic batched over `env_idx` and store non-simulation state for replay.

## Router metadata

`references/repo-routing-metadata.json` contains the structured scenario placement used by the managed repo-skills router. Do not hand-edit live router Markdown; import tooling consumes that JSON.
