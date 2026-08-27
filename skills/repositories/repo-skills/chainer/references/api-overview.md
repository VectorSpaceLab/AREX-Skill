# API Overview

This file records the verified public surface that the generated skill relies on.
The inspection environment verified Chainer `7.8.1`, ChainerMN `7.8.1`, and ONNX-Chainer opset support `7` through `11`.

## Core runtime facts

- `chainer.__version__` exposes the package version.
- `chainer.print_runtime_info(out=None)` prints platform, Chainer, ChainerX, NumPy, CuPy, and iDeep status.
- `chainer.backends.cuda.available` reports whether CuPy imported successfully.
- `chainer.backends.cuda.cudnn_enabled` reports whether cuDNN is usable.
- `chainer.backends.intel64.is_ideep_available()` reports iDeep availability.
- `chainerx.is_available()` reports whether ChainerX was built into the install.

## Device and backend helpers

- `chainer.backend.get_device(device_spec)`
- `chainer.backend.using_device(device_spec)`
- `chainer.backend.get_device_from_array(*arrays)`
- `chainer.backend.get_array_module(*args)`
- `chainer.backends.cuda.get_device_from_id(device_id)`
- `chainer.backends.cuda.get_device_from_array(array)`
- `chainer.backends.cuda.to_cpu(array, stream=None)`
- `chainer.backends.cuda.to_gpu(array, device=None, stream=None)`
- `chainer.backends.intel64.is_ideep_available()`

The inspected signature of `chainer.backend.get_device` accepts backend device objects, ChainerX devices, CuPy devices, strings, tuples, and integers.

## Training loop surface

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

## Dataset and serialization surface

- `chainer.dataset.DatasetMixin`
- `chainer.dataset.Iterator`
- `chainer.dataset.concat_examples`
- `chainer.dataset.ConcatWithAsyncTransfer`
- `chainer.dataset.to_device`
- `chainer.serializers.save_npz(file, obj, compression=True)`
- `chainer.serializers.load_npz(file, obj, path='', strict=True, ignore_names=None)`
- `chainer.serializers.save_hdf5(file, obj)` and `load_hdf5(file, obj)` when `h5py` is installed

## Export surface

- `onnx_chainer.export(model, args, filename=None, export_params=True, graph_name='Graph', save_text=False, opset_version=None, input_names=None, output_names=None, train=False, return_named_inout=False, external_converters=None, external_opset_imports=None, input_shapes=None, no_testcase=False)`
- `onnx_chainer.export_testcase(model, args, out_dir, output_grad=False, **kwargs)`
- `onnx_chainer.MINIMUM_OPSET_VERSION == 7`
- `onnx_chainer.MAXIMUM_OPSET_VERSION == 11`
- `chainer.exporters.caffe.export(model, args, directory=None, export_params=True, graph_name='Graph')`

## Distributed surface

- `chainermn.create_communicator(communicator_name='pure_nccl', mpi_comm=None, **kwargs)`
- `chainermn.create_multi_node_optimizer(actual_optimizer, communicator, double_buffering=False, zero_fill=True)`
- `chainermn.create_multi_node_evaluator(evaluator, communicator)`
- `chainermn.scatter_dataset(dataset, communicator)`
- `chainermn.scatter_index(index, communicator)`
- `chainermn.create_multi_node_checkpointer(name, comm, cp_interval=5, gc_interval=5, path=None)`
- `chainermn.links.MultiNodeChainList`
- `chainermn.links.create_multi_node_n_step_rnn(...)`
- `chainermn.functions.send/recv/bcast/gather/scatter/alltoall/allgather`

## Configuration keys that matter most

- `chainer.config.train`
- `chainer.config.enable_backprop`
- `chainer.config.use_cudnn`
- `chainer.config.use_static_graph`
- `chainer.config.use_ideep`
- `chainer.config.dtype`

## ChainerX surface

- `chainerx.ndarray`
- `chainerx.get_backend(...)`
- `chainerx.get_device(...)`
- `chainerx.get_default_device()`
- `chainerx.set_default_device(...)`
- `chainerx.using_device(...)`
- `chainerx.to_numpy(...)`

The skill treats ChainerX as optional unless the task explicitly asks for a ChainerX build or device-specific workflow.
