# YOLOX Inference Troubleshooting

## First checks

```bash
python scripts/yolox_inference_smoke.py --name yolox-nano --device auto --test-size 64
python -c "import yolox, torch, cv2; print(yolox.__version__, torch.cuda.is_available(), cv2.__version__)"
```

Run the smoke helper from the sub-skill directory, or adjust the script path accordingly.

## Failure matrix

| Symptom | Likely cause | Fix |
|---|---|---|
| `No module named 'yolox'` | YOLOX is not installed in the active Python. | Install YOLOX in the environment used for inference. |
| Checkpoint file missing | Pretrained weights were not downloaded or path is wrong. | Supply an existing checkpoint path; do not run real inference without weights. |
| `Missing key` / `Unexpected key` / size mismatch | Checkpoint and `Exp` disagree. | Match `--name`/`--exp-file`, `num_classes`, depth/width, and depthwise settings. |
| Old weights produce poor results unless `--legacy` is used | Preprocessing changed between old and current YOLOX. | Use `--legacy` for PyTorch demo/eval with old weights. Deployment demos do not support those old weights. |
| CUDA requested but unavailable | CPU-only torch, driver mismatch, or hidden GPU. | Use `--device cpu` for smoke checks or install/use a CUDA-capable torch runtime. |
| FP16 error | `--fp16` on CPU or unsupported CUDA. | Drop `--fp16` unless using compatible CUDA. |
| OpenCV cannot read image/video | Bad path, unsupported codec, missing permissions, or corrupt file. | Validate `cv2.imread`/`VideoCapture` before model work; use a supported codec. |
| GUI/window error in headless runtime | `cv2.imshow` needs a display. | Use `--save_result` or write images/video directly. |
| `--trt` assertion or missing `model_trt.pth` | TensorRT mode requires prior conversion. | Route to export/deployment and create the TensorRT artifact first. |
| Class names do not match outputs | Using COCO class names with custom dataset. | Provide class names matching the custom `Exp`/checkpoint, or avoid labeling with COCO names. |
| NMS/operator error | Torch/torchvision mismatch. | Install matching torch and torchvision builds for the same CPU/CUDA variant. |

## Debug order

1. Verify imports and device with the bundled smoke helper.
2. Resolve the experiment and print `exp.num_classes`, `depth`, `width`, and `test_size`.
3. Validate checkpoint existence and source model family.
4. Validate image/video input separately with OpenCV.
5. Only then run full inference.
