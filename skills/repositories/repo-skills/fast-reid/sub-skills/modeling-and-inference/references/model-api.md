# FastReID model API

This reference is self-contained for FastReID version 1.3-style source checkouts. It focuses on model construction and inference-adjacent APIs, not training loops or dataset layouts.

## Primary imports

```python
from fastreid.config import get_cfg
from fastreid.modeling import build_model, build_backbone, build_heads
from fastreid.modeling import META_ARCH_REGISTRY, BACKBONE_REGISTRY, REID_HEADS_REGISTRY
```

Verified public builder facts:

- `build_model(cfg)` selects `cfg.MODEL.META_ARCHITECTURE`, constructs the registered meta-architecture, moves it to `torch.device(cfg.MODEL.DEVICE)`, and does **not** load `cfg.MODEL.WEIGHTS`.
- `build_backbone(cfg)` selects `cfg.MODEL.BACKBONE.NAME` and returns the registered backbone module.
- `build_heads(cfg)` selects `cfg.MODEL.HEADS.NAME` and returns the registered ReID/classification head module.
- A CPU Baseline smoke with `MODEL.BACKBONE.PRETRAIN=False` returned a feature output shaped `(1, 2048)` for one random image tensor.

## Registry families

FastReID registers classes/functions by importing its modeling package. Standard registry members in this checkout include:

| Registry | Config key | Registered choices | Notes |
|---|---|---|---|
| `META_ARCH_REGISTRY` | `MODEL.META_ARCHITECTURE` | `Baseline`, `MGN`, `MoCo`, `Distiller` | `Baseline` is the standard ReID architecture; `MGN` has multi-branch behavior; `MoCo` and `Distiller` are research/training-oriented and usually need matching configs/checkpoints. |
| `BACKBONE_REGISTRY` | `MODEL.BACKBONE.NAME` | `build_resnet_backbone`, `build_osnet_backbone`, `build_resnest_backbone`, `build_resnext_backbone`, `build_regnet_backbone`, `build_effnet_backbone`, `build_shufflenetv2_backbone`, `build_mobilenetv2_backbone`, `build_mobilenetv3_backbone`, `build_repvgg_backbone`, `build_vit_backbone` | Some choices require compatible config keys such as depth, feature dimension, stride, pretrained path, or transformer stride/image assumptions. |
| `REID_HEADS_REGISTRY` | `MODEL.HEADS.NAME` | `EmbeddingHead`, `ClasHead` | `EmbeddingHead` returns embedding features in eval mode; `ClasHead` returns scaled class logits in eval mode. |

Loss functions are configured under `MODEL.LOSSES` and are used during `model.train()` forward passes. Common loss names are `CrossEntropyLoss`, `TripletLoss`, `CircleLoss`, and `Cosface`. In eval mode, standard ReID inference normally bypasses loss computation.

## Core config keys for model construction

Set these before calling `build_model(cfg)`:

```python
cfg = get_cfg()
# cfg.merge_from_file(user_config)  # optional, user-supplied path
cfg.defrost()
cfg.MODEL.DEVICE = "cpu"              # safe smoke default
cfg.MODEL.BACKBONE.PRETRAIN = False    # prevents backbone pretrain downloads
cfg.MODEL.HEADS.NUM_CLASSES = 1        # safe placeholder for construction
cfg.freeze()
model = build_model(cfg)
model.eval()
```

Frequently used model keys:

- `MODEL.DEVICE`: default is `cuda`; set `cpu` for CPU-only construction and smoke tests.
- `MODEL.META_ARCHITECTURE`: whole-model registry key, usually `Baseline` for standard ReID feature extraction.
- `MODEL.BACKBONE.NAME`: backbone builder registry key.
- `MODEL.BACKBONE.DEPTH`: backbone variant such as a ResNet depth string.
- `MODEL.BACKBONE.FEAT_DIM`: channel dimension expected by heads; common ResNet recipes use `2048`.
- `MODEL.BACKBONE.PRETRAIN`: if true, a backbone may attempt to resolve/download pretrained weights. Set false for no-network smokes.
- `MODEL.BACKBONE.PRETRAIN_PATH`: optional explicit local path for a pretrained backbone if a workflow intentionally uses one.
- `MODEL.HEADS.NAME`: head registry key, usually `EmbeddingHead` for ReID feature vectors.
- `MODEL.HEADS.NUM_CLASSES`: needed for training heads and weight tensors even if an eval-only smoke uses random features.
- `MODEL.HEADS.EMBEDDING_DIM`: if positive, adds an embedding projection and changes output feature dimension.
- `MODEL.HEADS.POOL_LAYER`: pooling class name such as `GlobalAvgPool`, `GeneralizedMeanPooling`, `GeneralizedMeanPoolingP`, `FastGlobalAvgPool`, `AdaptiveAvgMaxPool`, or `ClipGlobalAvgPool`.
- `MODEL.HEADS.CLS_LAYER`: classifier/logit transform such as `Linear`, `ArcSoftmax`, `CosSoftmax`, or `CircleSoftmax`.
- `MODEL.PIXEL_MEAN` and `MODEL.PIXEL_STD`: RGB-channel normalization values scaled to 0-255 pixel space.
- `MODEL.WEIGHTS`: checkpoint path used by predictor/trainer helpers, not by `build_model` itself.
- `INPUT.SIZE_TEST`: `[height, width]` used by demo-style feature extraction preprocessing.

## Tensor contracts

### Eval inference

- Input may be a tensor directly or a dict with key `"images"`.
- Shape is `(B, C, H, W)` with `C=3`.
- Dtype should be floating point, normally `float32`.
- Pixel order is RGB if following the demo preprocessing path.
- Values are normally in raw 0-255 image scale before FastReID model normalization. The `Baseline` meta-architecture subtracts `MODEL.PIXEL_MEAN` and divides by `MODEL.PIXEL_STD` in-place.
- Call `model.eval()` and use `torch.no_grad()` for feature extraction.

### Training forward

- Training mode expects a dict containing at least `"images"` and `"targets"`.
- The head returns logits/features; the meta-architecture converts those to a loss dict.
- Training workflows, dataloaders, distributed launch, resume, and optimizer/scheduler setup are outside this sub-skill.

## Layer/head vocabulary

Modeling imports expose reusable layer implementations such as normalized layers (`BN`, `syncBN`, `GhostBN`, `FrozenBN`, `GN`), pooling layers, squeeze/excitation, non-local blocks, context blocks, stochastic depth/drop blocks, and weight initializers. These are internal building blocks for FastReID registries; future agents should prefer config-driven model construction over direct layer assembly unless the user is extending a model family.

## Rank and rerank utility imports

The correct rank import in this checkout is:

```python
from fastreid.evaluation.rank import evaluate_rank
from fastreid.evaluation.rerank import re_ranking
```

Do not rely on `from fastreid.evaluation import evaluate_rank` for this checkout: the package-level evaluation namespace does not export it. Rank metrics can run with a pure-Python fallback if the optional Cython rank extension is unavailable.
