---
name: model-configs
description: "Select, inspect, customize, and debug SOLO-era MMDetection models,
  registries, configs, heads, post-processing, and optional compiled operators
  without relying on the source checkout."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Model configs

Use this skill when a Researcher must choose a SOLO/SOLOv2 model family, understand
how a legacy MMDetection configuration becomes a PyTorch module, or safely plan a
custom component. This is an operating guide for the pinned SOLO-era design, not a
modern MMDetection API reference.

## First classify the request

1. **Instance segmentation:** choose `SOLO`/`SOLOv2` and read
   `references/model-overview.md`. SOLO is box-free and uses a category branch plus
   mask prediction; SOLOv2 adds a mask-feature head and dynamic mask kernels. The
   decoupled and light heads are head variants, not new detector registry families.
2. **Bounding-box detection:** choose a detector family from the representative
   table in `references/api-reference.md`: two-stage RPN/R-CNN variants, or
   single-stage RetinaNet/FCOS/Fovea/ATSS/RepPoints/SSD families.
3. **Architecture modification:** identify the component registry and its parent
   detector boundary before editing a config. Follow the custom-component recipe
   below; do not assume a Python class is discoverable merely because its file
   exists.
4. **Inference/post-processing:** check the model's `test_cfg`, result contract,
   NMS/matrix-NMS path, and compiled-op requirements before trying an API.

A config is executable Python in this vintage. It may define shared variables,
expressions, `range(...)`, and nested dictionaries. Use the safe read-only helper
`python scripts/inspect_config.py CONFIG.py` to print model component types and
selected keys without importing the config, importing MMDetection, loading
weights, downloading data, or executing arbitrary config code. It is a summary
probe, not a full config validator.

## Build boundary: registry -> builder -> detector

- `mmdet.models.registry` exposes separate registries: `BACKBONES`, `NECKS`,
  `HEADS`, `LOSSES`, `DETECTORS`, `ROI_EXTRACTORS`, and `SHARED_HEADS`.
- `mmdet.models.builder.build_*` calls the legacy `build_from_cfg`: each config
  must be a dict with a string `type` (or an explicit class), and that name must
  already be registered. A list builds an `nn.Sequential`.
- Import side effects populate registries through package `__init__` files. A
  custom class needs both a registry decorator and an import reachable from the
  corresponding package initializer; otherwise `registry.get(type)` is `None`.
- `build_detector(model, train_cfg, test_cfg)` injects the two configs as default
  constructor arguments. A component's constructor owns its accepted keys; extra
  keys fail at construction rather than being silently ignored.
- The ordinary graph is `backbone -> optional neck -> head`; two-stage graphs add
  RPN/ROI extractors/bbox or mask heads. SOLO uses `SingleStageInsDetector`; SOLOv2
  additionally builds `mask_feat_head`. See the graph table in the API reference.

Before construction, confirm that `num_classes`, feature channels, number of
feature levels, grid/stride lists, and any mask-head channel widths agree. The
repository's representative config-construction pattern loads a config, sets
`model.pretrained = None`, and calls `build_detector`. That check exercises
Python imports and constructors, not forward correctness, compiled CUDA kernels,
data availability, or checkpoint compatibility.

## Select a model and config

Use the bundled model overview to map the goal to a family, then, from the
generated skill root, inspect a user-supplied config with the bundled helper:

```bash
python sub-skills/model-configs/scripts/inspect_config.py <CONFIG.py>
python sub-skills/model-configs/scripts/inspect_config.py --json <CONFIG.py>
```

Selection rules:

- `configs/solo/solo_*` -> `model.type='SOLO'`, normally `SOLOHead`.
- `configs/solo/decoupled_solo_*` -> `model.type='SOLO'`, with
  `DecoupledSOLOHead` or its light variant; it separates x/y mask branches.
- `configs/solov2/solov2_*` -> `model.type='SOLOv2'`, `SOLOv2Head`, and a
  `MaskFeatHead`; light variants alter backbone/head channels and input scale.
- Configs with `dcn` in the backbone or `use_dcn_in_tower=True` require the DCN
  extension. Do not use a DCN config as a CPU-only construction candidate.
- `fp16/` configs opt into the old `Fp16OptimizerHook`; this is a training
  precision policy, not a guarantee that every custom op supports half tensors.
- `8gpu`, `1x`, and `3x` in filenames describe the released schedule assumptions.
  The baseline learning rate is commonly for 8 GPUs x 2 images/GPU; rescaling or
  changing batch size requires an explicit optimization decision.

The config's data pipeline must match the model: SOLO/SOLOv2 training collects
`img`, `gt_bboxes`, `gt_labels`, and `gt_masks`; detector-only pipelines need not
collect masks. `test_cfg` controls filtering and final result limits. Dataset
paths, checkpoint URLs, and work directories are environment inputs: replace them
with local approved values and never bake source-checkout paths into a skill.

