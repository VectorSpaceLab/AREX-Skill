# Booster API Reference

## Core construction

```python
from colossalai.booster import Booster
from colossalai.booster.plugin import TorchDDPPlugin

plugin = TorchDDPPlugin()
booster = Booster(plugin=plugin)
model, optimizer, criterion, dataloader, scheduler = booster.boost(
    model, optimizer, criterion=criterion, dataloader=dataloader, lr_scheduler=scheduler
)
```

Inspected constructor:

```text
Booster(device=None, mixed_precision=None, plugin=None)
```

## Training loop shape

```python
model.train()
for batch in dataloader:
    optimizer.zero_grad()
    outputs = model(**batch) if isinstance(batch, dict) else model(batch)
    loss = criterion(outputs, batch)
    booster.backward(loss, optimizer)
    optimizer.step()
    if scheduler is not None:
        scheduler.step()
```

For pipeline parallelism, use:

```python
outputs = booster.execute_pipeline(data_iter, model, criterion, optimizer, return_loss=True)
```

`execute_pipeline` requires a criterion callable that accepts model outputs and inputs and returns the loss.

## Important methods

- `boost(model, optimizer=None, criterion=None, dataloader=None, lr_scheduler=None)`: wraps training components.
- `backward(loss, optimizer)`: plugin-aware backward pass.
- `execute_pipeline(data_iter, model, criterion, optimizer=None, return_loss=True, return_outputs=False)`: pipeline schedule entry point.
- `save_model` / `load_model`: model checkpoints; `save_model` supports `shard`, `size_per_shard`, `use_safetensors`, and `use_async`.
- `save_optimizer` / `load_optimizer`: optimizer state checkpoints; sharded and async options exist.
- `save_lr_scheduler` / `load_lr_scheduler`: scheduler checkpoint utilities.
- `enable_lora` / `save_lora_as_pretrained`: LoRA adapter workflows when PEFT and optional quantization dependencies are available.
- `no_sync`: disable gradient synchronization across data-parallel process groups when the selected plugin supports it.

## Dataloader preparation

Most plugins expose:

```python
plugin.prepare_dataloader(dataset, batch_size, shuffle=False, seed=1024, drop_last=False, pin_memory=False, num_workers=0, distributed_sampler_cls=None, **kwargs)
```

Use plugin-prepared dataloaders for distributed sampling unless you intentionally manage samplers yourself.
