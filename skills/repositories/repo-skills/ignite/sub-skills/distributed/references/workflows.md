# Distributed workflows

## 1. Start with the serial path

When no distributed backend is needed, keep the context manager explicit and lightweight.

```python
import ignite.distributed as idist

with idist.Parallel(backend=None) as parallel:
    parallel.run(lambda local_rank: print(idist.get_rank(), local_rank, idist.backend()))
```

Use this to confirm that your code still works without a process group.

## 2. Run a single-process native backend smoke check

A single-process `gloo` context is a safe way to verify native distributed support on CPU.

```python
import torch
import ignite.distributed as idist

with idist.Parallel(backend="gloo") as parallel:
    def report(local_rank):
        print(idist.get_rank(), local_rank, idist.get_world_size(), idist.device())

    parallel.run(report)
```

This exercises `initialize`, `finalize`, and the basic rank helpers without needing multiple hosts or GPUs.

## 3. Adapt a dataloader, model, and optimizer together

Use the auto-wrappers when a single training script should work in serial and distributed settings.

```python
from torch import nn, optim
import ignite.distributed as idist

loader = idist.auto_dataloader(dataset, batch_size=32, shuffle=True, num_workers=4)
model = idist.auto_model(nn.Linear(4, 2))
optimizer = idist.auto_optim(optim.SGD(model.parameters(), lr=0.1))
```

The wrappers keep the code path stable while adjusting backend-specific details behind the scenes.

## 4. Use rank-aware guards for side effects

`one_rank_only` and `one_rank_first` are the safest way to isolate logging, downloads, or workspace setup.

```python
import ignite.distributed as idist

@idist.one_rank_only()
def log_once():
    print("only rank 0 prints this")

with idist.one_rank_first():
    maybe_download_dataset()
```

Use these before touching the file system or an external service.

## 5. Launch multi-process or external-tool workflows

When the user launches with `torchrun`, `horovodrun`, or a TPU launcher, keep the code focused on backend detection and auto-wrappers.

```bash
torchrun --nproc_per_node=4 main.py
horovodrun -np 4 python main.py
```

Inside `main.py`, use `Parallel(backend="gloo")`, `Parallel(backend="nccl")`, `Parallel(backend="horovod")`, or `Parallel(backend="xla-tpu")` as appropriate.

## 6. Check collectives in the smallest possible way

Use `broadcast`, `all_reduce`, and `all_gather_tensors_with_shapes` on tiny tensors first.

```python
import torch
import ignite.distributed as idist

tensor = torch.tensor([idist.get_rank()], dtype=torch.float32)
print(idist.broadcast(tensor, src=0))
print(idist.all_gather(tensor))
```

If a shape-aware gather is needed, pass the known shapes list before scaling up the real workload.
