# Deployment Troubleshooting

- **Export directory lacks `infer_cfg.yml` or model files**: verify export command, output directory, weights path, and whether export failed before writing all artifacts.
- **`use_gpu=true` or `--device=GPU` fails**: check that PaddlePaddle is compiled with CUDA and that the requested GPU is visible. CPU export/inference does not prove CUDA deployment.
- **TensorRT mode fails or falls back**: verify TensorRT support in Paddle Inference, fixed/dynamic shapes, calibration mode, and model-family compatibility.
- **ONNX conversion fails**: use the model's supported opset and fixed-shape/export flags. Compare numeric outputs after conversion instead of assuming parity.
- **Paddle Lite build errors**: confirm target ABI, Lite library `with_extra/with_cv` settings, optimizer version, and model support.
- **Serving client cannot connect**: confirm server process, port, model directory, and client dependencies. Separate network/service failures from model export failures.
- **FastDeploy backend missing**: install the backend-specific package/runtime and verify the device first; do not run a GPU/vendor command in a CPU-only environment.
- **Benchmark logs missing**: benchmark scripts expect pre-existing exported models, output directories, and dependencies such as `pynvml`, `psutil`, or GPU runtimes. Create directories explicitly and run a single short case first.
