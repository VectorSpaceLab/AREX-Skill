# detrex API reference

This reference summarizes the package APIs exposed by detrex and the safe usage patterns that matter when building or debugging DETR-style components. It is self-contained: use it with the installed detrex package and the bundled smoke helper, not by opening the original repository files.

## Public import map

| Area | Import | Main public objects | Notes |
|---|---|---|---|
| Package root | `import detrex` | `layers`, `modeling`, `utils`, `data`, `config` | Root import eagerly imports these subpackages; a dependency problem in one subpackage can surface at root import time. |
| Layers | `from detrex import layers` or `from detrex.layers import ...` | attention, transformer, position embedding, MLP/FFN, box ops, conv blocks, denoising queries, compiled ops | `MultiScaleDeformableAttention` and `DCNv3` are backend-sensitive because they depend on compiled extension symbols. |
| Modeling | `from detrex import modeling` or `from detrex.modeling import ...` | `SetCriterion`, `BaseCriterion`, `HungarianMatcher`, losses, `ChannelMapper`, common backbones | The top-level `HungarianMatcher` is the legacy dict-style matcher; the newer matcher is exposed as `detrex.modeling.matcher.ModifedMatcher` with the misspelling preserved by the package. |
| Backbones | `from detrex.modeling.backbone import ...` | `ResNet`, `BasicStem`, `make_stage`, `ConvNeXt`, `FocalNet`, `TimmBackbone`, `TorchvisionBackbone`, `InternImage`, `EVAViT`, `EVA02_ViT` | Some backbones require extra packages or compiled ops. Use `pretrained=False` unless downloads are explicitly intended. |
| Data | `from detrex.data import ...` | `DetrDatasetMapper`, MaskFormer/COCO mappers, `ColorAugSSDTransform`, datasets namespace | Mappers expect Detectron2 dataset dicts and real image files; do not call them on synthetic dicts unless you provide a real image. |
| Config | `from detrex.config import get_config, try_get_key` | packaged LazyConfig loader and safe key selector | `get_config()` loads packaged config resources such as `common/train.py`; missing resources raise `RuntimeError`. |
| Checkpoint | `from detrex.checkpoint import DetectionCheckpointer` | Detectron2/fvcore checkpointer with conversion heuristics | Handles native `.pth`, Detectron/Caffe2 `.pkl`, and pycls `.pyth` conventions. |
| EMA | `from detrex.modeling.ema import ...` | `EMAState`, `EMAUpdater`, `EMAHook`, `may_build_model_ema`, `apply_model_ema_and_restore` | Requires a config with `train.model_ema` fields. |
| Utils | `from detrex.utils import ...` | `interpolate`, `inverse_sigmoid`, distributed helpers, `WandbWriter` | `WandbWriter` imports wandb and is opt-in for logging tasks. |

## Safe smoke command

Use the bundled helper when you need objective API evidence:

```bash
python scripts/api_smoke.py --strict
python scripts/api_smoke.py --strict --check-config common/train.py
python scripts/api_smoke.py --strict --check-cuda-extension
python scripts/api_smoke.py --json --tiny-cpu
```

The helper imports and inspects public objects, can run tiny CPU tensor checks, and only checks CUDA extension symbol availability when requested. It does not download weights, train, evaluate, or register datasets by default.

## Config helpers

```python
from detrex.config import get_config, try_get_key

cfg = get_config("common/train.py")
max_iter = try_get_key(cfg, "train.max_iter", "train.train.max_iter", default=None)
```

Use `try_get_key(cfg, *keys, default=...)` when project configs differ in nesting. It returns the first OmegaConf key that exists. Use `get_config(config_path)` only for packaged detrex config resources; for user/project config files, prefer Detectron2 `LazyConfig.load(path)` or the workflow-specific training/config sub-skill.

Common failure meanings:

- `RuntimeError: <name> not available in detrex configs!` means the string is not a packaged detrex config resource.
- `pkg_resources` import errors mean the Python packaging stack is incompatible with detrex's config loader; see troubleshooting.

## Layers

### Box operations

```python
import torch
from detrex.layers import box_cxcywh_to_xyxy, box_xyxy_to_cxcywh, box_iou, generalized_box_iou, masks_to_boxes

boxes_cxcywh = torch.tensor([[0.5, 0.5, 0.2, 0.4]])
boxes_xyxy = box_cxcywh_to_xyxy(boxes_cxcywh)
giou = generalized_box_iou(boxes_xyxy, boxes_xyxy)
```

Use normalized center-format boxes `(cx, cy, w, h)` for many DETR model outputs, then convert to `(x1, y1, x2, y2)` before GIoU helpers that expect corner format.

### Attention and transformer blocks

