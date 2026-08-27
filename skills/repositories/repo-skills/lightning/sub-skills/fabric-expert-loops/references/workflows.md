# Fabric Workflows

Use these patterns to help agents produce complete Fabric code without reopening the source repository.

## Convert a Raw PyTorch Loop

Start from the smallest safe transformation:

```python
import lightning as L

fabric = L.Fabric(accelerator="auto", devices="auto", precision="32-true")
fabric.launch()

train_loader = fabric.setup_dataloaders(train_loader)
model, optimizer = fabric.setup(model, optimizer)

for epoch in range(max_epochs):
    model.train()
    for batch in train_loader:
        optimizer.zero_grad(set_to_none=True)
        inputs, targets = batch
        loss = criterion(model(inputs), targets)
        fabric.backward(loss)
        optimizer.step()
```

Required edits when converting user code:

- Remove direct `model.to(device)`, `model.cuda()`, and batch `.to(device)` calls if using default `move_to_device=True`.
- Replace `loss.backward()` with `fabric.backward(loss)`.
- Wrap every model/optimizer pair with `fabric.setup` before use.
- Wrap dataloaders with `fabric.setup_dataloaders` before iteration.
- Use `fabric.device` only for tensors created outside wrapped dataloaders.
- Keep optimizer/scheduler stepping manual; Fabric does not own loop semantics.

## CPU-Safe Smoke Validation

Bundle-level validation command:

```bash
python sub-skills/fabric-expert-loops/scripts/fabric_smoke.py --max-steps 2 --checkpoint-path fabric-smoke.pt
```

Expected signals:

- Prints `fabric_smoke: ok` from rank-safe output.
- Shows a small final loss and `checkpoint_exists=True` when a checkpoint path is provided.
- Does not download data, require GPUs, or read from the original repository checkout.

CLI-launch validation when `fabric` is installed:

```bash
fabric run --accelerator=cpu --devices=1 sub-skills/fabric-expert-loops/scripts/fabric_smoke.py --max-steps 2
```

Do not add `fabric.launch()` to scripts intended only for `fabric run`; a script that needs to support both modes should guard the launch call or use the function-launch pattern intentionally.

## Gradient Accumulation

Fabric leaves accumulation policy to the user. Use `no_backward_sync` to avoid unnecessary gradient synchronization on supported distributed strategies:

```python
accumulate = 4
for step, batch in enumerate(train_loader):
    is_accumulating = (step + 1) % accumulate != 0
    with fabric.no_backward_sync(model, enabled=is_accumulating):
        loss = compute_loss(model, batch) / accumulate
        fabric.backward(loss)

    if not is_accumulating:
        optimizer.step()
        optimizer.zero_grad(set_to_none=True)
```

Checklist:

- Divide the loss by the accumulation factor when matching the effective learning rate of a larger batch.
- Call `optimizer.step()` and `zero_grad()` only at accumulation boundaries.
- Put the forward pass and `fabric.backward` inside `no_backward_sync`.
- Use the wrapped model returned by `fabric.setup`; otherwise `no_backward_sync` raises a setup-related error.

## Checkpoint and Resume

Fabric checkpointing is dictionary-based and strategy-aware:

```python
state = {
    "model": model,
    "optimizer": optimizer,
    "epoch": epoch,
    "global_step": global_step,
}
fabric.save(checkpoint_path, state)

resume_state = {"model": model, "optimizer": optimizer}
remainder = fabric.load(checkpoint_path, resume_state, strict=True, weights_only=True)
start_epoch = int(remainder.get("epoch", 0)) + 1
global_step = int(remainder.get("global_step", 0))
```

Guidelines:

- Call `fabric.save` and `fabric.load` on all ranks, not just rank zero.
- Put scalar resume metadata in the checkpoint dictionary, not in separate rank-local files.
- Use `fabric.load_raw` when importing a plain PyTorch `state_dict` into a Fabric-managed model.
- For FSDP/DeepSpeed/sharded checkpoints, route consolidation and portability questions to `../distributed-accelerators/SKILL.md`.

## Dataloaders and Samplers

Default Fabric behavior prepares dataloaders for distributed training:

```python
train_loader, val_loader = fabric.setup_dataloaders(train_loader, val_loader)
```

Use explicit flags when the user needs custom behavior:

```python
train_loader = fabric.setup_dataloaders(
    train_loader,
    use_distributed_sampler=False,
    move_to_device=False,
)

for batch in train_loader:
    batch = fabric.to_device(batch)
```

Decision table:

