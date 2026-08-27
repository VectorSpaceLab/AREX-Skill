# Runtime contracts

This reference describes what the config fields must line up with in the
checked-in Python APIs. It is intentionally a contract summary, not a copy of
the implementation.

## Config loading and plugin registration

The repository tools load configs with `mmcv.Config.fromfile` in
`tools/train.py` and `tools/test.py`. A public config sets:

```python
plugin = True
plugin_dir = 'projects/mmdet3d_plugin/'
```

The tools derive the import module from the directory name and import
`projects`. That import reaches `projects.mmdet3d_plugin`, whose package
initialization imports the evaluation hook and `voxformer` package. The latter
registers, among other classes:

- detector registry: `VoxFormer` and `LMSCNet_SS` from
  `projects/mmdet3d_plugin/voxformer/detectors/`;
- head registry: `VoxFormerHead` from `dense_heads/`;
- transformer/layer registries: `PerceptionTransformer`,
  `PerceptionTransformer3D`, `VoxFormerEncoder`, `VoxFormerEncoder3D`, their
  layers, and the standard/custom attention classes from `modules/`;
- dataset registry: `SemanticKittiDatasetStage1` and
  `SemanticKittiDatasetStage2` from `projects/mmdet3d_plugin/datasets/`;
- custom evaluation: `CustomDistEvalHook` from
  `projects/mmdet3d_plugin/core/evaluation/eval_hooks.py`.

A config-only parse cannot prove these registrations. A safe import preflight
should use the prepared legacy environment and the repository root on
`PYTHONPATH`; it should report the first failing layer rather than changing a
config to bypass a missing registry entry. Because `voxformer/modules/__init__.py`
imports the custom 3D module as part of package initialization, even a standard
plugin import can encounter the custom extension placeholder in an unmodified
checkout. The installed verification resolved that placeholder in an isolated
copy; the runtime skill must not claim that stock checkout import is clean.

## Model construction and image tensors

### Stage 1

`LMSCNet_SS` consumes the stage-1 dataset's pseudo occupancy rather than using
RGB features for its core `step` path. `LMSCNet_SS.foward_training()` selects
`img_metas[-1]`, reads `img_metas[0]['pseudo_pc']`, reshapes it to
`(256,256,32)`, permutes to `[batch,32,256,256]`, and computes a two-class
occupancy output at the configured `out_scale='1_2'`. The stage-1 target is
normalized to empty/occupied (`0`, `1`; `255` is ignored by the loss) by the
model path.

The stage-1 dataset uses a one-element queue wrapper and puts metadata in a
`DataContainer`. Its `img_metas` must contain `pseudo_pc`, `img_filename`, and
`sequence_id`; a missing pseudo occupancy file is a data-preparation failure,
not a model dimension tweak.

### Stage 2

`VoxFormer.extract_img_feat()` accepts an image tensor whose camera form is
`[B, N, C, H, W]` and returns a list of feature tensors shaped
`[B, N, C_feature, H_feature, W_feature]`. `VoxFormer.forward_train` and
`forward_test` first remove the outer queue element and preserve the camera
axis. With the repository's dataset/collator, the useful pre-detector shapes
are approximately:

- S: `[B, 1, 1, 3, 370, 1220]` → one camera image after queue removal;
- T: `[B, 1, 5, 3, 370, 1220]` → five image entries after queue removal.

The exact leading container shape can vary with the legacy MMCV collator, but
`model.cross_transformer.num_cams`, `model.self_transformer.num_cams`, the
feature camera dimension, and the lengths of `img_metas[...]['lidar2img']`,
`lidar2cam`, and `cam_intrinsic` must agree. The dataset crops images to
`img_H=370`, `img_W=1220` and normalizes RGB with ImageNet mean/std.

`VoxFormerHead.forward` requires:

- `mlvl_feats[0]` as `[B, num_cam, C, H, W]`, with `C=128` for the public FPN;
- `img_metas[0]['proposal']` containing a packed proposal grid that can be
  reshaped to `bev_h * bev_w * bev_z` (`128*128*16` in the public configs);
- `target` as semantic completion labels, including `255` for ignored voxels.

