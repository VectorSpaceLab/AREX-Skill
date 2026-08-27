# Custom operator contracts and source map

This reference records interfaces from the checked-in source. It deliberately
excludes and does not load the precompiled `*.so`, `*.o`, and swap artifacts.
Start with the parent [cuda-extensions skill](../SKILL.md), then route model
shape questions to [models-and-architectures](../../models-and-architectures/SKILL.md)
and saved-prediction/postprocessing questions to
[inference-and-evaluation](../../inference-and-evaluation/SKILL.md).

## Operator families

| Family | Python entry point | Intended input | Intended output | Native source/build evidence |
|---|---|---|---|---|
| 2D NMS | `cuda_functions/nms_2D/pth_nms.py:nms_gpu(dets, thresh)` | contiguous CUDA float tensor `N x 5`: `(y1,x1,y2,x2,score)` | selected indices, returned on CUDA | `src/nms_cuda.c`, `src/cuda/nms_kernel.cu`, `build.py` |
| 2D NMS CPU helper | `nms_cpu(dets, thresh)` | CPU-compatible `N x 5` tensor | CPU `LongTensor` indices | `src/nms.c` and `src/nms.h`; not a substitute for exact GPU detector execution |
| 3D NMS | `cuda_functions/nms_3D/pth_nms.py:nms_gpu(dets, thresh)` | contiguous CUDA float tensor `N x 7`: `(y1,x1,y2,x2,z1,z2,score)` | selected indices, returned on CUDA | `src/nms_cuda.c`, `src/cuda/nms_kernel.cu`, `build.py` |
| 3D NMS CPU helper | `nms_cpu(dets, thresh)` | CPU-compatible `N x 7` tensor | CPU `LongTensor` indices | `src/nms.c` and `src/nms.h`; not a substitute for exact GPU detector execution |
| 2D crop/resize | `roi_align_2D/roi_align/crop_and_resize.py:CropAndResizeFunction` | image `N,C,H,W`; normalized boxes `M x 4` `(y1,x1,y2,x2)`; integer `box_ind[M]` | `M,C,crop_height,crop_width` | `src/crop_and_resize_gpu.c`, `src/cuda/crop_and_resize_kernel.cu`, CPU `src/crop_and_resize.c`, `build.py` |
| 3D crop/resize | `roi_align_3D/roi_align/crop_and_resize.py:CropAndResizeFunction` | intended image `N,C,H,W,Z`; normalized boxes `M x 6` `(y1,x1,y2,x2,z1,z2)`; integer `box_ind[M]` | intended `M,C,crop_height,crop_width,crop_zdepth` | GPU `src/crop_and_resize_gpu.c`, `src/cuda/crop_and_resize_kernel.cu`; the checked-in CPU C source remains 2D-shaped |

The wrappers import `_ext` through `torch.utils.ffi`-generated modules. The
`_ext/*/__init__.py` files call `_wrap_function` on symbols exported by the
native library. A successful import therefore requires the extension's
compiled ABI, not just Python files on `sys.path`.

## NMS behavior

### 2D

`nms_gpu` extracts `dets[:, 4]`, sorts descending, reorders the rows to a
contiguous tensor, allocates CPU `LongTensor` buffers for `keep` and
`num_out`, and calls `nms.gpu_nms(keep, num_out, dets, thresh)`. It returns
`order[keep[:num_out[0]].cuda()].contiguous()`. The corresponding CPU helper
moves `dets` to CPU and passes box columns 0–3 plus score column 4 to
`nms.cpu_nms`.

The C/CUDA implementation uses inclusive box lengths (`x2-x1+1`,
`y2-y1+1`) and suppresses when IoU is at least the threshold in CPU code. The
CUDA kernel stores five values per row, computes pairwise masks, and uses
`threadsPerBlock = sizeof(unsigned long long) * 8` (64) for bit suppression;
the C wrapper copies the mask to CPU before producing the final keep list.

### 3D

`nms_gpu` extracts the final column as score, so the required row layout is
six coordinates followed by score. The native 3D implementation computes
inclusive volume with `(x2-x1+1)*(y2-y1+1)*(z2-z1+1)` and uses the same
mask-and-CPU-finalization pattern. The CUDA kernel stores seven values per
row. The CPU helper is explicit and useful for source understanding, but the
model code imports only `nms_gpu` aliases.

