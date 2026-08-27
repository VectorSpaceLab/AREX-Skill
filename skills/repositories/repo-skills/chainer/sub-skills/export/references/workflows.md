# Export Workflows

## 1. Export to ONNX

Use ONNX-Chainer when you want a graph format that other runtimes can consume.
The common path is:

1. Build or load a `Chain` / `Sequential` model.
2. Prepare a representative input array or `Variable`.
3. Call `onnx_chainer.export(...)` or `export_testcase(...)`.
4. Validate the output with `onnx.checker.check_model(...)`.

The bundled smoke script uses a tiny two-layer model and a single zero input.
That is enough to validate the exporter without any downloads.

### When to choose `export_testcase`

Choose `export_testcase(...)` when you want the ONNX graph and the paired I/O tensors in the protobuf testcase layout.
That is the right choice when you need a reproducible export artifact or when you want to compare against ONNX Runtime.

## 2. Export to Caffe

Use `chainer.exporters.caffe.export(...)` when you need the legacy Caffe file pair:

- `chainer_model.prototxt`
- `chainer_model.caffemodel`

A good Caffe export workflow is:

1. Build a model that stays inside the supported layer subset.
2. Wrap the model so the `__call__` path returns the desired output tensor.
3. Feed a list of `Variable` inputs.
4. Confirm both output files exist.

## 3. Model families from the repo

The repository provides export-oriented examples for:

- `examples/caffe_export`
- `onnx_chainer/examples/resnet50`
- `onnx_chainer/examples/yolov2tiny`

Those examples show how the exporter is used on vision models, but they are larger and more environment-specific than the bundled smoke script.

## 4. Error triage

If export fails:

- check that `onnx` is installed and at a compatible version
- confirm the requested opset is inside the supported range
- reduce the model to the smallest supported layer set
- verify that all inputs are arrays or `Variable` objects the exporter understands
- rerun `../../scripts/export_smoke.py` before trying the full model again