| Need | Setting |
| --- | --- |
| Let Fabric replace/wrap samplers for distributed training | `use_distributed_sampler=True` |
| Preserve a custom sampler exactly | `use_distributed_sampler=False` |
| Let Fabric move batches automatically | `move_to_device=True` |
| Move nested/custom batch objects manually | `move_to_device=False` then `fabric.to_device(batch)` |
| Download/preprocess once before other ranks read | `with fabric.rank_zero_first(local=False): ...` |

## Validation and Metrics

Fabric does not impose `validation_step`. Write validation loops directly:

```python
model.eval()
loss_total = torch.tensor(0.0, device=fabric.device)
count = torch.tensor(0, device=fabric.device)
with torch.no_grad():
    for inputs, targets in val_loader:
        logits = model(inputs)
        loss_total += criterion(logits, targets) * targets.numel()
        count += targets.numel()

loss_total = fabric.all_reduce(loss_total, reduce_op="sum")
count = fabric.all_reduce(count, reduce_op="sum")
val_loss = loss_total / count.clamp_min(1)
fabric.print(f"val_loss={val_loss.item():.4f}")
```

Use `all_reduce` or `all_gather` for global metrics. Do not assume a local metric value from one rank represents all data.

## Custom Trainer Loop Skeleton

Fabric can support a small trainer-like class when the user needs custom loop ownership but not full `Trainer` behavior:

```python
class MiniFabricTrainer:
    def __init__(self, *, accelerator="auto", devices="auto", precision="32-true", max_epochs=1):
        self.fabric = L.Fabric(accelerator=accelerator, devices=devices, precision=precision)
        self.max_epochs = max_epochs
        self.global_step = 0

    def fit(self, model, optimizer, train_loader, checkpoint_path=None):
        self.fabric.launch()
        train_loader = self.fabric.setup_dataloaders(train_loader)
        model, optimizer = self.fabric.setup(model, optimizer)
        state = {"model": model, "optimizer": optimizer, "global_step": self.global_step}

        if checkpoint_path:
            remainder = self.fabric.load(checkpoint_path, state, strict=False, weights_only=True)
            self.global_step = int(remainder.get("global_step", self.global_step))

        for epoch in range(self.max_epochs):
            model.train()
            for batch in train_loader:
                optimizer.zero_grad(set_to_none=True)
                loss = compute_loss(model, batch)
                self.fabric.backward(loss)
                optimizer.step()
                self.global_step += 1
```

Use this pattern only when the user explicitly needs custom control. If the user wants standard callbacks, logger integration, evaluation scheduling, checkpoint monitoring, or distributed sampler policy without manual code, route to `../training-core/SKILL.md`.

## Logging Pattern

```python
from lightning.fabric.loggers import CSVLogger

logger = CSVLogger(root_dir="logs", name="experiment")
fabric = L.Fabric(loggers=logger)
...
fabric.log("train_loss", loss.detach(), step=global_step)
fabric.log_dict({"lr": optimizer.param_groups[0]["lr"]}, step=global_step)
fabric.print(f"step={global_step} loss={float(loss):.4f}")
```

Use Fabric loggers for scalar/event recording and `fabric.print` for console output. Do not use `self.log`; that is a `LightningModule`/`Trainer` API.

## Precision and Device Pattern

Practical examples:

```python
L.Fabric(accelerator="cpu", devices=1, precision="32-true")
L.Fabric(accelerator="gpu", devices=1, precision="16-mixed")
L.Fabric(accelerator="gpu", devices=4, strategy="ddp", precision="bf16-mixed")
```

Guardrails:

- CPU examples in this skill are validated as safe syntax/patterns, not performance claims.
- GPU, TPU, FSDP, DeepSpeed, FP8, tensor parallel, and multi-node behavior requires hardware/optional dependencies; route the deep compatibility work to `../distributed-accelerators/SKILL.md`.
- Use `fabric.autocast()` only for operations outside the wrapped model forward that also need precision handling.

## Fabric CLI vs Programmatic Launch

Choose one launch owner:

| User command style | Code should do |
| --- | --- |
| `python train.py` with `Fabric(accelerator=..., devices=...)` | Call `fabric.launch()` before setup for distributed/process initialization. |
| `fabric run --accelerator=... --devices=... train.py` | Create `Fabric()` or `Fabric(...)`; do not call `fabric.launch()`. |
| Spawn/fork/XLA-style strategy needing a function | Use `fabric.launch(train_fn, args...)`; `train_fn` accepts `fabric`. |

Typical `argparse` script pattern:

```python
parser = argparse.ArgumentParser()
parser.add_argument("--max-steps", type=int, default=10)
args = parser.parse_args()

fabric = L.Fabric()
# If launched via `fabric run`, process setup is already handled.
# If launched with `python`, call fabric.launch() only if your strategy requires it.
```
