# Parallelism, Devices, Backends, And Auto Microbatching

Composer separates three concerns that are easy to mix up:

1. The launcher creates processes and sets rank environment variables.
2. Device helpers choose the concrete accelerator/backend for a process.
3. `parallelism_config` tells the `Trainer` whether and how to wrap the model
   for DDP, FSDP/FSDP2, or tensor parallelism.

For launch and sampler wiring, see
[launcher-and-ranks.md](launcher-and-ranks.md). For training-loop details, route
through `../training/SKILL.md`.

## Device Selection

Use Composer's device helpers when code needs Composer-compatible movement and
backend semantics:

```python
from composer.utils.device import get_device

# Auto: DeviceGPU when CUDA is available, otherwise DeviceCPU.
device = get_device()

# Explicit choices.
cpu = get_device('cpu')
gpu = get_device('gpu')
```

`get_device(device=None)` accepts an existing `Device` object or a string. The
recognized device strings are `cpu`, `gpu`, `mps`, `tpu`, `neuron`, and `hpu`.

| Device class | When to use | Distributed backend | Prerequisite |
| --- | --- | --- | --- |
| `DeviceCPU` | CPU-only training/probing. | `gloo` | PyTorch CPU build. |
| `DeviceGPU(device_id=None, allow_tf32=True)` | CUDA GPUs. | `nccl` | `torch.cuda.is_available()` is true. Defaults `device_id` to local rank. |
| `DeviceMPS` | Apple M-series local acceleration. | none configured | macOS/MPS-capable PyTorch. Not a drop-in for multinode distributed launch. |
| `DeviceTPU` | TPU/XLA training. | `xla` | `torch_xla`; on TPU VMs set `PJRT_DEVICE=TPU`. |
| `DeviceNeuron` | AWS Neuron devices. | `xla` | `torch_xla`; Composer sets `PJRT_DEVICE=NEURON` during construction. |
| `DeviceHPU` | Habana Gaudi HPUs. | `hccl` | Habana frameworks / habana torch plugin. |

Every Composer device implements `module_to_device`, `tensor_to_device`,
`batch_to_device`, and `optimizer_to_device`. `batch_to_device` recursively moves
nested tensors while leaving non-tensor metadata alone.

To inspect the available surface without launching training:

```bash
python scripts/device_probe.py
```

## Distributed Initialization

When code uses Composer distributed helpers outside the normal `Trainer` setup,
initialize the process group explicitly:

```python
from composer.utils import dist

dist.initialize_dist(device=None, timeout=300.0)
```

`initialize_dist` derives the backend from `get_device(device)`. If all rank
environment variables are absent or at single-rank defaults, Composer fills a
single-rank configuration and initializes with an in-process store. For
multirank jobs, the launcher or scheduler must supply complete `RANK`,
`WORLD_SIZE`, `LOCAL_RANK`, `LOCAL_WORLD_SIZE`, `NODE_RANK`, `MASTER_ADDR`, and
`MASTER_PORT` values.

A backend mismatch is not recoverable in-process. If a process group was already
initialized with one backend, requesting a different device/backend requires
restarting the Python process.

## DDP And FSDP Selection

Composer's distributed training is data-parallel by default. DDP is the default
wrapping strategy; FSDP is selected through `parallelism_config` when memory or
sharding behavior is needed.

Minimal FSDP shape:

```python
from composer import Trainer

fsdp_config = {
    'sharding_strategy': 'FULL_SHARD',
    'mixed_precision': 'DEFAULT',
    'activation_checkpointing': False,
    'activation_cpu_offload': False,
    'data_parallel_shard_degree': -1,
    'data_parallel_replicate_degree': None,
    'state_dict_type': 'full',
    'use_orig_params': True,
    'cpu_offload': False,
}

trainer = Trainer(
    model=composer_model,
    train_dataloader=train_dataloader,
    parallelism_config={'fsdp': fsdp_config},
    # other Trainer arguments live in the training sub-skill
)
```

Important FSDP1 rules:

- Do not pass a direct `device_mesh` into the FSDP1 config. Use
  `data_parallel_shard_degree` and `data_parallel_replicate_degree` instead.
- `sharding_strategy` commonly uses `FULL_SHARD`, `SHARD_GRAD_OP`, or
  `NO_SHARD`.
- `mixed_precision` can be `FULL`, `DEFAULT`, or `PURE`, or an explicit dtype
  dictionary. Composer maps the string modes to PyTorch FSDP mixed-precision
  policies using the Trainer precision context.
- `cpu_offload` is present in the config but Composer documentation warns that
  CPU offloading is not supported in the FSDP1 workflow.
- For sharded checkpoints, `state_dict_type='sharded'` saves rank shards under a
  prefix directory; resume with the same `state_dict_type` and point `load_path`
  at the shard directory, not an individual shard file.

## FSDP Auto-Wrap And Activation Checkpointing

Composer's FSDP wrapping logic is driven by model-owned hints. The model can:

