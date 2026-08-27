# Troubleshooting Distributed Accelerators

Use this reference to diagnose common Lightning accelerator, strategy, precision, and hardware failures. State whether a check is import-only, syntax-only, or requires real distributed/GPU execution.

## Fast Triage

1. Confirm package import and version:

```bash
python - <<'PY'
import lightning as L
import torch
print('lightning', L.__version__)
print('torch', torch.__version__)
PY
```

2. Check hardware visibility:

```bash
python - <<'PY'
import torch
print('cuda_available', torch.cuda.is_available())
print('cuda_count', torch.cuda.device_count())
print('cuda_version', torch.version.cuda)
print('mps_available', hasattr(torch.backends, 'mps') and torch.backends.mps.is_available())
PY
```

3. Validate configuration syntax without launching workers:

```bash
python scripts/strategy_config_check.py --mode trainer --accelerator cpu --devices 1 --strategy auto --precision 32-true
python scripts/strategy_config_check.py --mode trainer --accelerator cuda --devices 4 --strategy ddp --precision 16-mixed
```

4. Only after syntax checks, run a minimal real job on the target hardware with tiny data and `max_steps=1` or `fast_dev_run=True`.

## Install and Import Failures

| Signal | Likely cause | Response |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'lightning'` | Lightning is not installed in the active environment | Install `lightning`; ensure the command uses the same Python environment as the user’s script. |
| `ModuleNotFoundError: No module named 'pytorch_lightning'` | Legacy import package unavailable | Prefer `import lightning as L` or `import lightning.pytorch as pl`; install compatibility package only if the project requires legacy imports. |
| `ModuleNotFoundError: No module named 'deepspeed'` | DeepSpeed optional dependency missing | Install `deepspeed` in an environment whose CUDA/PyTorch versions match. |
| Transformer Engine import failure | Optional FP8 package missing or unsupported GPU | Install `transformer_engine` only on compatible NVIDIA stacks; require Hopper-class GPUs for the intended FP8 path. |
| Bitsandbytes import or runtime failure | Optional quantization package missing, non-Linux, non-CUDA, or unsupported wheel | Use CUDA/Linux-compatible `bitsandbytes`; otherwise choose FSDP/DeepSpeed/precision alternatives. |
| XLA/TPU import failure | XLA dependencies or TPU runtime missing | Install the correct XLA package for the target torch/runtime; validate in the TPU environment. |

## Invalid Trainer/Fabric/API Usage

- `MisconfigurationException` from `devices=2` on CPU-only or no visible GPU: check `torch.cuda.device_count()`, `CUDA_VISIBLE_DEVICES`, scheduler allocation, and whether the user meant CPU smoke test (`accelerator="cpu", devices=1`).
- User passes `strategy="ddp"` with `devices=1`: use `strategy="auto"` or increase devices; DDP is for multiple processes.
- User calls `.cuda()` or `.to(device)` in `LightningModule`: remove manual movement and let Lightning place modules/batches; use `self.device` only for newly created tensors.
- User creates tensors on the wrong device: use `x.new_tensor(...)`, `torch.zeros(..., device=self.device)`, or registered buffers.
- User combines `fabric run` with `fabric.launch()` incorrectly: with CLI launch, do not call `fabric.launch()` again unless following an explicit Lightning pattern for that launch mode.
- User asks for CLI flags: choose values here, then route syntax to `../cli-configuration/SKILL.md`.

## Strategy-Specific Failures

### DDP

Signals:

- Hang at startup, NCCL timeout, or one rank exits early.
- Error mentions unused parameters.
- Dataloader order/duplication looks wrong.

Responses:

- Confirm every rank runs the same script and reaches `Trainer.fit`.
- For CUDA, use NCCL; for CPU debugging, use Gloo.
- Increase `DDPStrategy(timeout=...)` for slow startup only after fixing rank/network issues.
- Set `find_unused_parameters=True` if the model conditionally skips parameters, but warn about slowdown.
- Let Lightning manage distributed sampler replacement unless the user deliberately needs a custom sampler.
- Use `gradient_as_bucket_view=True` or `static_graph=True` only after correctness is stable.

### FSDP

Signals:

- Out-of-memory persists under FSDP.
- Checkpoint cannot be loaded on a different number of devices.
- Model initialization OOMs before training starts.

Responses:

- Add an `auto_wrap_policy` for large repeated blocks; avoid sharding tiny layers.
- Move large layer construction into `configure_model()` or `trainer.init_module()` so Lightning can initialize under strategy control.
- Choose and document `state_dict_type`; use a full-state export/conversion path when portability matters.
- Try `FULL_SHARD` for memory, `SHARD_GRAD_OP` for speed if memory allows, and `HYBRID_SHARD` for selected multi-node cases.
- Consider activation checkpointing, BF16 mixed precision, or CPU offload only with clear speed/memory trade-offs.

### DeepSpeed

Signals:

- DeepSpeed import/build error.
- Optimizer/scheduler configuration rejected.
- Checkpoint path is a directory or missing a single `.ckpt` file.
- Stage 3/offload is much slower than expected.

Responses:

- Verify `deepspeed` installation against the current PyTorch/CUDA stack.
- Keep the configuration to one optimizer and one scheduler unless the user has a tested DeepSpeed-specific design.
- Explain that DeepSpeed, especially ZeRO stage 3, saves sharded checkpoint directories; plan a conversion path for single-file portability.
- Tune `allgather_bucket_size` and `reduce_bucket_size`; smaller values reduce memory but can slow communication.
- CPU offload requires enough CPU RAM and adds host-device transfer overhead.

### Model/Tensor Parallel

Signals:

- Import errors around distributed tensor APIs.
- Shape/placement errors after parallelizing layers.
- User expects it to work like DDP.

Responses:

- Confirm the user needs tensor/model parallel because layers do not fit on a single device.
- Treat `ModelParallelStrategy` as expert/experimental and CUDA-oriented.
- Keep basic dataloader/training-loop decisions separate: route Fabric loop details to `../fabric-expert-loops/SKILL.md` or standard Trainer details to `../training-core/SKILL.md`.

## Backend and Hardware Limitations

- CUDA: PyTorch must be compiled with CUDA support; driver/runtime versions must be compatible; `CUDA_VISIBLE_DEVICES` can hide GPUs.
- MPS: not all PyTorch operations or precision modes match CUDA behavior; use MPS-specific repros and CPU fallback for unsupported ops.
- TPU/XLA: requires XLA runtime and dependencies; many CUDA/NCCL assumptions do not apply.
- CPU: CPU DDP is useful for debugging launch semantics but does not validate GPU memory, NCCL, AMP, FSDP CUDA paths, DeepSpeed CUDA kernels, or FP8.
- FP8/Transformer Engine: requires NVIDIA Hopper-class GPUs and the optional package.
- BF16: CPU BF16 is available through PyTorch CPU autocast paths, while GPU speedups depend on hardware generation.

## Cluster Failures

Signals:

- The job launches too many or too few processes.
- Ranks disagree on world size.
- NCCL cannot connect across nodes.
- SLURM job starts but Lightning complains about task counts.

Responses:

- Match scheduler settings to `Trainer(devices=..., num_nodes=...)`.
- Ensure `MASTER_ADDR` and `MASTER_PORT` are reachable from all nodes for manually launched jobs.
- Verify `NODE_RANK`, `RANK`, `LOCAL_RANK`, and `WORLD_SIZE` are set by exactly one launcher/scheduler layer.
- On SLURM, prefer the scheduler-managed launch pattern; avoid nesting `torchrun`/manual launch inside an already managed multi-task job unless intentionally configured.
- If a custom cluster environment is needed, implement Lightning’s `ClusterEnvironment` interface and pass it through `plugins=[...]`.

## Reporting Standard

When handing back a fix, include:

- The final `accelerator`, `devices`, `num_nodes`, `strategy`, and `precision` values.
- Whether the recommendation is for CPU smoke, single-node GPU, multi-node, TPU, or MPS.
- Optional packages required, such as `deepspeed`, `bitsandbytes`, `transformer_engine`, or XLA packages.
- Validation level: import-only, configuration syntax-only, one-step CPU smoke, or real target distributed run.
- Remaining risks: hardware not available, cluster networking untested, checkpoint portability unresolved, or optional kernels unvalidated.
