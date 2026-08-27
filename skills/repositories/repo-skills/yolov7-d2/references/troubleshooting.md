# Cross-Cutting Troubleshooting

## Import fails before the task starts

Symptom: `ModuleNotFoundError: detectron2`.

Likely cause: Detectron2 is not installed for the user's PyTorch/Python/CUDA combination. Install Detectron2 first using the command matching the local PyTorch backend.

Symptom: `ModuleNotFoundError: timm`, `nbnb`, `pycocotools`, `omegaconf`, `scipy`, `wandb`, `onnx`, or `onnxruntime`.

Likely cause: repository metadata does not fully declare all workflow dependencies. Install the missing package only if the selected workflow needs it.

Symptom: `No module named alfred.dl.metrics` or `cannot import name logger from alfred`.

Likely cause: `alfred-py` API drift. This source expects older `alfred-py` module layout. Try a 2.x `alfred-py` release and rerun the import/config smoke.

## Optional mish-cuda warning

Importing `yolov7` may print a recommendation to install `mish-cuda` for speed and memory savings. Treat it as optional unless the user is optimizing GPU training/inference. Do not make `mish-cuda` a basic import requirement.

## Config merge failures

- Verify `_BASE_` paths resolve on a case-sensitive filesystem.
- Call `add_yolo_config(cfg)` before merging YOLOv7-d2 YAML configs.
- Check `MODEL.META_ARCHITECTURE` routes to an available registered architecture.
- Make sure `DATASETS.TRAIN` and `DATASETS.TEST` names are registered before training/evaluation.

## Dataset failures

Most repo configs assume COCO-style dataset names. For custom data, register COCO JSON/image roots using Detectron2's `register_coco_instances`, then align the config dataset names and class counts. Validate the JSON before launching training.

## Weight and checkpoint failures

YOLOv7-d2 configs often leave `MODEL.WEIGHTS` empty or point to user-downloaded weights. Confirm the file exists or the Detectron2 URL is valid. Do not download weights automatically unless the user explicitly asks.

## GUI/display failures

The original demo code uses OpenCV display windows when no output path is provided. In headless sessions, always write to an output file or directory, or use a bundled/helper script that prints predictions instead of opening a window.

## LazyConfig demo failure

The source `demo_lazyconfig.py` contains a module-level bare `q`, causing `NameError` before argument parsing. Remove that line in the user's working copy or use LazyConfig training/evaluation patterns instead. Do not diagnose this as a missing dependency.

## Backend scope

A CPU import/config check proves the package can be inspected; it does not prove GPU training, TensorRT, quantized inference, or throughput. Keep optional backend claims explicitly unverified unless the relevant hardware/toolchain/model artifacts are provided and checked.
