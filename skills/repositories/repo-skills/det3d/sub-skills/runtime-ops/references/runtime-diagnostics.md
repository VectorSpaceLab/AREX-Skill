# Runtime Diagnostics

Collect these facts without mutating the environment:

- Python version and platform;
- distribution/version and import location (keep local location private);
- torch version, compiled CUDA version, `torch.cuda.is_available()`, device
  count/name, and a tiny allocation/copy operation;
- `nvcc --version`, compiler version, and `CUDA_HOME` if available;
- presence/import errors for `spconv`, `yaml`, `easydict`, `addict`, dataset SDKs,
  OpenCV, VTK/Open3D, and Det3D extension modules;
- `pip check` and disk space before a rebuild.

Classify failures as: package metadata/import, missing optional dependency,
framework/backend, compiler/toolkit, extension ABI, dataset SDK/data, or
filesystem/permissions. Fix one class at a time and keep the exact error.

For distributed jobs also inspect GPU visibility, rank/world-size, master
address/port, NCCL/driver state, and whether another job owns the port.
