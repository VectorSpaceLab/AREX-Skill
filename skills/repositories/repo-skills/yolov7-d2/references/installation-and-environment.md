# Installation and Environment Guidance

YOLOv7-d2 is an older Detectron2-based ML repository with minimal package metadata. Treat dependency setup as a compatibility task rather than a plain `pip install`.

## Package names

- Distribution: `yolov7_d2` / PyPI spelling commonly shown as `yolov7-d2`.
- Import package: `yolov7`.
- Version in the distilled source: `0.0.3`.
- Core framework: PyTorch + Detectron2.

## Practical install order

1. Choose a Python version supported by the user's Detectron2/PyTorch stack. Python 3.10 was verified for skill construction; avoid assuming Python 3.13 works for compiled ML dependencies.
2. Install PyTorch and torchvision for the user's backend.
3. Install Detectron2 for the exact PyTorch/CUDA or CPU stack. Detectron2 is the dependency most likely to require version-specific installation commands.
4. Install YOLOv7-d2 and workflow packages.

Example shape:

```bash
python -m pip install torch torchvision
python -m pip install detectron2
python -m pip install yolov7-d2 timm nbnb omegaconf pycocotools scipy alfred-py wandb
```

If the user is operating a local checkout, install it in editable mode from that checkout after framework dependencies are ready:

```bash
python -m pip install -e .
```

## Dependencies to know

- `detectron2`: required for configs, model registry, training, inference, evaluation.
- `torch`, `torchvision`: required by every model workflow.
- `timm`: imported by backbone/model modules.
- `nbnb`: listed by the repository and used by model blocks.
- `alfred-py`: used by visualization, logger, checkpoint, and YOLO loss helper imports. Some newer `alfred-py` releases removed modules needed by this source; if `alfred.dl.metrics` or `alfred.logger` imports fail, try an older compatible `alfred-py` release from the 2.x line.
- `pycocotools`: needed for COCO annotations and mask/evaluation utilities. The repository requirements name `mmpycocotools`; modern environments often use `pycocotools` successfully.
- `scipy`: required by DETR matching imports.
- `wandb`: imported unconditionally by the training logger module even when W&B is disabled.
- `onnx`, `onnxsim`, `onnxruntime`: needed for export/deployment workflows, not for basic config inspection.

## Backend policy

CPU is sufficient for:

- Import checks.
- `add_yolo_config` checks.
- Config merge/preflight.
- CLI `--help` checks.
- COCO JSON validation and anchor clustering helpers.

CUDA/GPU is required or strongly expected for:

- Real training runs.
- Real model inference with production-sized configs/weights.
- Speed/FPS benchmarking.
- Some ONNX export validation and model-specific kernels.

TensorRT and quantization require separate toolchains and artifacts. Do not present them as verified just because PyTorch CUDA imports.

## Minimal smoke check

Use the root helper:

```bash
python scripts/smoke_import_and_config.py --config path/to/config.yaml
```

Expected signal: package imports, `add_yolo_config` succeeds, and the optional config summary shows a valid `MODEL.META_ARCHITECTURE`, dataset names, and output directory.
