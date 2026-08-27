# Legacy model workflows

All commands assume the repository root is the current directory. These are
procedures, not installers. Make sure the target TensorRT/CUDA environment has
been selected before compiling; the repository's Makefiles default to paths
such as `<CUDA_ROOT>` and `<TENSORRT_ROOT>`.

## 1. Inspect and validate before building

Run the safe, standard-library-only check:

```shell
python3 skills/disco/tensorrt-demos/sub-skills/legacy-models/scripts/validate-legacy-model-assets.py --repo-root .
```

The validator checks descriptors, expected model weights, the 1000-line
ImageNet synset/label file, and generated runtime outputs without opening or
copying binary content. It exits nonzero for missing source descriptors/weights or a
malformed label file. Missing engines and `pytrt` are warnings unless
`--require-runtime` is supplied.

Expected source paths:

```text
googlenet/deploy.prototxt
googlenet/deploy.caffemodel
googlenet/synset_words.txt
mtcnn/det1_relu.prototxt   mtcnn/det1_relu.caffemodel
mtcnn/det2_relu.prototxt   mtcnn/det2_relu.caffemodel
mtcnn/det3_relu.prototxt   mtcnn/det3_relu.caffemodel
```

Do not create placeholder weights to satisfy this check. The MTCNN prototxts
are deliberately the `*_relu` variants: their ReLU/Scale/Eltwise structure is
the repository's workaround for PReLU unsupported in TensorRT 3.x/4.x.

## 2. Build the GoogLeNet engine

```shell
cd googlenet
make TARGET=$(uname -m)       # use TARGET=x86_64 or TARGET=aarch64 as needed
./create_engine
cd ..
```

`googlenet/Makefile` includes `common/Makefile.config`. The C++ builder parses
`deploy.prototxt` and `deploy.caffemodel`, marks the Caffe `prob` output, uses
FP16 when `platformHasFastFp16()` reports it, and uses a 64 MiB workspace in
its TensorRT 7+ branch. It writes `googlenet/deploy.engine`, then reloads it
and expects two bindings: input `data` and output `prob`.

If the target needs non-default CUDA or TensorRT locations, pass Makefile
variables rather than editing generated output, for example:

```shell
make TARGET=x86_64 CUDA_INSTALL_DIR=/opt/cuda \
     TENSORRT_INCS='-I/opt/tensorrt/include' \
     TENSORRT_LIBS='-L/opt/tensorrt/lib'
```

`TENSORRT_INCS` and `TENSORRT_LIBS` are consumed by `common/Makefile.config`.
Check the actual Makefile/compiler output if a platform uses different parser
library names. The source links `nvinfer`, `nvparsers`, `nvinfer_plugin`, CUDA,
cuDNN, cuBLAS, and runtime libraries.

## 3. Build the three MTCNN engines

```shell
cd mtcnn
make TARGET=$(uname -m)
./create_engines
cd ..
```

The builder creates and then deserializes:

- `det1.engine` (PNet), max batch 1; outputs `prob1`, `conv4-2`.
- `det2.engine` (RNet), max batch 256; outputs `prob1`, `conv5-2`.
- `det3.engine` (ONet), max batch 64; outputs `prob1`, `conv6-2`, `conv6-3`.

It expects 3, 3, and 4 bindings respectively. A failure after serialization
usually indicates a parser, binding-name, or runtime compatibility issue, not
a missing Python package.

## 4. Compile the Cython `pytrt` bridge

From the repository root:

```shell
python3 -m pip install --user Cython   # only if Cython is already approved
make PYTHON=python3
```

The second command runs `python3 setup.py build_ext -if`, using NumPy's include
path plus `<CUDA_ROOT>/include`, `<TENSORRT_ROOT>/include`, and
`<SYSTEM_INCLUDE_ROOT>`. `setup.py` compiles `pytrt.pyx` as C++ and links
`trtNet.cpp`'s TensorRT/CUDA implementation through the extension build. It
links `nvinfer`, `cudnn`, `cublas`, `cudart_static`, `nvToolsExt`, `cudart`, and
`rt`. Override the setup file or environment only in a target-specific,
reviewed build; do not commit generated `pytrt.cpp` or `*.so` here.

