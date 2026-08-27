# ONNX and TorchScript Export

YOLOv7-d2's source export pattern loads a Detectron2 config, builds the model, loads `MODEL.WEIGHTS`, creates a sample image tensor, sets `model.onnx_export = True`, calls `torch.onnx.export`, simplifies with `onnxsim`, and then optionally traces TorchScript.

## Command shape

```bash
python export.py \
  --config-file path/to/config.yaml \
  --input path/to/sample.jpg \
  --verbose \
  --opts MODEL.WEIGHTS path/to/model.pth MODEL.DEVICE cpu
```

The source writes outputs under a `weights/` directory using the checkpoint basename, such as `model_final.onnx`, `model_final_sim.onnx`, and possibly `model_final.pt`.

## Preconditions

- The config must merge successfully after `add_yolo_config`.
- `MODEL.WEIGHTS` must point to a real checkpoint or supported URL.
- A sample image file is required; the source asserts that `--input` is a file.
- Install `onnx`, `onnxsim`, and any model-specific PyTorch/Detectron2 dependencies.
- Ensure the desired device is set consistently; export may be easier to debug on CPU but model-specific ops may differ.

## Output names by model family

The source helper chooses output names based on the config path:

- SparseInst configs: `masks`, `scores`, `labels` with input `images` and dynamic batch axis.
- DETR configs: intended names `boxes`, `scores`, `labels`.
- Other configs: one output named `outs`.

## Known source caveat

The DETR graph surgery helper calls `gs.import_onnx` and `gs.export_onnx` but the source export file does not import `onnx_graphsurgeon as gs`. If the user's DETR export reaches this path, install/import `onnx-graphsurgeon` and patch the local export script, or skip that postprocessing step and inspect the ONNX output manually.

## Validation after export

Run:

```bash
python scripts/inspect_onnx_model.py path/to/model.onnx --providers
```

Do not assume successful export means postprocessing is correct. Compare input layout, output names/shapes, score thresholds, and NMS/postprocess code against the intended deployment runtime.
