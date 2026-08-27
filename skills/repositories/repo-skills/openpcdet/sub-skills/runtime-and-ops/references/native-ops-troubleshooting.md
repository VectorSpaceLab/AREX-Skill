# Native Ops Troubleshooting

OpenPCDet builds seven CUDA extension modules from `setup.py`. Full 3D detection workflows should treat these imports as required:

| Extension module | Typical users |
|---|---|
| `pcdet.ops.iou3d_nms.iou3d_nms_cuda` | 3D IoU/NMS during post-processing and evaluation |
| `pcdet.ops.roiaware_pool3d.roiaware_pool3d_cuda` | ROI-aware pooling heads |
| `pcdet.ops.roipoint_pool3d.roipoint_pool3d_cuda` | ROI point pooling |
| `pcdet.ops.pointnet2.pointnet2_stack.pointnet2_stack_cuda` | PointNet++ set abstraction / stack ops |
| `pcdet.ops.pointnet2.pointnet2_batch.pointnet2_batch_cuda` | PointNet++ batch ops |
| `pcdet.ops.bev_pool.bev_pool_ext` | BEVFusion / view-transform pooling |
| `pcdet.ops.ingroup_inds.ingroup_inds_cuda` | Group index helper kernels |

## Diagnostic sequence

1. From the generated skill root, run `python scripts/inspect_openpcdet_runtime.py --require-cuda-ops`.
2. If imports fail, inspect the first failing extension and rebuild from a clean build directory.
3. Verify PyTorch and spconv CUDA suffixes match.
4. Verify the runtime linker can find PyTorch, CUDA runtime, and spconv shared libraries.
5. Rebuild with an explicit architecture list for the target GPU if the build targets the wrong compute capability.

## Common errors

- `undefined symbol` at import time: PyTorch ABI/CUDA variant mismatch, stale extension build, or missing shared library path.
- `fatal error: thrust/complex.h` or `nv/target`: incomplete CUDA/CCCL headers.
- `no kernel image is available for execution`: extension built without the active GPU architecture; rebuild with an appropriate `TORCH_CUDA_ARCH_LIST`.
- `CUDA_HOME environment variable is not set`: the PyTorch extension builder cannot locate toolkit headers/nvcc.
- `spconv` import succeeds but model fails in sparse conv: verify the exact `spconv-cuXXX` wheel and active PyTorch CUDA runtime; mixed variants can import but fail later.

## Safe final checks

After skill generation/integration, acceptable low-cost native checks are:

- Import all native extension modules.
- Run CLI `--help` for train/test where imports are required but no data is loaded.
- Load representative YAML configs without building a dataset/model.

Do not use a successful CLI help run as proof of dataset, checkpoint, or full kernel correctness.
