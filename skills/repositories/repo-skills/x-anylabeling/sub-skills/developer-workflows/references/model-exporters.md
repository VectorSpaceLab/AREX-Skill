# ONNX exporter utilities

X-AnyLabeling includes a set of model-export and ONNX Runtime demo utilities for selected model families. Treat them as reference-only development evidence unless the user explicitly provides the matching external repository, checkpoint weights, device, and export acceptance criteria.

These utilities are not the same as the post-training Ultralytics export button. For trained Ultralytics checkpoints, use `references/training-workflows.md` and route custom model loading to `../auto-labeling-models/SKILL.md` after export.

## Why reference-only

Most exporter utilities assume one or more of the following:

- An external model repository checked out separately.
- External checkpoint weights already downloaded.
- A repository-specific Python path or package installation.
- Torch and model-family-specific dependencies.
- GPU/CUDA, TensorRT, or large-memory CPU execution.
- Manual code patches in the upstream model before export.
- Local image files for inference demos.

Those assumptions were not verified during this skill construction. Do not present these utilities as turnkey scripts in a clean X-AnyLabeling package environment.

## Exporter inventory

| Utility | Model family | Main role | Key prerequisites and cautions |
|---|---|---|---|
| `export_deimv2_onnx.py` | DEIMv2 / DINOv3 object detection | ONNX Runtime inference demo after ONNX export | Requires a DEIMv2-exported ONNX model; documented upstream export commands assume external configs and checkpoints. |
| `export_dfine_onnx.py` | D-FINE object detection | ONNX Runtime demo | Uses hard-coded example paths in the utility; assumes D-FINE repo install and exported ONNX weights. |
| `export_geco_onnx.py` | GeCo few-shot object counting | ONNX export plus ONNX Runtime wrapper | Requires external GeCo code, Torch, ONNX, checkpoint file, and optional quantization support; `--device` choices are `cpu`/`gpu`. |
| `export_grounding_dino_onnx.py` | Grounding DINO | ONNX export and prompt-based validation | Requires external GroundingDINO code, config, checkpoint, text prompt, Torch/ONNX, and optional quantization. |
| `export_internimage_model_onnx.py` | InternImage | ONNX Runtime demo | Assumes external InternImage export process and model files; example paths are placeholders. |
| `export_pulc_attribute_model_onnx.py` | PaddleClas PULC attributes | ONNX Runtime demo by task | Requires PaddleClas export steps and task-specific model. |
| `export_recognize_anything_model_onnx.py` | Recognize Anything Model (RAM) | ONNX export and demo | Requires external RAM code and code adaptation before export, plus checkpoint and tag lists. |
| `export_rfdetr_onnx.py` | RF-DETR detection | ONNX Runtime demo | Requires external rf-detr install and exported ONNX weights; example paths are placeholders. |
| `export_rfdetr_seg_onnx.py` | RF-DETR instance segmentation | ONNX Runtime demo | Same external assumptions as RF-DETR detection, with segmentation output handling. |
| `export_sam3_onnx.py` | SAM 3 | Thin wrapper around `samexporter` | Requires a `samexporter` checkout/toolkit and produces multiple ONNX files with external `.onnx.data` sidecars. |
| `export_scrfd_onnx_demo.py` | SCRFD face detection with landmarks | ONNX Runtime inference demo | Has a normal CLI for model/image/output; requires an existing SCRFD ONNX model and image. |
| `export_u_rtdetr_onnx.py` | Ultralytics RT-DETR | ONNX Runtime demo | Assumes external Ultralytics package/source and exported model. |
| `export_yolov10_onnx.py` | YOLOv10 | ONNX Runtime demo | Requires external YOLOv10 install and exported ONNX weights. |
| `export_yolov8_obb_onnx.py` | YOLOv8 OBB | ONNX Runtime demo | Requires external Ultralytics install and an OBB ONNX model. |
| `export_yolow_onnx.py` | YOLO-World | ONNX Runtime demo | Requires external YOLO-World source/package and exported model. |

## Common ONNX Runtime interpretation pattern

The demo utilities usually implement some combination of:

1. Read an image with PIL or OpenCV.
2. Resize and pad to a model-specific square input.
3. Convert to `float32` NCHW tensor.
4. Create `onnxruntime.InferenceSession(model_path)`.
5. Run inference with model-specific input names.
6. Decode boxes, scores, masks, labels, or prompts.
7. Draw output to an image or print detections.

Use this pattern to understand output expectations or write a clean task-specific reproducer, but do not assume one model family's preprocessing works for another.

## Safe use checklist

Before attempting any exporter utility:

- Identify the exact model family and whether the task is export or inference-demo only.
- Ask the user for the external repository/package status if the utility depends on one.
- Ask for checkpoint/ONNX paths and a tiny input image.
- Confirm whether CPU is sufficient or whether CUDA/GPU is required.
- Confirm whether network downloads are allowed.
- Keep generated ONNX files, sidecars, and demo outputs in user-approved output directories.
- Do not mutate upstream model source unless the user explicitly approves the required patch.

## Routing after export

After a model is exported and the user wants to use it inside X-AnyLabeling:

- Route model config and custom adapter questions to `../auto-labeling-models/SKILL.md`.
- Route annotation data needed for validation to `../annotation-ui/SKILL.md`.
- Route conversion of labels used for training/evaluation to `../conversion-cli/SKILL.md`.
