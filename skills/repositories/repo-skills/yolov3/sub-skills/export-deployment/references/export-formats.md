# Export Formats Reference

`export.py:export_formats()` lists suffixes used by export and by `DetectMultiBackend` detection. The implemented `--include` export choices are `torchscript`, `onnx`, `openvino`, `engine`, `coreml`, and `paddle`.

| Format | Include arg | Suffix | CPU | GPU | Notes |
| --- | --- | --- | --- | --- | --- |
| PyTorch | source `.pt` | `.pt` | yes | yes | Input checkpoint, not an export target. |
| TorchScript | `torchscript` | `.torchscript` | yes | yes | Best portable smoke export. |
| ONNX | `onnx` | `.onnx` | yes | yes | Optional `onnx`; `--simplify` needs simplifier deps. |
| OpenVINO | `openvino` | `_openvino_model` | yes | no | Requires OpenVINO packages. |
| TensorRT | `engine` | `.engine` | no | yes | CUDA-only; do not run on CPU. |
| CoreML | `coreml` | `.mlmodel` | yes | no | Uses `coremltools`; macOS is the natural runtime target. |
| PaddlePaddle | `paddle` | `_paddle_model` | yes | yes | Requires Paddle/x2paddle stack. |
| TensorFlow family | not implemented by this repo | multiple | varies | varies | Rows remain for suffix detection of externally produced models. |

## Safe format inspection

```bash
python sub-skills/export-deployment/scripts/yolov3_export_format_matrix.py --format table
python sub-skills/export-deployment/scripts/yolov3_export_format_matrix.py --include torchscript onnx --strict --format json
```

`--strict` returns an error for entries such as `saved_model`, `pb`, `tflite`, `edgetpu`, and `tfjs` because this repo does not export TensorFlow formats.

## Native export smoke

Run only when weights are present or download is approved:

```bash
python export.py --weights yolov3-tiny.pt --img 64 --include torchscript --device cpu
```

After export, `export.py` prints matching detect, validate, Hub custom-load, and Netron visualization hints.
