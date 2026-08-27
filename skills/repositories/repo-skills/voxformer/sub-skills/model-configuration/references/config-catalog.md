# VoxFormer configuration catalog

All five public presets are Python config files, not independent packages. Each
sets `_base_ = ['../_base_/default_runtime.py']`. There is no S→T inheritance:
the four stage-2 files repeat their model and data dictionaries. The base
supplies `dist_params.backend='nccl'`, `workflow=[('train', 1)]`, logging,
`work_dir=None`, `load_from=None`, and `resume_from=None`; the child config
overrides or adds the values shown below. `Config.fromfile` resolves this base
before the tools build the model.

## Preset matrix

| Preset | Stage and role | Model / dataset | Image and temporal contract | Attention family |
|---|---|---|---|---|
| `qpn.py` | Stage 1, class-agnostic query proposal network | `LMSCNet_SS` / `SemanticKittiDatasetStage1` | One image entry; `_nsweep_=10`, `_depthmodel_='msnet3d'`; no `temporal` field | LMSCNet occupancy network; not the VoxFormer transformer |
| `voxformer-S.py` | Stage 2, standard single-image semantic completion | `VoxFormer` + `VoxFormerHead` / `SemanticKittiDatasetStage2` | `_num_cams_=1`, `_temporal_=[]` | `PerceptionTransformer`, `VoxFormerEncoder`, `DeformSelfAttention` |
| `voxformer-T.py` | Stage 2, standard temporal/multi-image semantic completion | same as S | `_num_cams_=5`, `_temporal_=[-12,-9,-6,-3]` (current image plus four references) | `PerceptionTransformer`, `VoxFormerEncoder`, `DeformSelfAttention` |
| `voxformer-S_deform3D.py` | Stage 2, custom 3D self-attention, single image | same as S | `_num_cams_=1`, `_temporal_=[]` | Standard cross transformer plus `PerceptionTransformer3D`, `VoxFormerEncoder3D`, `VoxFormerLayer3D`, `DeformSelfAttention3DCustom` |
| `voxformer-T_deform3D.py` | Stage 2, custom 3D self-attention, temporal/multi-image | same as T | `_num_cams_=5`, `_temporal_=[-12,-9,-6,-3]` | Standard cross transformer plus the custom 3D self-attention branch |

The README model table reports S/T and S/T-deform3D as separate 20-epoch
model families. The public config spelling is `voxformer-T_deform3D.py` (not a
hyphenated `T-3D.py`).

## Shared geometry and model fields

The stage-2 configs share these values:

- `point_cloud_range = [0, -25.6, -2.0, 51.2, 25.6, 4.4]` in metres and
  `voxel_size = [0.2, 0.2, 0.2]`. The implied full SemanticKITTI volume is
  `(256, 256, 32)` in the repository's x/y/z order.
- `model.pts_bbox_head.bev_h=128`, `bev_w=128`, `bev_z=16`, and
  `embed_dims=128`. `num_points_in_pillar=8`, cross/self layers are 3/2,
  cross/self sampling points are 8/8, and `num_levels=1`.
- `model.img_backbone` is ResNet-50 with `out_indices=(2,)`, frozen stage 1,
  non-trainable BN (`norm_cfg.requires_grad=False`, `norm_eval=True`). Its
  selected feature has 1024 channels; `img_neck` maps it to 128 channels with
  one FPN output (`num_outs=1`).
- `model.pts_bbox_head.positional_encoding` is
  `LearnedPositionalEncoding` with `num_feats=64` and 512 row/column
  embeddings. `cross_transformer` and the standard `self_transformer` both
  set `rotate_prev_bev=True`, `use_shift=True`, and `embed_dims=128`.
- `train_cfg.pts` repeats `voxel_size` and `point_cloud_range`, with
  `grid_size=[512, 512, 1]` and `out_size_factor=4`. This is an inherited
  mmdetection3d training-config contract; it is not the semantic output grid
  and should not be mistaken for `bev_h/w/z`.
- `CE_ssc_loss=True`, `geo_scal_loss=True`, and `sem_scal_loss=True` in the
  stage-2 head. Stage-2 labels are the 20 classes whose order is implemented
  in `VoxFormerHead.class_names`, beginning with `empty, car, bicycle` and
  ending with `pole, traffic-sign`.
- `data.samples_per_gpu=1`, `workers_per_gpu=4`, and the custom distributed
  sampler fields are present in every public preset. `data_root='./kitti/'`
  and `preprocess_root='./kitti/dataset'` are repository-relative defaults,
  not a guarantee that those artifacts exist.

The head's `get_ref_3d()` fixes the semantic scene size to `(51.2,51.2,6.4)`
and origin `[0,-25.6,-2]`. It creates 128×128×16 coarse voxel references.
`Header` upsamples its `[1,128,128,16]` feature volume by 2 and emits an
`ssc_logit` volume at `[1,20,256,256,32]`. If a geometry change is intended,
change the range, voxel size, head dimensions, reference construction, query
files, and target labels as one contract; changing only one field is unsafe.

## QPN / stage 1

`qpn.py` is not a VoxFormerHead config:

