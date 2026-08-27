# Launch Command Construction

`accelerate launch` wraps the lower-level torch, TPU, DeepSpeed, FSDP, SageMaker, or simple launcher selected by CLI flags and config values. Build commands so that Accelerate flags come before the target script/module and target arguments come after it.

## Decision Checklist

1. Pick the config source: default cache config, explicit `--config_file`, or all required flags inline.
2. Pick one launcher mode: CPU, single process, multi-GPU/XPU/NPU/HPU, TPU, DeepSpeed, FSDP, Megatron-LM, SageMaker, or no explicit distributed flag.
3. Decide whether the target is a file, Python module, or executable:
   - File: `accelerate launch train.py --epochs 3`.
   - Module: `accelerate launch --module package.train --epochs 3`.
   - Non-Python executable: `accelerate launch --no_python ./train.sh --epochs 3`.
4. Put all script-specific arguments after the target. If a script argument looks like an Accelerate flag, it is safe only after the target.
5. For multi-node, ensure the same launch command runs on every node, with a unique `machine_rank` per node unless a scheduler wrapper handles ranks.

## Common Commands

Single-process CPU debug:

```bash
accelerate launch --cpu --num_processes 1 train.py --max_steps 10
```

Single-node two-GPU launch without a config:

```bash
accelerate launch --multi_gpu --num_processes 2 --mixed_precision fp16 train.py --batch_size 8
```

Explicit config launch:

```bash
accelerate launch --config_file configs/multigpu.yaml train.py --batch_size 8
```

Python module launch:

```bash
accelerate launch --module my_package.train --config configs/model.yaml
```

No-Python launch for an executable script:

```bash
chmod +x ./run_training.sh
accelerate launch --no_python ./run_training.sh --arg value
```

Do not combine `--module` and `--no_python`.

## Multi-Node Launch

For two nodes with four processes per node, `num_processes` is total processes (`8`), not per-node processes. Use the rank-0 node's intranet address for `main_process_ip` when possible.

Rank 0:

```bash
accelerate launch \
  --multi_gpu \
  --num_processes 8 \
  --num_machines 2 \
  --machine_rank 0 \
  --main_process_ip 10.0.0.5 \
  --main_process_port 29500 \
  --rdzv_backend static \
  train.py --arg value
```

Rank 1:

```bash
accelerate launch \
  --multi_gpu \
  --num_processes 8 \
  --num_machines 2 \
  --machine_rank 1 \
  --main_process_ip 10.0.0.5 \
  --main_process_port 29500 \
  --rdzv_backend static \
  train.py --arg value
```

Use `--rdzv_backend c10d` in scheduler-managed jobs when static host assumptions are brittle. Keep `main_process_port` open and consistent across nodes.

## SLURM Planning

SLURM examples in Accelerate use `srun` to execute one launcher command per node. They derive the head node from `SLURM_JOB_NODELIST`, compute total processes from `SLURM_NNODES * GPUS_PER_NODE`, and flatten the command into one line because shell/scheduler layers can mishandle multiline launch strings.

Template for multi-GPU SLURM planning:

```bash
#!/bin/bash
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=1
#SBATCH --gres=gpu:4

GPUS_PER_NODE=4
HEAD_NODE_IP=$(scontrol show hostnames "$SLURM_JOB_NODELIST" | head -n 1)

LAUNCHER="accelerate launch \
  --num_processes $((SLURM_NNODES * GPUS_PER_NODE)) \
  --num_machines $SLURM_NNODES \
  --rdzv_backend c10d \
  --main_process_ip $HEAD_NODE_IP \
  --main_process_port 29500"
SCRIPT="train.py"
SCRIPT_ARGS="--batch_size 8"
CMD="$LAUNCHER $SCRIPT $SCRIPT_ARGS"
echo "$CMD"
srun $CMD
```

SLURM safety notes:

- Do not assume SLURM is installed. If `scontrol` or `srun` is missing, produce a plan or script template rather than executing it.
- Keep scheduler resource requests aligned with Accelerate flags. For example, `--gres=gpu:4` and `GPUS_PER_NODE=4` should match.
- For CPU distributed jobs, include `--cpu` in the launcher or set `use_cpu: true` in the config.
- If a backend needs hostfiles or scheduler-specific options, route backend semantics to distributed-training-backends.

## Config Versus Inline Flags

Prefer config files for stable training recipes and inline flags for one-off overrides or scheduler-provided values. Useful hybrid pattern:

```bash
accelerate launch \
  --config_file configs/base_multinode.yaml \
  --num_processes "$TOTAL_PROCESSES" \
  --num_machines "$NUM_MACHINES" \
  --machine_rank "$MACHINE_RANK" \
  --main_process_ip "$MASTER_ADDR" \
  --main_process_port "$MASTER_PORT" \
  train.py --arg value
```

Inline launch flags override missing or configurable values from the config. If a config contains `num_processes: -1`, pass `--num_processes` manually.

## Command Separator Pitfalls

Accelerate does not require a `--` separator before training-script arguments. The boundary is the positional target script/module/executable:

```bash
accelerate launch --num_processes 2 train.py --num_processes 99
```

In this example, the first `--num_processes 2` belongs to Accelerate; the second `--num_processes 99` belongs to `train.py`. If an argument intended for the training script is placed before `train.py`, Accelerate will parse it or reject it.
