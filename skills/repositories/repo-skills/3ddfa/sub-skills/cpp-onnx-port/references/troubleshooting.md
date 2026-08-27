# C++ / ONNX Troubleshooting

## Triage Order

Separate failures into these classes before changing code:

1. Build system and OpenCV discovery.
2. Missing or misplaced runtime weights/data files.
3. Image path and output directory issues.
4. YOLO detector failures.
5. ONNX predictor export/load failures.
6. Landmark post-processing mismatch.

## CMake Cannot Find OpenCV

Symptoms:

- `find_package(OpenCV REQUIRED)` fails.
- Headers such as `opencv2/dnn/dnn.hpp` are missing.
- Linker errors reference unresolved OpenCV symbols.

Checks/actions:

```bash
pkg-config --modversion opencv4 || true
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
```

Use OpenCV 4.2.0 or newer with DNN support. If OpenCV is installed in a non-default prefix, pass `OpenCV_DIR` or update the CMake search path according to that installation; do not treat this as a 3DDFA model issue.

## Demo Starts but Weights Are Missing

Symptoms:

- OpenCV errors while reading `weights/mb_1.onnx`.
- OpenCV errors while reading `weights/tiny-yolo-azface-fddb_82000.weights`.
- YOLO config loads but detector has no usable binary weights.

Expected files beside the C++ executable working directory:

```text
weights/mb_1.onnx
weights/tiny-yolo-azface-fddb_82000.weights
weights/tiny-yolo-azface-fddb.cfg
weights/param_mean_v2.txt
weights/param_std_v2.txt
weights/u_base.txt
weights/w_exp_base.txt
weights/w_shp_base.txt
```

The ONNX model and YOLO binary weights are external artifacts. The small `.cfg` and `.txt` files are source-distributed C++ support data.

## Image Is Empty or Output Is Missing

Symptoms:

- No output image is written.
- OpenCV assertions occur immediately after image loading.
- `res/test1.jpg` remains absent.

The stock demo expects to be run from the C++ directory and reads `../samples/test1.jpg`. It writes `res/test1.jpg`. Confirm:

```bash
cd "$REPO/c++"
test -s ../samples/test1.jpg
mkdir -p res
./build/demo
test -s res/test1.jpg
```

If a different input image is needed, adapt the demo's image path and rebuild or use a wrapper around the C++ classes. Do not debug detector/model quality until image loading and the output directory are confirmed.

## Detect: 0 Faces

Likely causes:

- Missing or wrong YOLO binary weights.
- The image is not readable or not the intended image.
- The face is too small, occluded, profile-view, or outside the detector's learned distribution.
- Detector confidence threshold `0.2` is still too high for the image.
- Detector rectangles are generated but later crops fail because boxes exceed image bounds.

The detector creates a 480 x 480 blob, runs OpenCV DNN, and accepts rows whose best class confidence is greater than `0.2`. It expands detected boxes by a factor of `1.4`. If debugging custom images, add rectangle clipping before cropping; out-of-bounds rectangles can produce OpenCV exceptions or invalid crops.

## ONNX Fails to Load in OpenCV DNN

Symptoms:

- `readNetFromONNX` throws parser errors.
- C++ starts but exits before inference.
- OpenCV reports unsupported layers or invalid shapes.

Checks/actions:

1. Confirm the ONNX path matches the hard-coded C++ model path or update/rebuild the C++ code.
2. Re-export with `scripts/export_mobilenet_to_onnx.py` using `--arch mobilenet_1 --num-classes 62` unless the checkpoint requires another MobileNet width.
3. Try a conservative opset such as `--opset 11` or `--opset 9` if the local OpenCV DNN parser is old.
4. If Python OpenCV is installed, test `cv2.dnn.readNetFromONNX` on the exported file before returning to C++.

## Converter Cannot Import PyTorch or MobileNet

Symptoms:

- `ModuleNotFoundError: torch` after running export.
- `mobilenet_v1.py was not found`.
- The `--help` command works but export does not.

PyTorch is required only for actual export. The helper imports it after parsing arguments so `--help` remains lightweight. For export, run in an environment with PyTorch and point `--repo-root` at a directory containing `mobilenet_v1.py` or a `c++/mobilenet_v1.py` copy.

## Converter Reports Missing or Mismatched Keys

Likely causes:

- Wrong `--arch` for the checkpoint width multiplier.
- Wrong `--num-classes`; the C++ port expects 62.
- Checkpoint key names use `fc_param.*` and need remapping to `fc.*`.
- Checkpoint was saved outside `state_dict`; select the right `--checkpoint-key` or provide a raw state dict.
- The file is not a MobileNet 3DDFA checkpoint.

Default behavior fails when important model keys are not supplied. Avoid `--allow-missing` for production C++ landmarks because it can export random-initialized layers.

## Landmark Points Are Implausible

Likely causes:

- ONNX model was exported with the wrong architecture or number of outputs.
- Shape/expression basis text files do not match the model's 62-D output convention.
- Old `param_mean.txt` / `param_std.txt` are used while the C++ code expects `_v2` files.
- Face crop is not clipped or aligned well enough after YOLO detection.
- Input preprocessing differs from the stock C++ predictor: 120 x 120 crop, scale `1/128`, mean `(127.5, 127.5, 127.5)`, no RGB swap.

## Known Limits

- The C++ port is a minimal landmark overlay demo.
- It uses CPU OpenCV DNN targets by default.
- It does not implement the full Python output surface such as dense vertices, PLY/OBJ serialization, PNCC, depth, PAF, or benchmark evaluation.
- External model weights must be acquired separately and verified by the operator.
