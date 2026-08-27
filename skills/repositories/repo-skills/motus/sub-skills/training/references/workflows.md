# Training workflows

All commands below are templates. Replace placeholders with paths and resources
for the target deployment, run them from the Motus project root, and review the
rendered command before execution. The repository's `scripts/train.sh`,
`scripts/slurm/*.sh`, and `scripts/slurm/launch.sh` are **reference-only**:
training is long-running, `sbatch`/`srun` have external cluster side effects,
and the checked-in scripts contain site-specific placeholder paths and
NCCL-interface assumptions. Do not bundle or execute them as a validation step.

## 1. Prepare a bounded run

Start with a copy of the appropriate YAML outside the runtime skill tree. For a
safe smoke configuration, use a real small dataset subset or
`dataset.max_episodes`, a small positive `training.max_steps`, modest
`num_workers`, frequent logging, and `logging.report_to: none` or
`tensorboard`. Do not use fake checkpoint paths to test model construction:
the WAN config, VAE, VLM, and dataset are required for a real GPU smoke run.

Run the following *non-destructive* checks with the bundled exporter only after
selecting a real checkpoint directory:

```bash
python - <<'PY'
from pathlib import Path
import importlib.util
for name in ("torch", "yaml", "omegaconf", "accelerate"):
    try:
        mod = __import__(name)
        print(f"{name}: {getattr(mod, '__version__', 'imported')}")
    except Exception as exc:
        print(f"{name}: ERROR: {exc}")
try:
    import torch
    print("cuda_available:", torch.cuda.is_available())
    print("gpu_count:", torch.cuda.device_count())
    if torch.cuda.is_available():
        print("device0:", torch.cuda.get_device_name(0))
        print("bf16:", torch.cuda.is_bf16_supported())
except Exception as exc:
    print("torch CUDA probe ERROR:", exc)
for name in ("deepspeed", "flash_attn", "wandb"):
    try:
        __import__(name)
        print(f"{name}: imported")
    except Exception as exc:
        print(f"{name}: unavailable ({type(exc).__name__}: {exc})")
PY

python scripts/export_config_json.py --yaml CONFIG.yaml --ckpt_dir CHECKPOINT_DIR
```

The first probe is an environment check, not a model check. The exporter reads
YAML and writes only `CHECKPOINT_DIR/config.json`; it does not load weights,
create a model, contact a service, or validate data. It creates a new checkpoint
directory if needed, but refuses to replace an existing `config.json` unless
`--force` is supplied after review. It must not be mistaken for a checkpoint
save.

## 2. Single-node torchrun + DeepSpeed

The supplied example uses eight GPUs and `configs/zero1.json`. Construct a
command with one process per visible GPU:

```bash
torchrun \
  --nnodes=1 \
  --nproc_per_node=GPU_COUNT \
  --node_rank=0 \
  --master_addr=127.0.0.1 \
  --master_port=29500 \
  train/train.py \
  --config CONFIG.yaml \
  --deepspeed configs/zero1.json \
  --run_name RUN_NAME \
  --report_to tensorboard
```

Use `--nproc_per_node` equal to the GPUs allocated to this job, not an
unrelated machine-wide count. A different free `--master_port` is needed if
multiple jobs share a node. `--checkpoint_dir`, `--wandb_project`, and
`--log_level` can be added as explicit CLI overrides. To run without
DeepSpeed, omit `--deepspeed` deliberately and re-check VRAM; omitting the
argument changes sharding behavior.

The effective checkpoint directory is formed by `train/train.py` as:

```text
system.checkpoint_dir / YAML_FILE_STEM / run_name
```

For example, a `robotwin.yaml` run named `robotwin_sft` is placed below the
configured base directory under `robotwin/robotwin_sft`. Rank 0 creates it.
Avoid reusing a directory for a different mode or topology unless the intent is
an explicit resume.

## 3. SLURM single node

