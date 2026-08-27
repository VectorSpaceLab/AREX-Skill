# Deployment notes

## ncnn

The repo's deployment docs describe the common flow as:

1. Export ONNX from a trained NanoDet checkpoint.
2. Convert ONNX to `ncnn` with the upstream `onnx2ncnn` tooling.
3. Optimize the result with `ncnnoptimize`.
4. Copy the generated `.param` and `.bin` files into the demo folder expected by the C++ example.

## MNN

The documented flow is:

1. Export ONNX from the checkpoint.
2. Convert the ONNX model with the MNN conversion tool.
3. Use the MNN C++ demo or Python interface with the matching input shape and normalization values.

## OpenVINO

The documented flow is:

1. Export ONNX from the checkpoint.
2. Use OpenVINO's Model Optimizer to convert the graph.
3. Match the mean / scale values to the training config when converting.
4. Use the generated XML / BIN / mapping files with the OpenVINO demo.

## LibTorch / TorchScript

1. Export TorchScript with the skill-owned exporter.
2. Build the LibTorch C++ demo with the exported model.
3. Keep the input shape and class count aligned with the training config.

## Android ncnn

- The Android example uses the same basic ncnn model files as the desktop ncnn flow.
- The deployment repo docs treat the Android project as a separate platform-specific consumer, not as a Python runtime dependency.

## What this skill bundles vs. what it only documents

- Bundled: Python-side config loading, inference, checkpoint export, and deploy conversion guidance.
- Documented only: the external C++/Android build systems and vendor toolchains.
