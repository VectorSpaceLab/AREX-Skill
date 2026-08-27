---
name: rl-workflows
description: "Train, smoke-test, save, load, and play PPO hover policies with
  HoverAviary and MultiHoverAviary."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# rl-workflows

## Read when

Use this sub-skill for reinforcement-learning tasks that mention PPO, SB3, train a hover policy, run a short PPO smoke, play a saved model, compare single-agent and multi-agent hover, Gymnasium hover IDs, or debug RL import/model-path failures.

## What this sub-skill owns

- Short, headless PPO training smoke runs for `HoverAviary` and `MultiHoverAviary`.
- Saving and loading SB3 `PPO` models as `final_model.zip` and `best_model.zip`-style artifacts.
- Headless or GUI playback of saved policies, including optional logger and wall-clock sync behavior.
- Choosing between single-agent hover (`hover-aviary-v0`, `HoverAviary`) and two-or-more-drone multi-hover (`multihover-aviary-v0`, `MultiHoverAviary`).
- Using `BaseRLAviary`, `ActionType`, `ObservationType`, `Logger`, and `sync` in the RL example pattern.
- Explaining the source `learn.run(..., local=False)` smoke branch and why long training must be explicitly requested.

## Route elsewhere

- Control-only PID, velocity, downwash, MRAC, `CtrlAviary`, `VelocityAviary`, and controller internals belong to the control-simulation sub-skill.
- Betaflight SITL, external Betaflight checkout layout, UDP ports, and `BetaAviary` belong to the betaflight-sitl sub-skill.
- General package installation/import routing belongs to the root repo skill, but RL-specific `torch`, `stable_baselines3`, `gymnasium`, and model-path failures are covered here.

## Quick operating route

1. Confirm the installed runtime has `gym_pybullet_drones`, `gymnasium`, `torch`, and `stable_baselines3`; the package has no CLI entry points, so prefer the bundled helper script.
2. Pick the RL task:
   - single-agent hover: `HoverAviary` / `hover-aviary-v0`, default one drone, target z approximately 1.0;
   - multi-agent hover: `MultiHoverAviary` / `multihover-aviary-v0`, default two drones, per-drone hover targets.
3. Start with a short headless smoke train, not full training. Use `gui=False`, kinematic observations, and one-dimensional RPM actions unless the task asks otherwise.
4. Use the saved `best_model.zip` or `final_model.zip` from the smoke run for playback; never assume `results/best_model.zip` exists.
5. Playback headless first when no display is available; enable GUI or plotting only after the model loads and the environment runs.

## Runtime references and helper

- [Workflows](references/workflows.md): smoke training, train-then-play, playback, single-agent vs multi-agent choices, and output layout.
- [API reference](references/api-reference.md): env IDs, constructors, enums, `learn.run`, `play.play`, `Logger`, and `sync` facts.
- [Troubleshooting](references/troubleshooting.md): import failures, missing model paths, local-vs-full training, plotting/results folders, multi-agent confusion, and headless operation.
- [RL workflow helper](scripts/run_rl_workflow.py): skill-owned automation for import checks, safe PPO smoke training, and separate playback.

## Native anchors

- Native smoke target: `tests/test_examples.py::test_learn`, which calls `learn.run(gui=False, plot=False, output_folder='tmp', local=False)`.
- Follow-on playback target: run playback against the model produced by the smoke training path, using `gui=False` first.
