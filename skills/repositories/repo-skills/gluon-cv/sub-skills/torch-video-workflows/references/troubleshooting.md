# Torch video troubleshooting

## Import and version failures

### `Unable to import dependency pytorch` or `ModuleNotFoundError: torch`

Install a PyTorch build before importing `gluoncv.torch`. GluonCV's version guard expects PyTorch `>=1.4,<2.0`; Torch 2.x may be rejected by `gluoncv.check._require_pytorch_version` even if it imports normally outside GluonCV.

Quick triage:

```bash
python - <<'PY'
import torch
print(torch.__version__)
print(torch.cuda.is_available())
PY
```

If a user only needs CPU sanity checks, choose a CPU PyTorch wheel and keep CUDA/DDP workflows optional.

### Missing `torchvision`

`gluoncv.torch` imports Torch data/transforms modules that can require `torchvision`. Match `torchvision` to the installed Torch version; mismatched Torch/TorchVision wheels often fail at import or operator registration time.

### `AttributeError: module 'PIL.Image' has no attribute 'LINEAR'`

This legacy GluonCV Torch code references `PIL.Image.LINEAR`, which was removed in newer Pillow. Use `Pillow<10` for this repository stack.

### Missing `decord`

`decord` is an optional video decoding dependency used by video dataset/script workflows. It is not needed for the bundled synthetic model smoke script, but it is often needed for real action-recognition datasets, feature extraction, or inference from video files.

## Model/config failures

### `ValueError: "..." is not among the following model list`

The Torch model zoo looks up `cfg.CONFIG.MODEL.NAME.lower()` in the registry. Fix spelling, case, and family suffixes, or run:

```bash
python sub-skills/torch-video-workflows/scripts/torch_video_model_smoke.py --list-models
```

Then set `cfg.CONFIG.MODEL.NAME` to an exact registry name.

### Wrong output class count

Set `cfg.CONFIG.DATA.NUM_CLASSES` to the selected dataset/head size before constructing the model. Common values:

- Kinetics-400: `400`
- Something-Something-V2 examples: `174`
- Kinetics-700 examples: `700`
- Custom classifier: your class count, and use a `_custom` model name when appropriate.

If the checkpoint/classifier head was trained with a different class count, loading can fail with shape mismatches.

### Pretrained downloads or cache failures

Keep `cfg.CONFIG.MODEL.PRETRAINED = False` for dry-runs. Setting it to `True` can invoke model-zoo weight lookup/download and may require network access or an existing cache. DirectPose demos also default to pretrained behavior in some source flows.

### I3D inflation / `PRETRAINED_BASE`

Some I3D builders require `cfg.CONFIG.MODEL.PRETRAINED_BASE = True` for 2D-to-3D inflation. If you disable it and the builder reports that I3D needs inflation, restore `PRETRAINED_BASE=True` or choose a non-I3D smoke model.

## Tensor shape failures

Action-recognition Torch models expect `[N, C, T, H, W]`.

Common mistakes:

- Passing `[N, T, C, H, W]` from a video loader without permuting axes.
- Passing a 4D image tensor to a video classifier.
- Using `T=1` for a model family that expects longer clips.
- Using a small spatial size for a model/test pattern that was built around `224x224` or `112x112`.
- Setting `cfg.CONFIG.DATA.CLIP_LEN` to a value that disagrees with the actual tensor time dimension.

Start with the bundled `resnet18_v1b_kinetics400` CPU smoke. For heavier families, increase frames/spatial size only after the model instantiates successfully.

## CUDA and DDP failures

### `--cuda` requested but CUDA is unavailable

The bundled smoke helper only moves the model/tensor to CUDA when `torch.cuda.is_available()` is true. A host with GPUs still needs a CUDA-enabled PyTorch build; CPU-only wheels report CUDA unavailable.

### NCCL/backend errors

The default DDP config uses `DIST_BACKEND='nccl'`, which is for CUDA distributed training. CPU-only environments should not use NCCL. Treat DDP as optional unless the user provides a working CUDA/distributed runtime.

### Rank, URL, and IP assertions

`spawn_workers` uses fields under `cfg.DDP_CONFIG`:

- `WORLD_SIZE`, `WORLD_RANK`
- `GPU_WORLD_SIZE`, `GPU_WORLD_RANK`
- `DIST_URL`
- `WOLRD_URLS` (source spelling)
- `AUTO_RANK_MATCH`
- `DISTRIBUTED`

If `AUTO_RANK_MATCH=True`, the local machine IP must appear in `WOLRD_URLS`, and the first URL must match `DIST_URL`; otherwise the helper can assert before launching workers. For single-node experiments, make these fields match the actual visible GPU count and address. For CPU sanity checks, avoid DDP entirely.

## Script workflow failures

- `train_ddp_pytorch.py` and `test_ddp_pytorch.py` require real annotation files, frame/video roots, and distributed/GPU settings. Use this sub-skill to validate model/config facts, then route full command building to `../training-evaluation-scripts/`.
- `feat_extract_pytorch.py` assumes real video data and originally moves the model to CUDA. Adapt with caution for CPU and expect slow runtime.
- `get_flops.py` requires `thop` and uses a synthetic tensor. FLOPS are shape-dependent.
- `get_fps.py` is a CUDA throughput benchmark. Do not report GPU FPS from a CPU-only environment.
- DirectPose demo/export scripts require image inputs, pose-specific config, optional downloads, and sometimes TVM; keep them reference-only unless those prerequisites are explicit.

## When to route elsewhere

- MXNet imports/model names: `../mxnet-model-zoo/`.
- Dataset/frame list, annotation, and transform layout: `../data-transforms-datasets/`.
- Full train/test/infer command templates: `../training-evaluation-scripts/`.
