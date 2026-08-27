# MODNet workflows

This reference expands the procedures in the parent `SKILL.md`. Commands are
examples; use absolute paths when a task may change its working directory.
Run from a checkout of `tensorrt_demos`, not from the skill directory.

## 1. Preflight and artifact policy

The repository's MODNet flow has four distinct artifacts:

| Artifact | Produced by | Runtime/backend | Required provenance |
|---|---|---|---|
| PyTorch checkpoint (`*.ckpt`) | upstream MODNet download | CUDA PyTorch export | upstream model/license and architecture compatibility |
| ONNX graph (`*.onnx`) | `torch2onnx.export` or supplied graph | CPU ONNX Runtime or TensorRT parser | exporter dimensions, opset, input/output names |
| TensorRT engine (`*.engine`) | Python builder or `onnx2trt` workaround | exact compatible TensorRT/CUDA/GPU target | builder version and fixed profile |
| input/background media | task owner | OpenCV/GStreamer | readable path, codec, dimensions |

The repository does not provide a portable checkpoint in this skill. A
serialized engine is not a portable substitute for a checkpoint and should not
be copied between unrelated TensorRT/GPU targets without an explicit
compatibility check.

Useful read-only checks:

```bash
cd /path/to/tensorrt_demos
python3 --version
python3 -c 'import torch; print(torch.__version__, torch.cuda.is_available())'
python3 -c 'import onnx, onnxruntime; print(onnx.__version__, onnxruntime.__version__)'
python3 -c 'import tensorrt as trt; print(trt.__version__)'
python3 -c 'import pycuda.driver as cuda; cuda.init(); print(cuda.Device(0).name())'
```

If a package is unavailable, classify the affected stage as blocked rather than
falling back to a different backend silently. The export stage specifically
uses CUDA (`.cuda()` on both the model and dummy input), ONNX validation can be
CPU-only, and TensorRT inference is CUDA-only.

## 2. Export PyTorch MODNet to fixed-shape ONNX

The source's recommended environment is a Python 3 virtual environment. Its
historical requirements pin `onnx==1.8.1`, `onnxruntime==1.6.0`, and
`torch==1.7.1` (with NumPy/OpenCV/PyImage and build helpers). The README
additionally describes a Jetson/aarch64 setup around PyTorch 1.7.0 and NumPy
below 1.17. These versions are historical evidence, not a guarantee that old
wheels install on a modern host. Prefer an isolated environment and record the
actual versions.

From `modnet/`:

```bash
python -m torch2onnx.export --width 512 --height 288 \
    /secure/path/modnet_webcam_portrait_matting.ckpt \
    /work/path/modnet.onnx
```

`-v`/`--verbose` passes verbose export logging to `torch.onnx.export`. The
script exits with an explicit missing-file error if the checkpoint does not
exist. It loads the state dict without `map_location='cpu'` and constructs a
CUDA `DataParallel` model, so a CPU-only host cannot truthfully run this
exporter without a source-level adaptation. Such an adaptation is outside the
repository workflow and must be labeled as a deviation.

Record:

- checkpoint path, source/license, and checksum if available;
- PyTorch and ONNX versions, CUDA device, and exporter command;
- export width/height (width first in CLI, H/W in tensor shape);
- ONNX opset and names (`input`, `output` expected from the source);
- output path and whether it is a generated artifact.

A custom shape must have positive dimensions and satisfy the MODNet HR branch's
height/width divisible-by-4 assertion. Keep the same shape for ONNX validation
and TensorRT engine building.

## 3. Validate ONNX on CPU

The repository visual script is:

```bash
cd modnet
python test_onnx.py
```

It expects `modnet/image.jpg` relative to the current directory and
`modnet.onnx` in that same directory. It opens a GUI window titled `Matte`; it
does not persist output. Use this as a quick source-faithful check when a
windowing environment is available.

For a headless assertion-backed check, use the same data contract in a small
throwaway script or notebook (do not add it to the runtime skill):

