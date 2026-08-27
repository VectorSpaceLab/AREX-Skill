# Cross-cutting troubleshooting

## Install/import

Use an isolated Python environment with TensorFlow 2.x, the package's base dependencies, and a compatible editable/wheel install. Run `scripts/check_stardist_env.py` from any working directory. `pip check` and imports of `stardist`, `stardist.models`, `stardist.geometry`, `stardist.matching`, and `stardist.data` are useful baseline gates. If `stardist.lib.stardist2d` or `stardist.lib.stardist3d` cannot import, the compiled extension build is broken; do not hide it by routing to an unverified accelerator.

## Optional dependencies/backends

- CUDA/TensorFlow GPU requires compatible TensorFlow GPU libraries and drivers; visible NVIDIA hardware alone proves nothing about TensorFlow execution.
- OpenCL/gputools is an optional data-generation and geometry path. Fall back to CPU C++ mode when missing.
- BioImage.IO is an optional extra; its missing imports or network/resource validation must be recorded as optional.
- QuPath/ImageJ is an external GUI workflow; static script validation is not GUI execution.
- Pretrained model retrieval may require network/cache access. Prefer local model directories offline.

## Data/config validation

Before model calls, verify axes, shape, channels, label dtype/values, grid divisibility, ray count, and anisotropy. Before metric calls, verify equal label shapes and integer non-negative IDs. Before exports, verify destination permissions, output formats, and coordinate units.

## API misuse

Use scalar `n_rays` with 2D `star_dist`; use a `Rays_Base` object with 3D `star_dist3D`. Keep probability map shape equal to the spatial prefix of distance tensors. For sparse NMS, ensure points/probabilities/distances have matching lengths. Treat `prob_thresh` and `nms_thresh` as validation-tuned parameters, not fixes for axes/model mismatch.

## Resource limits

Start with tiny fixtures, sparse outputs, and no tiling. Increase `n_tiles` for memory pressure; avoid dense/raw predictions unless needed. For block inference, enforce `min_overlap + 2*context < block_size` per axis and reconcile labels across blocks. Bound training and network/resource downloads.
