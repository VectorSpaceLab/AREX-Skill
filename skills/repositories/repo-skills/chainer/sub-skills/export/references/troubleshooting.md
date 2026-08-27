# Export Troubleshooting

## `onnx_chainer.export` cannot import ONNX

Symptom:

- The exporter raises `ImportError` and suggests installing ONNX.

Recovery:

- Install the legacy-compatible ONNX package expected by the Chainer docs.
- Run `../../scripts/export_smoke.py --format onnx` before retrying a larger model.

## Opset warnings or incompatible graphs

Symptoms:

- The exporter warns about the requested opset.
- `onnx.checker.check_model(...)` fails.

Recovery:

- Keep the opset inside the supported `7` through `11` range unless you are deliberately experimenting.
- Start with `input_names`, `output_names`, and `input_shapes` set explicitly when the graph shape is ambiguous.

## Output names do not match expectations

Symptoms:

- Testcase protobuf names differ from the expected names.
- A downstream runtime cannot find the input or output tensor.

Recovery:

- Pass `input_names=` and `output_names=` to `export(...)` or `export_testcase(...)`.
- Confirm `export_testcase(...)` wrote `test_data_set_0/input_*.pb` and `output_*.pb`.

## Unsupported model operation

Symptoms:

- Export fails only for a full model, but the tiny smoke script passes.
- The error references a Chainer function node or link that is not converted.

Recovery:

- Reduce the model until you find the unsupported function.
- Provide an `external_converters` mapping for ONNX custom operators when appropriate.
- For Caffe, keep the model within the legacy supported layer subset.

## Caffe output files are missing

Symptoms:

- `chainer_model.prototxt` or `chainer_model.caffemodel` is missing.

Recovery:

- Ensure the output directory exists before export.
- Pass inputs as a list of `chainer.Variable` objects.
- Use a model whose `__call__` returns the tensor you actually want exported.
