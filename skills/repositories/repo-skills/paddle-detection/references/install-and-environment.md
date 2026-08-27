# Installation and Environment Boundaries

Read this before importing `ppdet`, invoking repository tools, or choosing a backend.

## Baseline

- Distribution: `paddledet`; import root: `ppdet`.
- Install a compatible PaddlePaddle build first. The checked source branch documents PaddlePaddle 2.3.2 or newer for its dygraph workflows; the production inspection used PaddlePaddle 2.6.2 CPU with Python 3.10.
- Install the repository's `requirements.txt` rather than mixing arbitrary extras. It pins NumPy below 2 and OpenCV at or below 4.6.0 and adds PyYAML, Shapely, SciPy, pycocotools, VisualDL, MOT, image augmentation, and packaging dependencies.
- From a source checkout, `python -m pip install -e .` exposes `ppdet`; use a released package/config bundle when model-zoo downloads are expected.

## Preflight

```bash
python -c "import paddle, ppdet; print('paddle', paddle.__version__, 'cuda', paddle.is_compiled_with_cuda()); print('ppdet', ppdet.__version__)"
python -c "import paddle; paddle.utils.run_check()"
python -m pip check
```

Run [`../scripts/check_paddledet_environment.py`](../scripts/check_paddledet_environment.py) for a structured report. It reports missing optional modules instead of hiding them behind a traceback.

## Backend matrix

| Backend | Use | Evidence status | Required setup |
| --- | --- | --- | --- |
| CPU | Config parsing, imports, data validation, CLI help, small model construction, and deterministic smoke checks. | Verified for package inspection. | CPU PaddlePaddle wheel, baseline requirements. |
| CUDA GPU | Training, fast inference, AMP, multi-GPU launch, and many industrial pipelines. | Optional/unverified by this skill; a visible GPU does not prove the installed Paddle wheel has CUDA. | CUDA-enabled PaddlePaddle build, compatible driver/runtime, `use_gpu=true` or `--device=GPU`. |
| TensorRT | Paddle Inference acceleration and benchmark modes `trt_fp32`, `trt_fp16`, `trt_int8`. | Optional/unverified. | Paddle build compiled with TensorRT, compatible TensorRT/CUDA, exported model shape constraints. |
| XPU/NPU/MLU/GCU/Iluvatar | Vendor-specific training/inference branches exposed by `ppdet.utils.check`. | Optional/unverified. | Vendor Paddle package and device runtime; never substitute CPU claims for this evidence. |
| Paddle Serving | Server/client deployment. | Optional/unverified. | `paddle_serving_server`, `paddle_serving_client`, exported serving model, running service. |
| Paddle Lite | Mobile/embedded deployment. | Optional/unverified. | Lite optimizer/library, target ABI/toolchain, converted model and device runtime. |
| FastDeploy/ONNX/OpenVINO | Third-party deployment paths. | Optional/unverified. | Matching converter/runtime and model support; verify output parity separately. |

## Installation pitfalls

- `ppdet.model_zoo` imports `pkg_resources`; very new setuptools releases may omit that compatibility module. If the import fails with `No module named 'pkg_resources'`, use a compatible setuptools release rather than changing PaddleDetection source.
- PP-Tracking emits a non-fatal warning when `numba` is absent. Install the version supported by the target Python only when using the PP-Tracking path; do not add it to a minimal CPU-only environment just for core detection.
- Keep `numpy<2.0` for this branch. A newer NumPy can make Paddle or older OpenCV/augmentation code fail at import time.
- `pycocotools`, `lapx`, `motmetrics`, `pyclipper`, `imgaug`, and VisualDL are workflow-dependent. If omitted, route only to workflows that do not import them and report the missing optional dependency clearly.
- `pip install -e .` may generate local version/model-zoo metadata files ignored by Git. Those files are source-build artifacts, not public runtime skill content.
