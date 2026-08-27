---
name: training-and-experiments
description: "Run and debug ProtoMotions training, inference, experiment
  configs, GPC/PEFT, domain randomization, checkpoints, and distributed jobs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ProtoMotions training and experiments

Use this sub-skill for `protomotions train-agent`, `protomotions inference-agent`, experiment file design, algorithm-family selection, config overrides, checkpoint/resume behavior, GPC/PEFT, domain randomization, and SLURM/multi-GPU operations.

## Read first

- `references/training-cli.md`: command shapes, required arguments, inference overrides, and safe bounded runs.
- `references/experiment-families.md`: Mimic, ADD, AMP, ASE, MaskedMimic, GPC/PEFT, steering, and path-following routes.
- `references/configuration-and-resume.md`: dataclass config lifecycle and artifact roles.
- `references/gpc-peft.md`: tracker/prior/SFT/RLFT checkpoint contracts and PEFT actor shape.
- `references/domain-randomization-and-slurm.md`: sim2sim randomization and distributed/SLURM scaling.
- `scripts/build_training_command.py`: command-template generator that avoids hard-coding local paths.

## Standard action pattern

1. Identify the robot, simulator backend, motion file, experiment config, run name, env count, and batch size.
2. Verify the backend environment and assets before training.
3. Use `--create-config-only` when the task is to inspect or migrate configs without launching long training.
4. Use a new `--experiment-name` for config changes; resume ignores new training CLI overrides.
5. Use `--full-eval --headless` for bounded inference validation.
6. For multi-GPU, remember `--num-envs` and `--batch-size` are per GPU/process; total scale is multiplied by `--ngpu * --nodes`.

## Common command skeletons

```bash
protomotions train-agent \
  --robot-name g1 \
  --simulator isaaclab \
  --experiment-path <experiment.py> \
  --experiment-name <run_name> \
  --motion-file <motion_lib.pt> \
  --num-envs 4096 \
  --batch-size 16384 \
  --ngpu 1
```

```bash
protomotions inference-agent \
  --checkpoint <run_dir>/last.ckpt \
  --simulator mujoco \
  --num-envs 1 \
  --headless \
  --full-eval
```

## Decision points

- Use Mimic for reference motion tracking; use AMP/ASE/ADD when adversarial style/skill embeddings or differential discriminators match the task.
- Use GPC/PEFT for staged discrete latent prior training and task adaptation.
- Use domain-randomized G1 tracker workflows for sim2sim/real deployment candidates.
- Use MuJoCo inference for quick G1/H1 debug; do not assume SMPL/SMPL-X spherical-joint transfer.
- Use `--overrides` only for scalar values; create a new experiment file for nested objects/lists/dataclass changes.
