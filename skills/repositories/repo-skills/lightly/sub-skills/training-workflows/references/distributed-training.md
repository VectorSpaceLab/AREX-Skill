# Distributed training

Use this reference only when the task explicitly needs multi-process or multi-GPU Lightly training. The default training skill path should stay single-process unless distributed behavior is the point of the request.

## Core pattern

The package examples use PyTorch Lightning DDP with synchronized batch norm and, for some losses, distributed feature gathering:

```python
trainer = pl.Trainer(
    max_epochs=10,
    accelerator="gpu",
    devices="auto",
    strategy="ddp",
    sync_batchnorm=True,
    use_distributed_sampler=True,
)
```

Loss-side distributed gathering is method dependent. In the repository docs, it matters for SimCLR, Barlow Twins, and SwaV; do not assume it helps every recipe.

## What changes in distributed mode

- **Batch size is per device**: the effective global batch is `batch_size_per_device * num_devices`.
- **Batch norm statistics become cross-device** when synchronized batch norm is on.
- **Data loading becomes per rank**: worker counts multiply with the number of processes.
- **Checkpointing should be rank-aware**: only the main rank should write the final checkpoint.

## Practical caveats

- Start from a single-device recipe first, then enable DDP.
- Keep `drop_last=True`; uneven final batches are a common source of distributed shape and synchronization issues.
- If a run hangs before the first step, check the port, stale workers, and sampler configuration before changing the model.
- A free local port is often enough to unblock a run that stalls during process-group setup.
- Reduce `num_workers` if the job hangs while loading data or if the host is memory constrained.
- On CPU-only experiments, distributed support is optional and should be treated as a special-case smoke path rather than the default training route.

## Common distributed knobs

- `strategy="ddp"` for process-based distributed training
- `sync_batchnorm=True` for cross-rank batch norm statistics
- `use_distributed_sampler=True` on modern Lightning versions
- `gather_distributed=True` on the losses that benefit from cross-rank negatives or assignments
- `devices="auto"` when you want portable code, or an explicit count when you need to bound the run

## Good rule of thumb

If a recipe works on one device but not in DDP, first check:

1. whether the loss actually wants distributed gathering
2. whether the batch size is large enough per rank
3. whether the data loader is sharded and dropping the last batch
4. whether the port, sampler, or worker count is causing the stall