`models/mrcnn.py` and `models/ufrcnn.py` call 2D/3D NMS while producing RPN
proposals and again for class-wise final detections. `models/retina_net.py`
and `models/retina_unet.py` call 2D/3D NMS in final detection filtering. These
calls receive `torch.cat((boxes, scores.unsqueeze(1)), 1)` and thresholds from
configuration. See [models-and-architectures](../../models-and-architectures/SKILL.md)
for model/config routing; do not infer a successful model run from the source
call alone.

## 2D RoIAlign/crop-and-resize

`CropAndResizeFunction` stores `(crop_height, crop_width,
extrapolation_value)`. Its `forward(image, boxes, box_ind)` creates a zeros
output and dispatches on `image.is_cuda`:

- CUDA: `_backend.crop_and_resize_gpu_forward(image, boxes, box_ind,
  extrapolation_value, crop_height, crop_width, crops)`.
- CPU: `_backend.crop_and_resize_forward(...)`.

Its backward dispatches similarly and returns an image gradient plus `None`
for boxes and box indices. The native 2D CPU code reads `N,C,H,W`, resizes
`crops` to `M,C,crop_height,crop_width`, validates `box_ind`, and performs
bilinear interpolation with normalized coordinates. The GPU wrapper passes
THC tensors and the current CUDA stream to the `.cu` launcher.

The optional `RoIAlign` module has constructor
`(crop_height, crop_width, extrapolation_value=0, transform_fpcoor=True)`. Its
docstring describes pixel-coordinate boxes `(x1,y1,x2,y2)` and the code
normalizes them to `(y1,x1,y2,x2)` for the backend. With
`transform_fpcoor=True` it applies the half-pixel spacing transform; with
`False` it directly divides the four coordinates by `width-1`/`height-1`.
The model path uses the direct `CropAndResizeFunction` alias `ra2D`, not this
module class.

## 3D RoIAlign/crop-and-resize

The direct 3D Python function adds `crop_zdepth` to the constructor and passes
it to the backend. The GPU C wrapper reads five-dimensional image/gradient
shapes, resizes five-dimensional output, and calls a CUDA launcher. The CUDA
kernel indexes output as `z + crop_zdepth * (x + crop_width * (y +
crop_height * (d + depth*b)))`, interpolating eight neighboring voxels and
using `atomicAdd` in backward.

There are two important source-backed limitations:

1. `roi_align_3D/roi_align/src/crop_and_resize.c` is textually a 2D
   `THFloatTensor` implementation: it reads four dimensions, four-coordinate
   boxes, and has no `crop_zdepth` parameter. The 3D `build.py` still lists
   this file as its CPU source. Do not claim a verified 3D CPU fallback.
2. `roi_align_3D/roi_align/roi_align.py` has a 2D-style docstring and calls
   `CropAndResizeFunction` without the required `crop_zdepth`. The model's
   `pyramid_roi_align` instead calls `ra3D(pool_y, pool_x, pool_z, 0)`
   directly. Treat the `RoIAlign` class as an unresolved source defect, not a
   working 3D contract.

The model path extracts `boxes = rois[:, :dim*2]`, uses the final ROI column
as integer `batch_ixs`, detaches both before backend dispatch, and uses
`ra2D` for two spatial dimensions or `ra3D` for three. For shape and pyramid
level context, follow [models-and-architectures](../../models-and-architectures/SKILL.md).

## Build-input map

Each NMS `build.py`:

- starts with `src/nms.c` and `src/nms.h`;
- when `torch.cuda.is_available()` is true, adds `src/nms_cuda.c`,
  `src/nms_cuda.h`, defines `WITH_CUDA`, and sets `with_cuda=True`; and
- points `extra_objects` at `src/cuda/nms_kernel.cu.o` before passing all of
  this to `torch.utils.ffi.create_extension('_ext.nms', ...)`.

Each RoIAlign `build.py`:

- starts with `src/crop_and_resize.c` and its header;
- conditionally adds `src/crop_and_resize_gpu.c`/header and the compiled CUDA
  object when CUDA is available;
- uses `-fopenmp` and `-std=c99`; and
- passes `_ext.crop_and_resize` to the same legacy FFI factory.

The README manual `nvcc` step chooses the architecture and creates the object;
`build.py` itself does not choose a modern `TORCH_CUDA_ARCH_LIST`. The active
2D CUDA directory also contains `backup.cu` and `fix.cu`, but those are not
listed by `build.py`; they are historical source variants, not active build
inputs. Use [compatibility.md](compatibility.md) and
[troubleshooting.md](troubleshooting.md) before considering any modernization.
