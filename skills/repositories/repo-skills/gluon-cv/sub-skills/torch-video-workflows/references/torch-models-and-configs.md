# Torch models and configs

## Verified API facts

- Import path: `gluoncv.torch.model_zoo`.
- Model constructor: `get_model(cfg)`, where `cfg.CONFIG.MODEL.NAME.lower()` selects the registered model.
- Registry helper: `get_model_list()` returns 48 Torch model names.
- Config helper: `gluoncv.torch.engine.config.get_cfg_defaults(name='action_recognition')` returns a cloned YACS config. Alternate roots are `coot` and `directpose`.
- Verified tiny CPU smoke: with `cfg.CONFIG.MODEL.NAME = 'resnet18_v1b_kinetics400'`, `cfg.CONFIG.MODEL.PRETRAINED = False`, `cfg.CONFIG.DATA.NUM_CLASSES = 400`, and input tensor shape `[1, 3, 1, 224, 224]`, the forward output shape is `(1, 400)`.

## Model registry families

The 48-name Torch registry includes these practical families:

| Family | Representative names | Notes |
| --- | --- | --- |
| ResNet video/action | `resnet18_v1b_kinetics400`, `resnet34_v1b_kinetics400`, `resnet50_v1b_kinetics400`, `resnet50_v1b_sthsthv2`, `resnet50_v1b_custom` | 2D-style action-recognition models; repo tests use `[N, 3, 1, 224, 224]` and multi-frame variants. |
| I3D | `i3d_resnet50_v1_kinetics400`, `i3d_resnet101_v1_kinetics400`, `i3d_nl5_resnet50_v1_kinetics400`, `i3d_nl10_resnet101_v1_kinetics400`, `i3d_resnet50_v1_sthsthv2`, `i3d_resnet50_v1_custom` | Usually expects longer clips such as 16 or 32 frames. Some I3D flows require `PRETRAINED_BASE=True` for inflation. |
| I3D slow | `i3d_slow_resnet50_f32s2_kinetics400`, `i3d_slow_resnet50_f16s4_kinetics400`, `i3d_slow_resnet50_f8s8_kinetics400`, corresponding ResNet-101 and Kinetics-700 variants | Names encode clip length/frame-rate style (`f32s2`, `f16s4`, `f8s8`). |
| SlowFast | `slowfast_4x16_resnet50_kinetics400`, `slowfast_8x8_resnet50_kinetics400`, `slowfast_16x8_resnet101_kinetics400`, `slowfast_16x8_resnet50_sthsthv2`, custom/feature variants | Large and often GPU-heavy; a CPU instantiation can validate config/name routing, but full speed/training claims need CUDA verification. |
| R(2+1)D | `r2plus1d_v1_resnet18_kinetics400`, `r2plus1d_v1_resnet50_kinetics400`, `r2plus1d_v2_resnet152_kinetics400`, custom variants | Repo tests use `[N, 3, 16, 112, 112]` for many R(2+1)D checks. |
| CSN / IRCSN | `ircsn_v2_resnet152_f32s2_kinetics400` | Heavy model; treat pretrained and full forward as optional unless resources are explicit. |
| TPN | `tpn_resnet50_f8s8_kinetics400`, `tpn_resnet50_f16s4_kinetics400`, `tpn_resnet50_f32s2_kinetics400`, ResNet-101 variants, custom/feature variants | Clip length in the name should match config/input time dimension. |
| DirectPose | `directpose_resnet50_lpf_fpn_coco` | Uses the `directpose` config root and image tensors, not `[N, C, T, H, W]` video tensors. Pretrained/demo flows may download weights or images. |
| COOT / video-language | `multimodaltransformer_coot` | Uses the `coot` config root and a multi-module video/text transformer object; do not treat it like a simple `torch.nn.Module` video classifier. |

## Config creation pattern

Use YACS config nodes and set model/data fields before calling `get_model(cfg)`:

```python
import torch
from gluoncv.torch.engine.config import get_cfg_defaults
from gluoncv.torch.model_zoo import get_model

cfg = get_cfg_defaults(name="action_recognition")
cfg.CONFIG.MODEL.NAME = "resnet18_v1b_kinetics400"
cfg.CONFIG.MODEL.PRETRAINED = False        # avoids model-zoo weight downloads
cfg.CONFIG.DATA.NUM_CLASSES = 400          # must match the selected head/dataset

model = get_model(cfg).eval()
x = torch.rand(1, 3, 1, 224, 224)          # [N, C, T, H, W]
with torch.no_grad():
    y = model(x)
print(tuple(y.shape))                       # expected for this model: (1, 400)
```

Critical config fields:

