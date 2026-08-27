# Deployment and Inference Troubleshooting

## Fast recovery order

1. If the checkpoint is a Torch pickle and you do not trust the source, do **not** open the trust gate. Prefer ONNX or OpenVINO instead.
2. If you need OpenVINO export, check whether `openvino`, `onnxscript`, and `nncf` are installed.
3. If you want INT8 PTQ or INT8 ACQ, confirm that a datamodule is available.
4. If you only need runtime prediction, prefer `Engine.predict(...)` over the legacy Torch inferencer.

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Torch checkpoint load fails with a trust error | `TRUST_REMOTE_CODE` is unset | Only for trusted checkpoints, set `TRUST_REMOTE_CODE=1`; otherwise export to ONNX or OpenVINO. |
| Torch inference feels unsafe or too indirect | Legacy checkpoint replay is pickle-based | Use `Engine.predict(...)` for new work or switch to exported runtime formats. |
| `OpenVINOInferencer` cannot import | `openvino` is missing | Install `anomalib[openvino]` or the `openvino` package. |
| ONNX export with `dynamo=True` fails on `onnxscript` | Optional dependency missing | Install `anomalib[openvino]` or `onnxscript`, or export with `dynamo=False`. |
| INT8 PTQ / INT8 ACQ export fails | No datamodule was provided | Pass a datamodule with calibration and validation loaders. |
| INT8 ACQ export warns about `max_drop` | `max_drop` is outside the usual small range or not relevant to the chosen compression | Keep `max_drop` in `[0, 1]` and use it only with `INT8_ACQ`. |
| OpenVINO export or quantization fails on compression | `nncf` is missing | Install `anomalib[openvino]` or `nncf`. |
| OpenVINO helper leaves files in the working directory | `openvino_cache/` is created automatically | Run in a temp directory or remove the cache after debugging. |
| Gradio helper is unavailable | Optional UI dependency not installed | Treat `tools/inference/gradio_inference.py` as reference-only unless you need the UI path. |

## Trust model

- `TorchInferencer` loads a pickled model object from the checkpoint.
- Only set `TRUST_REMOTE_CODE=1` for checkpoints you own or otherwise trust.
- If the checkpoint source is untrusted, the safe recovery path is to export to ONNX or OpenVINO and deploy that artifact instead.

## Quantization notes

- `FP16` and `INT8` do not need calibration data.
- `INT8_PTQ` needs a datamodule because it uses the validation loader for calibration.
- `INT8_ACQ` also needs a datamodule and may use a default image-level F1 metric if none is supplied.
- A missing datamodule is a configuration issue, not a dependency issue.

## Input-shape and path notes

- `Engine.predict` can consume a dataset, datamodule, `data_path`, or explicit dataloaders.
- `OpenVINOInferencer` accepts `.xml`, `.bin`, or `.onnx`; if you pass `.bin`, the matching `.xml` must exist beside it.
- The `basic_torch_inference.py` source example is only a stub in this checkout, so do not use it as a working recipe.
