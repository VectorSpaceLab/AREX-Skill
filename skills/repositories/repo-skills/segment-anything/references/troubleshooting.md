# Troubleshooting

## Purpose

Use this for cross-cutting Segment Anything failures. Workflow-specific details live in each sub-skill's `references/troubleshooting.md`.

## Import or Install Fails

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: segment_anything` | Package is not installed in the active Python. | Install the package, then run `scripts/check_environment.py`. |
| `ModuleNotFoundError: torch` or `torchvision` | Backend packages are not installed. | Install PyTorch/TorchVision for the target CPU/CUDA platform. |
| Optional imports such as `cv2`, `pycocotools`, `onnx`, or `onnxruntime` fail | Workflow extras are missing. | Install only the optional package needed for the selected sub-skill. |
| `pip check` reports dependency conflicts | Mixed package indexes or incompatible wheels. | Reinstall the backend stack consistently before debugging SAM code. |

## Checkpoint and Model Type Problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `KeyError` for `sam_model_registry[model_type]` | Unsupported model key. | Use `default`, `vit_h`, `vit_l`, or `vit_b`. |
| Missing/unexpected keys during checkpoint load | Checkpoint file does not match model type. | Pair `vit_b` with the ViT-B checkpoint, `vit_l` with ViT-L, and `vit_h/default` with ViT-H. |
| `FileNotFoundError` while building SAM | Checkpoint path is wrong or not mounted. | Ask the user for a local `.pth` checkpoint path; the package does not download checkpoints automatically. |

## Device and Memory Problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| CUDA requested but unavailable | CPU-only PyTorch, hidden GPU, or driver/wheel mismatch. | Check `torch.cuda.is_available()` and pass `--device cpu` when needed. |
| GPU out of memory | Large checkpoint, image, batch size, AMG grid, crop layers, or binary mask output. | Try `vit_b`, smaller images, lower `points_per_batch`, lower `points_per_side`, fewer crop layers, or CPU for debugging. |
| Very slow CPU inference | SAM is compute-heavy, especially ViT-H. | Use CPU only for small diagnostics; recommend CUDA for production throughput. |

## Image and Data Problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Poor masks or color-inverted behavior | RGB/BGR mismatch. | Use `image_format="BGR"` for raw OpenCV arrays or convert to RGB before `set_image`. |
| Shape assertions or transform errors | Image is not `H x W x 3` uint8 or prompts use wrong shape/order. | Read `references/data-formats.md` and validate image/prompt arrays before calling APIs. |
| Empty automatic mask results | Thresholds too strict or image/checkpoint mismatch. | Lower `pred_iou_thresh`/`stability_score_thresh`, verify image loading, and test a smaller model first. |

## Where to Go Next

- Prompt shape and iterative refinement failures: `../sub-skills/prompted-segmentation/references/troubleshooting.md`.
- AMG optional dependency, output, and memory failures: `../sub-skills/automatic-mask-generation/references/troubleshooting.md`.
- ONNX export, quantization, and browser failures: `../sub-skills/onnx-and-browser/references/troubleshooting.md`.
