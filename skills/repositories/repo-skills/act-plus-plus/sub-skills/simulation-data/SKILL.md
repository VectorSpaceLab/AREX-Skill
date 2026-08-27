---
name: simulation-data
description: "Routes simulated ALOHA episode generation, replay, visualization,
  mirroring, compression, and truncation workflows for ACT++ HDF5 data."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# simulation-data

Use this sub-skill when the task is about creating, replaying, visualizing, mirroring, compressing, truncating, or validating simulated ACT++ episode data.

## Typical triggers

- "Generate 50 scripted transfer-cube episodes"
- "Replay episode_0.hdf5"
- "Mirror and compress the insertion dataset"
- "Why does sim reset assert on BOX_POSE?"
- "What fields are in the episode HDF5 file?"

## What this sub-skill covers

- Joint-space and end-effector MuJoCo/DM Control environments.
- Scripted transfer-cube and insertion demo generation.
- Replaying HDF5 action traces back into simulation.
- Rendering videos and qpos plots from HDF5 episodes.
- Mirroring, JPEG compression, and truncation of episode files.
- Dataset layout and camera-name conventions for sim files.

## What it excludes

- Model training and checkpoint management, which belong in [policy-training](../policy-training/SKILL.md).
- VINN feature caching and k-selection, which belong in [vinn-offline](../vinn-offline/SKILL.md).
- Real-robot alignment, servo diagnostics, and Mobile ALOHA deployment.

## Read these first

- [Workflow recipes](references/workflows.md)
- [Data format notes](../../references/data-formats.md)
- [Simulation troubleshooting](references/troubleshooting.md)

## Run this helper first

Before a long rollout, use [check_sim_backend.py](scripts/check_sim_backend.py) to confirm the sim backend can create and reset both environment variants from a chosen checkout.
