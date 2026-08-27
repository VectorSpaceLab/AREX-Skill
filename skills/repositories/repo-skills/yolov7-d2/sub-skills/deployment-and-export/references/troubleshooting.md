# Deployment and Export Troubleshooting

## `onnx` or `onnxsim` missing

Install `onnx` and `onnxsim` for export. Install `onnxruntime` for ORT inference. Keep these separate from the basic training/config dependencies.

## Export asserts input is not a file

The source export script requires `--input` to be a single image file. Use a small representative image, not a directory or video.

## Export writes to unexpected path

The source constructs output paths under `weights/` using the checkpoint basename. Ensure that directory exists and is writable, or patch the user's export launcher to accept an explicit output path.

## DETR export graph-surgery failure

If the error names `gs`, the source likely reached `change_detr_onnx` without importing `onnx_graphsurgeon`. Install/import `onnx-graphsurgeon` or bypass that helper and inspect outputs manually.

## ONNXRuntime shape/layout mismatch

Compare the model's ONNX input shape/layout to the ORT preprocessor. YOLOv7-d2 export paths can use different layouts for SparseInst, DETR, and YOLOX-like models.

## TensorRT build failure

Check TensorRT installation, CUDA compatibility, compiler/CMake versions, model opset, dynamic shape settings, and GPU availability. TensorRT engines are not portable across arbitrary TensorRT/GPU environments.

## Quantized output looks wrong

Check calibration data, opset, model family, preprocessing normalization, output scale/zero-point handling, and whether postprocess code expects float outputs.