The logical equivalent of the checked-in single-node template is:

1. Request one node, the intended number of GPUs, enough host memory and CPU
   workers, and the correct partition.
2. Load the site CUDA module and activate the environment in the batch job.
3. Set `PYTHONPATH` to the project root if the site environment does not
   already import the package.
4. Set `OMP_NUM_THREADS` to a value compatible with `cpus-per-task` and set
   NCCL variables only after confirming the site's interface/HCA names.
5. Use `SLURM_JOB_NUM_NODES`, `SLURM_GPUS_ON_NODE`, and `SLURM_NODEID` to
   construct the same torchrun command as above. For one node, the master
   address can be `127.0.0.1` or the resolved hostname.

A generic command body is:

```bash
MASTER_ADDR="$(hostname)"
MASTER_PORT="${MASTER_PORT:-29500}"
torchrun \
  --nnodes="${SLURM_JOB_NUM_NODES:-1}" \
  --nproc_per_node="${SLURM_GPUS_ON_NODE:-GPU_COUNT}" \
  --node_rank="${SLURM_NODEID:-0}" \
  --master_addr="$MASTER_ADDR" \
  --master_port="$MASTER_PORT" \
  train/train.py \
  --config "$CONFIG_FILE" \
  --deepspeed configs/zero1.json \
  --run_name "$RUN_NAME" \
  --report_to tensorboard
```

Do not copy `PROJECT_ROOT`, conda, log, partition, `NCCL_IB_HCA`, or
`NCCL_SOCKET_IFNAME` values from a different cluster. Site-specific NCCL
settings can make an otherwise valid job fail or select the wrong network.
`sbatch` is a submission side effect and must be user-approved.

## 4. SLURM multi-node

For N nodes with G GPUs per node, use one launcher task per node and let each
node run torchrun with `--nproc_per_node=G`:

```bash
nodes="$(scontrol show hostnames "$SLURM_JOB_NODELIST")"
MASTER_ADDR="$(printf '%s\n' "$nodes" | head -n 1)"
export MASTER_ADDR
export MASTER_PORT="${MASTER_PORT:-29500}"

srun bash -c '
  torchrun \
    --nnodes="$SLURM_JOB_NUM_NODES" \
    --nproc_per_node="$SLURM_GPUS_ON_NODE" \
    --node_rank="$SLURM_NODEID" \
    --master_addr="$MASTER_ADDR" \
    --master_port="$MASTER_PORT" \
    train/train.py \
    --config "$CONFIG_FILE" \
    --deepspeed configs/zero1.json \
    --run_name "$RUN_NAME" \
    --report_to tensorboard
'
```

This template assumes the batch environment exports the variables used by the
`srun` workers and that every node sees the same project, YAML, checkpoints,
dataset paths, and DeepSpeed JSON. Validate hostname resolution and the master
port before launching. Start with `N=1`; then validate a two-node short run
before scaling out. A multi-node launch can hang rather than fail fast when
NCCL routing, firewall, or rank counts are wrong.

The checked-in multi-node flow uses `scontrol show hostnames`, sets a master
address, exports config/run-name/port, and invokes a worker through `srun`.
That is useful for understanding topology, but it is not a portable script and
is intentionally not bundled here.

## 5. Checkpoint choice: scratch, fine-tune, or resume

### Stage 2 / pretrain from base backbones

Use `training_mode: pretrain` (as in the latent-action example), set both
selectors to null, and point `model.wan.*` and `model.vlm.checkpoint_path` at
real foundation checkpoints:

```yaml
training_mode: pretrain
resume:
  checkpoint_path: null
finetune:
  checkpoint_path: null
```

The model loads Wan2.2 and Qwen3-VL. This requires the WAN architecture
`config.json`, WAN weights, VAE, and VLM checkpoint. It is not a way to recover
from an interrupted run.

### Stage 3 fine-tune from Stage 2