| Object | Import | Typical use | Important inputs |
|---|---|---|---|
| `MultiheadAttention` | `detrex.layers` | Standard attention wrapper compatible with detrex transformer layers | Match `embed_dim`, `num_heads`, and `batch_first` with surrounding tensors. |
| `ConditionalSelfAttention` | `detrex.layers` | Conditional DETR encoder/decoder self-attention | `query`, `key`, `value`, `query_pos`, `key_pos`; usually sequence-first unless configured otherwise. |
| `ConditionalCrossAttention` | `detrex.layers` | Conditional DETR decoder cross-attention | Also needs `query_sine_embed`; set `is_first_layer=True` for first decoder layer behavior. |
| `BaseTransformerLayer` | `detrex.layers` | Compose attention, FFN, norm by operation order | `operation_order` must match the supplied number of attention modules and norms. |
| `TransformerLayerSequence` | `detrex.layers` | Repeat one `BaseTransformerLayer` | Pass a single layer plus `num_layers`; passing a list with `num_layers` triggers an assertion. |
| `MultiScaleDeformableAttention` | `detrex.layers` | Deformable-DETR attention over multi-level features | Requires `reference_points`, `spatial_shapes`, `level_start_index`; compiled extension is used on CUDA. |

Minimal CPU-safe shape pattern for position embedding and FFN:

```python
import torch
from detrex.layers import FFN, PositionEmbeddingSine

mask = torch.zeros(2, 10, 12, dtype=torch.bool)
pos = PositionEmbeddingSine(num_pos_feats=16, normalize=True)(mask)
ffn = FFN(embed_dim=32, feedforward_dim=64, output_dim=32, num_fcs=2)
out = ffn(torch.randn(2, 5, 32))
assert pos.shape == (2, 32, 10, 12)
assert out.shape == (2, 5, 32)
```

### Multi-scale deformable attention shape checklist

For `MultiScaleDeformableAttention(batch_first=True)`, keep these dimensions aligned:

```text
query:             (batch, num_query, embed_dim)
value:             (batch, sum(H_l * W_l), embed_dim)
spatial_shapes:    (num_levels, 2) as (height, width)
level_start_index: (num_levels,) cumulative starts for flattened levels
reference_points:  (batch, num_query, num_levels, 2 or 4)
```

The sum of `height * width` across `spatial_shapes` must equal `value.shape[1]`. Last dimension of `reference_points` must be `2` for points or `4` for boxes. On CUDA tensors, detrex calls the compiled `detrex._C.ms_deform_attn_forward/backward` symbols; on CPU tensors, it can use the pure PyTorch implementation when the module imported successfully.

### MLP, conv, denoising, and shape helpers

| Object | Purpose | Notes |
|---|---|---|
| `MLP(input_dim, hidden_dim, output_dim, num_layers)` | Simple linear/ReLU stack without identity | Used for prediction heads and projections. |
| `FFN(embed_dim, feedforward_dim, output_dim=None, num_fcs=2, add_identity=True)` | Transformer feed-forward network | `num_fcs` must be at least 2. |
| `ConvNormAct` / `ConvNorm` | Conv2d with optional norm and activation | `ConvNorm` is a partial with no activation. |
| `ShapeSpec(channels=None, height=None, width=None, stride=None)` | Lightweight tensor metadata | Used by `ChannelMapper` and backbone/neck wiring. |
| `apply_label_noise`, `apply_box_noise`, `GenerateDNQueries` | Denoising-query helpers for DN/DINO-style training | Treat as training-model internals; validate class counts and box format before use. |
| `LayerNorm` | Layer normalization variant | Check channel ordering before using with image-like tensors. |

## Losses, costs, matchers, and criteria

### Loss modules

```python
from detrex.modeling.losses import CrossEntropyLoss, FocalLoss, DiceLoss, L1Loss, GIoULoss
```

| Loss | Expected inputs | Notes |
|---|---|---|
| `CrossEntropyLoss` | logits and integer labels | Accepts optional `class_weight`; wraps `torch.nn.functional.cross_entropy` behavior with detrex reduction/weight handling. |
| `FocalLoss` | logits or probabilities and labels/targets depending on `activated` | Default sigmoid focal settings are common for DETR-style classification. |
| `DiceLoss` | prediction masks and target masks | Check flattening and `avg_factor` semantics before comparing to other implementations. |
| `L1Loss` | predicted boxes and target boxes | Frequently normalized by `avg_factor=num_boxes`. |
| `GIoULoss` | corner-format boxes `(x1, y1, x2, y2)` | Convert from center format before use. |

### Cost modules and matcher APIs

Two matcher styles coexist:

