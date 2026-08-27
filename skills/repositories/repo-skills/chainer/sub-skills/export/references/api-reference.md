# Export API Reference

## ONNX-Chainer

- `onnx_chainer.export(model, args, filename=None, export_params=True, graph_name='Graph', save_text=False, opset_version=None, input_names=None, output_names=None, train=False, return_named_inout=False, external_converters=None, external_opset_imports=None, input_shapes=None, no_testcase=False)`
- `onnx_chainer.export_testcase(model, args, out_dir, output_grad=False, **kwargs)`
- `onnx_chainer.convert_parameter(parameter, context)`
- `onnx_chainer.MINIMUM_OPSET_VERSION == 7`
- `onnx_chainer.MAXIMUM_OPSET_VERSION == 11`

Important notes:

- `export()` forwards the model with `train=False` by default.
- `export_testcase()` writes `model.onnx` plus `test_data_set_0/input_*.pb` and `output_*.pb` files.
- `output_grad=True` also writes gradient tensors for model parameters.
- `no_testcase=False` is deprecated when a filename is supplied directly to `export()`.

## Caffe export

- `chainer.exporters.caffe.export(model, args, directory=None, export_params=True, graph_name='Graph')`

Important notes:

- The exporter writes `chainer_model.prototxt` and `chainer_model.caffemodel`.
- The input is expected to be a list of `chainer.Variable` objects.
- The exporter supports a legacy subset of functions and links, centered on layers such as linear, convolution, deconvolution, pooling, LRN, batch normalization, and a few related vision ops.

## Validation helpers

- `onnx.checker.check_model(...)` is the normal structural check after ONNX export.
- `onnx.load_tensor(...)` is convenient for checking testcase protobufs.

## Practical constraints

- ONNX export needs the `onnx` package and the Chainer pin from the docs.
- Caffe export is best treated as a compatibility path for models that stay inside the supported layer subset.
- Use the bundled smoke script before trying a large pretrained model.