- Set `module._fsdp_wrap = True` or `False` on modules to force a wrapping
  decision.
- Define `fsdp_wrap_fn(self, module)` on the root model to decide which children
  should be wrapped.
- Return a dictionary from `fsdp_wrap_fn` for experimental per-module custom FSDP
  arguments.

Activation checkpointing uses analogous hints:

- `module._activation_checkpointing = True` or `False`.
- `activation_checkpointing_fn(self, module)`.

Keep model-definition details in the model/training guidance. This sub-skill
only owns how these hints relate to distributed wrapping.

## FSDP2 Basics

FSDP2 is an experimental Composer path built on PyTorch's modern DTensor-style
fully-sharded APIs. Use it when the repository task explicitly needs FSDP2 or
when a config already uses `parallelism_config={'fsdp2': ...}`.

Minimal shape:

```python
fsdp2_config = {
    'device_mesh': None,
    'reshard_after_forward': True,
    'activation_checkpointing': False,
    'activation_cpu_offload': False,
    'state_dict_type': 'sharded',
    'load_monolith_rank0_only': False,
    'mixed_precision': 'DEFAULT',
    'verbose': False,
}

trainer = Trainer(
    model=composer_model,
    train_dataloader=train_dataloader,
    parallelism_config={'fsdp2': fsdp2_config},
)
```

FSDP2 caveats:

- Treat APIs and config behavior as experimental.
- `sync_module_states` is managed by Composer and should not be set as a user
  override.
- `state_dict_type` is typically `sharded` for FSDP2. If
  `load_monolith_rank0_only=True` while loading a monolithic checkpoint, use
  `state_dict_type='full'`.
- Checkpoint formats are not all interchangeable with older FSDP1
  `SHARDED_STATE_DICT` flows. Keep save/load `state_dict_type` consistent.
- FSDP2 is the path to investigate when tasks combine FSDP with tensor
  parallelism, but verify the current PyTorch distributed support first.

## Tensor Parallel Basics

Tensor parallelism uses PyTorch's tensor-parallel APIs and a Composer TP config.
It is experimental and should be treated as a distributed-backend feature, not a
single-process device flag.

Minimal shape:

```python
from torch.distributed.tensor.parallel import ColwiseParallel, RowwiseParallel
from composer import Trainer

tp_config = {
    'tensor_parallel_degree': 2,
    'layer_plan': {
        'model.block0.fc1': ColwiseParallel(),
        'model.block0.fc2': RowwiseParallel(),
    },
}

trainer = Trainer(
    model=composer_model,
    train_dataloader=train_dataloader,
    parallelism_config={'tp': tp_config},
)
```

TP rules of thumb:

- `tensor_parallel_degree` must fit the launched world size and the intended
  mesh layout.
- `layer_plan` maps model submodule names to PyTorch tensor-parallel placement
  plans.
- Use a PyTorch build that exposes tensor-parallel APIs.
- Composer documentation notes that some TP combinations, including TP without
  FSDP, may not be supported. Prefer explicit smoke checks for the exact model
  and backend.

## Auto Microbatching

`device_train_microbatch_size` controls per-device microbatching. Setting it to
`'auto'` asks Composer to find a microbatch size that avoids CUDA OOM during
training:

```python
trainer = Trainer(
    model=composer_model,
    train_dataloader=train_dataloader,
    device_train_microbatch_size='auto',
)
```

Behavior and constraints:

- Auto microbatching starts from the train dataloader batch size and halves the
  device microbatch size after CUDA OOM or excessive memory retries until the
  batch fits or size 1 still fails.
- It is a GPU feature; CPU, MPS, TPU, HPU, or Neuron errors are not CUDA OOMs.
- It catches OOMs in the forward/backward training path. OOMs caused by
  callbacks, algorithms that run their own forward/backward outside the trainer
  loop, dataloader workers, checkpointing, or logging allocations may not be
  recoverable by auto microbatching.
- With explicit `parallelism_config`, Composer expects auto microbatching to be
  compatible with the selected strategy. TP/FSDP2 or sequence-parallel flows may
  require manual microbatch sizes.
- Profiling and auto microbatching are a poor combination: use a short auto run
  to find a stable value, then rerun profiling with an explicit integer
  microbatch size.
- BatchNorm can become statistically noisy when microbatches are tiny. Consider
  SyncBatchNorm, GroupNorm, or explicit fixed microbatch tuning for such models.

## Backend Preflight

Before accepting a distributed config, verify:

1. The launcher command creates the expected `world_size` and rank ranges.
2. The selected device exists on every rank (`python scripts/device_probe.py`).
3. The selected backend matches the device class (`nccl` for CUDA, `gloo` for
   CPU, `xla` for XLA devices, `hccl` for HPU).
4. Any FSDP/TP degree divides or otherwise matches the intended process mesh.
5. The dataloader uses a rank-aware sampler unless the dataset is iterable or
   already sharded.
