# Strategy Guide

This reference helps future agents choose Lightning distributed strategies and write concrete `Trainer` or `Fabric` configuration without reopening the source repository.

## Decision Table

| User need | Start with | Why | Watch for |
| --- | --- | --- | --- |
| Single-device smoke test or portable local repro | `accelerator="cpu", devices=1, strategy="auto", precision="32-true"` | Safe baseline that avoids GPU and distributed launch assumptions. | It does not validate CUDA, NCCL, FSDP, DeepSpeed, or TPU behavior. |
| One GPU or one Apple GPU | `accelerator="gpu"` or explicit `"cuda"`/`"mps"`, `devices=1`, `strategy="auto"` | Lightning chooses a single-device strategy. Use `"cuda"` to avoid `"gpu"` resolving to MPS on Apple systems. | GPU visibility and precision support must be checked separately. |
| Normal multi-GPU data parallel training | `accelerator="cuda"`, `devices=N`, `strategy="ddp"` | DDP is the default scalable choice when the model fits per GPU. | Avoid manual `.cuda()`/`.to(device)` in model code; Lightning owns device placement. |
| DDP is out of memory even at small batch size | `strategy="fsdp"` or `FSDPStrategy(...)` | FSDP shards parameters, gradients, and optimizer state to reduce memory. | Requires multiple GPUs and careful wrapping/checkpoint choices. |
| Very large model with ZeRO/offload needs | `strategy="deepspeed_stage_2"`, `"deepspeed_stage_3"`, or `DeepSpeedStrategy(...)` | DeepSpeed provides ZeRO stages, CPU offload, and large-model optimizations. | Requires `deepspeed`; single optimizer/scheduler is the safe assumption. |
| Tensor/model parallel or 2D parallelism | `ModelParallelStrategy(...)` | Lightning examples use tensor parallel plus FSDP-style data parallel for LLM-scale models. | Experimental surface; requires CUDA and PyTorch distributed tensor support. |
| Multi-node cluster | Match `Trainer(num_nodes=X, devices=Y)` with launcher or scheduler resources | Lightning can read common cluster environments, including SLURM. | `MASTER_ADDR`, `MASTER_PORT`, ranks, firewall, and scheduler task counts must match. |
| CLI-driven distributed job | Choose settings here, encode through CLI elsewhere | Strategy decision belongs here; parser/YAML syntax belongs in CLI sub-skill. | Cross-link `../cli-configuration/SKILL.md`. |

## Trainer Patterns

```python
import lightning as L

# Portable syntax-only or CPU smoke baseline
trainer = L.Trainer(accelerator="cpu", devices=1, strategy="auto", precision="32-true")

# Normal multi-GPU DDP
trainer = L.Trainer(accelerator="cuda", devices=4, strategy="ddp", precision="16-mixed")

# Let Lightning pick a backend when the environment varies
trainer = L.Trainer(accelerator="auto", devices="auto", strategy="auto")
```

Use `lightning as L` for new code. Existing projects may use `import lightning.pytorch as pl` or legacy `pytorch_lightning`; do not rewrite imports unless the task asks for modernization.

## Fabric Patterns

Fabric accepts the same core choices but leaves the training loop to user code:

```python
import lightning as L

fabric = L.Fabric(accelerator="cuda", devices=4, strategy="ddp", precision="16-mixed")
fabric.launch()
```

If the user asks how to structure `fabric.setup`, `fabric.backward`, dataloaders, manual gradient accumulation, or checkpoint dictionaries, route to `../fabric-expert-loops/SKILL.md` and return here only for the hardware/strategy decision.

## DDP

Use DDP when each GPU can hold the full model and optimizer state.

```python
import lightning as L
from lightning.pytorch.strategies import DDPStrategy

strategy = DDPStrategy(
    find_unused_parameters=False,
    gradient_as_bucket_view=True,
    static_graph=True,
)
trainer = L.Trainer(accelerator="cuda", devices=4, strategy=strategy)
```

High-value DDP knobs from source/docs/tests:

- `process_group_backend`: choose backend explicitly, commonly `"nccl"` for CUDA or `"gloo"` for CPU debugging.
- `timeout`: increase for slow multi-node startup or large initialization.
- `start_method`: controls multiprocessing launch behavior for spawn/fork-style variants.
- `find_unused_parameters`: enable only when the model has conditionally unused parameters; it can slow training.
- `gradient_as_bucket_view=True`: can reduce peak gradient memory in DDP.
- `static_graph=True`: can improve performance when parameter usage is identical every iteration.
- `ddp_comm_hook`, `ddp_comm_state`, `ddp_comm_wrapper`: use for communication compression or custom all-reduce behavior.

Common DDP advice:

- Do not add a manual `DistributedSampler`; Lightning injects distributed samplers for normal dataloaders unless the user deliberately disables replacement.
- Do not call `.cuda()`, `.to("cuda")`, or move batches manually inside `LightningModule` hooks; use `self.device` only for creating new tensors.
- For a one-node CPU distributed repro, `Trainer(accelerator="cpu", devices=2, strategy="ddp")` is syntactically valid but still launches worker processes and is not a lightweight smoke test.

## FSDP

Use FSDP when DDP cannot fit the model or optimizer states in device memory.

