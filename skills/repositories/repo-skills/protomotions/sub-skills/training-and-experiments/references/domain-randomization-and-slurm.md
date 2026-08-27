# Domain randomization and SLURM

## Domain randomization purpose

Domain randomization helps policies transfer across physics engines or to real robots by training under variation in action outputs, contact/friction, mass/center of mass, sensor observations, resets, and perturbations.

Common randomization families:

- Action noise: perturb PD targets/actions.
- Friction randomization: sample static/dynamic friction and restitution buckets.
- Object asset randomization: sample scene object friction, mass/density, and center of mass.
- Center of mass randomization: perturb selected robot bodies such as torso.
- Observation noise: noisy actor observations and clean critic observations.
- Push/perturbation randomization: periodic velocity/angular impulses.
- Reset noise: perturb initial root/DOF states.

At inference/export time, observation noise is disabled; robustness comes from training exposure.

## Simulator friction conversion

Different simulators combine friction differently. PhysX backends use average-like behavior, while MuJoCo uses max-like behavior. ProtoMotions has utility logic to convert friction settings when switching simulators so effective friction stays closer to the intended config. Do not hand-tune cross-sim friction before checking that conversion path.

## Cross-simulator limits

- G1/H1 hinge-joint policies trained with a transfer-oriented domain-randomization recipe are the best sim2sim candidates.
- SMPL/SMPL-X spherical joints do not transfer cleanly to MuJoCo/Newton because joint representation differs.
- A policy's model card or training config is the evidence for expected transfer; backend availability alone is not.

## SLURM launcher concepts

ProtoMotions' SLURM workflow is source-checkout oriented and intended as a customizable cluster template. It syncs code, generates a batch script, submits arrays, and relies on an autoresume callback.

Key arguments and semantics:

- `--ngpu`: GPUs per node.
- `--nodes`: number of nodes.
- `--num-envs`: environments per GPU/process.
- `--batch-size`: batch size per GPU/process.
- Total GPUs = `ngpu * nodes`.
- Effective envs and batch scale by total GPUs.
- `--slurm-time` and array size bound sequential resume attempts.
- `--use-slurm` registers autoresume behavior during training.

## Autoresume behavior

The autoresume callback saves before walltime and signals graceful stop. Next array job resumes from the last checkpoint. This is not a replacement for correct run names and resolved-config consistency.

## Operational cautions

- Customize cluster login, base directory, account, partition, mounts, and container image paths before using a SLURM launcher.
- Do not expose cluster credentials in scripts or generated docs.
- Use explicit checkpoints and experiment names when recovering interrupted jobs.
- Keep per-GPU batch/env sizing in mind when scaling nodes.
