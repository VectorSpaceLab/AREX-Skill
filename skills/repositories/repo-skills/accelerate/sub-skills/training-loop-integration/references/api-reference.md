# Training Loop API Reference

This reference distills the Accelerate APIs most often needed when migrating raw PyTorch loops. It is self-contained and can be used without reopening external project files.

## `Accelerator` construction

Use `from accelerate import Accelerator` and instantiate one accelerator near the start of the script.

Important constructor arguments verified for Accelerate `1.15.0.dev0`:

- `device_placement=True`: lets Accelerate place models and dataloader batches on `accelerator.device`.
- `mixed_precision=None | "no" | "fp16" | "bf16" | "fp8"`: selects automatic mixed precision; `fp16` requires a supported non-CPU device, while `fp8` requires an installed FP8 backend.
- `gradient_accumulation_steps=1`: number of minibatches to accumulate; values greater than 1 should be paired with `accelerator.accumulate(model)`.
- `cpu=False`: forces CPU execution.
- `dataloader_config=DataLoaderConfiguration(...)`: controls sharding, dispatching, even batches, seedable sampling, non-blocking transfers, and stateful dataloaders.
- `step_scheduler_with_optimizer=True`: wraps schedulers so they step only when optimizer steps are valid.
- `kwargs_handlers=[...]`: accepts handlers such as `DistributedDataParallelKwargs`, `InitProcessGroupKwargs`, `GradScalerKwargs`, and autocast/FP8/profile handlers.
- `gradient_accumulation_plugin=GradientAccumulationPlugin(...)`: advanced accumulation configuration; do not pass both this and `gradient_accumulation_steps != 1`.

Useful runtime attributes:

- `accelerator.device`: the device selected by the current launch/environment.
- `accelerator.num_processes`, `process_index`, `local_process_index`, `is_main_process`: process metadata.
- `accelerator.distributed_type`: current distributed mode.
- `accelerator.mixed_precision`: resolved mixed precision mode.
- `accelerator.sync_gradients`: true only when accumulated gradients should synchronize and an optimizer update should happen.
- `accelerator.optimizer_step_was_skipped`: true when mixed-precision overflow skipped the optimizer update.

## `prepare()`

`accelerator.prepare(*args, device_placement=None)` accepts PyTorch dataloaders, modules, optimizers, and LR schedulers, then returns prepared objects in the same order.

Typical use:

```python
model, optimizer, train_loader, eval_loader, scheduler = accelerator.prepare(
    model, optimizer, train_loader, eval_loader, scheduler
)
```

Rules and pitfalls:

- Prepare related objects together so wrappers are internally consistent.
- Unpack in exactly the same order as passed.
- Do not call `.to("cuda")` on batches after using automatic placement. If you need manual placement, use `accelerator.device` and consider `device_placement=False` or per-object `device_placement=[...]`.
- `device_placement=[True, True, False, False]` can customize placement per argument, but this is not compatible with some backend modes such as DeepSpeed or Megatron-LM.
- TPU/XLA can fail if the optimizer is created around parameters on a different device than the model. Let Accelerate place objects, or move the model before creating the optimizer.
- Distributed training cannot train a model loaded with `device_map="auto"`; use a single process or a backend designed for that model-loading path.

## Backward, optimizer, scheduler

Replace `loss.backward()` with:

```python
accelerator.backward(loss)
```

`accelerator.backward` scales the loss by gradient accumulation steps outside DeepSpeed, uses GradScaler when native AMP is active, and delegates to backend-specific backward paths when needed.

When using prepared schedulers, the wrapped `AcceleratedScheduler` coordinates with optimizer steps:

- With `step_scheduler_with_optimizer=True`, `scheduler.step()` is gated by gradient sync and skipped optimizer steps.
- During accumulation, if gradients are not syncing and `adjust_scheduler=True`, the wrapper advances internal scheduler bookkeeping instead of performing a real scheduler step.
- If `split_batches=False`, the wrapper may step the underlying scheduler once per process per real training step to preserve expected schedule semantics.
- Set `step_scheduler_with_optimizer=False` only when the scheduler should be stepped independently, such as epoch-level scheduling.

## Gradient accumulation

Simple pattern:

```python
accelerator = Accelerator(gradient_accumulation_steps=4)
model, optimizer, train_loader, scheduler = accelerator.prepare(model, optimizer, train_loader, scheduler)

for batch in train_loader:
    with accelerator.accumulate(model):
        outputs = model(batch["inputs"])
        loss = loss_fn(outputs, batch["labels"])
        accelerator.backward(loss)
        if accelerator.sync_gradients:
            accelerator.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        scheduler.step()
        optimizer.zero_grad()
```

Advanced configuration:

```python
from accelerate.utils import GradientAccumulationPlugin

plugin = GradientAccumulationPlugin(
    num_steps=4,
    adjust_scheduler=True,
    sync_with_dataloader=True,
    sync_each_batch=False,
)
accelerator = Accelerator(gradient_accumulation_plugin=plugin)
```

Use `sync_each_batch=True` only when you need lower memory pressure in distributed accumulation and accept slower synchronization. Use `sync_with_dataloader=False` only for expert loops that intentionally decouple gradient sync from dataloader boundaries.

For manual multi-forward accumulation under DDP, `accelerator.no_sync(model)` can suppress synchronization and `accelerator.trigger_sync_in_backward(model)` can force synchronization on a later backward pass.

## Gradient clipping

Use Accelerate's clipping helpers instead of raw PyTorch helpers:

```python
accelerator.backward(loss)
if accelerator.sync_gradients:
    accelerator.clip_grad_norm_(model.parameters(), max_norm)
optimizer.step()
```

