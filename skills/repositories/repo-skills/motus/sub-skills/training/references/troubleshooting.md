# Training troubleshooting

Classify the failure before changing configuration. Keep the original YAML,
command, environment probe, and rank-0/rank-last logs with the run record.

## Installation and import

**`ModuleNotFoundError: wandb`, `deepspeed`, `flash_attn`, or another package**

- `train/train.py` imports `wandb` at module import time even when
  `--report_to none` is selected. Therefore `none` avoids W&B initialization,
  but it does not avoid the import requirement in this source revision.
- `--deepspeed` requires a working DeepSpeed installation compatible with the
  installed PyTorch/CUDA and Accelerate versions.
- Install the repository requirements in the intended Python 3.10 environment,
  then install flash-attn with the project's documented
  `pip install flash-attn --no-build-isolation` only when the CUDA toolchain and
  compatible PyTorch are present. Do not blindly install into a different
  interpreter.
- Verify with `python -c 'import torch, accelerate, omegaconf, wandb'` and,
  when requested, separate `import deepspeed` and `import flash_attn` checks.
  Record versions and `which python`.
- The repository has no `pyproject.toml` or `setup.py`; run from the project
  root or export an appropriate `PYTHONPATH`. `train/train.py` appends its
  parent root itself, but WAN imports and dataset package resolution still need
  the source tree available.

The known inspection shell may differ from the requested Python 3.10/CUDA
2.7.1+cu128 environment. Treat any version mismatch as evidence of the wrong
interpreter, not as a Motus model result.

## Optional dependencies and backend

**Flash-attention missing or slow training**

Flash-attn is an optional performance dependency in the installation guide but
is expected for practical training. Without it, startup may fail in an imported
WAN/attention module or execution may become much slower and exceed memory.
Confirm the package was built against the active torch/CUDA. Do not substitute a
CPU wheel for a CUDA training run.

**CUDA unavailable / CPU-only parser succeeds**

YAML parsing, help output, and exporter execution are CPU-safe checks. The
actual model uses CUDA autocast, bf16, WAN VAE, and multi-billion-parameter
backbones. Motus documents training at more than 80 GB VRAM, with A100 80 GB,
H100, or B200 examples. An A100 SM 8.0 must be probed for bf16 support and free
memory; the stated inspection hardware/versions are not proof that a full run
fits. Stop on `torch.cuda.is_available() == False`, insufficient GPUs, missing
VAE, or missing model files.

**DeepSpeed initialization errors**

Check that `--deepspeed` points to valid JSON and that `import deepspeed` works
in the same interpreter. The supplied `zero1.json` and `zero2.json` enable bf16
and use automatic batch/gradient settings. Despite its filename, `zero2.json`
has `zero_optimization.stage: 1` in this source snapshot; treat it as a
variant of ZeRO-1, not ZeRO-2. If changing `stage`, reduce-scatter, or batch
settings, validate against the installed DeepSpeed version and allocated GPU
count.

## Config and data

**Config not found / YAML parse failure**

Use a path relative to the project root or an absolute path on the target
machine. Parse with OmegaConf or PyYAML before launching. Avoid shell comments
on a continued command line: the checked-in training guide shows a fragile
`--deepspeed ... \ # comment` pattern; put comments on their own line.

**Unknown dataset / dataset constructor failure**

The factory supports `robotwin`, `ac_one`, `latent_action`, `aloha_agilex_2`,
and `lerobot` in this revision. Check `dataset.type` spelling and required
paths. `latent_action.dataset_dir` is a list; LeRobot needs `dataset.params`
with `repo_id`, `root`, and usually `embodiment_type`. For robotwin, check
`data_mode`, `task_mode`, `task_name`, and episode limits. Use the sibling data
skill for layout and conversion; do not fix a data-shape error by changing model
shape fields without checking the dataset.

**Missing files or empty dataset**

Inspect every local path before a GPU run: dataset root(s), WAN
`config.json`, WAN checkpoint, VAE `.pth`, VLM checkpoint, and any T5/cache
paths required by the chosen dataset. A non-null checkpoint selector must point
to an actual saved state. An empty dataset or no validation samples can appear
only after expensive model startup, so preflight it with dataset-specific
read-only checks where available.

**Tensor-shape / action-chunk mismatch**

Compute `common.num_video_frames * common.video_action_freq_ratio`. Compare
that result and `common.action_dim` with the selected dataset's action sequence.
Check video height/width and state dimensions. The source computes
`config.common.action_chunk_size` after loading; it does not fully validate
these relationships. Do not use `action_expert.chunk_size` as a YAML override;
comments in embodiment configs say it is derived.

## Checkpoint and mode failures

**WAN/VLM unexpectedly reloaded or not loaded**

The entry point sets `model.load_pretrained_backbones = False` when either
`resume.checkpoint_path` or `finetune.checkpoint_path` is non-null. This is
intentional for resume/fine-tune and avoids overwriting adapted weights. For a
scratch/pretrain run, clear both selectors and ensure foundation paths exist.
The VAE is still needed for video processing in resume/fine-tune.

**`load_pretrain_weights` says wrong mode / file not found**

Set `training_mode: finetune` for Stage 3 partial loading. Check both accepted
directory layouts:

```text
PARENT/pytorch_model/mp_rank_00_model_states.pt
PARENT/mp_rank_00_model_states.pt
```

The loader filters `action_expert.input_encoder.*` and
`action_expert.decoder.*`; missing keys in these areas can be expected. Other
large unexpected/missing key sets require matching the Stage 2 model/config.

**Resume does not continue / scheduler behaves differently**

