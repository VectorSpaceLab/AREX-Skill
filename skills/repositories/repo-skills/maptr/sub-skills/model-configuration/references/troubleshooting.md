# Configuration troubleshooting

Use the static checker first. Its diagnostics are intentionally conservative: a
`PASS` means the selected structural checks passed, never that plugin import,
custom ops, data, or a model forward is ready.

| Symptom / diagnostic | Likely cause | Recovery | Stop condition |
|---|---|---|---|
| `missing required key` for `model`, `data`, `pts_bbox_head`, or `transformer` | Wrong file, unresolved base, or non-MapTR config | Run the checker on the named MapTR file; with MMCV installed, inspect the resolved config; restore the nearest family template. | Stop if the intended config is not a MapTR detector or inheritance cannot be resolved. |
| `plugin=True` but `plugin_dir` is absent | Launcher derives a package from the config directory; custom registrations may not load | Set the documented package-relative `plugin_dir` or intentionally provide a package with the same import contract. | Stop if the path is absolute, not a Python package, or outside the approved runtime layout. |
| `plugin_dir does not exist` | Typo, wrong project root, or package not present | Correct the path relative to the runtime root; do not disable plugin merely to hide a registry error. | Stop before model build until path spelling and package placement are resolved. |
| `KeyError: MapTR` / `MapTRHead` / `MapTRPerceptionTransformer` | Plugin initializer did not import, import failed, or versions disagree | Verify `plugin=True`, package importability, and the documented stack; capture the first import exception. | Stop if full plugin import is not proven; static PASS does not override this. |
| `KeyError: GeometryKernelAttention` | GKT module was not registered or the nested config is not from the GKT family | Restore the GKT nested attention structure and resolve the plugin import failure. | Stop if choosing GKT without native extension/runtime proof. |
| `No module named GeometricKernelAttention` | Custom GKT extension was not built or is not on the active Python path | Build and test it only under the environment plan for this release; do not copy an arbitrary `.so`. | Stop on missing compiler/toolkit, incompatible ABI, or any unverified CUDA architecture. |
| `undefined symbol`, `invalid device function`, or CUDA launch failure in GKT | Extension built for another Torch/CUDA/device ABI | Rebuild against the exact active Torch/CUDA combination and run the tiny forward/backward probe. | Stop if legacy compiler/toolkit cannot be reproduced. Do not claim GKT works. |
| GKT constructor rejects `embed_dims`/`num_heads` | Channel width is not divisible by head count | Choose a head count dividing `embed_dims`; retain power-of-two channels per head when possible. | Stop if the intended model width cannot satisfy the op's contract. |
| Range mismatch diagnostic names coder, encoder, assigner, or pipeline | `point_cloud_range` changed in only one location | Propagate the six values to all listed consumers and deliberately review `post_center_range`. | Stop before build; stale normalization can silently corrupt geometry. |
| BEV dimensions disagree (`bev_size`, positional encoding, head) | `bev_h`/`bev_w` changed partially | Update head, learned positional encoding, dataset splits, and any reshape/grid assumptions as a unit. | Stop if an encoder variant has different shape semantics and no source evidence. |
| `num_classes` differs from `map_classes` length | New map classes were not propagated | Update derived count, head/coder, and every dataset split. Keep object `class_names` separate. | Stop if annotations do not contain the proposed classes. |
| Point-count mismatch warning | `num_pts_per_vec` and GT count changed inconsistently | Set both deliberately; confirm dataset fixed-point format and assigner interpolation. | Stop if variable-length annotations are assumed without a conversion plan. |
| `LSSTransform` with missing `dbound` / bad voxel z | BEV pool config copied into a GKT/BEVFormer edit or vice versa | Start from `maptr_tiny_r50_24e_bevpool`; restore `dbound`, z bounds, single-level inputs, and calibration contract. | Stop if camera metadata or `bev_pool` compatibility is unavailable. |
| LSS runtime missing calibration fields | Dataset pipeline does not provide matrices expected by `BaseTransform` | Route to data preparation; verify real `camera2ego`, intrinsics, augmentation, LiDAR/ego transforms, and image shape. | Stop; never fabricate identity calibration to make the model start. |
| Fusion checker says modality/input mismatch | `model.modality`, `input_modality`, `lidar_encoder`, and point pipeline were mixed | Start from `maptr_tiny_fusion_24e`; preserve point loaders, `points` collection, LiDAR range, sparse shape, and fuser channels. | Stop if LiDAR ops or data are unavailable. |
| Fusion `AttributeError`/`None` points | Fusion branch calls voxelization without points | Fix the data contract and pipeline; camera-only data cannot feed this branch. | Stop before training/evaluation. |
| Temporal shape/scene errors | `queue_length`, nested image metadata, and `video_test_mode` disagree | Keep queue values synchronized; test with a real sequence; remember queue 1 supplies no history. | Stop if temporal metadata/can-bus fields are absent. |
| Decoder reference shape assertion | Wrong decoder/attention family or reference dimensionality | Preserve the release's 2-D reference point path and use the matching decoder config. | Stop if a custom 3-D reference design is being inferred from this release. |
| `FileNotFoundError` for pretrained weights or ann files | Dataset/checkpoint path issue, not model configuration | Route to data preparation or training/evaluation; use a documented path. | Stop; do not bypass with empty files. |
| Checker falls back to AST and warns about `_base_` | MMCV is not installed, so full inheritance is unresolved | Install/activate the approved config inspection environment or inspect a self-contained copy. | Stop if required values live only in bases and cannot be verified. |

## Difficult synthetic cases

### Case A: range changed in one place

Starting from the R50 GKT baseline, change only the top-level range to
`[-20,-20,-2,20,20,2]` while leaving the coder, encoder, assigner, and dataset
values unchanged. The checker should exit non-zero and identify at least the
stale `bbox_coder.pc_range`, transformer encoder/cross-attention range,
`train_cfg.pts.point_cloud_range`, assigner range, or `data.*.pc_range`.
Recovery is to propagate the value and review `post_center_range`, BEV cell
resolution, and filters. Do not proceed on a warning-free hand edit that did
not inspect all resolved paths.

### Case B: incompatible BEV pool/temporal fusion edit

Start from `maptr_tiny_r50_24e_bevpool.py`, add `model.modality='fusion'` and
`queue_length=4`, but do not add `lidar_encoder`, point loading/collection, or a
fusion fuser. The checker should report modality/fusion keys missing and warn
that the LSS encoder has a single-level/calibration contract. Recovery is to
choose one complete family: either restore camera-only LSS with its calibration
and queue contract, or start from `maptr_tiny_fusion_24e` and retain its GKT,
LiDAR, sparse encoder, point pipeline, and fuser. Do not infer that temporal
queue support makes the two families compatible.

### Case C: apparent GKT readiness

A config contains `GeometryKernelAttention` and the source extension directory
exists, but importing the extension raises an ABI symbol error. The checker may
still pass static structure. Expected action is to classify the result as
`static-checked / GKT unverified`, preserve the import error, and stop native
execution until an exact compatible build and forward/backward probe pass.

## Stop policy

Stop and hand off an unresolved issue when any of these remains true:

- required inherited values cannot be resolved;
- a range, class count, point count, BEV dimension, modality, or queue contract
  is inconsistent;
- plugin registration is unproven or fails;
- a required MMCV/mmdet3d/GKT custom op has an import, ABI, CUDA, or shape error;
- required real dataset metadata is absent;
- the request crosses into data preparation, training/evaluation, or
  visualization.

Record the exact config, diagnostic, evidence label, and next owner. Never turn a
runtime uncertainty into a version or command claim.
