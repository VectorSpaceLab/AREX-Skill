# Configuration troubleshooting

Use the symptom and the smallest evidence-backed correction. Keep the
original config and record the exact variant/fields changed.

## Inheritance and field overrides

**Symptom:** `Config.fromfile` reports a missing field, an unexpected default,
or a dumped config differs from the source.

**Check:** inspect `_base_` first. All public presets inherit only
`projects/configs/_base_/default_runtime.py`; they do not inherit from S or T.
The base supplies `dist_params`, `workflow`, logger defaults, and null
`work_dir`/checkpoint pointers. The child overrides `work_dir`, logging,
runner/epochs, and often `checkpoint_config`.

**Repair:** use a repository-relative config path and load it through the
legacy MMCV stack. Do not assume a commented assignment overrides a live one;
for example, stage-2 `checkpoint_config = None` is live and the preceding
commented interval is not. If using `--cfg-options`, print or dump the merged
fields before execution and ensure `model`, `data.train`, `data.val`, and
`data.test` were not accidentally replaced wholesale.

## Registry or plugin import failures

**Symptom:** `KeyError: VoxFormer`, `VoxFormerHead`, `PerceptionTransformer`,
`SemanticKittiDatasetStage2`, or an import failure from `projects`.

**Check:** confirm `plugin=True`, exactly
`plugin_dir='projects/mmdet3d_plugin/'`, repository root as the working/import
root, and that the sibling environment preflight has passed. The tools import
`projects`, which triggers the project package's registry imports. Do not fix a
registry error by changing `model.type` to an upstream class.

**Repair:** route missing packages, MMCV/mmdetection3d ABI errors, or CUDA
operator failures to `../environment-and-installation/SKILL.md`. If the error
is the custom 3D wrapper's placeholder guard during package import, use the
custom-extension caveat below. A static parse from `validate_config.py` cannot
prove registry registration.

## Standard versus custom deform3D

**Symptom:** `voxformer-S_deform3D.py` or `voxformer-T_deform3D.py` fails while
importing `deform3dattn_custom_cn`, or reports
`NotImplementedError("Use sys.path.append here to modify the path to your .so file")`.

**Cause:** `projects/mmdet3d_plugin/voxformer/modules/multi_scale_deformable_attn_3D_custom_function.py`
contains a deliberate placeholder `sys.path` line and raises before loading
the extension. The custom configs also select
`PerceptionTransformer3D`/`VoxFormerEncoder3D`/`DeformSelfAttention3DCustom`.

**Repair:** do not claim that the standard routes are unavailable. Route the
operator/toolchain repair to `../environment-and-installation/SKILL.md`; after
an approved compatible extension and import path are ready, re-run the plugin
and selected deform3D import preflight. Otherwise select the matching standard
S/T config. Do not make a fake module or silently fall back while retaining a
published deform3D claim.

## Dimension and camera mismatches

**Symptom:** reshape errors around `proposal`, unexpected FPN attention shapes,
`index out of bounds`, or errors involving `num_cams`.

**Check these coupled values:**

- range and voxel size imply the public full volume `(256,256,32)`;
- `VoxFormerHead` expects coarse `bev_h=128`, `bev_w=128`, `bev_z=16`, and
  proposal metadata that reshapes to `128*128*16`;
- FPN `out_channels`, all transformer `embed_dims`, and positional
  `num_feats` are 128, 128, and 64 respectively;
- S uses `_num_cams_=1`, `temporal=[]`; T uses `_num_cams_=5`,
  `temporal=[-12,-9,-6,-3]` in all three data splits;
- the input image entries and projection metadata lists have the same camera
  count. The dataset crops each image to 370×1220.

**Repair:** run the validator, then inspect the actual collated batch. For a
geometry adaptation update the dataset target/query shapes, head dimensions,
`get_ref_3d()` scene assumptions, and output expectations together. For a
single-image adaptation copy S or update both transformer `num_cams` fields,
all `data.*.temporal` values, and the dataset-produced metadata. Do not only
change `_num_cams_`.

## Missing ResNet or model checkpoint

**Symptom:** file-not-found for `ckpts/resnet50-19c8e357.pth`, missing keys, or a
checkpoint loads but the model fails at the first forward.

**Check:** stage-2 configs use `model.pretrained.img` for the ResNet-50
initialization; `tools/test.py` clears that field before loading its required
full checkpoint. `load_from`/`resume_from` are null in the base by default.
Confirm the checkpoint's stage, S/T/deform3D family, `embed_dims`, head class,
and output class count before changing the config.

**Repair:** place or explicitly reference an operator-approved weight at the
expected path, or route checkpoint acquisition/placement to the environment
and training/evaluation siblings. Never substitute a QPN checkpoint for a
stage-2 checkpoint, and never infer compatibility from a filename alone.
Record whether the run is initialization, resume, or test-time full-checkpoint
loading.

## Backend or native operator mismatch

**Symptom:** import errors from `mmcv.ops`, `mmdet3d.ops`, CUDA symbols, or
Torch/Torch ABI messages despite a syntactically valid config.

**Repair:** stop before model execution and use the environment route. The
standard branch needs the legacy OpenMMLab/MMCV native attention stack; the
custom branch needs the extra compiled `deform3dattn_custom_cn` extension. A
CPU config parse is still useful, but CPU is not a substitute for the model
or custom attention backend. Report the blocked backend explicitly rather than
editing the config to hide it.

## Invalid stage/data settings

**Symptom:** a model builds but cannot find `.pseudo`, labels, or query files,
or losses/targets have the wrong class count.

**Check:**

- QPN: `model.type='LMSCNet_SS'`, `class_num=2`, dataset
  `SemanticKittiDatasetStage1`, pseudo voxel path based on
  `sequences_msnet3d_sweep10/.../voxels/*.pseudo`.
- Stage 2: `model.type='VoxFormer'`, `VoxFormerHead` with 20 fixed classes,
  dataset `SemanticKittiDatasetStage2`, `labels_tag='labels'`, and
  `query_tag='query_iou5203_pre7712_rec6153'` in the public baseline.
- Stage 2's `target` is a full semantic volume; a stage-1 checkpoint alone
  does not replace its query proposal files.

**Repair:** restore the matching public preset and send artifact generation or
layout issues to `../dataset-preparation/SKILL.md`. Keep train/val/test
`type`, `split`, `test_mode`, tags, and depth/sweep settings aligned. A custom
`eval_range` of 25.6 or 12.8 must match the label masking behavior in the
stage-2 dataset rather than only changing the displayed metric range.

## Checkpoint output and execution boundary

**Symptom:** an agent proposes to validate a config by launching distributed
training or test.

**Repair:** do not launch from this route. `validate_config.py` is read-only;
use the training/evaluation sibling to preflight commands and checkpoints.
`dist_params.backend='nccl'` and the documented four-GPU commands are runtime
requirements, not evidence that a local config parse succeeded.