Use `training_mode: finetune`, leave resume null, and set the Stage 2 Motus
checkpoint in `finetune.checkpoint_path`:

```yaml
training_mode: finetune
resume:
  checkpoint_path: null
finetune:
  checkpoint_path: "STAGE2_CHECKPOINT_OR_PARENT"
```

The entry point disables initial WAN/VLM backbone loading and calls the partial
Motus loader. The loader tries both
`<parent>/pytorch_model/mp_rank_00_model_states.pt` and
`<parent>/mp_rank_00_model_states.pt`. It skips action input/decoder keys by
design. Confirm the checkpoint layout before spending GPU time.

### Resume an interrupted run

Set `resume.checkpoint_path` to the exact directory saved at a step, keep
`finetune.checkpoint_path: null`, and normally retain the original
`training_mode` and topology:

```yaml
resume:
  checkpoint_path: "CHECKPOINT_STEP_DIRECTORY"
  reset_scheduler: false
finetune:
  checkpoint_path: null
```

`Accelerator.load_state` restores the complete state. The trainer extracts
`10000` from `checkpoint_step_10000`, restores model/optimizer/scheduler/data
loader/RNG state, and runs until `max_steps`. With
`reset_scheduler: true`, it applies the current scheduler parameters and resets
the custom schedule's warmup progress; use this only intentionally when
changing the schedule.

The code disables WAN/VLM reload whenever either selector is set. For both
resume and fine-tune, WAN/VLM are therefore not reloaded as foundation models;
the VAE remains needed for video processing. This is the source behavior, not a
suggestion to delete backbone paths from the YAML.

### Ambiguous state to reject

Do not set both selectors. The source does not enforce exclusivity and may
attempt partial fine-tune initialization followed by full state loading. If a
resume directory is missing or cannot be loaded, stop and repair the path
rather than clearing it and unintentionally starting a scratch run.

## 6. Logging and signals

Choose reporting deliberately:

- `tensorboard` is the lowest-friction persistent local option; inspect the
  configured `tensorboard_log_dir` under the run directory.
- `wandb` requires the package and a working W&B environment/API setup; rank 0
  initializes it with `logging.wandb_project` and the resolved run name.
- `all` requires both and duplicates scalar reporting.
- `none` prevents backend initialization and is useful for isolated checks.

A healthy startup reports the loaded YAML, dataset type, optional training mode,
derived action chunk size, checkpoint directory, logging backend, model and
optimizer creation, and dataloader creation. During execution rank 0 reports
`Step ... Loss: ... (Video: ..., Action: ...)`, learning rates, and step time.
Validation reports video/action metrics at `system.val_interval`; checkpoint
saves occur at `system.save_interval` and once at completion.

A normal saved checkpoint is an Accelerator/DeepSpeed state directory, not just
a JSON file. `train/train.py` also attempts to write a filtered `config.json`
inside every saved checkpoint. If that write fails, treat the checkpoint as
less reproducible and use the exporter after diagnosing the directory.

## 7. Recovery after interruption

1. Preserve the existing checkpoint directory and logs.
2. Inspect the last complete `checkpoint_step_<N>` and ensure it contains the
   expected Accelerator/DeepSpeed state files.
3. Copy the prior YAML, change only intentional resource or schedule values,
   set `resume.checkpoint_path` exactly, and clear `finetune.checkpoint_path`.
4. Re-run safe path/package/GPU/NCCL checks and use the same world size unless
   a deliberate topology change has been validated.
5. Choose `reset_scheduler` explicitly; do not silently reset it because a new
   `max_steps` was chosen.
6. Use a new `run_name`/output directory only if the checkpoint semantics and
   operator record make the branch clear. Never overwrite an unrelated run.

If a job was killed during checkpoint save, choose the previous complete step;
partial directories may not be loadable. For NCCL/network failure, fix the
cluster environment first and resume from the last complete state rather than
starting scratch.
