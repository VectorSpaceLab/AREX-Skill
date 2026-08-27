---
name: model-configuration
description: "It guides agents in selecting and safely editing MapTR model
  configurations, resolving model variants, and checking backend prerequisites
  without running a model."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# MapTR model configuration

Use this skill when the task is to choose a MapTR config family, make a
coordinated architecture or geometry edit, or explain a registration/backend
failure before training or evaluation. It is a configuration and static
compatibility guide; it does **not** prepare datasets, launch jobs, inspect
checkpoints/metrics, or render results. Route those tasks to the sibling
skills named by the parent MapTR router.

## Safe entry procedure

1. Start with a named family in the table in
   [configuration.md](references/configuration.md); do not mix fragments from
   different families until their encoder, modality, and queue contracts agree.
2. Copy the nearest config and edit the copy. Keep `_base_`, `plugin`, and
   `plugin_dir` intact unless the package layout is intentionally changed.
3. Treat `point_cloud_range`, `voxel_size`, BEV dimensions, map classes, fixed
   point counts, queue length, and modality as one coupled contract.
4. Run the bundled checker before any model build:
   `python <skill-root>/sub-skills/model-configuration/scripts/check_maptr_config.py <config.py>`.
5. Read its warnings as stop points, not as proof of runtime readiness. It
   parses configuration only and never imports the MapTR plugin or builds a
   model.

## Named families

| Family | Encoder / input | Good starting point | Main constraints |
|---|---|---|---|
| GKT camera | `BEVFormerEncoder` plus `GeometrySptialCrossAttention` and `GeometryKernelAttention` | `maptr_tiny_r50_24e` | Camera-only, fixed 3 map classes, custom CUDA op required for native execution. |
| GKT long run | Same GKT path, 110 epochs | `maptr_tiny_r50_110e` | Training duration and checkpoint handling belong elsewhere; preserve the same geometry contract. |
| GKT nano | GKT with R18 and smaller BEV | `maptr_nano_r18_110e` | `bev_h=80`, `bev_w=40`, `num_vec=100`, two decoder layers; do not copy R50 dimensions blindly. |
| BEVFormer | `BEVFormerEncoder` plus `SpatialCrossAttention` and `MSDeformableAttention3D` | `maptr_tiny_r50_24e_bevformer` | Camera metadata and MMCV deformable attention must match; no GKT build is implied. |
| BEV pool / LSS | `LSSTransform` and `mmdet3d.ops.bev_pool` | `maptr_tiny_r50_24e_bevpool` | Uses `dbound`, 3-D `voxel_size`, camera calibration metadata, and a z range different from GKT. |
| Camera + LiDAR fusion | GKT camera encoder plus `lidar_encoder` and `ConvFuser` | `maptr_tiny_fusion_24e` | Requires `modality='fusion'`, `use_lidar=True`, point pipeline keys, sparse voxel ops, and matching feature channels. |
| Argoverse2 | GKT camera path with AV2 dataset class | `maptr_tiny_r50_av2_24e` | AV2 camera count/calibration and BEV orientation differ from the common nuScenes family. |
| T4 variants | GKT or BEVFormer with smaller op launch steps | `*_t4` configs | These are memory/launch-parameter variants, not interchangeable encoders. |

The default R50 camera family records `[-15,-30,-2,15,30,2]`,
`[0.15,0.15,4]`, `bev_h=200`, `bev_w=100`, 3 map classes, 20 points per
line, 900 point queries (`50 * 20`), 50 vectors, 256 channels, and
`queue_length=1`. These are observed release defaults, not universal MapTR
requirements.

## Coupled edit checklist

When changing `point_cloud_range`, update the same six-number value in the
head bbox coder, transformer encoder/cross-attention, train config assigner,
BEV/grid geometry, and each dataset split (`train`, `val`, `test`). Update
range filters in pipelines too. Recompute or deliberately review
`post_center_range`; it is not automatically derived. If voxelization is
active, update `voxel_size`, grid dimensions, and any LSS bounds together.

When changing BEV dimensions, update `pts_bbox_head.bev_h/bev_w`, learned
positional encoding rows/columns, dataset `bev_size`, and any encoder or fuser
reshape assumptions. When changing map classes, update `map_classes`,
`num_map_classes`/head `num_classes`, dataset split `map_classes`, and the
annotation contract. When changing points per line, update both GT and
prediction counts and confirm the assigner can interpolate the two counts.

For temporal edits, keep `queue_length`, `video_test_mode`, the dataset queue,
and the image tensor shape consistent. A queue of one is still a temporal-capable
model but supplies no history during training. Do not make a temporal config a
fusion config by adding only `queue_length`.

## Registration and backend gate

The training/test entry points first load `Config.fromfile`, then, when
`plugin=True`, derive a dotted package from `plugin_dir` and import it so the
MapTR, head, transformer, attention, dataset, loss, and assigner registries are
populated. The expected convention is a package directory such as
`projects/mmdet3d_plugin/`, represented as a dotted import rooted at the
runtime package namespace. Keep the path importable and do not rely on a
working-directory accident.

The checker can verify path spelling and static key consistency, but it does
not prove that the package imports. Full plugin import is **not verified** by
this skill. GKT additionally calls `GeometricKernelAttentionFunc`, backed by
the package's `GeometricKernelAttention` extension; a present source directory
is not a built, ABI-compatible, or CUDA-capable extension. The host's visible
CUDA framework and the documented legacy versions do not establish a working
GKT build. Stop at the compatibility boundary described in
[compatibility.md](references/compatibility.md) when the op is missing or
built for another Torch/MMCV/CUDA combination.

## Model anatomy in one pass

`MapTR` is an `MVXTwoStageDetector`. It extracts camera features, optionally
voxelizes a LiDAR branch, and calls `MapTRHead`. `MapTRHead` creates BEV
queries for the attention encoder (only for `BEVFormerEncoder`), structured
instance/point queries, a `MapTRPerceptionTransformer`, classification and
point-regression branches, a `MapTRNMSFreeCoder`, `MapTRAssigner`, and point
losses. `MapTRDecoder` refines 2-D reference points layer by layer. GKT's
`GeometrySptialCrossAttention` rebatches visible camera queries and delegates
sampling to `GeometryKernelAttention`; BEVFormer uses the MMCV-compatible
3-D deformable attention path; LSS projects image features through depth and
`bev_pool`. Details and signatures are in
[api-reference.md](references/api-reference.md).

## Expected checker use

A successful static check prints the config path, parser (`mmcv.Config` or
AST fallback), family/encoder, range and BEV summary, and `PASS` for required
keys. It may print `WARN` for unresolved inheritance or an unverified custom
op. A non-zero exit means do not build the model. For a deliberately broken
file, the expected result is a non-zero exit with a diagnostic naming the
missing key, invalid six-number range, bad plugin path, or incompatible
modality/encoder coupling. See [troubleshooting.md](references/troubleshooting.md)
for recovery and stop conditions.

## Boundaries

- Dataset conversion, annotation files, filesystem layout, and calibration
  generation are data-preparation work; do not substitute guessed paths here.
- Training/evaluation launch commands, distributed settings, checkpoints, and
  metric interpretation are training-evaluation work.
- Visualization, video, and qualitative rendering are visualization work.
- This skill does not claim that a config can run merely because static parsing
  passes. A native model build remains gated on the exact legacy environment,
  all required MMDetection3D/MMCV ops, plugin registration, and GKT ABI proof.
