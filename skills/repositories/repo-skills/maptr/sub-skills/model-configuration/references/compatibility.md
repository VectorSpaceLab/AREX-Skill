# Compatibility and backend gates

Use this page to separate what the source documents, what static configuration
checks can prove, and what requires a native runtime test.

## Documented target stack

The repository installation document records this legacy combination:

```text
Python 3.8
PyTorch 1.9.1 + cu111, torchvision 0.10.1 + cu111
a matching mmcv-full 1.4.0 build
mmdet 2.14.0
mmsegmentation 0.14.1
timm
mmdetection3d from the bundled 0.17.2-era source
gcc >= 5 is suggested for compilation
shapely 1.8.5.post1 and av2 are listed by the observed requirements/evidence
```

These are documented procedure/version observations, not a guarantee that a
new host can install or execute them. Modern Torch, MMCV, CUDA, compiler, or
Python substitutions are not automatically compatible with this code's old
registries, decorators, extension ABI, or MMDetection3D ops.

## Capability gates

| Gate | Static checker can establish | Native proof still required |
|---|---|---|
| Python config syntax | Yes, with AST fallback | N/A |
| `_base_` resolution | Only with installed `mmcv.Config` | Confirm the resolved values are intended. |
| `plugin_dir` spelling and directory | Usually yes | Import package and complete registration. |
| `MapTR`/head/attention type registration | No | Import plugin and build registries. |
| MMCV `MSDeformableAttention3D` / mmdet3d `bev_pool` | No | Import the exact package and run a compatible op probe. |
| GKT source and config fields | Yes, structurally | Build/load the `GeometricKernelAttention` extension and run CUDA forward/backward. |
| LiDAR sparse encoder | Only presence of fusion keys | Matching mmdet3d sparse/voxel ops, tensor shapes, and point data. |
| LSS calibration contract | Presence of `LSSTransform` and keys | Real image metadata and `bev_pool` execution. |
| Dataset annotations/files | No | Data-preparation and dataset smoke test. |
| Accuracy, speed, memory, metrics | No | Training/evaluation workflow. |

## GKT build contract

The documented installation sequence builds the extension from the
`maptr/modules/ops/geometric_kernel_attn` package with its `setup.py` after
installing the bundled mmdetection3d package. The extension module is named
`GeometricKernelAttention` and exports
`geometric_kernel_attn_cuda_forward` and
`geometric_kernel_attn_cuda_backward`. The Python function wrapper imports that
module and calls both symbols during autograd.

A config using GKT therefore needs all of these to agree:

1. PyTorch C++/CUDA extension ABI and the CUDA toolkit used for compilation.
2. The runtime CUDA driver/device and the extension's compiled architecture.
3. The Torch and MMCV versions expected by the old source APIs.
4. `embed_dims % num_heads == 0`, valid `kernel_size`, and a compatible
   `im2col_step`.
5. Camera count, feature level count, BEV range, and reference-point shapes.

A source directory or a successful `python setup.py` return code alone is not
sufficient evidence. The minimum meaningful native test is a tiny forward and
backward using tensors on the target device through the actual wrapper, followed
by the real model's registration/build path. This skill does not run or claim
that test. If `GeometricKernelAttention` cannot import, if symbols are missing,
or if a CUDA launch reports an invalid device/ABI, stop and select a
BEVFormer/LSS family only after checking its own backend gates; do not silently
fall back from a GKT config.

## Plugin import contract

The training and test launchers call `Config.fromfile` first. If `plugin` is
truthy, they derive a dotted import from the directory containing
`plugin_dir`, then import it. With the documented `plugin_dir='projects/mmdet3d_plugin/'`,
the intended package is the repository's `projects.mmdet3d_plugin` namespace,
which imports `bevformer` and `maptr` initializers and registers the custom
classes.

This derivation is string-based and assumes importable package components. A
leading absolute path, a path with a trailing component that is a Python file,
or a package not on `PYTHONPATH` can produce a confusing module import error.
The static checker verifies a normalized directory and warns when the path is
not importable by ordinary package naming; it does not call `importlib` on the
plugin. The exact launcher remains responsible for runtime behavior.

## Variant-specific checks

### GKT / BEVFormer

Both use the attention-style BEV path and typically require one feature level in
these configs. GKT's nested attention is the custom geometry kernel; BEVFormer
uses `SpatialCrossAttention` with an `MSDeformableAttention3D` nested config.
They are not drop-in string substitutions. The camera metadata and feature
shapes must match the selected implementation.

### BEV pool / LSS

The LSS family calls `bev_pool` from mmdetection3d and constructs bounds from
`pc_range` and `voxel_size`. It expects a single feature level, calibration
matrices, and image shape metadata. A config may statically pass while failing
on missing `camera2ego`, `camera_intrinsics`, `img_aug_matrix`, `lidar2ego`, or
related metadata.

### Fusion

Fusion is not simply camera plus a flag. The source config has a LiDAR point
voxelizer, sparse middle encoder, `model.modality='fusion'`, a transformer
`modality='fusion'`, and a fuser with camera/LiDAR channels. The data pipeline
loads points and sweeps and collects `points`. The LiDAR branch uses a separate
`lidar_point_cloud_range` and fine voxel size in the observed fusion config.

### AV2

The AV2 config uses `CustomAV2LocalMapDataset`, AV2 annotation files, custom
multi-view image loading/padding, and a camera count setting that differs from
the usual six-camera constructor default. Keep the AV2 data contract intact;
do not reuse nuScenes metadata assumptions.

## Safe evidence labels

Use these labels in handoffs and incident reports:

- **documented**: directly described by the installation/config/source files.
- **static-checked**: obtained from config parsing or source-text inspection
  without importing/building the runtime.
- **environment-observed**: a version/device/file fact observed during this
  session, not a successful model proof.
- **native-verified**: only after an actual import/op/model smoke test passes.
- **unverified**: expected but not tested, especially GKT and legacy CUDA ops.

For this generated skill, GKT custom-op/CUDA verification and full plugin import
remain **unverified**. Do not elevate them because the checker prints PASS.
