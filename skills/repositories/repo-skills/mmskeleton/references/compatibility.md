# Compatibility and Runtime Baseline

Read this before installing MMSkeleton or deciding whether a failure is an API
problem, a backend problem, or an optional detector limitation.

## Verified core baseline

The generated graph was inspected against the repository commit recorded in
`repo-provenance.md`. The private verification environment used:

- Python 3.7.16.
- PyTorch 1.13.1 with CUDA 11.7 and torchvision 0.14.1.
- CUDA compiler 11.7.99 and GCC/G++ 11.2.0 for the repository's Cython/CUDA
  extension build.
- NumPy 1.21.5, Cython 0.29.33, MMCV 1.7.2 lightweight, and lazy-import 0.2.2.
- The repository installed with its CPU and GPU NMS extensions. Core package
  imports, graph construction, `mmskl --help`, and a tiny ST-GCN CUDA forward
  all passed on a free A100.

These versions are an inspection baseline, not a claim that every modern
combination is supported. The repository's own installation guide documented
Python 3.7 and PyTorch 1.2 with CUDA 9.2 or 10.0; those historical Conda
artifacts were unavailable during this run, so a compatible newer legacy stack
was used.

## Core backend rules

- Recognition processors call `.cuda()` and the native package build includes a
  CUDA NMS extension. A CPU import or model construction is not proof of the
  full GPU path.
- Align `torch.version.cuda`, the `nvcc` used to compile extensions, and the
  host compiler. CUDA 11.7 rejected a newer compiler during the first build.
- Use a free visible GPU for the tiny smoke. An occupied default device can
  produce an apparent out-of-memory failure even when the installation is
  sound.

## Optional detector stack

Pose and video-to-skeleton workflows add MMDetection, detector configs and
checkpoints, HRNet, OpenCV/video support, and MMCV custom operators. The
lightweight MMCV package does not provide `mmcv._ext`; an attempted matching
`mmcv-full` source build was blocked by a missing `thrust/complex.h` in the
available private toolkit. Therefore this graph routes those workflows through
an explicit readiness gate and does not claim detector execution.

## Checkpoints and data

The model aliases in the recognition sub-skill resolve to remote model URLs in
the original package. Downloads are network side effects and are not performed
by the bundled smoke. Use a local checkpoint when possible, verify its class and
graph compatibility, and validate processed skeleton data before full runs.
