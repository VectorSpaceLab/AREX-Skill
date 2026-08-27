# Engine build workflows

This reference turns the repository's README/source evidence into explicit,
reviewable procedures. Commands are examples only: they are not safe
preflight commands if they compile, download, install, create symlinks, patch,
or overwrite files. Run them only after the gate in `SKILL.md` is satisfied and
with output locations approved.

## 1. Read-only preflight

From the generated skill directory, run the bundled diagnostics against an explicitly supplied repository root without changing it:

```shell
python3 scripts/validate-engine-build-inputs.py --repo-root /path/to/tensorrt_demos --all
python3 scripts/check_cuda_arch.py
```

Then, in the checkout, these are the native help candidates:

```shell
python3 yolo/yolo_to_onnx.py --help
python3 yolo/onnx_to_tensorrt.py --help
python3 modnet/onnx_to_tensorrt.py --help
python3 plugins/gpu_cc.py
```

The first three import optional packages before argparse. A `ModuleNotFoundError`
is therefore an environment block, not a CLI defect. `gpu_cc.py` uses the CUDA
Driver API and reports architecture strings such as `80`; no output means that
`libcuda` could not be loaded or initialization/device enumeration failed.

Before any builder, make a build record with at least:

- repository commit and clean/dirty state;
- model key, model file hashes, cfg/graph input shape and output names;
- `python3`, TensorRT, CUDA toolkit/driver, compiler, GPU architecture;
- plugin `.so` name/hash and build flags;
- calibration directory/cache identity for INT8;
- intended output path and overwrite decision;
- expected deserialization and binding/I/O checks.

## 2. Caffe GoogLeNet

Inputs in `googlenet/`:

- `deploy.prototxt`;
- `deploy.caffemodel`.

Build and inspect the C++ executable only after setting valid paths in the
included `common/Makefile.config` (or passing supported make variables):

```shell
cd /path/to/tensorrt_demos/googlenet
make TARGET=x86_64
./create_engine
```

The source marks the Caffe tensor `prob`, selects FP16 when the platform has
fast FP16, uses max batch 1, and writes `deploy.engine`. It then deserializes
the file and asserts two bindings. If using a different output name or model,
change the source and its verification expectation deliberately; do not merely
rename the file.

On x86, `README_x86.md` says to update TensorRT include/library paths in
`common/Makefile.config` and to build the Cython extension from the repository
root using `setup.py` before running the demo. That extension is an inference
runtime concern; it is not needed to understand the Caffe parser build itself.

## 3. Caffe MTCNN

Inputs in `mtcnn/`:

- `det1_relu.prototxt` + `det1_relu.caffemodel` (PNet);
- `det2_relu.prototxt` + `det2_relu.caffemodel` (RNet);
- `det3_relu.prototxt` + `det3_relu.caffemodel` (ONet).

The `_relu` names are important. The README says these model files replace
PReLU with ReLU/Scale/Elementwise Addition to work around TensorRT 3/4 PReLU
support. Do not silently substitute similarly named original MTCNN files.

```shell
cd /path/to/tensorrt_demos/mtcnn
make TARGET=x86_64
./create_engines
```

`create_engines.cpp` builds:

| Engine | Marked outputs | Max batch | Binding assertion |
|---|---|---:|---:|
| `det1.engine` | `prob1`, `conv4-2` | 1 | 3 |
| `det2.engine` | `prob1`, `conv5-2` | 256 | 3 |
| `det3.engine` | `prob1`, `conv6-2`, `conv6-3` | 64 | 4 |

The executable deserializes all three immediately. If an old Caffe parser or
implicit-batch branch is unavailable, stop at the compatibility gate rather
than changing parser APIs without rechecking output dimensions.

## 4. TensorFlow frozen graph → UFF SSD

The input model key is positional and must be one of `MODEL_SPECS` in
`ssd/build_engine.py`:

```shell
cd /path/to/tensorrt_demos/ssd
python3 build_engine.py ssd_mobilenet_v1_coco
```

The repository shell convenience script builds four models, but it is a
multi-output mutation and should only be used after review:

```shell
./build_engines.sh
```

For each model, `build_engine.py`:

1. loads the frozen `.pb` described by the model spec;
2. removes assertion/identity and obsolete graph nodes;
3. collapses namespaces into `Input`, `MultipleGridAnchorGenerator`, `NMS`,
   `concat_box_loc`, and `concat_box_conf` plugins;
4. rewrites `AddV2` → `Add` and `FusedBatchNormV3` → `FusedBatchNorm`;
5. exports a temporary `.uff` with output node `NMS`;
6. registers input `Input` with `(3,300,300)`, marks `MarkOutput_0`, enables
   FP16, builds a legacy engine with 256 MiB workspace, and writes
   `TRT_<model>.bin`.

The source loads `libflattenconcat.so` directly only for TensorRT < 7; the
README and `install.sh` document versioned `.so.5`/`.so.6` links. The exact
plugin must correspond to the TensorRT ABI. A missing `uff`, `graphsurgeon`,
TensorFlow 1-compatible graph, or plugin is a hard block.

## 5. DarkNet → ONNX

The source script expects to run from `yolo/` and finds the cfg and weights by
model stem:

```shell
cd /path/to/tensorrt_demos/yolo
python3 yolo_to_onnx.py -m yolov4-416
```

