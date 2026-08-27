# Serving, Lite, FastDeploy, C++, and Edge Backends

## Paddle Serving

Serving requires an exported serving model, a running server, and a client. Export with `--export_serving_model=True`; the export should create `serving_server/` and `serving_client/`. Start the server with a Paddle Serving runtime and then use a client script against the service. Treat server startup, ports, GPU IDs, and client dependencies as external runtime evidence.

## Paddle Lite

Lite deployment requires an inference model, the Lite optimizer/toolchain, target ABI/library, and often a device-specific build. Convert the exported `infer_cfg.yml` to JSON with the bundled helper when preparing a Lite demo. PP-PicoDet and keypoint models have model-version constraints; verify the Lite release and target architecture.

## C++ and Paddle Inference

C++ deployment uses the Paddle Inference C++ library and CMake/build flags. Do not run C++ build instructions as a smoke check; first validate exported artifacts and the matching prediction library.

## ONNX and third-party runtimes

Paddle2ONNX conversion is model-family dependent. Some families require fixed shape, specific opsets, or special export flags. After conversion, run an ONNXRuntime inference and compare outputs on a tiny fixture before treating the conversion as successful.

## FastDeploy and vendor backends

FastDeploy routes PaddleDetection models to CPU/GPU, TensorRT, OpenVINO, ONNXRuntime, Paddle Lite, Kunlun, Ascend, Rockchip, Amlogic, Sophgo, and other targets. Each backend needs its own runtime package and device evidence. This skill can plan and preflight artifacts; it does not certify vendor backend execution without native runtime results.
