---
name: simulator-foundations
description: "Use ProtoMotions simulator, robot, terrain, scene, and tutorial
  building blocks without jumping into full training."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ProtoMotions simulator foundations

Use this sub-skill for tasks that ask how ProtoMotions creates simulators, loads robots, builds terrains/scenes, reads context views, or validates a robot/environment setup before training.

## Read first

- `references/simulator-api.md`: factories, config objects, import order, and simulator state concepts.
- `references/tutorial-map.md`: progressive learning path from simulator creation to DeepMimic.
- `references/visualization.md`: motion and random-pose visual checks and safety notes.
- `scripts/smoke_config_factories.py`: safe script that constructs robot and simulator config objects without creating a simulator runtime.

## Typical tasks

- Choose a simulator backend for a small debug run.
- Create a robot config with `robot_config("g1")`, `robot_config("smpl")`, or another registered name.
- Build `simulator_config(...)` from a robot, backend name, headless flag, env count, and experiment name.
- Add procedural terrain or scene objects to an environment config.
- Understand `EnvContext` and `MdpComponent` bindings for observations/rewards/terminations.
- Validate a custom robot's MJCF/config before training.

## Safe workflow

1. Confirm backend environment and import order using the install sub-skill.
2. Construct configs only; do not instantiate simulator classes until backend dependencies are verified.
3. Run a small robot/simulator config smoke:

   ```bash
   python scripts/smoke_config_factories.py --robot g1 --simulator mujoco --num-envs 1
   ```

4. For visual checks, start with one environment, headless where possible, then enable rendering only when the display/Kit backend is ready.
5. If changing robot assets or custom simulator adapters, prefer unit tests or factory smokes before long rollouts.

## Key invariants

- Robot configs own asset paths, body-name mappings, control gains, default root height, trackable bodies, and per-simulator physics params.
- Simulator configs are selected by backend name and must use that robot's matching simulation params.
- `BaseEnv` composes simulator, terrain, scene library, motion library, observation/reward/termination components, and control components.
- MDP components are pure tensor functions wired to context paths plus static params.
- Tutorial scripts are educational and backend-runnable; they are not a substitute for environment-specific install verification.
