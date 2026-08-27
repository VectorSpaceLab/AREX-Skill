# Collaborative Training Workflows

## Purpose

Read this for the practical patterns that turn the averaging and optimizer APIs into a usable collaborative-training run.

## 1) Average tensors directly

Use `DecentralizedAverager` when you want peers to average a fixed tensor list or a model state without writing a custom optimizer wrapper.

```python
import torch
from hivemind import DHT, DecentralizedAverager

state = [torch.randn(8, 8), torch.zeros(8)]
dht = DHT(start=True)
averager = DecentralizedAverager(
    state,
    dht=dht,
    start=True,
    prefix="my_group",
    target_group_size=2,
)

with averager.get_tensors() as tensors:
    tensors[0].add_(1)

averager.step(wait=True)
```

Use this when:

- you need a small demonstration of peer averaging
- you want to test the group formation logic separately from optimizer state
- you need explicit control over the tensors being averaged

## 2) Wrap a normal PyTorch optimizer

`hivemind.Optimizer` is the primary training workflow.

```python
import torch
import hivemind

model = torch.nn.Linear(10, 2)
base_opt = torch.optim.Adam(model.parameters(), lr=1e-3)
dht = hivemind.DHT(start=True)

opt = hivemind.Optimizer(
    dht=dht,
    run_id="demo",
    batch_size_per_step=32,
    target_batch_size=1024,
    optimizer=base_opt,
    use_local_updates=True,
    matchmaking_time=3.0,
    averaging_timeout=10.0,
)
```

Practical reminders:

- `run_id` must match across peers that should collaborate.
- `target_batch_size` is the swarm-wide epoch boundary.
- `batch_size_per_step` is the local contribution from one peer.
- `opt.load_state_from_peers()` is useful before the first minibatch when joining late.
- `use_local_updates=True` makes the run more asynchronous; leave it off if you want the simplest behavior.

## 3) Handle state sharing and progress reporting

When you need training state or progress metadata, prefer `TrainingStateAverager` and `ProgressTracker`.

- `TrainingStateAverager` is the right abstraction when optimizer state, learning-rate schedule state, and extra tensors should move together.
- `ProgressTracker` helps peers converge on the same global epoch and broadcast progress metadata into the DHT.

Common triggers:

- a peer joins late and must catch up
- you need consistent learning-rate schedules across peers
- you want visible logs for samples/sec and local epoch numbers

## 4) Choose a compression strategy

Default to the least surprising option first.

- `NoCompression` — safest, easiest to debug.
- `Float16Compression` — common balance for collaborative training.
- `Uniform8BitQuantization` / `Quantile8BitQuantization` — useful when bandwidth is tight and small error is acceptable.
- `RoleAdaptiveCompression` — choose different strategies for parameters, gradients, optimizer statistics, or activations.
- `SizeAdaptiveCompression` — helpful when tiny tensors should stay lossless and large tensors can be compressed.
- `BlockwiseQuantization` — only when you intentionally want the optional `bitsandbytes` path.

## 5) Use the installed CLI and preflight

This workflow does not have a dedicated console script of its own, but the package preflight helper is useful before you start a collaborative run:

```bash
python scripts/check_install.py
python scripts/check_install.py --check-cuda
python scripts/check_install.py --check-albert
```

The optional ALBERT check intentionally fails when the extra training dependencies are missing; that is a useful signal before you hand the recipe to another agent.
