# Deployment Export Troubleshooting

## Optional Dependency Missing

Symptom examples:

- `ImportError` involving `caffe2`, `caffe2.proto`, or `caffe2.python`.
- `ModuleNotFoundError: onnx`.
- ONNX export crashes or emits unsupported operator errors.

Actions:

1. Switch to `--export-method tracing --format torchscript` if the user only needs a deployable artifact.
2. Treat Caffe2 as optional unless the user's runtime explicitly requires it and the local PyTorch build includes Caffe2.
3. Treat ONNX as optional/advanced; confirm package, opset, custom op, and downstream runtime expectations before retrying.
4. Do not install broad backend packages or mutate an existing environment without user approval.

## Missing Sample Inputs

Tracing and Caffe2 tracing need representative sample inputs. If `--sample-image` is omitted, the export driver may try to read the first sample from the config's test dataset. That fails when the dataset is not registered, not present, or unsuitable for deployment.

Actions:

- Provide `--sample-image SAMPLE.jpg` for command-line export planning.
- Ensure the image format matches the config's `INPUT.FORMAT` expectations.
- Avoid random tensors for final traces of detection models unless the goal is only a synthetic smoke test.
- If the model has proposal/mask/keypoint branches, choose an image likely to exercise the relevant branches.

## Unsupported Method or Model Combination

Symptoms include scripting compiler errors, missing `Instances` attributes, unsupported operators, Caffe2 tracer key errors, or conversion assertions.

Actions:

- Use tracing for PointRend and Cascade R-CNN rather than scripting.
- Use TorchScript tracing/scripting before Caffe2/ONNX for official model families.
- Include every used `Instances` field in `scripting_with_instances` field maps.
- Route custom architecture exportability design to extension-projects; this sub-skill can diagnose method choice but does not own rewriting custom modules.

## TorchScript Input or Output Confusion

`TracingAdapter` flattens structured inputs and outputs into tensors. A saved traced model may not accept Detectron2 `list[dict]` inputs directly.

Actions:

- Save or document the adapter's `inputs_schema` and `outputs_schema` behavior in the deployment wrapper.
- Test the traced model through tensor inputs first, then rebuild outputs with `outputs_schema` in Python validation.
- If `allow_non_tensor=True` was used, do not expect schemas to rebuild arbitrary new inputs; that mode is for a single trace path.

## Dynamic Batch and Resolution Mismatch

Symptoms include wrong output shape, trace check failure, or inference failures on a different number of images.

Actions:

- For tracing, keep the number of input images the same as the trace sample.
- Use scripting for supported models when dynamic batch is required.
- Use representative image sizes and test at least one different resolution if dynamic resolution matters.
- Avoid Caffe2 tracing for batch inference; it is not supported in the documented path.

## Raw Caffe2 Outputs Lack Post-Processing

Caffe2-format exports can produce raw tensors such as boxes, scores, classes, masks, or keypoint logits without Detectron2's final resizing and formatting. This is expected for lower-level deployment artifacts.

Actions:

- Compare outputs at the same boundary: raw graph outputs to raw expected outputs, or wrapper outputs to eager Detectron2 outputs.
- Use `Caffe2Model` as a Python reference wrapper when Caffe2 is available.
- Implement application-specific post-processing in the deployment application rather than assuming protobuf files return fully formatted predictions.

## Custom Ops Unsupported

Symptoms include missing torchvision custom ops, Caffe2 operator failures, ONNX custom op errors, or runtime inability to load the exported artifact.

Actions:

- For tracing/scripting TorchScript, ensure torchvision runtime operators are available in Python or C++.
- For Caffe2, ensure the model does not rely on operators missing in Caffe2, such as some deformable convolutions or custom extension ops.
- For ONNX, distinguish export success from runtime success; a graph can export but still be unusable in the target runtime.

## Benchmark Results Look Wrong

Benchmarks are sensitive to data, hardware, warmup, worker count, input shape, and model device.

Actions:

- Confirm the benchmark task matches the question: data, data-advanced, train, or eval.
- Confirm weights and dataset paths are valid and not silently falling back to empty or tiny workloads.
- Record GPU count, CPU count, RAM, batch size, workers, input image sizes, precision/AMP, and warmup behavior.
- Do not compare benchmark numbers across machines unless the environment is controlled.

## Demo CLI Caveat

Do not rely on the repository's demo CLI as a deployment-export runtime dependency. In this checked source state, that demo path imports a missing `vision.fair.detectron2.demo.predictor` module. Use deployment/export APIs and command-builder patterns instead.
