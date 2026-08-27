---
name: cuda-extensions
description: "Safely diagnose and plan use of this repository's legacy 2D/3D NMS
  and RoIAlign CUDA extensions without compiling or treating precompiled
  binaries as portable."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Legacy CUDA extensions

Use this sub-skill when a model import, proposal stage, RoIAlign call, or
installation question reaches `cuda_functions/`. It is an operating guide for
compatibility diagnosis and source-backed interface selection, not a build
recipe to execute automatically.

## Non-negotiable boundaries

- **Do not run `build.py` from this skill.** It invokes the removed
  `torch.utils.ffi.create_extension` API and can write native build output.
  `scripts/check_legacy_cuda_compat.py` is the read-only diagnostic entry point.
- **Do not compile the checked-in CUDA sources as part of normal diagnosis.**
  The host has no `nvcc`, and source modernization plus ABI validation is a
  separate engineering task.
- Treat exact execution of the historical detector path as
  **optional/unverified**. This includes MRCNN/U-FRCNN/RetinaNet/Retina U-Net
  runs that import the custom operators. A framework-level CUDA tensor smoke is
  evidence only for PyTorch and the driver; it is not evidence that these
  extensions work.
- There is no CPU substitute for claiming exact legacy detector execution.
  The source contains `nms_cpu`, and RoIAlign has a CPU branch, but using those
  branches does not verify the model's imported `nms_gpu`/legacy CUDA ABI path.
  Do not silently change a CUDA failure into a CPU result.
- Do not load or inspect the checked-in `*.so`, `*.o`, or swap files as runtime
  evidence. They are host- and ABI-specific artifacts; the source and wrappers
  are the portable evidence.

For a one-command, non-mutating report, run from the repository root:

```bash
python skills/disco/medical-detection-toolkit/sub-skills/cuda-extensions/scripts/check_legacy_cuda_compat.py \
  --repo-root .
```

Add `--framework-cuda-smoke` only when a tiny PyTorch allocation is safe on the
selected GPU. Read [compatibility](references/compatibility.md) before
interpreting the result, then use [troubleshooting](references/troubleshooting.md)
for a stop/route decision.

## Current verified classification

The prepared inspection stack reports a modern CUDA-capable PyTorch wheel,
CUDA available, and an A100-class (`sm_80`) device. The host driver reports CUDA 13.0. `nvcc` is absent and
`torch.utils.ffi` cannot be imported. The repository pins `torch==0.4.1` and
its README describes precompiled TitanX-era operators. Therefore the current
host is useful for a safe PyTorch CUDA smoke and static inspection, but it is
not a verified environment for the legacy operators or exact detector path.
These facts are recorded with evidence in
[compatibility.md](references/compatibility.md); do not weaken this
classification because `nvidia-smi` reports a newer driver or because a `.so`
file exists.

## Routing procedure

1. **Run the read-only checker.** Record the Python interpreter, torch/driver
   facts, presence of `torch.utils.ffi`, `nvcc`, README architecture mappings,
   build inputs, and native artifacts. The checker never imports a custom
   extension and never calls `build.py`.
2. **Separate framework CUDA from custom-op CUDA.** If the optional framework
   smoke succeeds, report only that `torch.cuda` can allocate and execute a
   tiny tensor on the selected device. A failure due to device memory, device
   selection, or driver state is a host issue; it still does not justify
   trying the legacy extension.
3. **Check dimensionality before reading signatures.** `cf.dim == 2` routes
   model proposal/detection NMS to 2D; a 3D configuration routes to 3D. The
   Mask/Faster R-CNN family additionally routes feature maps to the direct
   `ra2D` or `ra3D` function wrapper. See
   [custom-ops.md](references/custom-ops.md).
4. **Classify compatibility blockers.** Missing `torch.utils.ffi`, missing
   `nvcc`, an unsupported architecture, or an unverified precompiled binary is
   a stop condition—not a prompt to patch imports, symlink libraries, or use
   CPU silently.
5. **Route upward.** For model selection, configuration, tensor shapes, and
   output contracts, continue with
   [models-and-architectures](../models-and-architectures/SKILL.md). For
   prediction, postprocessing, 2D-to-3D merging, and saved-result behavior,
   continue with [inference-and-evaluation](../inference-and-evaluation/SKILL.md).
   Return here only for custom-op import/build/ABI diagnosis.

## Interfaces at a glance

### NMS

- `cuda_functions/nms_2D/pth_nms.py:nms_gpu(dets, thresh)` accepts a contiguous
  tensor with columns `(y1, x1, y2, x2, score)`, sorts by column 4, calls the
  legacy `_ext.nms.gpu_nms`, and returns selected indices on CUDA. Its explicit
  `nms_cpu` uses the same five-column convention but is not a CUDA execution
  substitute.
