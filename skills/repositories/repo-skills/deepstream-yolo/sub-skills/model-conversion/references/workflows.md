# Export and conversion workflow

The commands below assume the generated skill root is the current working directory.

## 1. Choose the family first

- Match the checkpoint to the family matrix.
- Use the bundled script only for the Ultralytics-family exporters that were inspected here.
- For other families, treat the matrix as a routing guide and follow the upstream repo requirements in the reference-only notes.

## 2. Prepare the exporter environment

The verified inspection environment contains:

- Python 3.11
- `torch`
- `ultralytics`
- `onnx`
- `onnxslim`
- `onnxruntime`

That is enough to inspect the bundled Ultralytics-family exporters and to run their CLI help or tiny export smoke tests.

## 3. Run the exporter

Common flags:

- `-w / --weights` — required input checkpoint.
- `-s / --size` — input resolution, either one number or `H W`.
- `--dynamic` — dynamic batch export.
- `--batch` — static batch size.
- `--simplify` — ONNX simplification step.
- `--opset` — ONNX opset version.

Example pattern for the bundled YOLOv8-family path:

```bash
python sub-skills/model-conversion/scripts/export_yoloV8.py -w yolov8s.pt --dynamic
```

## 4. Check the outputs

A successful export should produce:

- the ONNX file next to the checkpoint name, and
- `labels.txt` when the model metadata includes class names.

Copy those artifacts into the DeepStream deployment folder and pair them with the matching config template.

## 5. Route the result back to deployment

After export:

- use `deployment` to choose the matching `config_infer_primary*.txt`, and
- confirm the `onnx-file` and label count line up with the generated files.

## 6. When export fails

- Missing dependency: install the exporter's required Python stack.
- Missing labels: rerun the exporter from the intended checkpoint directory.
- Wrong family: switch to the family matrix rather than forcing a mismatched script.
- Legacy upstream repo: check the reference-only notes and install that repo's documented stack.
