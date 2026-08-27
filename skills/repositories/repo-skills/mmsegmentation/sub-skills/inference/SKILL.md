---
name: inference
description: "Run MMSegmentation semantic segmentation and depth inference from
  configs, checkpoints, or model aliases, with safe visualization, saved masks,
  device selection, and remote-sensing prerequisites."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Inference

Use this sub-skill when an agent needs to run MMSegmentation inference on images, image batches, videos, or tiled remote-sensing rasters from an existing model. It covers the high-level `MMSegInferencer` path, the lower-level `init_model` / `inference_model` / `show_result_pyplot` path, and the remote-sensing `RSImage` / `RSInferencer` concepts.

## Choose the entry point

- Prefer `MMSegInferencer` when the user gives a model alias, a config path plus optional weights, wants one-call outputs, or needs saved visualization and predicted masks under an output directory.
- Prefer `init_model` + `inference_model` when the user needs direct access to `SegDataSample`, custom Python control flow, video-frame loops, or explicit `show_result_pyplot` rendering.
- Use `RSImage` + `RSInferencer` only for geospatial/tiled remote-sensing images after confirming `GDAL`/`osgeo` is installed and the model config/checkpoint are local.
- For dataset conversion or config authoring, route to `../data-configuration/SKILL.md`; for training or evaluation launch, route to `../training-evaluation/SKILL.md`; for custom model code, route to `../model-customization/SKILL.md`.

## Fast starts

### Safe import/signature smoke checks

Run these without model downloads or checkpoint loading:

```bash
python sub-skills/inference/scripts/mmseg_inference_smoke.py --help
python sub-skills/inference/scripts/mmseg_inference_smoke.py
python sub-skills/inference/scripts/mmseg_inferencer_smoke.py --help
python sub-skills/inference/scripts/mmseg_inferencer_smoke.py
```

### Config/checkpoint image inference

Use local files for deterministic behavior:

```bash
python sub-skills/inference/scripts/mmseg_inference_smoke.py \
  --config PATH/TO/MMSEG_CONFIG.py \
  --checkpoint PATH/TO/CHECKPOINT.pth \
  --image PATH/TO/IMAGE.png \
  --device cpu \
  --out-file outputs/demo_overlay.png
```

The script sets `show=False` whenever `--out-file` is provided, so it is safe for headless sessions.

### Inferencer one-call outputs

Use a local config and local weights unless the user explicitly allows model-alias downloads:

```bash
python sub-skills/inference/scripts/mmseg_inferencer_smoke.py \
  --model PATH/TO/MMSEG_CONFIG.py \
  --weights PATH/TO/CHECKPOINT.pth \
  --image PATH/TO/IMAGE.png \
  --device cpu \
  --out-dir outputs/inferencer
```

`out_dir` saves color overlays under `vis/` and predicted label-index masks under `pred/`.

## Reference map

- `references/api-reference.md` documents callable signatures, return objects, labels/palettes, devices, and saved-output behavior.
- `references/workflows.md` gives image, batch, video, headless, and remote-sensing workflows.
- `references/deployment.md` summarizes when to switch from PyTorch inference to MMDeploy/runtime inference.
- `references/troubleshooting.md` covers missing checkpoints, downloads, headless display, CPU/CUDA, GDAL, MMCV, and dependency compatibility.