- `cfg.CONFIG.MODEL.NAME`: model registry name. `get_model(cfg)` lowercases and validates it against the Torch registry.
- `cfg.CONFIG.MODEL.PRETRAINED`: keep `False` for offline dry-runs; `True` can trigger model-zoo weight lookup/download.
- `cfg.CONFIG.MODEL.PRETRAINED_BASE`: some inflated I3D models use this as a backbone-inflation requirement.
- `cfg.CONFIG.DATA.NUM_CLASSES`: classifier head output size. Kinetics-400 models use 400; Something-Something-V2 examples use 174; Kinetics-700 variants use 700.
- `cfg.CONFIG.DATA.CLIP_LEN` and `cfg.CONFIG.DATA.FRAME_RATE`: keep these consistent with model names/config YAMLs and with the synthetic or decoded video tensor.
- `cfg.DDP_CONFIG.*`: distributed launch settings used by the repo DDP helper.

## Tensor shapes

Action-recognition Torch classifiers consume video clips shaped `[N, C, T, H, W]`:

- `N`: batch size.
- `C`: channels, normally `3` RGB.
- `T`: time/frames. Examples: `1` for ResNet v1b sanity checks, `8/16/32/64` for I3D slow, TPN, R(2+1)D, and SlowFast variants.
- `H, W`: spatial size. Repo tests use `224x224` for most families and `112x112` for R(2+1)D.

Do not pass `[N, T, C, H, W]` or `[T, H, W, C]` directly to the model. Data loaders/transforms may output a different layout; normalize to `[N, C, T, H, W]` before the forward call.

## Script and YAML guidance

The source action-recognition scripts provide reference workflows, but they are large/data/GPU-heavy and are not bundled here:

- `train_ddp_pytorch.py`: loads `get_cfg_defaults(name='action_recognition')`, merges `--config-file`, builds `get_model(cfg)`, creates data loaders, and calls `spawn_workers`.
- `test_ddp_pytorch.py`: same config pattern, then distributed evaluation and result merge.
- `feat_extract_pytorch.py`: builds a model and a `VideoClsDataset`, then saves per-video feature arrays. It assumes a GPU in the original script; adapt deliberately for CPU only if performance is acceptable.
- `get_flops.py`: builds a synthetic `[1, 3, num_frames, input_size, input_size]` tensor and uses `thop`.
- `get_fps.py`: measures CUDA throughput; treat FPS/latency as GPU-only unless you rewrite the benchmark for CPU and label it as CPU timing.
- Action YAMLs set `DDP_CONFIG`, data annotation/data paths, `CONFIG.DATA.CLIP_LEN`, `CONFIG.DATA.FRAME_RATE`, `CONFIG.DATA.NUM_CLASSES`, and `CONFIG.MODEL.NAME/PRETRAINED`. Replace dataset paths and distributed endpoints for your environment.

Use `../training-evaluation-scripts/` when the user wants a complete command template. Use this sub-skill to decide the Torch model, config root, key fields, and smoke-check strategy.

## DDP launch helper facts

`gluoncv.torch.engine.launch.spawn_workers(main, cfg)` uses `torch.multiprocessing.spawn` and the `cfg.DDP_CONFIG` block:

- `DISTRIBUTED=True` triggers multiprocessing over `torch.cuda.device_count()` GPUs on each node.
- `DIST_BACKEND` defaults to `nccl`, which requires CUDA-capable distributed setup; use CPU-only smokes before attempting it.
- `DIST_URL`, `WORLD_SIZE`, `WORLD_RANK`, and `WOLRD_URLS` must match the actual node topology. Note the source config key is spelled `WOLRD_URLS`.
- With `AUTO_RANK_MATCH=True`, the helper compares local IP against `WOLRD_URLS`; mismatches can assert before training starts.

## DirectPose and COOT routing notes

- DirectPose uses `get_cfg_defaults(name='directpose')`, DirectPose model names, COCO-style image data, and pose-specific train/demo/export scripts. Its input and output contracts are not the video-classifier `[N, C, T, H, W] -> logits` contract.
- COOT uses `get_cfg_defaults(name='coot')` and the `multimodaltransformer_coot` registry name. It builds a video-language transformer object with video/text poolers and sequencers, not a simple classifier forward.
- Keep DirectPose/COOT full demos, TVM export, and training reference-only unless the user provides data, weights/cache, and backend resources.

## Evidence basis

This guidance is distilled from GluonCV Torch package modules, Torch model-zoo registry/config files, PyTorch tutorial index, action-recognition scripts/YAMLs, DirectPose scripts, and Torch model-zoo tests. Public use of this skill only requires an installed `gluoncv` package and the files bundled in this skill tree.
