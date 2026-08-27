---
name: "torch-video-workflows"
description: "Routes GluonCV PyTorch action-recognition, video model-zoo,
  DirectPose, COOT, YACS config, DDP, and smoke-check workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# torch-video-workflows

Use this sub-skill when the user is working with GluonCV's PyTorch side: action recognition, video models, Torch model zoo names, YACS config files, DDP launch helpers, DirectPose, COOT/video-language, or Torch-specific import/runtime failures.

## Use this route for

- Instantiating PyTorch video/action models through `gluoncv.torch.model_zoo.get_model(cfg)`.
- Listing Torch model names with `gluoncv.torch.model_zoo.get_model_list()`.
- Creating or editing YACS configs with `get_cfg_defaults(name='action_recognition')`, `coot`, or `directpose`.
- CPU sanity checks for SlowFast, I3D, R(2+1)D, TPN, CSN/IRCSN, and ResNet video models.
- Optional CUDA/DDP planning for `train_ddp_pytorch.py`, `test_ddp_pytorch.py`, DirectPose DDP, feature extraction, FLOPS, and FPS scripts.
- Diagnosing missing or incompatible `torch`, `torchvision`, `Pillow`, or `decord` dependencies.

## Do not use this route for

- MXNet model-zoo APIs such as `gluoncv.model_zoo.get_model(name, **kwargs)`. Use `../mxnet-model-zoo/`.
- Dataset directory layouts, annotation files, frame lists, and transforms. Use `../data-transforms-datasets/`.
- Full command construction for the broad script zoo. Use `../training-evaluation-scripts/`.

## Read first

- `references/torch-models-and-configs.md` for verified Torch model-zoo APIs, model families, config patterns, tensor shapes, and script/DDP guidance.
- `references/troubleshooting.md` for PyTorch import, legacy dependency, CUDA, DDP, pretrained download, and tensor-shape failures.

## Skill-owned script

- `scripts/torch_video_model_smoke.py` — safe helper that creates a GluonCV Torch config, selects a model, disables pretrained weights by default, lists the 48-name registry, and can run a CPU forward pass on a synthetic `[N, C, T, H, W]` tensor. Add `--cuda` only when a CUDA-enabled Torch install is actually available.

## Typical CPU sanity flow

```bash
python sub-skills/torch-video-workflows/scripts/torch_video_model_smoke.py --list-models
python sub-skills/torch-video-workflows/scripts/torch_video_model_smoke.py \
  --model resnet18_v1b_kinetics400 --classes 400 --frames 1 --height 224 --width 224
```

Expected verified signal for the default CPU smoke is an output tensor shape of `(1, 400)` for `resnet18_v1b_kinetics400` with `pretrained=False`.

## Cross-links

- Route MXNet action-recognition and other GluonCV MXNet models to `../mxnet-model-zoo/`.
- Route video dataset/frame-list preparation and transforms to `../data-transforms-datasets/`.
- Route full train/eval/inference command templates to `../training-evaluation-scripts/` after model/config choices are known.
