# DAMO-YOLO workflows

This reference is the root route map. Use it when you need the high-level shape of the repo before opening a focused sub-skill.

## Workflow map

| User goal | Sub-skill | Bundled helpers | Notes |
|---|---|---|---|
| Train, fine-tune, resume, evaluate, distill, or validate a COCO config | `training` | `launch_train.sh`, `launch_eval.sh`, `validate_coco_config.py` | Requires CUDA/NCCL for the real training/eval path. Use `--workdir` when configs read relative TinyNAS structure files. |
| Run image, video, or camera demos on Torch/ONNX/TensorRT engines | `inference` | `damo_yolo_safe_demo.py` | Torch can fall back to CPU; ONNX Runtime and TensorRT need their own optional runtimes. |
| Export ONNX, inspect deployment backends, or plan TensorRT/INT8 workflows | `deployment` | `check_deploy_env.py`, `export_onnx_safe.py` | Use this route before trying engine builds, ONNX Runtime NMS, or partial quantization. |
| Sanity-check the installed package, config, and model build before a longer run | root + chosen sub-skill | `check_model_smoke.py` | Good for quick environment validation when the user is unsure which route will work. |

## Common command shapes

### Training and evaluation

```bash
sub-skills/training/scripts/validate_coco_config.py --config /path/to/config.py --workdir /path/to/assets
sub-skills/training/scripts/launch_train.sh --config /path/to/config.py --workdir /path/to/assets --gpus 8
sub-skills/training/scripts/launch_eval.sh --config /path/to/config.py --ckpt /path/to/checkpoint.pth --workdir /path/to/assets --gpus 8
```

### Demo inference

```bash
python sub-skills/inference/scripts/damo_yolo_safe_demo.py image \
  -f /path/to/config.py \
  --engine /path/to/checkpoint.pth \
  --path /path/to/image.jpg \
  --infer-size 640 640
```

### Deployment and export

```bash
sub-skills/deployment/scripts/check_deploy_env.py
sub-skills/deployment/scripts/export_onnx_safe.py \
  -f /path/to/config.py \
  -c /path/to/checkpoint.pth \
  --output /path/to/model.onnx \
  --workdir /path/to/assets
```

## Route selection reminders

- Use training when the task needs dataset registration, COCO annotation validation, class-count alignment, or distributed launch.
- Use inference when the task already has an engine artifact and only needs to run or troubleshoot demos.
- Use deployment when the task produces a portable graph or engine, or when the optional backend stack needs diagnosis.
- Keep `--workdir` in mind whenever a config reads relative structure text or relative dataset paths.
