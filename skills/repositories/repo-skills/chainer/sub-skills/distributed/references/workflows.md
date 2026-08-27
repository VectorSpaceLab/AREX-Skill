# ChainerMN Workflows

## 1. Convert a single-node trainer to data parallel

The minimal conversion pattern is:

```python
import chainer
import chainermn

comm = chainermn.create_communicator()
device = comm.intra_rank
chainer.cuda.get_device_from_id(device).use()

optimizer = chainermn.create_multi_node_optimizer(
    chainer.optimizers.Adam(), comm)
```

Then use the wrapped optimizer in the normal Chainer `StandardUpdater` and `Trainer` flow.

## 2. Scatter datasets

To preserve epoch semantics, load the full dataset only on rank 0 and scatter it:

```python
if comm.rank == 0:
    train, test = chainer.datasets.get_mnist()
else:
    train, test = None, None

train = chainermn.scatter_dataset(train, comm)
test = chainermn.scatter_dataset(test, comm)
```

This creates per-rank subsets, duplicating some elements if needed to balance shards.

## 3. Wrap evaluators and rank-zero extensions

Validation can be parallelized by wrapping a normal evaluator:

```python
evaluator = extensions.Evaluator(test_iter, model, device=device)
evaluator = chainermn.create_multi_node_evaluator(evaluator, comm)
trainer.extend(evaluator)
```

Register noisy output extensions such as `PrintReport`, `ProgressBar`, and `DumpGraph` only on `comm.rank == 0`.

## 4. Launch locally or across hosts

Single-node multi-process launch:

```bash
mpiexec -n 4 python train_mnist.py
```

Multi-node launch typically adds host selection to the MPI launcher.
All data paths and environment variables must be visible on every host.

## 5. CPU-only debugging

If you only need CPU execution, use the `naive` communicator and do not install CuPy.
You still need a working MPI runtime and `mpi4py`.

## 6. Model-parallel workflows

Use `MultiNodeChainList` when different ranks own different model fragments.
The repo's model-parallel examples use patterns such as:

- rank-specific subchains
- `add_link(..., rank_in=..., rank_out=...)`
- `create_multi_node_n_step_rnn(...)` for split RNNs
- fixed process counts for models that assume a particular split

Model-parallel scripts should validate rank count before running the full job.

## 7. MultiprocessIterator with MPI

When `MultiprocessIterator` and InfiniBand are both involved, set the multiprocessing start method before communicator creation:

```python
import multiprocessing
multiprocessing.set_start_method('forkserver')
p = multiprocessing.Process()
p.start()
p.join()
comm = chainermn.create_communicator()
```

## 8. What the bundled probe does

`../../scripts/chainermn_probe.py` checks:

- ChainerMN import and version
- Chainer CUDA availability
- `mpi4py` module availability
- `mpiexec` and `mpicc` in `PATH`
- optional communicator creation when run with `--create`