`clip_grad_norm_` unscales native AMP gradients before clipping and handles FSDP/XLA cases. `clip_grad_value_` is not supported with DeepSpeed or FSDP; use norm clipping there.

## Mixed precision

Constructor-level mixed precision is usually enough:

```python
accelerator = Accelerator(mixed_precision="bf16")
```

Use `accelerator.autocast()` when additional operations outside the model should run under autocast:

```python
with accelerator.autocast():
    loss = custom_loss_fn(outputs, labels)
```

Notes:

- `accelerator.backward(loss)` handles native AMP scaling when a scaler is active.
- `fp16` is unsupported on CPU and requires a supported accelerator device.
- `bf16` requires hardware/runtime support.
- `fp8` requires a valid FP8 backend and is usually a backend-specific topic; route backend recipe details to `../distributed-training-backends/`.

## Dataloaders

`DataLoaderConfiguration` controls prepared dataloader behavior:

```python
from accelerate.utils import DataLoaderConfiguration

config = DataLoaderConfiguration(
    split_batches=False,
    dispatch_batches=None,
    even_batches=True,
    use_seedable_sampler=False,
    data_seed=None,
    non_blocking=False,
    use_stateful_dataloader=False,
)
accelerator = Accelerator(dataloader_config=config)
```

Key semantics:

- `split_batches=False`: each process gets a batch of the script's batch size, so global batch size is per-process batch size times `num_processes`.
- `split_batches=True`: a single batch is split across processes, preserving the script's effective batch size; the batch size must be a round multiple of process count.
- `dispatch_batches=None`: defaults to `True` for iterable datasets and `False` otherwise.
- `even_batches=True`: duplicates samples from the dataset start as needed so every process has equal batch shapes.
- `use_seedable_sampler=True` plus `set_seed(...)` improves reproducibility.
- `non_blocking=True` requires compatible dataloader pinning, usually `pin_memory=True`, and can overlap host-to-device transfers.
- `use_stateful_dataloader=True` requires `torchdata >= 0.8.0` and lets save/load state track dataloader progress.

## Gather, reduce, and metrics

For raw all-process tensor collection:

```python
gathered = accelerator.gather(tensor)
```

All processes participate, tensors must have compatible shapes, and the result is concatenated along dimension 0.

For metrics, prefer:

```python
predictions, labels = accelerator.gather_for_metrics((predictions, labels))
```

`gather_for_metrics` removes duplicated samples from the last batch when possible. For variable-length tensors, pad first:

```python
predictions = accelerator.pad_across_processes(predictions, dim=1, pad_index=pad_id)
predictions, labels = accelerator.gather_for_metrics((predictions, labels))
```

For non-tensor or irregular data, `gather_for_metrics(data, use_gather_object=True)` can gather Python objects, but it is inefficient with GPU tensors because they must be pickled and transferred through CPU memory.

For scalar reductions:

```python
mean_loss = accelerator.reduce(loss.detach(), reduction="mean")
```

Supported reductions are `"sum"`, `"mean"`, `"max"`, and `"none"`.

## DDP kwargs and communication hooks

Use `DistributedDataParallelKwargs` when adapting DDP wrapper behavior:

```python
from accelerate import Accelerator
from accelerate.utils import DistributedDataParallelKwargs

kwargs = DistributedDataParallelKwargs(
    find_unused_parameters=True,
    static_graph=False,
    gradient_as_bucket_view=False,
)
accelerator = Accelerator(kwargs_handlers=[kwargs])
```

Relevant fields include `dim`, `broadcast_buffers`, `bucket_cap_mb`, `find_unused_parameters`, `check_reduction`, `gradient_as_bucket_view`, and `static_graph`.

Communication hook fields:

```python
from accelerate.utils import DDPCommunicationHookType, DistributedDataParallelKwargs

kwargs = DistributedDataParallelKwargs(
    comm_hook=DDPCommunicationHookType.FP16,
    comm_wrapper=DDPCommunicationHookType.NO,
)
accelerator = Accelerator(kwargs_handlers=[kwargs])
```

Available hook concepts include no hook, fp16/bf16 compression, PowerSGD, and batched PowerSGD, depending on PyTorch distributed support. Hook registration only has an effect on prepared DDP models.

## Process-group kwargs

For distributed initialization settings such as timeout:

```python
from datetime import timedelta
from accelerate import Accelerator
from accelerate.utils import InitProcessGroupKwargs

init_kwargs = InitProcessGroupKwargs(timeout=timedelta(minutes=30))
accelerator = Accelerator(kwargs_handlers=[init_kwargs])
```

Use this for true distributed initialization tuning; route launch topology and config-file questions to `../configuration-and-cli/`.

## Local SGD

Accelerate provides `LocalSGD` for reduced synchronization frequency in DDP-style loops:

```python
from accelerate.local_sgd import LocalSGD

with LocalSGD(accelerator=accelerator, model=model, local_sgd_steps=8, enabled=True) as local_sgd:
    for batch in train_loader:
        with accelerator.accumulate(model):
            loss = loss_fn(model(batch["inputs"]), batch["labels"])
            accelerator.backward(loss)
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()
            local_sgd.step()
```

Keep the Local SGD context outside the inner dataloader loop and call `local_sgd.step()` after each optimizer update path.

## Logging basics

For simple main-process output:

```python
accelerator.print("validation", metrics)
```

For distributed-aware logging:

```python
from accelerate.logging import get_logger

logger = get_logger(__name__, log_level="INFO")
logger.info("only main process by default")
logger.debug("all processes", main_process_only=False)
logger.debug("all processes in order", main_process_only=False, in_order=True)
```

Tracking integrations and profiler setup belong in `../checkpointing-and-tracking/`.