The head produces a dictionary with `ssc_logit`. `Header` consumes the coarse
3D feature `[1,128,128,128,16]` in its source comments/implementation shape
(conceptually `[B,embed_dims,bev_h,bev_w,bev_z]`), upsamples the spatial volume
by 2, and emits logits with 20 channels at the full
`[B,20,256,256,32]` SemanticKITTI volume for the public batch-one path. The
implementation has hard-coded batch-one assumptions in parts of this path;
do not promise arbitrary batch sizes from a config edit.

## Labels, losses, and evaluation outputs

`VoxFormerHead` uses a fixed 20-class list and creates `Header(self.n_classes,
..., feature=self.embed_dims)`. With the public configs, `CE_ssc_loss`,
`sem_scal_loss`, and `geo_scal_loss` return the stage-2 training loss entries
`loss_ssc`, `loss_sem_scal`, and `loss_geo_scal`. `ssc_loss.py` ignores target
label `255`; it treats class `0` as empty for geometry and all nonzero classes
as occupied.

On validation/test, `VoxFormerHead.validation_step()` returns a dictionary:

```text
y_pred: integer class volume after argmax over ssc_logit
y_true: target volume copied to CPU/NumPy
```

`custom_multi_gpu_test` collects these dictionaries, and each SemanticKITTI
dataset's `evaluate()` adds them to its project `SSCMetrics` instance. The
reported keys are prefixed `ssc_SemanticKITTI/` and include per-class
`SemIoU_*`, `mIoU` (mean non-empty semantic IoU), `IoU` (binary completion IoU),
`Precision`, and `Recall`. The metrics utility uses `y_true != 255` as the
valid mask. A metric key or value is not evidence that a config/model was
correct unless the associated data and checkpoint run completed.

The custom `CustomDistEvalHook` calls `custom_multi_gpu_test` and can support
dynamic intervals. The public configs use `evaluation=dict(interval=1)`; QPN
also passes its `test_pipeline`. `checkpoint_config=None` in all stage-2
presets disables periodic checkpoint saving in the child config, while QPN
sets `checkpoint_config=dict(interval=1)`.

## Checkpoint and pretrained contract

- Every stage-2 public model sets
  `model.pretrained=dict(img='ckpts/resnet50-19c8e357.pth')`. This is an
  image-backbone initialization path, resolved relative to the process working
  directory as used by the legacy config/tooling. The file is not bundled.
- `docs/install.md` asks the operator to place the ResNet-50 weights under
  `ckpts/`. Missing it normally fails model initialization or weight loading;
  do not silently remove the field when reproducing a published setup.
- The base sets `load_from=None` and `resume_from=None`. `tools/train.py` may
  set `cfg.resume_from` from `--resume-from` only when the supplied file
  exists. `tools/test.py` explicitly sets `cfg.model.pretrained=None` before
  constructing the model and then loads the required positional checkpoint
  into the built model. Thus a test checkpoint is a full model checkpoint,
  not just the ResNet file.
- A QPN checkpoint and a stage-2 VoxFormer checkpoint have different model
  keys and targets. Pair a checkpoint with the exact family/stage/config that
  produced it; a stage-1 checkpoint does not create stage-2 `queries` files.
- The README links external model artifacts for QPN, S, T, S-deform3D, and
  T-deform3D. The links are provenance only; weights must be obtained and
  approved separately and are never part of this skill.

## Device and backend expectations

Static config validation and shape arithmetic are safe on CPU. Actual model
execution is CUDA-first: standard attention uses MMCV deformable attention and
project execution uses the legacy OpenMMLab native stack. The deform3D branch
additionally imports `deform3dattn_custom_cn`, built from `deform_attn_3d` with a
compatible CUDA/Torch ABI. There is no truthful CPU substitute for either
full model execution or the custom operator.

Use the sibling environment route for package/version and backend checks. Keep
these distinct outcomes in reports:

1. config parsed and fields are coherent;
2. plugin registries imported;
3. standard MMCV/native CUDA operators are available;
4. the custom deform3D extension and its placeholder path are resolved;
5. data artifacts and the selected checkpoint exist;
6. a real train/test/evaluation run completed.

Passing an earlier item never implies the later items.
