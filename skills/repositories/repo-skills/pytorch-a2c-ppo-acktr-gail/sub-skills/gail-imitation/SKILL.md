---
name: gail-imitation
description: "Prepare expert demonstrations and reason about GAIL imitation
  learning in pytorch-a2c-ppo-acktr-gail."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# gail-imitation

Use this sub-skill when the task is about Generative Adversarial Imitation Learning (GAIL) in this repo: preparing expert demonstrations, converting expert HDF5 trajectories to the `.pt` format consumed by the code, checking `ExpertDataset` behavior, or explaining how `--gail` changes the training loop.

## Route first

- Expert data schema or conversion: read `references/gail-data-format.md`, then use `scripts/convert_gail_h5_to_pt.py` for a safe local conversion helper.
- End-to-end GAIL flow: read `references/gail-workflow.md` for how `main.py --gail` locates expert files, creates `ExpertDataset`, updates `Discriminator`, and replaces rewards.
- Failures and environment issues: read `references/troubleshooting.md` before changing code.
- Generic PPO/MuJoCo command construction, tuning, checkpoint playback, or evaluation belongs in `../training-workflows/`.
- Policy, rollout storage, action distribution, or optimizer internals belong in `../model-components/`.

## Operating constraints

- Do not download expert demonstrations or install simulators unless the user explicitly asks; upstream expert data is external and not bundled.
- Do not launch long MuJoCo, PyBullet, Atari, or CUDA training as a smoke check. Prefer converter help, tiny synthetic HDF5 fixtures, and optional `ExpertDataset` loading.
- `--gail` is valid only for vector observations in the current training loop; image/Atari observations trip the `len(envs.observation_space.shape) == 1` assertion.
- `setup.py` does not declare `h5py`; ensure it is installed from the environment or requirements evidence before using HDF5 conversion.

## Bundled helper

```bash
python sub-skills/gail-imitation/scripts/convert_gail_h5_to_pt.py \
  --h5-file gail_experts/trajs_halfcheetah.h5 \
  --pt-file gail_experts/trajs_halfcheetah.pt
```

The helper performs local validation only and writes a PyTorch dictionary with `states`, `actions`, `rewards`, and `lengths` tensors.