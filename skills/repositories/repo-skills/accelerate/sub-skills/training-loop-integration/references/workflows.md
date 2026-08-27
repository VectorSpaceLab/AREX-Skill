# Training Loop Workflows

Use these workflows to migrate raw PyTorch training and evaluation loops to Accelerate while preserving the original model, optimizer, loss, and dataloader logic.

## Minimal migration from raw PyTorch

Original PyTorch loops usually look like this:

```python
device = "cuda"
model.to(device)

for batch in train_loader:
    inputs, labels = batch
    inputs = inputs.to(device)
    labels = labels.to(device)
    optimizer.zero_grad()
    outputs = model(inputs)
    loss = loss_fn(outputs, labels)
    loss.backward()
    optimizer.step()
    scheduler.step()
```

Accelerate migration:

```python
from accelerate import Accelerator

accelerator = Accelerator()
model, optimizer, train_loader, scheduler = accelerator.prepare(
    model, optimizer, train_loader, scheduler
)

for batch in train_loader:
    inputs, labels = batch
    optimizer.zero_grad()
    outputs = model(inputs)
    loss = loss_fn(outputs, labels)
    accelerator.backward(loss)
    optimizer.step()
    scheduler.step()
```

Migration decisions:

- Remove hard-coded CUDA device strings.
- Do not move dataloader batches manually when `device_placement=True`.
- Keep object construction mostly unchanged, then call `prepare()` once objects exist.
- Replace only the backward call; optimizer and scheduler APIs remain familiar.
- Keep launch/config decisions outside this sub-skill and route them to `../configuration-and-cli/`.

## Novice-safe migration checklist

1. Add `from accelerate import Accelerator`.
2. Create `accelerator = Accelerator()` before the loop.
3. Delete `device = "cuda"`, `model.cuda()`, and batch `.cuda()` calls.
4. If the code still needs a device variable, use `device = accelerator.device`.
5. Call `accelerator.prepare(model, optimizer, train_loader, scheduler)` and unpack in the same order.
6. Replace `loss.backward()` with `accelerator.backward(loss)`.
7. Replace process-wide `print()` with `accelerator.print()`.
8. For evaluation metrics, gather predictions and labels with `accelerator.gather_for_metrics(...)`.

## Expert migration checklist

Before editing, classify the existing loop:

- Single-process CPU/GPU with no mixed precision: minimal migration is enough.
- Manual DDP: remove direct `DistributedDataParallel(...)` wrapping and let `prepare()` wrap the model. Carry only needed DDP options through `DistributedDataParallelKwargs`.
- Manual AMP: remove direct `GradScaler` and most explicit autocast usage unless custom loss logic must be autocast; use `Accelerator(mixed_precision=...)`.
- Manual accumulation: use `gradient_accumulation_steps` plus `accelerator.accumulate(model)`.
- Manual metric all-gather: replace with `gather_for_metrics`, and add `pad_across_processes` for variable sequence lengths.
- Manual scheduler stepping: decide whether the scheduler is per optimizer update or per epoch; set `step_scheduler_with_optimizer` accordingly.

## Gradient accumulation with scheduler

Preferred pattern:

```python
from accelerate import Accelerator

accelerator = Accelerator(gradient_accumulation_steps=gradient_accumulation_steps)
model, optimizer, train_loader, scheduler = accelerator.prepare(
    model, optimizer, train_loader, scheduler
)

for epoch in range(num_epochs):
    model.train()
    for batch in train_loader:
        with accelerator.accumulate(model):
            outputs = model(batch["inputs"])
            loss = loss_fn(outputs, batch["labels"])
            accelerator.backward(loss)
            if accelerator.sync_gradients:
                accelerator.clip_grad_norm_(model.parameters(), max_grad_norm)
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()
```

Why this works:

- `accelerator.backward` accounts for accumulation scaling outside backend paths that handle it themselves.
- `accelerator.accumulate(model)` suppresses unnecessary DDP gradient synchronization until the update boundary.
- `accelerator.sync_gradients` identifies the safe time to clip gradients or run logic that should happen only at update boundaries.
- Prepared schedulers coordinate with skipped optimizer steps and gradient accumulation bookkeeping.

When using an epoch-level scheduler, construct the accelerator with `step_scheduler_with_optimizer=False`, prepare the scheduler, and call `scheduler.step()` outside the batch loop.

## Mixed precision migration

Simple constructor-level AMP:

```python
accelerator = Accelerator(mixed_precision="fp16")
```

For custom operations outside the model:

```python
with accelerator.autocast():
    loss = custom_loss(outputs, targets)
accelerator.backward(loss)
```

Migration notes:

- Remove manual `torch.cuda.amp.GradScaler` unless you are doing an unsupported custom path.
- Keep loss computation inside the model when possible, especially with Transformers-style models, because Accelerate handles model autocast cleanly.
- Use `bf16` only when the device and runtime support it.
- Do not request `fp16` on CPU-only environments.
- Treat `fp8` as backend-specific and route deep recipe work to `../distributed-training-backends/`.