The resume path must include `step_<N>` for the trainer to restore the intended
`global_step`; otherwise it logs a warning and starts the counter at zero even
though `Accelerator.load_state` is attempted. Use the exact complete
Accelerator state directory. `reset_scheduler: true` intentionally resets the
custom schedule to current YAML values; false synchronizes scheduler progress.
Do not combine resume with a fine-tune path.

**Checkpoint directory contains only `config.json`**

The exporter is not a checkpoint writer. It only writes filtered configuration.
A real save requires the training loop/Accelerator and may include DeepSpeed
rank state files. Preserve the last complete checkpoint if a save was
interrupted.

## CLI, API, and workflow errors

**`train/train.py --help` fails before showing flags**

This source imports `wandb` before parsing. Install the import dependency or
use a static parser inspection. Verified parser flags are:
`--config`, `--checkpoint_dir`, `--log_level`, `--report_to` with choices
`wandb|tensorboard|all|none`, `--wandb_project`, `--run_name`, `--deepspeed`,
and `--local_rank`. A successful `--help` is a CPU/parser check only.

**W&B/TensorBoard issues**

For W&B, install/import `wandb`, set the project/name intentionally, and check
credentials/network on rank 0. For TensorBoard, check writable
`system.checkpoint_dir` and `logging.tensorboard_log_dir`. For `all`, diagnose
each backend independently. Use `none` only after confirming the unconditional
W&B import is satisfied.

**Run name/checkpoint path collision**

The code appends YAML stem and run name to `system.checkpoint_dir`. A CLI
`--checkpoint_dir` changes the base; it does not name a checkpoint step. Use a
new run name for scratch/fine-tune branches and an exact existing step directory
for resume. Do not delete a prior run to solve a collision.

## Distributed and NCCL failures

**NCCL timeout, hang at startup, or `connection refused`**

- Confirm every process has the same `--nnodes`, `--nproc_per_node`,
  `--node_rank`, `--master_addr`, and `--master_port`.
- For multi-node, resolve the first SLURM hostname from
  `scontrol show hostnames "$SLURM_JOB_NODELIST"`; ensure it is reachable from
  every node and the port is permitted by the cluster.
- Confirm all nodes see the same code/config/checkpoint/data paths and use the
  same torch/CUDA/DeepSpeed stack.
- Check `NCCL_DEBUG=INFO` logs and use site-approved `NCCL_SOCKET_IFNAME` and
  `NCCL_IB_HCA`; do not copy the example's `bond1`/`mlx5_*` values to another
  cluster. Temporarily disabling IB (`NCCL_IB_DISABLE=1`) can isolate an IB
  problem, but may be much slower and should be a diagnostic, not a default.
- The reference scripts increase async error handling and heartbeat timeouts
  for long checkpoint saves. Apply such values only with cluster-admin
  guidance; a long timeout can hide a real rank failure.

**One rank crashes and the others hang**

Read the first failing rank's traceback, not only the later NCCL timeout. Common
causes are a missing local path, malformed sample, OOM, or mismatched package.
Stop the allocation, fix the first cause, and resume from the last complete
checkpoint. Do not restart all ranks repeatedly without changing the cause.

**GPU OOM**

Confirm allocated GPUs and per-process `batch_size`; this is the source's
DataLoader batch size per process. Reduce batch size or frame/resolution only
with an explicit experiment record, use gradient accumulation consistently,
check DeepSpeed sharding, and reduce dataloader workers if host memory is the
issue. Do not assume ZeRO-1 and the file named zero2 have the same memory
behavior. Inspect fragmentation and consider the source's
`PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` setting.

## Workflow-specific errors

**Validation repeatedly fails or is too expensive**

Validation is rank-0-only and the trainer calls `evaluate_model` for two
batches by default at `val_interval`. It runs actual WAN/VLM inference and can
be expensive. For a smoke run, make `val_interval` large or use a small
validation dataset while preserving at least one valid sample. Do not confuse
missing validation metrics with a failed training step.

**Loss is NaN/Inf**

Record the first step, video/action losses, learning rates, input ranges, and
rank. Check data normalization, bad frames/actions, bf16/flash-attn compatibility,
learning rates, and gradient clipping (`grad_clip_norm` defaults to 0.5 in
examples). Reproduce on a bounded dataset/run with the same mode; do not reset
or overwrite a good checkpoint until the input/config cause is isolated.

**Slow data loading or worker crashes**

Check `system.num_workers`, `pin_memory`, host RAM, file descriptor limits,
network filesystem throughput, and dataset cache/T5 fallback behavior. Reduce
workers for diagnosis (0 means main process only) and lower `max_episodes` for
a bounded check. Dataset-specific fixes belong in the sibling data skill.

**Job interrupted during save or preemption**

Use the previous complete `checkpoint_step_<N>`, not a directory created at the
interruption boundary. Keep the same mode, clear `finetune` for a resume, set
`resume.checkpoint_path`, and choose scheduler reset deliberately. Preserve
logs and avoid destructive cleanup until the resumed job is verified.

## Known source limitations and intentional omissions

- No full static config validator is shipped by Motus; the checks above are
  operating safeguards, not claims about source-enforced validation.
- The parser's `--local_rank` value is accepted but environment ranks drive
  `setup_distributed`/Accelerate.
- The provided `zero2.json` filename and stage disagree.
- The entry point imports W&B unconditionally, so `report_to: none` is not a
  dependency-free mode in this snapshot.
- WAN/VLM checkpoint availability, dataset contents, cluster network names,
  exact VRAM headroom, and Stage 1-only VGM procedure were not verified here.
- This sub-skill intentionally omits detailed dataset layouts, conversion
  commands, and inference CLI/API; use the linked sibling skills.
