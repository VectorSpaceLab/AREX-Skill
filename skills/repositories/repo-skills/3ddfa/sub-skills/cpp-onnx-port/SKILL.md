---
name: cpp-onnx-port
description: "Operate the optional 3DDFA C++ OpenCV DNN port, checkpoint-to-ONNX
  export, weight placement, build/run expectations, and C++ troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# cpp-onnx-port

Use this sub-skill when the task is about the optional 3DDFA C++ demo, OpenCV DNN execution, MobileNet checkpoint export to ONNX, C++ weight placement, CMake/OpenCV build behavior, or C++ output failures.

Do not use this sub-skill as the primary guide for Python inference, rendering internals, training, or benchmark evaluation. Route those tasks to sibling skills when available:

- Python image/video inference and checkpoint choice: `../python-inference/SKILL.md`
- Geometry, vertices, OBJ/PLY, PNCC, depth, and rendering internals: `../geometry-rendering/SKILL.md`
- Training recipes, losses, checkpoints, and benchmarks: `../training-evaluation/SKILL.md`

## Operating Map

1. For C++ build and demo behavior, read `references/cpp-build-and-runtime.md`.
2. For checkpoint export, read `references/onnx-export.md` and use `scripts/export_mobilenet_to_onnx.py` instead of relying on the original conversion helper.
3. For missing faces, missing weights, OpenCV DNN, ONNX, CMake, or output-image failures, read `references/troubleshooting.md`.

## Key Constraints

- The C++ port is optional and unoptimized; it relies on OpenCV DNN and was documented for OpenCV 4.2.0 or newer.
- The C++ demo uses CPU OpenCV DNN backends for both the YOLO face detector and MobileNet landmark predictor.
- The source distribution includes C++ matrix/config text files, but the MobileNet ONNX file and YOLO binary weights are external artifacts that must be supplied by the operator.
- The C++ demo is hard-coded around a single sample image and writes a landmark-overlay image under its result directory unless the C++ source is adapted.
- Keep `num_classes=62` for C++ landmark compatibility: 12 pose/projection values, 40 shape coefficients, and 10 expression coefficients.

## Safe Actions

- Build only after confirming OpenCV development headers/libraries are available and the required external model files are present.
- Export ONNX from a known 3DDFA MobileNet checkpoint with the bundled helper and inspect remapped checkpoint keys before trusting the file.
- Treat CMake, OpenCV, detector, predictor, and output-path problems as separate failure classes; do not debug them as one generic C++ failure.