```python
import lightning as L
from lightning.pytorch.strategies import FSDPStrategy

strategy = FSDPStrategy(
    auto_wrap_policy={MyTransformerBlock},
    sharding_strategy="FULL_SHARD",
    state_dict_type="sharded",
)
trainer = L.Trainer(accelerator="cuda", devices=4, strategy=strategy, precision="bf16-mixed")
```

Decision rules:

- Start with `strategy="fsdp"` or `FSDPStrategy()` only after confirming the model is large enough to benefit.
- Wrap large repeated layers such as transformer blocks; avoid sharding tiny layers where communication overhead dominates.
- Use `configure_model()` or `trainer.init_module()` for very large model initialization so parameters are created under Lightning placement/sharding control.
- Try `FULL_SHARD` for maximum memory savings; try `SHARD_GRAD_OP` for more speed if memory allows; use `HYBRID_SHARD` for selected multi-node layouts.
- For checkpoint portability, document whether the user needs sharded or full state dicts and whether they need to load without the original world size.

High-value `FSDPStrategy` parameters verified from source/signature evidence include `auto_wrap_policy`, `activation_checkpointing_policy`, `sharding_strategy`, `state_dict_type`, `cpu_offload`, `mixed_precision`, `limit_all_gathers`, `use_orig_params`, and process-group/device-mesh style options in current PyTorch-backed implementations.

## DeepSpeed

Use DeepSpeed when the user specifically needs ZeRO stages, offload, activation checkpointing, or DeepSpeed optimizer/runtime features.

```python
import lightning as L
from lightning.pytorch.strategies import DeepSpeedStrategy

trainer = L.Trainer(
    accelerator="cuda",
    devices=4,
    precision="16-mixed",
    strategy=DeepSpeedStrategy(stage=2, offload_optimizer=False),
)
```

Shortcut strategy strings from docs include:

- `"deepspeed_stage_1"`: shard optimizer states.
- `"deepspeed_stage_2"`: shard optimizer states and gradients; commonly a better starting point than stage 1.
- `"deepspeed_stage_2_offload"`: offload optimizer work/state to CPU for lower GPU memory at a speed cost.
- `"deepspeed_stage_3"`: shard optimizer states, gradients, and parameters.
- `"deepspeed_stage_3_offload"`: stage 3 plus CPU offload for maximum memory savings at higher communication/CPU cost.

High-value `DeepSpeedStrategy` knobs include `stage`, `offload_optimizer`, `offload_parameters`, `remote_device`, `offload_params_device`, `offload_optimizer_device`, `allgather_bucket_size`, `reduce_bucket_size`, `logging_batch_size_per_gpu`, `config`, `load_full_weights`, and `parallel_devices`/cluster/process-group options.

DeepSpeed constraints to state explicitly:

- Install `deepspeed` separately and ensure its CUDA build matches the installed PyTorch/CUDA stack.
- Prefer one optimizer and one scheduler unless the user has verified DeepSpeed support for their exact loop.
- DeepSpeed checkpoints may be directories with sharded components, especially for ZeRO stage 3; plan a conversion/export path if the user needs a single checkpoint file.
- CPU offload trades GPU memory for CPU RAM, host-device traffic, and often lower throughput.

## Model and Tensor Parallel

Lightning includes `ModelParallelStrategy` examples for tensor parallelism and 2D parallelism. Use it only when the user is already in expert LLM/model-parallel territory.

```python
from lightning.pytorch.strategies import ModelParallelStrategy

strategy = ModelParallelStrategy(
    data_parallel_size="auto",
    tensor_parallel_size=2,
)
trainer = L.Trainer(accelerator="cuda", devices=4, strategy=strategy)
```

Practical guidance:

- Treat this as experimental and hardware-specific.
- It is not a substitute for ordinary DDP; use it when layers must be split across devices.
- Adapt concepts from the bundled guidance rather than pointing to source examples at runtime; do not require the original repository checkout.

## Multi-Node and Cluster Notes

For manually launched clusters, the number of processes launched per node must match `devices`, and the number of nodes must match `num_nodes`.

```python
trainer = L.Trainer(accelerator="cuda", devices=8, num_nodes=4, strategy="ddp")
```

Checklist for multi-node issues:

- Scheduler resources: `nodes`, tasks per node, GPUs per node, and `Trainer(num_nodes, devices)` agree.
- Environment: `MASTER_ADDR`, `MASTER_PORT`, `NODE_RANK`, `LOCAL_RANK`, `RANK`, and `WORLD_SIZE` are set by the launcher or scheduler.
- Network: nodes can reach each other on the selected master port; firewalls do not block it.
- Backend: CUDA jobs normally use NCCL; CPU debugging uses Gloo.
- SLURM: let Lightning detect the SLURM environment when using `srun`/scheduler-managed launch; do not also manually launch duplicate workers unless the scheduler script requires it.

## Syntactic Validation Script

Use the bundled script before proposing a risky launch:

```bash
python scripts/strategy_config_check.py --mode trainer --accelerator cuda --devices 4 --strategy ddp --precision 16-mixed
python scripts/strategy_config_check.py --mode trainer --accelerator cuda --devices 4 --strategy fsdp --precision bf16-mixed --dry-run-summary
python scripts/strategy_config_check.py --mode fabric --accelerator cpu --devices 1 --strategy auto --precision 32-true
```

Expected success signal contains `CONFIG_CHECK_OK`. Expected limitation: it does not launch DDP/FSDP/DeepSpeed workers, allocate GPUs, or prove cluster connectivity.
