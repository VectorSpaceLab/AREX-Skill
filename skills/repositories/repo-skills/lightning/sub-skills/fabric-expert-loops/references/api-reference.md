# Fabric API Reference

This reference targets Lightning 2.6.x. Public package facts used for this skill: current repository version is 2.6.2, `lightning.fabric` imports as 2.6.2, and the inspected index wheel during generation was 2.6.1 because 2.6.2 was not published there. CPU-only inspection was used; do not claim GPU runtime validation from this skill.

## Imports

Prefer the modern aggregate package imports:

```python
import lightning as L
fabric = L.Fabric(accelerator="auto", devices="auto")
```

Equivalent direct imports are valid:

```python
from lightning.fabric import Fabric, seed_everything
fabric = Fabric(accelerator="cpu", devices=1)
```

Avoid mixing Fabric loop code with `Trainer` APIs in the same loop. `Trainer` ownership belongs in `../training-core/SKILL.md`.

## Constructor

Verified public signature shape:

```python
Fabric(
    *,
    accelerator="auto",
    strategy="auto",
    devices="auto",
    num_nodes=1,
    precision=None,
    plugins=None,
    callbacks=None,
    loggers=None,
)
```

Key options:

| Option | Use |
| --- | --- |
| `accelerator` | Hardware selector: `"auto"`, `"cpu"`, `"gpu"`, `"cuda"`, `"mps"`, or `"tpu"`. |
| `strategy` | Distribution/wrapping selector: `"auto"`, `"ddp"`, `"fsdp"`, `"deepspeed"`, single-device, or a Strategy object. Route deep strategy design to `../distributed-accelerators/SKILL.md`. |
| `devices` | Device count, list/string device ids, or `"auto"`. Applies per node. |
| `num_nodes` | Multi-node count. Use with launch environment or `fabric run` options. |
| `precision` | `None` for strategy/device defaults, or strings such as `"32-true"`, `"32"`, `"64-true"`, `"64"`, `"16-mixed"`, `"bf16-mixed"`. |
| `plugins` | Precision/checkpoint/cluster/plugin customizations. Keep practical usage here; route internals to `distributed-accelerators`. |
| `callbacks` | Fabric callbacks with hooks invoked via `fabric.call(...)`; not interchangeable with all `Trainer` callback assumptions. |
| `loggers` | One Fabric logger or a list, for `fabric.log` and `fabric.log_dict`. |

## Core Loop Methods

| Method | Pattern | Notes |
| --- | --- | --- |
| `fabric.launch()` | Call near the start when process creation is configured in code. | Do not call when the script is launched with `fabric run`; CLI launch already initializes processes. |
| `fabric.launch(fn, *args, **kwargs)` | For spawn/fork/XLA-style launchers, pass a callable that accepts the `Fabric` object. | Use `fabric.launch(train_fn)`, not `fabric.launch(train_fn())`. |
| `fabric.setup(model, *optimizers, scheduler=None, move_to_device=True)` | Wrap model and optimizers; returns model plus wrapped optimizer(s), and scheduler if passed. | Remove direct `.to(device)`/`.cuda()` calls when `move_to_device=True`. |
| `fabric.setup_dataloaders(*loaders, use_distributed_sampler=True, move_to_device=True)` | Wrap one or more `DataLoader` objects. | Set `use_distributed_sampler=False` for a custom sampler that must be preserved. |
| `fabric.backward(loss, model=None)` | Replace `loss.backward()`. | Required for precision/plugins; pass `model=` with DeepSpeed when multiple models are set up. |
| `fabric.no_backward_sync(model, enabled=True)` | Skip gradient sync during accumulation on supported distributed strategies. | The `model` must already be returned by `fabric.setup`. |
| `fabric.clip_gradients(model, optimizer, clip_val=... or max_norm=...)` | Strategy-aware gradient clipping. | Provide exactly one of `clip_val` or `max_norm`. |
| `fabric.to_device(obj)` | Manually move tensors/modules/collections when not using automatic dataloader movement. | Useful with `move_to_device=False` or tensors created outside wrapped loaders. |
| `fabric.autocast()` | Run extra operations under the selected precision context. | Usually model forward is already covered by the wrapper. |