```python
import cv2, numpy as np, onnx, onnxruntime as ort

img = cv2.imread("modnet/image.jpg")
assert img is not None
img = cv2.resize(img, (512, 288), cv2.INTER_AREA)
img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
img = ((img.transpose(2, 0, 1).astype(np.float32) - 127.5) / 127.5)[None]
model = onnx.load("modnet.onnx")
onnx.checker.check_model(model)
session = ort.InferenceSession("modnet.onnx", providers=["CPUExecutionProvider"])
input_name = session.get_inputs()[0].name
output_name = session.get_outputs()[0].name
assert session.get_inputs()[0].shape == [1, 3, 288, 512]
result = session.run([output_name], {input_name: img})[0]
assert result.shape[0:2] == (1, 1)
assert result.shape[-2:] == (288, 512)
assert np.isfinite(result).all()
```

Some ONNX Runtime versions report symbolic dimensions as strings or use a
slightly different shape representation. For this repository's fixed export,
resolve that as a shape mismatch unless the actual runtime tensor is proven to
be `[1,3,288,512]`. The output is a sigmoid matte and should normally be
finite and approximately in `[0,1]`; treat severe out-of-range or all-constant
output as a diagnostic signal, not as an automatic pass.

CPU ONNX validation and TensorRT validation answer different questions:

- CPU ONNX: graph parses, preprocessing is wired correctly, and the output
  shape/value range is plausible.
- CUDA TensorRT: the graph parses under the installed TensorRT version, the
  fixed profile builds, CUDA buffers execute, and the engine output can be
  resized/blended.

Do not report CPU ONNX success as TensorRT success.

## 4. Build the TensorRT engine on 7.2+

First inspect the ONNX graph's actual input name and shape. The source exporter
uses lowercase `input`; the historical TensorRT builder's profile line uses
uppercase `Input`. TensorRT optimization profiles are name-sensitive. If the
builder raises an unknown-tensor/profile error, patch only that name locally or
use a tiny local wrapper that calls the same builder with the graph's actual
name. Keep the patch and version in the run record.

For the documented export, use:

```bash
cd modnet
python onnx_to_tensorrt.py -v --width 512 --height 288 \
    modnet.onnx modnet.engine
```

Although the builder parser advertises `--int8` and `--dla_core`, both paths
raise `RuntimeError` because they are explicitly unimplemented. The builder
always enables FP16. It uses a 1 GiB workspace and an explicit-batch network,
then serializes `modnet.engine`. TensorRT must be version 7+; MODNet's
InstanceNormalization requirement makes TensorRT 7.1/7.2 the historical floor
for this repository's tested path.

The builder source sets a static profile min/opt/max to
`(1,3,height,width)`, so a profile is not a dynamic-resolution capability.
With a graph exported at `512x288`, passing the default builder dimensions
`640x480` is a contract violation even if a parser accepts the graph. Use
`--width 512 --height 288` or re-export the graph at the desired dimensions.

After building, verify the serialized file exists and record:

```bash
ls -lh modnet.engine
sha256sum modnet.engine
```

A successful build does not prove runtime deserialization on another machine;
rebuild for the target when in doubt.

## 5. TensorRT 7.1 workaround

The root README documents a TensorRT 7.1 failure in the standard path:
`InstanceNormalization does not support dynamic inputs`. Its workaround is a
local build of the repository's initialized `modnet/onnx-tensorrt` submodule.
Because this submodule is intentionally not bundled into the skill and may be
uninitialized, do not run these commands blindly. Confirm the exact checkout,
network access, compiler, CUDA headers, TensorRT development libraries, and
permission to create build files first.

Source-faithful sequence from the repository root:

```bash
cd modnet
git submodule update --init --recursive
sed -i '21s/cmake_minimum_required(VERSION 3.13)/#cmake_minimum_required(VERSION 3.13)/' \
    onnx-tensorrt/CMakeLists.txt
mkdir -p onnx-tensorrt/build
cd onnx-tensorrt/build
cmake -DCMAKE_CXX_FLAGS=-I<CUDA_ROOT>/targets/aarch64-linux/include \
      -DONNX_NAMESPACE=onnx2trt_onnx ..
make -j4
cd ../..
LD_LIBRARY_PATH=$(pwd)/onnx-tensorrt/build \
    onnx-tensorrt/build/onnx2trt modnet.onnx -o modnet.engine -d 16 -v
```