```python
# Legacy matcher: dict outputs/targets style.
from detrex.modeling import HungarianMatcher
legacy_matcher = HungarianMatcher(cost_class=1, cost_bbox=5, cost_giou=2)
indices = legacy_matcher(
    {"pred_logits": pred_logits, "pred_boxes": pred_boxes},
    [{"labels": labels, "boxes": boxes}],
)

# Newer cost-module matcher: tensor-list style. The exported name is misspelled.
from detrex.modeling.matcher import ModifedMatcher, FocalLossCost, L1Cost, GIoUCost
matcher = ModifedMatcher(
    cost_class=FocalLossCost(alpha=0.25, gamma=2.0, weight=2.0),
    cost_bbox=L1Cost(weight=5.0),
    cost_giou=GIoUCost(weight=2.0),
)
indices = matcher(pred_logits, pred_boxes, [labels], [boxes])
```

Use the legacy matcher with `SetCriterion`. Use the newer `ModifedMatcher` pattern with `BaseCriterion` or code that already passes separate logits, boxes, labels, and boxes lists. Both return a list of `(prediction_indices, target_indices)` tensors per batch item.

### Criterion classes

| Object | Matcher style | Output keys | When to use |
|---|---|---|---|
| `SetCriterion` | Legacy dict matcher | `loss_class`, `loss_bbox`, `loss_giou`, plus aux suffixes | Older Conditional-DETR/DETR-style configs. |
| `BaseCriterion` | Newer tensor-list matcher | `loss_class`, `loss_bbox`, `loss_giou`, plus aux suffixes | Newer modular detrex losses and cost modules. |

Both normalize by the number of target boxes and use distributed all-reduce when `torch.distributed` is initialized.

## Checkpointing

```python
import torch.nn as nn
from detrex.checkpoint import DetectionCheckpointer

model = nn.Linear(4, 2)
checkpointer = DetectionCheckpointer(model, save_dir="")
# checkpointer.load(user_checkpoint_path)  # Use only when the user provides a checkpoint.
```

`DetectionCheckpointer` extends the Detectron2/fvcore checkpointer with these behaviors:

- Handles native PyTorch checkpoint dictionaries.
- Converts Detectron/Caffe2 `.pkl` and pycls `.pyth` structures into a `{"model": ...}` state dictionary.
- Applies name-matching heuristics through conversion utilities.
- Suppresses expected missing/unexpected messages for selected legacy buffers such as pixel statistics and old anchor buffers.
- With DistributedDataParallel, checks whether workers can read the checkpoint and synchronizes model parameters if only the main worker loaded it.

For checkpoint conversion and model-zoo choices, route to the model-zoo/converter sub-skill. Use this API reference only for programmatic loading/debugging.

## Exponential moving average (EMA)

```python
from detrex.modeling.ema import EMAState, EMAUpdater, may_build_model_ema, EMAHook, apply_model_ema_and_restore
```

Core flow:

1. Ensure `cfg.train.model_ema.enabled` is true and the config also supplies `decay` and `device` fields expected by the hook.
2. Call `may_build_model_ema(cfg, model)` before constructing the `EMAHook`; it attaches `model.ema_state`.
3. During training, `EMAHook.after_step()` updates the EMA state.
4. For evaluation or checkpointing with EMA weights, use `apply_model_ema_and_restore(model)` as a context manager or `apply_model_ema(model, save_current=True)` if you need manual restore state.
5. Save/checkpoint `may_get_ema_checkpointer(cfg, model)` output together with the model checkpointer when EMA is enabled.

EMA stores parameters and buffers, not only trainable parameters. It removes a `DistributedDataParallel` wrapper before accessing the underlying model.

## Distributed helpers

```python
from detrex.utils import get_rank, get_world_size, is_dist_avail_and_initialized
from detrex.utils.dist import setup_for_distributed, slurm_init_distributed_mode
```

- `get_rank()` returns `0` when `torch.distributed` is unavailable or not initialized.
- `get_world_size()` returns `1` when not distributed.
- `is_dist_avail_and_initialized()` is the safe guard before all-reduce or barriers.
- `setup_for_distributed(is_master)` patches `print` to reduce non-master output; call it only from launcher/distributed setup code.
- `slurm_init_distributed_mode(args)` is specific to SLURM/NCCL-style CUDA distributed launch and expects an `args.slurm` object plus SLURM environment variables. Do not call it from a normal API smoke.

## WandB writer

```python
from detrex.utils.events import WandbWriter
```

`WandbWriter` is a Detectron2 `EventWriter` that logs smoothed scalar storage values and optional visualization images to Weights & Biases. It expects a config with:

```text
cfg.train.wandb.params  # keyword arguments for wandb.init(...)
```

Use it only when the user explicitly wants WandB logging and has configured the WandB runtime. It can initialize a networked logging session, so it is not part of default API smoke checks beyond import/signature inspection.
