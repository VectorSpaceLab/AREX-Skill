# AdelaiDet model and workflow overview

Use this file to choose the right sub-skill and config family before launching a job.

## Public model families

| Family | Main task | Typical config root | Route | Notes |
| --- | --- | --- | --- | --- |
| FCOS | Anchor-free object detection | `configs/FCOS-Detection/` | `train-eval`, `demo-visualize`, `export-convert` | Core detector and proposal generator used by several families. |
| BlendMask | Instance segmentation | `configs/BlendMask/` | `train-eval`, `demo-visualize` | Combines FCOS-style detection with basis masks and attention. |
| CondInst | Conditional convolution instance segmentation | `configs/CondInst/` | `train-eval`, `demo-visualize`, `export-convert` | Often paired with BoxInst weak supervision variants. |
| BoxInst | Box-supervised instance segmentation | `configs/BoxInst/` | `train-eval`, `data-prep` | Needs box-supervised setup and image color pairwise settings. |
| SOLOv2 | Instance segmentation | `configs/SOLOv2/` | `train-eval`, `demo-visualize` | Uses SOLOv2 mask head and may require OpenCV helpers. |
| BAText / ABCNet | Text spotting / scene text detection and recognition | `configs/BAText/` | `text-spotting`, `train-eval`, `demo-visualize` | Uses Bezier curves, BezierAlign, TextEvaluator, dictionaries/lexicons. |
| MEInst | Mask encoding instance segmentation | `configs/MEInst-InstanceSegmentation/` | `train-eval`, `data-prep`, `export-convert` | May require PCA mask-component generation under `MEInst/LME`. |
| FCPose | Keypoint/person pose | `configs/FCPose/` | `train-eval`, `data-prep` | Uses COCO person data preparation and FCOS-style proposals. |
| DenseCL | Self-supervised pretraining support | `configs/DenseCL/` | `train-eval` | Treat as specialized training/config support rather than demo/export first. |

## Common config patterns

AdelaiDet config files extend Detectron2 configs and add `adet.config.add_adet_config` defaults. Always merge configs through `adet.config.get_cfg()` or a launcher that calls it before `merge_from_file`.

Common override examples:

```bash
MODEL.WEIGHTS /path/to/model.pth
OUTPUT_DIR output/adet-run
SOLVER.IMS_PER_BATCH 16
MODEL.FCOS.NUM_CLASSES 80
MODEL.BATEXT.CUSTOM_DICT path/to/dict.txt
MODEL.DEVICE cuda
```

Do not assume every family has the same keys. Read the family README/reference and inspect the target YAML before using overrides.

## Route decision quick checks

- **Install/build/import failure** → `setup-build`.
- **Which config should I use or how do I train/evaluate it?** → `train-eval`.
- **Run a picture/video/webcam demo or visualize dataset records** → `demo-visualize`.
- **Any task mentioning text spotting, ABCNet, BAText, Bezier curves, lexicons, or `TextEvaluator`** → `text-spotting`.
- **Dataset directory layout, annotation conversion, semantic masks, or MEInst components** → `data-prep`.
- **Checkpoint key migration, stripped checkpoints, ONNX export, or deployment conversion** → `export-convert`.

## Runtime risk levels

| Activity | Safe first check | Needs external data/weights? | Notes |
| --- | --- | --- | --- |
| Import/config/custom-op smoke | `scripts/check_install.py --cuda-ops` | No | Required before CUDA tasks. |
| CLI parser check | `--help` through wrappers | No | Confirms imports and parser wiring. |
| Demo inference | `demo-visualize` wrapper dry run | Yes | Needs config, weights, and images/video/webcam. |
| Training/evaluation | `train-eval` wrapper dry run | Yes | Needs dataset registration and model-specific config. |
| Dataset preparation | `data-prep` dry run | Yes | Needs COCO/PIC/LVIS/text annotation files. |
| ONNX export | `export-convert` wrapper dry run | Usually | Needs config and checkpoint; runtime comparison needs optional runtimes. |
