# Troubleshooting detrex package APIs

Start with the bundled helper unless the failure already identifies a specific API:

```bash
python scripts/api_smoke.py --strict
python scripts/api_smoke.py --strict --check-config common/train.py
python scripts/api_smoke.py --strict --check-cuda-extension
python scripts/api_smoke.py --json --tiny-cpu
```

The helper is intentionally safe: no downloads, no training, no dataset registration, and no native repo tests.

## Import failures

| Symptom | Likely cause | What to do |
|---|---|---|
| `ModuleNotFoundError: No module named 'detectron2'` | detrex depends on Detectron2 runtime APIs. | Install/use an environment with compatible Detectron2, PyTorch, and torchvision. Re-run `api_smoke.py --strict`. |
| `ModuleNotFoundError: No module named 'pkg_resources'` or config import fails around `pkg_resources` | detrex's config helper imports `pkg_resources`; newer packaging environments may omit it. | Install a compatible `setuptools` that provides `pkg_resources`, then retry `from detrex.config import get_config`. |
| `ModuleNotFoundError: No module named 'timm'` | `TimmBackbone` wrapper imports timm lazily but raises when instantiated without timm. | Use `TorchvisionBackbone` or install timm. Keep `pretrained=False` unless downloads are explicitly allowed. |
| `RuntimeError: Failed to import timm` | Same as missing timm, surfaced from the wrapper constructor. | Install timm or switch backbone. |
| `No module named 'wandb'` while importing `detrex.utils` or `WandbWriter` | WandB writer imports the wandb package. | Install/configure wandb only for logging tasks; do not require it for non-WandB API work if importing narrower modules is enough. |
| `No module named 'pycocotools'`, `cv2`, or image/segmentation utilities | Data mappers and transforms depend on common vision packages. | Install the missing package or avoid mapper execution for pure API inspection. |

## Compiled extension and CUDA-sensitive APIs

### Multi-scale deformable attention unavailable

Symptoms:

- `ImportError: Cannot import 'detrex._C', therefore 'MultiScaleDeformableAttention' is not available.`
- `detrex._C` imports but lacks `ms_deform_attn_forward` or `ms_deform_attn_backward`.
- CUDA tensors enter multi-scale deformable attention and fail inside an extension call.

Check first:

```bash
python scripts/api_smoke.py --strict --check-cuda-extension
```

Interpretation:

- If `detrex._C` is missing, the package was not built with its extension or the extension cannot load with the active PyTorch/CUDA ABI.
- If symbols are missing, the extension build is incomplete or mismatched.
- If the extension exists but a forward pass fails, inspect tensor device, dtype, shape, and PyTorch/CUDA compatibility.

Shape checklist for `MultiScaleDeformableAttention`:

```text
sum(height * width for spatial_shapes) == value length
spatial_shapes.dtype is integer-like and shape is (num_levels, 2)
level_start_index starts at 0 and matches cumulative feature sizes
reference_points last dimension is 2 or 4
query/value embed_dim matches module embed_dim
embed_dim is divisible by num_heads
CUDA operator path receives CUDA tensors only when the extension is available
```

### DCNv3 unavailable

`DCNv3` and `DCNv3Function` are also compiled-op-sensitive. If they behave like dummy classes/functions or fail at construction, treat it as an extension build/runtime mismatch. Do not substitute DCNv3 into a backbone unless the required operator is available.

## Config helper failures

| Symptom | Meaning | Fix |
|---|---|---|
| `RuntimeError: common/foo.py not available in detrex configs!` | `get_config()` only loads packaged detrex config resources. | Use a valid packaged resource such as `common/train.py`, or use Detectron2 `LazyConfig.load()` for user/project files. |
| `OmegaConf.select` returns `None` unexpectedly | The queried key path does not exist or the config structure differs. | Use `try_get_key(cfg, "key.a", "fallback.key", default=...)` and inspect top-level keys. |
| A LazyCall object instantiates a backbone and downloads weights | `pretrained=True` or a remote checkpoint setting was used. | Set `pretrained=False` for API work; use a user-provided local checkpoint only when needed. |

## Loss, matcher, and criterion mismatches

### Legacy matcher vs newer matcher

Symptoms:

- `TypeError` saying matcher got the wrong number of arguments.
- A criterion expects dict outputs/targets but you pass separate tensors.
- A matcher expects separate logits/boxes/target lists but you pass a dict.

Use the correct pair:

```python
# Legacy pair
from detrex.modeling import SetCriterion, HungarianMatcher
matcher = HungarianMatcher(cost_class=1, cost_bbox=5, cost_giou=2)
# matcher(outputs_dict, targets_list)

# Newer modular pair; package spelling is ModifedMatcher.
from detrex.modeling import BaseCriterion
from detrex.modeling.matcher import ModifedMatcher, FocalLossCost, L1Cost, GIoUCost
matcher = ModifedMatcher(FocalLossCost(weight=2), L1Cost(weight=5), GIoUCost(weight=2))
# matcher(pred_logits, pred_boxes, gt_labels_list, gt_bboxes_list)
```

### Box-format errors

