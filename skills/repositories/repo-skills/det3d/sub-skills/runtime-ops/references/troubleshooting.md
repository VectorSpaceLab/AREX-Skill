# Runtime Troubleshooting

- **`yaml` missing**: install the package providing PyYAML in the selected
  environment; this is required by config utilities.
- **`spconv` missing**: choose the historically compatible build or explicitly
  limit the workflow; do not claim VoxelNet/SECOND full execution without it.
- **`det3d.ops.*` missing**: inspect build logs, package location, torch/toolkit
  ABI, and extension outputs; do not copy stale shared objects.
- **`nvcc` missing but CUDA is available**: framework wheels include runtime
  libraries but not necessarily a compiler. Install/provide a compatible toolkit
  or omit source builds with an explicit block.
- **Pillow/setuptools/protobuf conflicts**: use an isolated environment and
  evidence-backed pins; do not downgrade a shared environment implicitly.
- **NCCL or device errors**: validate driver/runtime/device visibility, then
  reduce to one GPU before testing distributed launch.
- **Optional visualization imports fail**: keep core headless workflows separate;
  install VTK/Open3D/display dependencies only for that route.
- **Permissions/disk failures**: select a writable work/build directory and
  retain source data; never delete unknown outputs as a recovery shortcut.