## Customize without breaking contracts

For a custom backbone, neck, head, loss, detector, ROI extractor, or shared head:

1. Define an `nn.Module` with a constructor whose keyword names match the config.
2. Implement the expected tensor/list-of-feature-map interface. A backbone emits
   feature maps selected by `out_indices`; FPN-like necks consume those maps and
   emit a list; heads consume the list and expose `forward`, `loss`, and inference
   methods expected by their detector.
3. Register with the correct registry (`@BACKBONES.register_module`, etc.).
4. Import the class from the package `__init__.py` that is imported by
   `mmdet.models`; registration is import-time, not filesystem discovery.
5. Replace only the relevant nested `type` and shape parameters in a config.
6. Start with `pretrained=None`, instantiate the model, and run a tiny tensor
   forward or a focused native test only after dependencies are proven.

`BaseDetector` requires `extract_feat`, `forward_train`, `simple_test`, and
`aug_test`. `SingleStageDetector` passes backbone/neck features to one bbox head;
`TwoStageDetector` performs proposal assignment/sampling and ROI heads;
`SingleStageInsDetector` passes masks and metadata to the instance head and
raises `NotImplementedError` for augmentation testing in this snapshot. Do not
silently substitute a bbox head for a SOLO instance head: the data and result
contracts differ.

Loss configs are also registry configs. Common registered choices include
`FocalLoss`, `CrossEntropyLoss`, `SmoothL1Loss`, `BalancedL1Loss`, `IoULoss`,
`GIoULoss`, and `GHMC/GHMR`; the SOLO heads additionally define a local
`dice_loss` helper while their historical configs still spell the nested loss as
`type='DiceLoss'`. Verify the exact target head before reusing that key outside
SOLO. Preserve the expected label encoding, `use_sigmoid`, reduction/`avg_factor`,
and `loss_weight`; changing these can produce a numerically valid but
semantically wrong model. See `references/api-reference.md` for the compact
contract table.

## Post-processing and precision

For bbox heads, `multiclass_nms` skips score column 0 as background, filters by
`score_thr`, dispatches the configured `nms`/`soft_nms`, and caps `max_num`. NMS
accepts NumPy arrays or tensors and preserves the input type; GPU tensors use
`nms_cuda`, CPU tensors use `nms_cpu`. CPU NMS tests cover float32/float64, while
GPU tests cover float32 and skip float64. SOLO/SOLOv2 use category scores and
mask-specific post-processing; SOLOv2 applies `points_nms` to category heatmaps
and `matrix_nms` to same-class masks before `max_per_img`.

For legacy FP16, set `fp16` in the config only when the installed MMCV runner and
model support it. The hook keeps FP32 optimizer weights, converts the model to
half, patches BatchNorm/GroupNorm to FP32, scales loss, and copies gradients and
parameters. Custom modules should use `@auto_fp16` and `@force_fp32` only on
`nn.Module` methods and only after verifying tensor dtypes. FP16 does not repair a
missing extension or make an unsupported CUDA kernel safe.

## Verification ladder

Use the smallest sufficient check and record what it does *not* prove:

1. **Static config summary:** run `scripts/inspect_config.py`; verify types, keys,
   stage widths, mask collections, and test thresholds.
2. **Registry/build smoke:** in a compatible environment, import `mmdet.models`,
   load a config through the legacy `mmcv.Config`, remove `pretrained`, and call
   `build_detector`. This may require all package imports and compiled ops.
3. **CPU utility candidate:** run the focused CPU NMS or pure-PyTorch matrix-NMS
   checks if the extension imports successfully. A CPU check does **not** validate
   custom CUDA kernels.
4. **Forward candidate:** use a tiny input only for a model without required DCN
   or other blocked extensions. CUDA forward and training are environment- and
   memory-dependent; full training is out of scope for this sub-skill.

Native acceptance candidates are therefore: representative config construction;
CPU NMS or pure-PyTorch matrix-NMS utility checks when imports permit; and CUDA
operator/forward checks only when the selected model requires them and a compatible
GPU build is available. Do not call a blocked CUDA candidate successful, and do
not run full training as a native check.

If an import fails with `ModuleNotFoundError` or a missing `.so` such as
`nms_cpu`, `nms_cuda`, `deform_conv_cuda`, `roi_align_cuda`, or
`sigmoid_focal_loss_cuda`, classify it as an expected build/environment failure,
not as a model-config semantic failure. Read `references/troubleshooting.md`.

## Safety and boundaries

Do not copy compiled extensions, checkpoints, datasets, generated logs, or source
scripts into this skill. The bundled inspector is deliberately AST-based and
read-only. Training, distributed launchers, visualization, publishing, model
weight downloads, dataset conversion, and source-mutation helpers remain
reference-only because they are long-running, environment-mutating, networked,
or write artifacts. Use approved project tooling outside this runtime subtree
when those actions are explicitly authorized.
