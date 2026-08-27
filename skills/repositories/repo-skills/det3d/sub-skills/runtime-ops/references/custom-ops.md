# Custom Operators

`setup.py` declares CUDA extensions for PointNet2, rotated ROI align, ROI pool
3D, IoU3D, NMS, sigmoid focal loss, and synchronized batch normalization.
Other operator areas include point-cloud C++ helpers, rotated 2D IoU,
correlation/alignment, and sparse-convolution consumers.

A compatible GPU driver plus `torch.cuda.is_available()` proves only framework
runtime access. Source extension builds additionally require a CUDA toolkit
with `nvcc`, headers, a supported host compiler, matching torch C++ ABI, enough
memory/disk, and architecture flags for the target GPU. A missing `nvcc` cannot
be fixed by reinstalling only the torch wheel.

After building, verify each module import and a tiny operation before training.
Do not reuse `.so` files from another Python, torch, CUDA, compiler, or platform.
`ModuleNotFoundError: det3d.ops.nms.nms` usually means the extension was not
built/installed into the active package; rebuilding is valid only after the ABI
matrix is checked.