## Rank and Distributed Utilities

| API | Use |
| --- | --- |
| `fabric.device` | Current root device for this process. Use for new tensors/metrics when needed. |
| `fabric.global_rank`, `fabric.local_rank`, `fabric.node_rank`, `fabric.world_size` | Rank-aware control flow and logging. |
| `fabric.is_global_zero` | Gate one-time global side effects such as writing metadata. |
| `fabric.print(...)` | Print only from local rank 0. |
| `fabric.rank_zero_first(local=False)` | Let rank 0 create/download/prepare resources before other ranks proceed. |
| `fabric.barrier()` | Synchronize all processes. Use sparingly and call from every rank. |
| `fabric.broadcast(obj, src=0)` | Broadcast a serializable object or tensor from one rank. |
| `fabric.all_gather(data)` | Gather equal-shaped tensors or nested tensor collections across ranks. |
| `fabric.all_reduce(data, reduce_op="mean")` | Reduce tensors or nested tensor collections in place. |

## Checkpoint APIs

Use Fabric checkpointing for strategy-aware save/load. All processes must call these methods.

```python
state = {"model": model, "optimizer": optimizer, "epoch": epoch, "global_step": step}
fabric.save("checkpoint.pt", state)
remainder = fabric.load("checkpoint.pt", state, strict=True, weights_only=True)
epoch = int(remainder.get("epoch", 0))
```

Notes:

- Include wrapped model and optimizer objects in the state dictionary; Fabric unwraps/wraps as needed.
- Use `fabric.load(path)` with no `state` to return a checkpoint dictionary.
- Use `fabric.load_raw(path, model_or_optimizer, strict=True, weights_only=True)` for a raw PyTorch state dict created outside Fabric.
- For untrusted checkpoints, prefer `weights_only=True` where supported by the installed PyTorch/Lightning combination.
- Some distributed strategies save sharded checkpoints; use strategy-specific consolidation tools only when required.

## Logging APIs

Fabric logger support is intentionally lower level than `Trainer` logging.

```python
from lightning.fabric.loggers import CSVLogger

fabric = L.Fabric(loggers=CSVLogger(root_dir="logs", name="fabric-demo"))
fabric.log("train_loss", loss, step=global_step)
fabric.log_dict({"epoch": epoch, "lr": scheduler.get_last_lr()[0]}, step=global_step)
```

Guidelines:

- Log scalar values or logger-supported payloads.
- Use `fabric.print` for rank-safe console messages.
- Keep metric synchronization explicit; use `all_gather` or `all_reduce` when values must be global.

## Fabric CLI

The `lightning-fabric` package exposes a `fabric` console command. Practical command forms:

```bash
fabric run --help
fabric run --accelerator=cpu --devices=1 train.py --max-steps 10
fabric run --accelerator=cuda --devices=4 --strategy=ddp --precision=16-mixed train.py
```

CLI launch behavior:

- `fabric run` sets launch environment variables and starts worker processes through the supported backend.
- The target script must create a `Fabric` object. It should not call `fabric.launch()` when invoked through `fabric run`.
- CLI-supported accelerator choices include `cpu`, `gpu`, `cuda`, `mps`, `tpu`, and `auto`.
- CLI strategies exclude spawn/fork/notebook/XLA/TPU/offload-style entries that need special handling.
- `fabric run` forwards unknown remaining arguments to the script; parse them with `argparse` or another script-local parser.

## Wrappers and Unwrapping

`fabric.setup` returns wrapped module and optimizer objects. Treat these as the objects to use in the loop.

Rules of thumb:

- Run forward passes on the wrapped model returned by `fabric.setup`.
- Step the wrapped optimizer returned by `fabric.setup`.
- Do not call methods on a stale pre-setup model copy after setup.
- If a custom method is used as an alternate forward path under DDP/FSDP, ensure it runs through the wrapped module path or explicitly mark/route it according to Lightning Fabric wrapper guidance.
- For serialization, prefer `fabric.save` and `fabric.load` instead of manually unwrapping unless integrating with non-Fabric code.