- `model.type='LMSCNet_SS'`, `class_num=2`, `input_dimensions=[256,32,256]`,
  and `out_scale='1_2'`. In `LMSCNet_SS`, `input_dimensions` is consumed as
  `(W,H,D)` for the occupancy tensor; the middle value is the 32-channel
  depth/height axis used by the first 2D convolution. The runtime input is
  reshaped to `[batch,32,256,256]`.
- `SemanticKittiDatasetStage1` exposes `class_names=['empty','occupied']`,
  reads pseudo occupancy files under
  `sequences_<depthmodel>_sweep<nsweep>/<sequence>/voxels/*.pseudo`, and
  reshapes the training target to `128×128×16`. It uses `nsweep=10` and
  `depthmodel='msnet3d'` in this preset.
- The stage-1 `train_cfg.pts.grid_size`, range, and voxel size are present for
  framework compatibility. `input_dimensions` and `out_scale` control the
  LMSCNet path; do not copy the stage-2 `VoxFormerHead` fields into this model.
- Stage 1 creates class-agnostic occupancy/query information for stage 2. The
  exact query filename suffix is selected by the stage-2 `query_tag`; see
  `../dataset-preparation/SKILL.md` for generation and layout. The checked-in
  `LMSCNet_SS.foward_test` contains a `save_query_path` reference whose setup
  is commented out in the source, so inspect/fix the output destination before
  relying on QPN test to generate files.

## Stage 2 data coupling

All four stage-2 presets use:

```python
dataset_type = 'SemanticKittiDatasetStage2'
_nsweep_ = 10
_depthmodel_ = 'msnet3d'
_labels_tag_ = 'labels'
_query_tag_ = 'query_iou5203_pre7712_rec6153'
eval_range = 51.2
```

Each `data.train`, `data.val`, and `data.test` entry passes `split`,
`test_mode`, `data_root`, `preprocess_root`, `eval_range`, `depthmodel`,
`nsweep`, `temporal`, `labels_tag`, and `query_tag`. Stage 2 reads query
proposal files from the `queries` directory and full labels from the selected
`labels_tag`; a stage-1 weight file does not satisfy this input contract.
`eval_range` may be adapted to 25.6 or 12.8 only with the corresponding label
mask semantics implemented by `SemanticKittiDatasetStage2.get_gt_info()`.

## Single versus temporal input

- S passes `temporal=[]` to the dataset. The dataset returns one RGB image,
  and `_num_cams_=1` must match the one feature-camera dimension.
- T passes four offsets. `SemanticKittiDatasetStage2.get_input_info()` returns
  the current frame followed by the four reference-frame images, and metadata
  contains matching projection lists. The intended feature-camera dimension
  is five, hence `_num_cams_=5` in both T configs.
- The data collator adds an outer one-element queue dimension. The detector
  takes the final queue element (`img[:, -1, ...]`) and preserves the inner
  image/camera dimension. A useful expected shape after collation is
  `[B,1,1,3,H,W]` for S and `[B,1,5,3,H,W]` for T, before the detector removes
  the queue dimension. Do not infer T from a non-empty variable alone: update
  `_num_cams_`, `temporal`, dataset-produced image lists, and metadata together.
- To adapt T to one image, copy S or set `_num_cams_=1` and
  `_temporal_=[]` everywhere that `data.*.temporal` is passed. Keep the same
  `labels_tag`, `query_tag`, range, and class order unless the data artifacts
  were regenerated for another contract.

## Standard versus deform3D adaptation

The cross-attention branch is the same in S/T and their deform3D counterparts:
`DeformCrossAttention` wraps MMCV's `MSDeformableAttention3D`. Only the
self-attention branch changes as follows:

| Standard | Deform3D |
|---|---|
| `type='PerceptionTransformer'` | `type='PerceptionTransformer3D'` |
| `VoxFormerEncoder` / `VoxFormerLayer` | `VoxFormerEncoder3D` / `VoxFormerLayer3D` |
| `DeformSelfAttention` | `DeformSelfAttention3DCustom` |

Switch all three coupled self-branch types together. Do not change only the
attention `type`, and do not replace cross attention with the custom 3D
self-attention. The custom function imports `deform3dattn_custom_cn` and the
checked-in wrapper first raises `NotImplementedError` until its placeholder
extension path is repaired. This is a source caveat, not a reason to hide the
standard S/T routes. Use the environment sibling for the CUDA/ABI/build gate.

## Safe adaptation checklist

1. Copy the nearest public config and give it a new `work_dir`.
2. Change only one conceptual axis at a time: stage, S/T, geometry, or
   standard/deform3D.
3. Keep `model.embed_dims`, FPN `out_channels`, transformer `embed_dims`,
   positional `num_feats` relationship, and FFN dimensions compatible. The
   public relationship is 128 / 128 / 64, with FFN `feedforward_channels=1024`
   and `_ffn_dim_=256`.
4. If changing camera or temporal count, update both transformer `num_cams`
   fields and the dataset `temporal` list in train/val/test.
5. If changing stage, change `model.type`, dataset type, class count/target
   contract, and all stage-specific data tags together. Never mix QPN's
   two-class target with the 20-class head.
6. Run `validate_config.py`, then perform plugin and dataset/model construction
   preflights in the prepared environment. Only after those pass hand off to
   the training/evaluation route.
