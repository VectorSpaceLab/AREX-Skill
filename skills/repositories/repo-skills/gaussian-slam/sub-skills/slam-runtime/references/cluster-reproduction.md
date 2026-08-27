# Safe SLURM reproduction plan

The repository's `scripts/reproduce_sbatch.sh` is a useful source anchor but is a
site template, not a drop-in job. It requests one node/GPU, 12 CPUs, a `gpu`
partition, a 24-hour limit, and a scene array. It contains placeholders that
must be reviewed, a fixed example array, a case mismatch for the ScanNet++
config directory, and a trailing shell continuation after `--group_name`.
Generate a plan with `scripts/render_sbatch_plan.py` and review it before any
manual submission.

## Plan generation

The planner only prints a script. It does not call `sbatch`, invoke
`run_slam.py`, acquire datasets, or use W&B credentials:

```bash
python scripts/render_sbatch_plan.py \
  --dataset Replica \
  --scene room0 --scene room1 \
  --input-root <scene-input-root> \
  --output-root <output-root> \
  --experiment-name reproduce \
  --partition gpu --gpus 1 --cpus 12 --time 24:00:00
```

Supply scene names explicitly. The planner maps the public dataset label
`ScanNetPP` to the repository's lowercase `scannetpp` config directory; it does
not guess a dataset layout. `--check-files` performs local config existence
checks only.

## Review checklist

Before manually writing the emitted plan to a batch file and submitting it:

- run from the repository root, or make `cd` explicit in the batch file;
- set a valid environment activation command for the cluster; the source
  template's `<path-to-conda.sh>` is a placeholder;
- confirm the array range is `0-(number of scenes - 1)` and that each scene has
  a matching config filename;
- confirm the configured partition, one GPU allocation, CPU count, time limit,
  and output/log directories are appropriate;
- make input and output roots writable and unique for the experiment;
- keep `use_wandb: false` or set `DISABLE_WANDB=true` unless W&B logging has a
  deliberate network/auth policy;
- check that the generated command has no trailing `\\` after the last
  argument; and
- preserve stdout/stderr and inspect every output directory after completion.

## Corrected recipe shape

The following is a shape to review, not a command to execute here. Replace all
angle-bracket placeholders and scene names. It has no submission command:

```bash
#!/usr/bin/env bash
#SBATCH --output=<output-root>/logs/%A_%a.log
#SBATCH --error=<output-root>/logs/%A_%a.log
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --gpus-per-node=1
#SBATCH --partition=gpu
#SBATCH --cpus-per-task=12
#SBATCH --time=24:00:00
#SBATCH --array=0-1

set -euo pipefail
cd <repository-root>
# source <path-to-conda.sh>
# Activate the prepared Gaussian-SLAM environment using your site policy.

scenes=(room0 room1)
scene="${scenes[$SLURM_ARRAY_TASK_ID]}"
mkdir -p <output-root>/logs

DISABLE_WANDB=true python run_slam.py \
  configs/Replica/"${scene}".yaml \
  --input_path <scene-input-root>/"${scene}" \
  --output_path <output-root>/Replica/reproduce/"${scene}" \
  --group_name reproduce
```

`--group_name` is only a W&B grouping value; it is harmless while W&B is
forced off but does not name the output directory. Keep the command's last line
free of a continuation character. Set `START_TIME` only if logging it; the
source template prints an unset variable.

## Runtime recovery on a cluster

- A failed array element should be rerun with a new output path or an explicit,
  reviewed resume policy; this repository does not expose a general resume
  flag for an interrupted Gaussian-SLAM loop.
- Preserve the element log and inspect `config.yaml`, pose checkpoint, and
  submaps before deciding whether mapping reached a boundary.
- For an OOM, lower diagnostic mapping points/iterations or frame limit in a
  copied config, request a suitable GPU, and never infer that a CPU partition
  can run the pipeline.
- For missing extensions, repair the environment on the node or rebuild for
  its Torch/CUDA and SM architecture before rerunning.
- For W&B failures, rerun with `DISABLE_WANDB=true`; do not place API keys in
  the batch script.