The source README uses an aarch64 CUDA include path and is aimed at Jetson;
that exact path is not portable to x86_64. Adjust only after confirming the
installed CUDA/TensorRT development layout. The workaround uses FP16 (`-d 16`)
and should be tested with the same runtime that will deserialize the engine.
If the submodule is missing, use `git submodule status` and stop with an
explicit dependency block rather than treating the empty directory as source.

## 6. Run image, video, and camera matting

From the repository root, ensure `modnet/modnet.engine` exists:

```bash
python3 trt_modnet.py --image modnet/image.jpg
```

The demo constructs the `Camera` first, then an optional writer, then
`TrtMODNet`, `Background`, and `BackgroundBlender`. A missing camera image or
failed capture causes `ERROR: failed to open camera!`; a missing engine raises
when `TrtMODNet` tries to open the fixed path.

Examples:

```bash
# Still source repeated with a still replacement background
python3 trt_modnet.py --image /data/person.jpg \
    --background /data/office.jpg

# Video source and looping video background; save basename, not extension
python3 trt_modnet.py --video /data/person.mp4 --video_looping \
    --background /data/beach.mp4 --create_video /data/matted-output

# Jetson onboard camera at a requested capture size
python3 trt_modnet.py --onboard 0 --width 1280 --height 720

# USB camera, copying capture-owned frames
python3 trt_modnet.py --usb 0 --width 640 --height 480 --copy_frame
```

Image and video source dimensions are preserved unless `--do_resize` is used
for those source types. The engine always resizes internally and returns a
matte at the original frame dimensions, so output blending follows the source
frame shape. Background images/videos are resized to the camera output
`width,height`, not to the engine's fixed shape.

`Background` recognizes only lowercase `.jpg`, `.png`, `.mp4`, and `.ts` suffixes.
An empty background argument produces black. Video backgrounds loop when
`read()` reaches EOF. The demo does not verify that foreground and background
have matching frame rates; it simply reads one frame from each on every loop.

## 7. Demo mode and output writer

`BackgroundBlender(demo_mode=True)` mutates a copy/reference of the background
and matte according to a 360-frame cycle. The exact intervals use half-open
ranges:

| Frames | Effect |
|---:|---|
| 0–59 | black background, reveal original image left-to-right |
| 60–119 | black background only |
| 120–179 | replacement background, reveal replacement left-to-right |
| 180–239 | replacement background |
| 240–299 | original background, reveal original image left-to-right |
| 300–359 | original image / original background |

At the end of each call, `count = (count + 1) % 360`. The code's last phase
sets the matte to all ones, so it displays the original image. The source
comments call the sixth phase “original background,” but the implementation is
the authoritative behavior.

`--create_video NAME` calls `get_video_writer(NAME, width, height)`. The writer
runs `gst-inspect-1.0` and, if the returned text contains `omxh264dec`, creates
an OpenCV GStreamer writer to `NAME.ts`; otherwise it creates an OpenCV `mp4v`
writer to `NAME.mp4`. A system without `gst-inspect-1.0`, a broken GStreamer
pipeline, or an unavailable codec can fail before frames are processed. Check
`writer.isOpened()` in a task-specific wrapper if recording must be guaranteed;
the repository demo does not do that check.

## 8. Native candidates and safe verification

The repository's native candidates for this sub-skill are:

```bash
python3 modnet/onnx_to_tensorrt.py --help
python3 trt_modnet.py --help
```

They are help-only checks, not CPU substitutes. Both import backend-specific
modules before or during parser setup: the builder imports TensorRT, and the
demo imports PyCUDA/TensorRT through `pycuda.autoinit` and `utils.modnet`.
Therefore a missing `tensorrt`, `pycuda`, CUDA driver, or compatible ABI is a
classified environment block, not evidence that the CLI contract is wrong.

The supplied safe validator is intentionally weaker and backend-independent:

```bash
python3 skills/disco/tensorrt-demos/sub-skills/matting-inference/scripts/validate-matting-config.py --help
```

It validates dimensions, suffixes, fixed-path expectations, and optional
artifact existence without importing repository modules or mutating anything.
