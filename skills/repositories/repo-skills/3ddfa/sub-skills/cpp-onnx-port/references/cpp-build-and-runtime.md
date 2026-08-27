# C++ Build and Runtime Reference

## What the C++ Port Provides

The optional C++ port builds one executable named `demo`. It combines:

- a YOLO face detector loaded through OpenCV DNN from a Darknet `.cfg` file plus external binary `.weights` file;
- a MobileNet 3DDFA landmark predictor loaded through OpenCV DNN from an ONNX file;
- small C++ matrix helpers and text basis files for converting the 62-D MobileNet output into 68 landmark points;
- a simple demo loop that draws the 68 points on one image and writes an output image.

The port is documented as not optimized. It is a landmark demo, not a complete replacement for Python dense rendering, OBJ/PLY export, PNCC, depth, PAF, training, or benchmark workflows.

## Build Prerequisites

Required:

- C++ compiler and CMake.
- OpenCV development package with DNN support, version 4.2.0 or newer.
- The C++ source files and `CMakeLists.txt` from a 3DDFA checkout.

The CMake project links `${OpenCV_LIBS}` and builds:

```text
demo.cpp
face_reconstruction.cpp
yolo.cpp
matrix.cpp
```

A modern equivalent of the documented build flow is:

```bash
cd "$REPO/c++"
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

The original documentation used `mkdir build && cd build && cmake .. && make`; both patterns are equivalent when OpenCV is discoverable by CMake.

## Expected Runtime Layout

Run the executable from the C++ directory so hard-coded relative paths resolve as expected:

```bash
cd "$REPO/c++"
./build/demo
```

The demo expects the following runtime files relative to the C++ directory:

```text
weights/
  mb_1.onnx                              # external, or adapt code to another ONNX name
  tiny-yolo-azface-fddb_82000.weights    # external Darknet weights
  tiny-yolo-azface-fddb.cfg              # small text config included with the C++ port
  param_mean_v2.txt                      # 62-row parameter mean used by the C++ predictor
  param_std_v2.txt                       # 62-row parameter std used by the C++ predictor
  u_base.txt                             # 204-row mean landmark basis vector
  w_exp_base.txt                         # 204 x 10 expression basis text data
  w_shp_base.txt                         # 204 x 40 shape basis text data
res/
  test1.jpg                              # output path used by the demo
../samples/test1.jpg                     # input image path hard-coded by the demo
```

The source distribution also contains older `param_mean.txt` and `param_std.txt`; the current C++ predictor code uses the `_v2` files.

External artifacts are not bundled in the source C++ tree:

- `mb_1.onnx` or another 62-output MobileNet ONNX model.
- `tiny-yolo-azface-fddb_82000.weights` for the YOLO face detector.

The small text `.cfg` and basis `.txt` files are part of the C++ port and should remain beside the external weights in `weights/`.

## Demo Behavior

Important hard-coded defaults in the C++ demo:

- Predictor ONNX path: `weights/mb_1.onnx`.
- YOLO weights path: `weights/tiny-yolo-azface-fddb_82000.weights`.
- YOLO config path: `weights/tiny-yolo-azface-fddb.cfg`.
- Input image path: `../samples/test1.jpg`.
- Output image path: `res/test1.jpg`.

Runtime steps:

1. Load YOLO detector and MobileNet ONNX predictor with OpenCV DNN.
2. Read the image.
3. Build a 480 x 480 detector blob with scale `0.00392`, RGB channel swap enabled, and no crop.
4. Run YOLO and keep detections with confidence greater than `0.2`.
5. Crop each detected rectangle and create a 120 x 120 MobileNet blob with scale `1/128`, mean `(127.5, 127.5, 127.5)`, no RGB swap, and no crop.
6. Run the ONNX predictor and print per-face inference time when benchmark mode is enabled.
7. Denormalize the 62-D output with `param_mean_v2.txt` and `param_std_v2.txt`.
8. Reconstruct 68 2D landmark positions using the shape/expression bases and draw them on the original image.
9. Write `res/test1.jpg`.

## C++ Predictor Shape Contract

The C++ predictor assumes the ONNX output has exactly 62 values:

```text
0..11    projection/pose rows and offsets
12..51   40 shape coefficients
52..61   10 expression coefficients
```

The post-processing code uses:

- `u_base.txt` as a 204 x 1 vector reshaped into 3 x 68 landmarks;
- `w_shp_base.txt` as 204 x 40;
- `w_exp_base.txt` as 204 x 10;
- `param_mean_v2.txt` and `param_std_v2.txt` as 62 x 1.

Do not export a classifier with a different `num_classes` for the stock C++ landmark path unless the C++ post-processing and text basis files are changed consistently.

## Verification Expectations

Minimum practical checks before treating the C++ path as ready:

```bash
# OpenCV must be visible to CMake.
cd "$REPO/c++"
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release

# Required external artifacts must exist.
test -s weights/mb_1.onnx
test -s weights/tiny-yolo-azface-fddb_82000.weights

# The output directory must exist or be created.
mkdir -p res
./build/demo
test -s res/test1.jpg
```

If any step fails, classify it with `references/troubleshooting.md` before retrying.
