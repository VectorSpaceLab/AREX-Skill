# Compatibility and backend gate

Read this before attempting a historical model import, training run, checkpoint
restore, GPU NMS call, or viewer inference.

## What the source expects

This is a 2019-era source tree with no package metadata. The public install
notes describe Python 3.6+, PyTorch 1.0+, NumPy/Numba/SciPy/scikit-image/Pillow,
Fire, tensorboardX, protobuf, OpenCV, a historical `spconv`, and optional Apex
and NuScenes devkit. Generated protobuf modules require a protobuf generation
runtime compatible with the old descriptors; protobuf 3.20.x is the safer
inspection-era choice than current protobuf releases.

The model/data imports also assume old Python behavior such as
`collections.Iterable`, eager Numba CUDA compilation, and legacy spconv names.
These are compatibility clues, not a recommendation to patch a production
installation blindly.

## Required gate for detector execution

Before a separately supplied compatible checkout is used, run the bundled
`check_legacy_backend.py` probe. With `--require-detector`, it must find the
legacy surface expected by the source, including:

- `spconv.utils.VoxelGeneratorV2`;
- `spconv.utils.non_max_suppression` (plus the related NMS helpers);
- the sparse module/container/layer behavior used by the source;
- a Numba CUDA version that can compile the repository's kernels;
- a compatible Torch/CUDA ABI and the optional packages required by the chosen
  config.

A modern `spconv` 2.x wheel can be importable while failing this gate. The
inspected current-style stack exposed a different API and did not establish
legacy detector compatibility. Do not alias symbols, replace NMS with a modern
operator, or modify generated skill instructions as a casual workaround.

## Verification boundary

The accepted runtime graph verifies only the following as executable/safe
claims:

- deterministic NumPy geometry checks;
- read-only KITTI/NuScenes layout validation;
- protobuf/config reasoning and static API inspection;
- dependency probes and CLI parser/help checks.

The following remain unverified and guarded:

- sparse VoxelNet/SECOND/PointPillars construction;
- GPU and rotated NMS kernels;
- full training, evaluation, multi-GPU, Apex/fp16, and checkpoint restoration;
- viewer `buildNet` and inference endpoints;
- real KITTI/NuScenes info generation, database sampling, and dataset metrics.

CUDA framework availability is necessary but insufficient. A CPU import does
not substitute for the historical sparse backend, and a successful one-element
CUDA tensor allocation does not validate detector kernels.

## Recovery choices

1. If a historical checkpoint or exact experiment is not required, migrate to a
   maintained SECOND implementation such as OpenPCDet or MMDetection3D.
2. If exact compatibility is required, obtain a reproducible legacy environment
   with a matching Python/Torch/spconv/Numba/CUDA combination, then rerun the
   backend probe before changing any dataset or model state.
3. If only data or geometry work is needed, keep the detector route disabled and
   use the CPU-safe sub-skills and helpers in this graph.

Record the exact backend versions, missing symbols, and first failing import in
the task handoff. Never report “verified” when the gate is blocked.
