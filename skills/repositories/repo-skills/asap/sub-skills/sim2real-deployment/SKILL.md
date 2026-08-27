---
name: sim2real-deployment
description: "Run ASAP sim2sim playback, sim2real policy runtime, Unitree/ROS2
  bridges, joystick or keyboard controls, and real-data collection safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# sim2real-deployment

Use this sub-skill when the task is to operate ASAP deployment code: MuJoCo sim2sim playback, sim2real policy runtime on a Unitree G1, ROS2/Unitree bridge setup, joystick or keyboard command input, and real-world data collection.

## First Safety Gate

Real robot deployment can injure people and damage hardware. Do **not** start policy actions on physical hardware until a qualified human confirms the robot is mechanically configured for the intended DOF count, in low-level mode, on a clear test area or support rig, with emergency-stop procedures ready. The bundled instructions explain repository behavior; they do not replace a hardware safety review.

## Route by Need

- **Local MuJoCo sim2sim playback**: read [`references/workflows.md`](references/workflows.md#sim2sim-mujoco-playback) and run the simulator plus policy terminals from the repository `sim2real/` directory.
- **Real Unitree G1 policy runtime**: read [`references/workflows.md`](references/workflows.md#sim2real-unitree-g1-runtime) and [`references/troubleshooting.md`](references/troubleshooting.md#real-hardware-and-ddsnetwork-failures) before changing `INTERFACE` away from localhost.
- **Keyboard, joystick, or MuJoCo viewer controls**: use [`references/workflows.md`](references/workflows.md#control-maps) for the exact key/button maps implemented by `base_policy.py`, `deepmimic_dec_loco.py`, and `unitree_sdk2py_bridge.py`.
- **Robot/config/model path edits**: use [`references/configuration.md`](references/configuration.md) before editing `sim2real/config/g1_29dof_hist.yaml`.
- **Safe readiness check**: run the bundled [`scripts/deployment_doctor.py`](scripts/deployment_doctor.py) to check imports, config shape, assets, model paths, joystick visibility, and network-interface expectations without initializing Unitree DDS or commanding motors.
- **Real-data collection**: use [`references/workflows.md`](references/workflows.md#real-data-collection-with-listener_deltaapy) for `listener_deltaa.py` and its recording keys.

## Working Directory Convention

Deployment commands in ASAP are written to run from the repository `sim2real/` directory, because config paths point to `../humanoidverse/...`, policy scripts append `./rl_policy`, and model examples use `./models/...`.

```bash
cd sim2real
python sim_env/base_sim.py --config=config/g1_29dof_hist.yaml
python rl_policy/deepmimic_dec_loco_height.py --config=config/g1_29dof_hist.yaml \
  --loco_model_path=./models/dec_loco/20250109_231507-noDR_rand_history_loco_stand_height_noise-decoupled_locomotion-g1_29dof/model_6600.onnx \
  --mimic_model_paths=./models/mimic
```

## Boundaries and Cross-Links

- For HumanoidVerse training, checkpoint export, Hydra overrides, or evaluation, use [`../training-and-evaluation/SKILL.md`](../training-and-evaluation/SKILL.md) and the root [`../../SKILL.md`](../../SKILL.md).
- For SMPL/AMASS shape fitting, motion fitting, or retargeting, use [`../motion-retargeting/SKILL.md`](../motion-retargeting/SKILL.md).
- For base installs, simulator backends, ROS2, and optional SDK prerequisites, use root [`../../references/install-and-backends.md`](../../references/install-and-backends.md) when present.
- For cross-cutting package/import/config failures, use root [`../../references/troubleshooting.md`](../../references/troubleshooting.md) when present; keep deployment-specific failures in this sub-skill's [`references/troubleshooting.md`](references/troubleshooting.md).

This sub-skill intentionally excludes HumanoidVerse training internals and SMPL motion retargeting details except where a trained ONNX policy or retargeted mimic model path is required for deployment.
