# Training API Reference

This page collects the core objects that the training sub-skill uses most often.

## Model construction

- `chainer.Variable`
- `chainer.Function`
- `chainer.Link`
- `chainer.Chain`
- `chainer.ChainList`
- `chainer.Sequential`
- `chainer.links.Classifier`
- `chainer.functions` for activations, losses, and array transforms

Use `Chain` when the number of child links is fixed, and `ChainList` when the model is naturally list-like.
Use `Sequential` when the model is a simple linear pipeline of links and functions.

## Dataset and iterator layer

- `chainer.dataset.DatasetMixin`
- `chainer.dataset.Iterator`
- `chainer.dataset.concat_examples(...)`
- `chainer.dataset.ConcatWithAsyncTransfer`
- `chainer.dataset.to_device(...)`
- `chainer.datasets.TupleDataset`
- `chainer.datasets.SerialIterator`
- `chainer.datasets.SubDataset`
- `chainer.datasets.split_dataset(...)`
- `chainer.datasets.split_dataset_random(...)`

The docs expect datasets to implement `__len__` and `__getitem__`.

## Trainer layer

- `chainer.training.Trainer(updater, stop_trigger=None, out='result', extensions=None)`
- `chainer.training.StandardUpdater(iterator, optimizer, converter=..., device=None, loss_func=None, loss_scale=None, auto_new_epoch=True, **kwargs)`
- `chainer.training.ParallelUpdater(iterator, optimizer, converter=..., models=None, devices=None, loss_func=None, loss_scale=None, auto_new_epoch=True)`
- `chainer.training.make_extension(...)`
- `chainer.training.get_trigger(...)`
- `chainer.training.extensions.Evaluator(...)`
- `chainer.training.extensions.PrintReport(...)`
- `chainer.training.extensions.LogReport(...)`
- `chainer.training.extensions.ProgressBar(...)`
- `chainer.training.extensions.snapshot(...)`
- `chainer.training.extensions.snapshot_object(...)`
- `chainer.training.extensions.DumpGraph(...)`

The inspected signatures confirmed that `Trainer`, `StandardUpdater`, and `ParallelUpdater` are the main orchestration entry points.

## Serialization

- `chainer.serializers.save_npz(file, obj, compression=True)`
- `chainer.serializers.load_npz(file, obj, path='', strict=True, ignore_names=None)`
- `chainer.serializers.save_hdf5(file, obj)`
- `chainer.serializers.load_hdf5(file, obj)`

Only parameters and persistent values are serialized automatically.
If a model needs an extra value to survive save/load, register it with `add_persistent`.

## Device and backend helpers

- `chainer.backend.get_device(device_spec)`
- `chainer.backend.using_device(device_spec)`
- `chainer.backend.get_device_from_array(*arrays)`
- `chainer.backends.cuda.get_device_from_id(device_id)`
- `chainer.backends.cuda.get_device_from_array(array)`
- `chainer.backends.cuda.to_cpu(array, stream=None)`
- `chainer.backends.cuda.to_gpu(array, device=None, stream=None)`
- `chainer.backends.cuda.available`
- `chainer.backends.cuda.cudnn_enabled`
- `chainer.backends.intel64.is_ideep_available()`

## Configuration keys that affect training

- `chainer.config.train`
- `chainer.config.enable_backprop`
- `chainer.config.use_cudnn`
- `chainer.config.use_static_graph`
- `chainer.config.use_ideep`
- `chainer.config.dtype`

## Practical notes

- `Trainer.extend()` accepts either bare callables or extension objects.
- `Evaluator` usually runs with `train=False` under the hood.
- `ParallelUpdater` is the built-in multi-GPU training path inside a single host.
- `save_npz` and `load_npz` are the simplest way to persist a toy model in smoke tests.