The extension has two wrappers:

- `PyTrtGooglenet(engine_path, (3,224,224), (1000,1,1))`, fixed batch 1.
- `PyTrtMtcnn(engine_path, input_shape, output_shapes...)`, selecting det1,
  det2, or det3 by the engine path and requiring `set_batchsize()` before
  `forward()`.

A successful build does not prove engine compatibility. Import it and run a
small engine trial only after the exact TensorRT runtime and generated engines
are present.

## 5. Run GoogLeNet classification

The script imports `PyTrtGooglenet` at startup, loads
`googlenet/synset_words.txt`, and deserializes `googlenet/deploy.engine`.
The input is resized to 224×224, converted BGR HWC→CHW, converted to float32,
and subtracts `[104, 117, 123]`. Output `prob` is squeezed, sorted, and the
three highest scores are displayed with their corresponding labels.

Examples:

```shell
python3 trt_googlenet.py --image /path/to/image.jpg
python3 trt_googlenet.py --video /path/to/video.mp4 --video_looping
python3 trt_googlenet.py --usb 0 --width 1280 --height 720 --copy_frame
python3 trt_googlenet.py --rtsp 'rtsp://user:pass@host/live.sdp' --rtsp_latency 200
python3 trt_googlenet.py --onboard 0 --width 1280 --height 720
python3 trt_googlenet.py --gstr 'v4l2src device=/dev/video0 ! video/x-raw, width=(int){width}, height=(int){height} ! videoconvert ! appsink'
```

`--crop` center-crops a square before resize. `--do_resize` forces image/video
sources to the requested `--width`/`--height`; otherwise an image keeps its
native dimensions before the model's own 224×224 resize. The asynchronous
variant has the same camera arguments and crop behavior:

```shell
python3 trt_googlenet_async.py --image /path/to/image.jpg --crop
```

Use `--help` after `pytrt` and the engines are available. The repository's
async script contains a display-help toggle defect in its keyboard branch
(`show_help` is referenced without being initialized); treat this as a source
bug and prefer the synchronous script for a first trial.

## 6. Run MTCNN face detection

`trt_mtcnn.py` imports `TrtMtcnn`, which eagerly loads all three fixed paths:
`mtcnn/det1.engine`, `mtcnn/det2.engine`, and `mtcnn/det3.engine`. The pipeline
accepts an OpenCV BGR image, rescales large frames to no more than 1280×720,
converts BGR to RGB, runs PNet→RNet→ONet, and maps coordinates/landmarks back
to the original size.

```shell
python3 trt_mtcnn.py --image /path/to/faces.jpg --minsize 40
python3 trt_mtcnn.py --video /path/to/video.mp4 --video_looping --minsize 60
python3 trt_mtcnn.py --usb 0 --width 1280 --height 720 --copy_frame
python3 trt_mtcnn.py --rtsp 'rtsp://user:pass@host/live.sdp' --rtsp_latency 200
python3 trt_mtcnn.py --onboard 0 --width 1280 --height 720
```

The public CLI exposes `--minsize` only. The utility defaults are PNet
threshold 0.7, RNet 0.6, ONet 0.7, scale factor 0.709, and NMS IoU thresholds
0.5/0.7/0.7 (PNet per-scale/combined, RNet, ONet Min-overlap). Keep `minsize`
at least 40; the fixed PNet input stack is designed around a maximum 1280×720
frame and up to nine scales. See [api-reference.md](../api-reference.md) for
shapes and the exact post-processing contract.

## 7. Verification sequence

1. Run the validator in source-only mode.
2. Build each engine and retain the builder's binding verification output.
3. Build/import `pytrt` in the same environment.
4. Run `python3 trt_googlenet.py --help` and `python3 trt_mtcnn.py --help`.
   These are conditional native checks, not CPU checks.
5. Run each demo against a local image; confirm the expected output shape and
   visible result. Use `Esc` to stop the repeating image source.
6. If any stage is unavailable, report the exact gate (`missing weights`,
   `TensorRT parser`, `pytrt import`, `engine deserialization`, or input
   backend) instead of claiming the demo works.