Before this build, verify both `yolov4-416.cfg` and `yolov4-416.weights` exist
and match. The source parses `net`, convolutional, maxpool, shortcut, route,
upsample, and yolo blocks; calculates class count, anchor count, output heads,
and dimensions; emits an ONNX graph; calls `onnx.checker.check_model`; and
writes `yolov4-416.onnx`. It does not fetch weights itself.

The naming forms documented by the script include `yolov3-tiny`, `yolov3`,
`yolov3-spp`, `yolov4-tiny`, `yolov4`, `yolov4-csp`, `yolov4x-mish`, and
`yolov4-p5`, followed by a dimension such as `288`, `416`, `608`, `416x256`,
`448`, or `896`. The cfg is the source of truth for custom models; the list is
not a guarantee that every derivative file exists.

## 6. ONNX → YOLO TensorRT

First compile the custom plugin in `plugins/` for the actual target:

```shell
cd /path/to/tensorrt_demos/plugins
make computes=80
```

`computes` is a space-separated pair/list accepted by the Makefile. If omitted,
the Makefile invokes its local `gpu_cc.py`. It uses `nvcc`, TensorRT headers,
`libnvinfer`, `libnvinfer_plugin`, CUDA, cuDNN, cuBLAS, and host C++11. The
result is `libyolo_layer.so`; retain the build log and architecture flags.

Then, from `yolo/`, build the baseline FP16 engine:

```shell
python3 onnx_to_tensorrt.py -m yolov4-416
```

The script reads `<model>.onnx` and `<model>.cfg`, checks parser errors,
forces batch 1, registers the custom plugin, adds `detections`, and writes
`<model>.trt`. It uses a fixed input shape from cfg and a 1 GiB workspace. The
Python import of `plugins.py` tries `../plugins/libyolo_layer.so`, so invoke
from the expected directory or adapt the loader only in a reviewed patch.

The historical scripts create derivative names by symlink, for example:

```shell
ln -s yolov3-608.cfg yolov3-int8-608.cfg
ln -s yolov3-608.onnx yolov3-int8-608.onnx
python3 onnx_to_tensorrt.py -v --int8 -m yolov3-int8-608
```

Prefer copying or using an isolated build directory if symlinks are not
approved. The output is `yolov3-int8-608.trt`; the cfg and ONNX stem must agree
with the calibration cache stem.

## 7. YOLO INT8 calibration

Prepare an approved `calib_images/` directory of representative `.jpg` files.
The repository calibrator:

- requires each network height and width to be divisible by 32;
- warns below 500 JPEGs (the README cites 500 as NVIDIA guidance and uses
  1,000 COCO validation images as an example);
- reads BGR with OpenCV, resizes, converts to RGB, transposes CHW, converts
  float32, and divides by 255;
- uses batch 1 and writes/reads a binary calibration cache.

Before building, check that the image population represents deployment, not
just convenient files. Do not reuse a cache after changing model weights,
cfg/input shape, preprocessing, or calibration population without a recorded
reason. A successful cache write is not an accuracy result; run the appropriate
COCO/mAP or task-level comparison afterward.

## 8. YOLO DLA

On a compatible Xavier-class target, use the same ONNX/cfg stem and explicit
core:

```shell
python3 onnx_to_tensorrt.py -v --int8 --dla_core 0 -m yolov3-dla0-608
python3 onnx_to_tensorrt.py -v --int8 --dla_core 1 -m yolov3-dla1-608
```

The TensorRT 7/8 branch sets DLA as the default device, sets the core, enables
strict types and GPU fallback, and adds a fixed optimization profile. The
TensorRT < 7 branch rejects DLA. Confirm the actual number of DLA cores and
runtime device-selection APIs on the target. The historical README says the
TensorRT 7.1 Python API could not explicitly select a DLA core at inference,
and records a failed `yolov4-tiny-416` DLA build; preserve these as known
limits rather than treating engine serialization as proof of placement.

## 9. MODNet ONNX → TensorRT

Use a dedicated output path and an ONNX model whose input is compatible with
the selected dimensions:

```shell
cd /path/to/tensorrt_demos/modnet
python3 onnx_to_tensorrt.py --width 640 --height 480 modnet.onnx modnet.engine
```

The parser requires TensorRT major 7 or later. The source creates an explicit
batch network, sets batch 1, an input profile named `Input`, FP16 and GPU
fallback, and a 1 GiB workspace. `--int8` and `--dla_core` are parsed but then
raise `RuntimeError`; they are not working MODNet build modes in this checkout.

For TensorRT 7.1, the README documents building the third-party `onnx-tensorrt`
submodule and invoking `onnx2trt` with `-d 16` to work around dynamic
InstanceNormalization. This is an optional, version-locked workaround and
requires an explicit third-party build approval. TensorRT 7.2 is the preferred
historical direct-converter path because the README says the InstanceNorm
issue was fixed there.

## Post-build checks

For every output:

```shell
stat -c '%n %s bytes' <engine>
sha256sum <engine>
```

Then use a version-matched deserializer or the repository executable's built-in
check. Check named I/O/bindings, fixed batch and dimensions, plugin creator
availability, and representative outputs. Do not use a CPU-only import or a
successful file write as evidence that a TensorRT engine is valid.
