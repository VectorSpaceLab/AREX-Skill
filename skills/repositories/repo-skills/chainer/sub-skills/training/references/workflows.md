# Training Workflows

## 1. Build a model

Most Chainer workflows begin with a `Link` or `Chain`.
A `Chain` is the usual choice when the architecture has a fixed set of child links.
Use `ChainList` when the topology is list-like, and `Sequential` when the model is a straight pipeline.

Typical model-building steps:

1. Import `chainer.links as L` and `chainer.functions as F`.
2. Define the child links in `__init__()` inside `self.init_scope()`.
3. Implement `__call__()` or `forward()` with the define-by-run logic.
4. Wrap the model with `L.Classifier(...)` when you want the built-in classification loss and accuracy reporting.

## 2. Prepare the dataset and iterator

Use `DatasetMixin`, `TupleDataset`, or a repo-provided concrete dataset.
For a toy smoke check, a tiny `TupleDataset` is often enough.
For real examples, the repo uses:

- `examples/mnist` for a minimal in-memory classification workflow
- `examples/cifar` for image classification on a small vision dataset
- `examples/ptb` and `examples/seq2seq` for RNN and seq2seq workflows
- `examples/serialization` for save/load behavior

The iterator layer is usually `SerialIterator` for a single process.
Use `MultiprocessIterator` only when the workflow needs it and the process model is compatible.

## 3. Choose the updater and trainer

The common single-host path is:

```python
optimizer = optimizers.SGD()
optimizer.setup(model)
updater = training.StandardUpdater(train_iter, optimizer, device=None)
trainer = training.Trainer(updater, (n_iter, 'iteration'), out='result')
```

If you need data-parallel multi-GPU execution on one host, replace `StandardUpdater` with `ParallelUpdater` and provide a `devices` map.

Add extensions such as `Evaluator`, `LogReport`, `PrintReport`, `ProgressBar`, and `snapshot` after the trainer is created.

## 4. Save and resume

Training state is typically saved with `save_npz` on the model, the optimizer, or the full trainer.
`load_npz` restores the corresponding state.
If you need HDF5, install `h5py` and use `save_hdf5` / `load_hdf5`.

For a smoke check, use `scripts/serialization_smoke.py` instead of a full example download.

## 5. CPU and GPU execution

- CPU-only workflows use NumPy arrays and `device=None` or `@numpy`-style backend helpers.
- GPU workflows use CuPy arrays and `to_gpu()` / `to_cpu()`.
- `chainer.backends.cuda.available` tells you whether the GPU path is actually usable.
- `chainer.backends.cuda.cudnn_enabled` tells you whether cuDNN is active.

If the user wants a GPU example, explain that CuPy must be installed separately.

## 6. Static graph optimization

Chainer has an experimental static graph optimization path for models whose control flow is stable across iterations.
Use it when the model repeats the same call structure and you are not using ChainerX.
If the model is dynamic, keep the ordinary define-by-run path.

## 7. How the bundled smoke script maps to the workflow

`../../scripts/training_smoke.py` exercises the shortest useful path:

1. Define a tiny model.
2. Create a tiny synthetic `TupleDataset`.
3. Run a `SerialIterator`.
4. Attach `StandardUpdater`, `Trainer`, `LogReport`, and `PrintReport`.
5. Confirm that the loop completes and reports a loss and accuracy.

That script is the best first check when the user only wants to know whether the core training stack is functioning.
