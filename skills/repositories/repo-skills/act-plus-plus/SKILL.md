---
name: act-plus-plus
description: "Routes ACT++, ACT, Diffusion Policy, VINN, and MuJoCo simulation
  workflows for bimanual ALOHA episode data and imitation-learning tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# act-plus-plus

Use this repo skill when a task is about the ACT++ / Mobile ALOHA imitation-learning repository: simulated ALOHA episode generation, ACT or Diffusion Policy training, HDF5 episode utilities, MuJoCo + DM Control task behavior, or VINN feature workflows.

## Start here

1. Read [repo provenance](references/repo-provenance.md) if you need to check whether this skill matches the checkout or if code changed.
2. Run or read [scripts/check_environment.py](scripts/check_environment.py) before expensive workflows. It checks the external package/backend stack without running training.
3. Use the route table below, then stay inside the owning sub-skill and its linked references.
4. For command flags and data shapes that cross multiple workflows, read [CLI reference](references/cli-reference.md), [data formats](references/data-formats.md), and [API reference](references/api-reference.md).
5. For backend, dependency, or real-robot caveats, read [cross-cutting troubleshooting](references/troubleshooting.md).

## Install notes

For a checkout, install the repo's Python stack before launching any workflow:

- install the external Python dependencies needed by the workflow you want;
- install the repository itself in editable mode;
- install the `detr/` subpackage in editable mode so the `util` and `models` imports resolve;
- then run `scripts/check_environment.py` before long jobs.

The exact dependency set depends on the chosen workflow: simulation only needs MuJoCo / DM Control plus image and HDF5 utilities, while policy training and VINN also need CUDA-enabled torch plus robomimic / diffusers support.

## Route by user intent

| User task | Read |
| --- | --- |
| Generate scripted simulated episodes, replay actions, render videos, mirror/compress/truncate HDF5 episodes, or debug MuJoCo/DM Control rendering | [simulation-data](sub-skills/simulation-data/SKILL.md) |
| Train/evaluate ACT, CNNMLP, Diffusion Policy, or the ACT VQ latent model; inspect checkpoint/stat files; convert README commands into current CLI flags | [policy-training](sub-skills/policy-training/SKILL.md) |
| Cache BYOL/ResNet image features, select nearest-neighbor `k`, inspect VINN feature-file layouts, or avoid the raw VINN scripts' interactive traps | [vinn-offline](sub-skills/vinn-offline/SKILL.md) |
| Understand supported task names, camera names, HDF5 schemas, or how episode files flow between data and training | [overview](references/overview.md) and [data formats](references/data-formats.md) |
| Diagnose `ModuleNotFoundError`, `BOX_POSE` assertion failures, missing `MUJOCO_GL`, CUDA errors, mismatched robomimic/diffusers installs, or Mobile ALOHA hardware dependencies | [troubleshooting](references/troubleshooting.md) |

## Repository operating model

- Core simulated tasks are transfer cube and bimanual insertion. The sim data flow uses an end-effector environment for scripted demos, then replays joint commands into the joint-space environment to record observations.
- Episode files are HDF5 datasets with `/observations/qpos`, `/observations/qvel`, `/action`, and `/observations/images/<camera>` groups. Compressed/mirrored variants add `compress=true` and `/compress_len`.
- ACT/CNNMLP/Diffusion training is driven by `imitate_episodes`-style arguments. Current training code uses `--num_steps`; older README command snippets may say `--num_epochs`.
- Training and VINN paths call `.cuda()` directly. Treat CUDA as required unless the code is explicitly modified.
- MuJoCo rendering needs an offscreen GL backend such as `MUJOCO_GL=egl`; do not treat a CPU import as proof that rendered sim data generation works.
- Real robot branches depend on the external Mobile ALOHA / Interbotix stack and hardware. This generated skill covers them only as troubleshooting/gap notes, not as a verified runtime route.

## Minimal checks

Use the bundled checkers rather than launching long training or real robot code first:

```bash
python scripts/check_environment.py
python sub-skills/simulation-data/scripts/check_sim_backend.py --repo-root /path/to/act-plus-plus --task sim_transfer_cube
python sub-skills/policy-training/scripts/check_policy_stack.py --repo-root /path/to/act-plus-plus
python sub-skills/vinn-offline/scripts/check_vinn_stack.py --repo-root /path/to/act-plus-plus
```

The `--repo-root` examples accept any checkout of ACT++; they are not tied to the source checkout used to build this skill.

## What is intentionally not routed

- Servo calibration, `align`-style robot movement, Dynamixel diagnostics, and real Mobile ALOHA runtime deployment require external hardware packages and are not verified here.
- `train_actuator_network` is an experiment-oriented utility with hard-coded data/log paths and dataset fields; treat it as reference evidence only.
- The empty `byol_pytorch` gitlink in the inspected checkout was not used as source evidence. VINN guidance is based on the available ACT++ VINN scripts and feature-file contracts.