- DETR predictions and targets are commonly `(cx, cy, w, h)` normalized to `[0, 1]`.
- GIoU helpers and GIoU cost/loss expect `(x1, y1, x2, y2)` corner format.
- Convert with `box_cxcywh_to_xyxy()` before `generalized_box_iou()` or `GIoULoss`.

### Loss normalization surprises

Many detrex loss modules accept `avg_factor` and `loss_weight`. When comparing with raw PyTorch losses, reproduce detrex reduction and normalization before declaring a mismatch.

## Backbone and neck wiring errors

| Symptom | Cause | Fix |
|---|---|---|
| `KeyError` in `ChannelMapper` | `in_features` names do not match backbone output keys. | Print/inspect backbone output keys; update both `in_features` and `input_shapes`. |
| `GroupNorm` or convolution channel error | `ShapeSpec(channels=...)` does not match actual feature channel count. | Correct shape metadata or choose matching backbone output stages. |
| Timm wrapper raises an error mentioning `feature_info` | The selected timm model does not provide feature metadata with `features_only=True`. | Choose a timm model that supports feature extraction, set appropriate `out_indices`, or use another backbone. |
| Timm wrapper raises an error mentioning `norm_layer` | The selected timm model rejected the custom norm layer. | Set `norm_layer=None` or choose a compatible model. |
| Torchvision wrapper cannot import `create_feature_extractor` | torchvision is too old or incompatible. | Use a torchvision version with feature extraction support. |
| The returned keys are `p1/p2/p3` but the neck expects `res3/res4/res5` | timm and torchvision wrappers use different naming conventions. | Rename output keys in the wrapper/neck config or update `ChannelMapper.in_features`. |

## Data mapper failures

| Symptom | Likely cause | Fix |
|---|---|---|
| Image read failure | `dataset_dict["file_name"]` is missing, unreadable, or points to a non-image. | Provide a real image path/URI readable by Detectron2 `PathManager`. |
| `check_image_size` assertion | Dataset dict dimensions disagree with the image. | Correct `height`/`width` metadata or regenerate dataset registration. |
| Missing/empty instances after transform | Cropping/resize removed objects or annotations are malformed. | Inspect transformed annotations and `iscrowd`; verify boxes/polygons before filtering. |
| Segmentation unexpectedly removed | `DetrDatasetMapper(mask_on=False)` removes `segmentation`. | Set `mask_on=True` for tasks that require instance masks, or use a MaskFormer mapper. |
| `padding_mask` missing | `DetrDatasetMapper` does not emit it; COCO/MaskFormer LSJ mappers do. | Use the mapper expected by the model config. |

Do not run mappers for pure import tests: they read real images and invoke Detectron2 transforms.

## Checkpoint loading messages

`DetectionCheckpointer` intentionally applies matching heuristics. Messages are not always fatal:

- `incorrect_shapes`: a checkpoint tensor shape differs from the model shape. This is common when the class head count or query count changed; confirm whether skipping that parameter is intended.
- `missing_keys`: model parameters are not present in the checkpoint. It may be expected for new heads or buffers, but not for backbone stages that should initialize from a checkpoint.
- `unexpected_keys`: checkpoint parameters are unused by the model. It may be expected when loading a larger checkpoint into a smaller model.
- DDP warning about workers reading a checkpoint: only the main worker has the file; the checkpointer may sync parameters after loading, but full resume can still be fragile if optimizer/checkpointables differ.

For converter decisions or checkpoint surgery, route to the model-zoo/converter sub-skill.

## EMA surprises

| Symptom | Cause | Fix |
|---|---|---|
| `Name ema_state is reserved` | Model already has an `ema_state` attribute before `may_build_model_ema`. | Remove/rename the conflicting attribute or do not call detrex EMA setup twice. |
| `Call may_build_model_ema first` | `EMAHook` was constructed before the model got `ema_state`. | Call `may_build_model_ema(cfg, model)` before creating the hook. |
| EMA state on wrong device | `cfg.train.model_ema.device` or `cfg.model.device` does not match intended placement. | Set the EMA device explicitly and move state with `EMAState.to(device)` if needed. |
| Evaluation changed weights permanently | EMA was applied without restore. | Use `apply_model_ema_and_restore(model)` as a context manager. |

## WandB writer issues

`WandbWriter` calls `wandb.init(config=OmegaConf.to_container(cfg, resolve=True), **cfg.train.wandb.params)`. Failures usually mean:

- `cfg.train.wandb.params` is missing or not a mapping.
- WandB credentials/runtime are not configured.
- Networked logging is disabled or unavailable.
- Event storage is not active because the writer was called outside Detectron2 training/evaluation storage context.

Do not instantiate `WandbWriter` in default smoke checks. Treat it as opt-in logging behavior.

## Distributed helper issues

- `get_world_size()` returning `1` and `get_rank()` returning `0` is normal outside initialized distributed training.
- `slurm_init_distributed_mode(args)` expects SLURM variables and CUDA/NCCL setup; calling it in a normal local API script will fail.
- `setup_for_distributed()` monkey-patches Python `print`; call it only from launcher setup code, not from reusable library functions.