## Evaluation and metrics

For fixed-size predictions:

```python
model.eval()
for batch in eval_loader:
    with torch.no_grad():
        outputs = model(batch["inputs"])
    predictions = outputs.argmax(dim=-1)
    predictions, labels = accelerator.gather_for_metrics((predictions, batch["labels"]))
    metric.add_batch(predictions=predictions, references=labels)
```

For variable-length sequence predictions:

```python
predictions = accelerator.pad_across_processes(predictions, dim=1, pad_index=tokenizer.pad_token_id)
labels = accelerator.pad_across_processes(labels, dim=1, pad_index=-100)
predictions, labels = accelerator.gather_for_metrics((predictions, labels))
```

Use `gather_for_metrics` rather than raw `gather` for metrics because it can drop duplicated samples introduced to make final batches even across workers.

## Early stopping and NaN stop conditions

Distributed loops must make the stop decision collectively:

```python
if torch.isnan(loss.detach()):
    accelerator.set_trigger()

if accelerator.check_trigger():
    accelerator.print("Stopping because at least one process triggered early stop")
    break
```

Use this for validation-triggered early stopping, NaN detection, or custom stop conditions that might be true on only one process.

## Dataloader behavior migration

When the original code assumes a global batch size, decide how Accelerate should shard batches:

```python
from accelerate.utils import DataLoaderConfiguration

accelerator = Accelerator(
    dataloader_config=DataLoaderConfiguration(split_batches=True, even_batches=True)
)
```

Guidance:

- If you want the effective global batch size to grow with process count, keep `split_batches=False`.
- If you want the script's batch size to remain the effective global batch size, use `split_batches=True` and ensure batch size is divisible by process count.
- Keep `even_batches=True` for normal training when all processes must see equal-shaped batches.
- For exact evaluation counts, rely on `gather_for_metrics` to remove duplicated final-batch samples when possible.
- Use `use_seedable_sampler=True` and `accelerate.utils.set_seed(...)` when reproducibility matters more than preserving the exact original sampler behavior.

## DDP kwargs migration

If the original script used raw DDP options:

```python
from accelerate.utils import DistributedDataParallelKwargs

kwargs = DistributedDataParallelKwargs(find_unused_parameters=True)
accelerator = Accelerator(kwargs_handlers=[kwargs])
```

Use cases:

- `find_unused_parameters=True` for models with conditional branches that do not use all parameters every forward pass.
- `static_graph=True` for stable graphs that meet PyTorch DDP static-graph requirements.
- `bucket_cap_mb` and `gradient_as_bucket_view` for performance tuning.
- Communication hooks for compression/PowerSGD experiments.

Do not wrap the model in `torch.nn.parallel.DistributedDataParallel` yourself before `prepare()`.

## DDP communication hooks

Example:

```python
from accelerate.utils import DDPCommunicationHookType, DistributedDataParallelKwargs

kwargs = DistributedDataParallelKwargs(
    comm_hook=DDPCommunicationHookType.FP16,
    comm_wrapper=DDPCommunicationHookType.NO,
)
accelerator = Accelerator(kwargs_handlers=[kwargs])
```

Use communication hooks only after validating baseline DDP correctness. Compression and PowerSGD-style hooks trade exact communication behavior for speed or bandwidth savings and should be benchmarked against model quality.

## Local SGD workflow

```python
from accelerate.local_sgd import LocalSGD

model, optimizer, train_loader, scheduler = accelerator.prepare(model, optimizer, train_loader, scheduler)

for epoch in range(num_epochs):
    model.train()
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

Keep Local SGD disabled until the regular distributed loop is correct, then enable and compare convergence.

## Distributed-aware logging

Simple output:

```python
accelerator.print(f"epoch {epoch}: {metrics}")
```

Debug logging:

```python
from accelerate.logging import get_logger

logger = get_logger(__name__, log_level="DEBUG")
logger.debug("batch shape %s", tuple(batch["inputs"].shape), main_process_only=False, in_order=True)
```

Use ordered all-process logs sparingly because they can slow a training loop.

## CPU-first migration smoke

After migration, run the training script on CPU with a tiny dataset first:

- Force CPU with `Accelerator(cpu=True)` temporarily or use launch/config options from `../configuration-and-cli/`.
- Keep a tiny model and dataset to validate object preparation, backward, scheduler, and metric gathering.
- Use the bundled `scripts/accelerator_loop_smoke.py` as a reference for a minimal self-contained loop.

## Synthetic hard cases for verification

Case 1: migrate a CPU loop that combines gradient accumulation, prepared scheduler, clipping gated by `sync_gradients`, and evaluation metric gathering. Assertions should verify that at least one optimizer step occurred, the scheduler advanced coherently, gradients were zeroed after stepping, and gathered metric tensors have expected lengths.

Case 2: debug a distributed evaluation hang caused by variable-length predictions. The expected fix is to add `pad_across_processes` before `gather_for_metrics`, or use object gathering only for truly irregular non-tensor payloads, and to explain why all processes must enter collectives with compatible shapes.