- `cuda_functions/nms_3D/pth_nms.py:nms_gpu(dets, thresh)` accepts
  `(y1, x1, y2, x2, z1, z2, score)`, sorts by the final column, calls the same
  legacy symbol, and returns selected CUDA indices. Its `nms_cpu` uses the
  seven-column convention.
- Both native implementations use inclusive `+1` extents in IoU and suppress
  when overlap is `>= thresh` on CPU. The CUDA kernels use a 64-bit suppression
  mask with 64 threads per block and perform the final keep scan on CPU.
- `models/mrcnn.py`, `models/ufrcnn.py`, `models/retina_net.py`, and
  `models/retina_unet.py` import `nms_gpu` directly for RPN and/or final
  detection suppression. These imports make exact legacy detector execution
  depend on the custom extension even when ordinary PyTorch CUDA is healthy.

### RoIAlign / crop-and-resize

- The 2D direct wrapper is
  `cuda_functions/roi_align_2D/roi_align/crop_and_resize.py:CropAndResizeFunction`.
  Construct it as `(crop_height, crop_width, extrapolation_value=0)` and call
  it with `(image, boxes, box_ind)`. The image is `N,C,H,W`; boxes are
  `M,4` normalized `(y1,x1,y2,x2)`; `box_ind` is length `M`; output is
  `M,C,crop_height,crop_width`.
- The 3D direct wrapper is
  `cuda_functions/roi_align_3D/roi_align/crop_and_resize.py:CropAndResizeFunction`.
  Construct it as `(crop_height, crop_width, crop_zdepth,
  extrapolation_value=0)`. Its intended image is `N,C,H,W,Z`, boxes are
  `M,6` normalized `(y1,x1,y2,x2,z1,z2)`, and output is
  `M,C,crop_height,crop_width,crop_zdepth`.
- `models/mrcnn.py` and `models/ufrcnn.py` call the direct wrappers as `ra2D`
  or `ra3D` in `pyramid_roi_align`; model ROIs are normalized and include a
  batch-index column before the wrapper separates `boxes` and `batch_ixs`.
- The optional `RoIAlign` classes in `roi_align.py` accept pixel-coordinate
  boxes in an `(x1,y1,x2,y2)` docstring and normalize them when
  `transform_fpcoor=True`. The 2D class is coherent with the 2D constructor.
  The checked-in 3D `RoIAlign` class is not a reliable 3D interface: it has a
  2D docstring/coordinate split and calls `CropAndResizeFunction` without the
  required `crop_zdepth`. Use the direct 3D wrapper facts above and treat this
  class as source evidence of drift, not as verified API.

For exact argument and dispatch details, follow the linked
[custom-ops reference](references/custom-ops.md). For model-level shape and
configuration contracts, follow [models-and-architectures](../models-and-architectures/SKILL.md).

## Build prerequisites (read-only planning only)

The README's historical sequence manually compiles an architecture-specific
CUDA object with `nvcc`, then invokes the per-op `build.py`:

```text
cuda_functions/nms_xD/src/cuda/
nvcc -c -o nms_kernel.cu.o nms_kernel.cu -x cu -Xcompiler -fPIC -arch=[arch]
python build.py

cuda_functions/roi_align_xD/roi_align/src/cuda/
nvcc -c -o crop_and_resize_kernel.cu.o crop_and_resize_kernel.cu -x cu -Xcompiler -fPIC -arch=[arch]
python build.py
```

The README examples map TitanX to `sm_52`, GTX 960M to `sm_50`, and GTX
1070/1080(Ti) to `sm_61`; they do not document A100 `sm_80`. Each `build.py`
uses `torch.utils.ffi.create_extension`, old TH/THC tensor APIs, C/CUDA
sources, and a precompiled `.cu.o` in `extra_objects`. This means all of the
following are prerequisites for a real legacy build: a matching historical
PyTorch/FFI ABI (the package pins 0.4.1), C/CUDA compiler headers and runtime,
`nvcc`, a target architecture flag, and compatible source/build tooling. A
CUDA-capable driver alone is insufficient. Never turn this planning section
into an unreviewed build command; use the checker and stop on the blockers in
[troubleshooting](references/troubleshooting.md).

## Review checklist

Before handing a CUDA issue to another skill or user, record:

- the exact `cf.dim`, model family, and whether the failure is at NMS, RoIAlign,
  import, or build planning;
- the input shape/column convention and whether tensors are contiguous and on
  CUDA;
- checker output for torch, `torch.utils.ffi`, `nvcc`, device capability, and
  README arch mapping;
- whether a checked-in binary was merely present or actually verified (the
  default is **not verified**);
- a clear optional/unverified label for exact detector execution, with no CPU
  substitution; and
- the next route: models/configuration, inference/result handling, or a
  separate source-modernization project.

All bundled material is cross-linked here: [custom-ops.md](references/custom-ops.md),
[compatibility.md](references/compatibility.md),
[troubleshooting.md](references/troubleshooting.md), and
[check_legacy_cuda_compat.py](scripts/check_legacy_cuda_compat.py).
