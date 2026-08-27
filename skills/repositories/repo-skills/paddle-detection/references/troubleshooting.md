# Cross-cutting Troubleshooting

## Import and installation

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: paddle` | PaddlePaddle was not installed, or the wrong Python is active. | Run the preflight helper with the intended Python, install a CPU/GPU PaddlePaddle wheel matching Python/driver, then run `paddle.utils.run_check()`. |
| `ModuleNotFoundError: pkg_resources` while importing `ppdet` | Incompatible recent setuptools removed the legacy compatibility module used by `ppdet.model_zoo`. | Use a setuptools release that still provides `pkg_resources`; do not patch the repository just to hide the environment mismatch. |
| NumPy/OpenCV binary or ABI error | NumPy 2 or an incompatible OpenCV wheel is installed. | Pin NumPy below 2 and OpenCV at or below the repository requirement; recreate the private environment if pip mixed incompatible wheels. |
| PP-Tracking warns that `numba` is unavailable | The tracking branch has an optional numba acceleration/import path. | Install a Python-compatible numba only when using PP-Tracking; core detection and config workflows can continue without it. |
| `pip check` reports conflicts | Requirements were installed into a shared/user environment or an unsupported Python. | Prefer a new private environment, install PaddlePaddle first, then `requirements.txt`, then editable PaddleDetection. |

## Config and API

- `ArgsParser` requires `-c/--config` and parses `-o key=value` overrides into nested dictionaries. A missing `=` or an invalid YAML scalar can fail before model construction.
- `load_config(path)` accepts YAML/YML, recursively resolves `_BASE_`, and merges into global configuration state. Inspect `cfg.architecture`, `cfg.metric`, `cfg.num_classes`, readers, dataset roots, and `cfg.save_dir` after loading.
- `Trainer(cfg, mode=...)` accepts `train`, `eval`, or `test`. `test` still builds the model/test dataset but avoids the full training loop; it is the safer model-construction smoke path.
- A config missing `architecture` or `num_classes` is invalid. A class-count mismatch between annotations, label list, and config often surfaces later as shape or metric errors; validate it before training.

## Weights, configs, and downloads

- Local weights should be checked for existence and the expected suffix before invoking train/eval/infer/export.
- Remote weights and dataset download helpers require network access and may write caches. Ask for network permission and record the URL/version when reproducibility matters.
- `ppdet.model_zoo.list_model(filters)` reads the packaged `MODEL_ZOO` list. `get_weights_url(name)` returns a `ppdet://models/...` URI. `get_config_file(name)` can download a config archive using the package version; the inspected source build reports version `0.0.0` and attempted a 404 `configs/0.0.0/configs.tar` URL. Prefer an explicit local YAML in a source checkout or a released package/cache.

## Device and deployment

- `use_gpu=true` on a CPU Paddle build exits with a backend error. Check `paddle.is_compiled_with_cuda()` before setting the flag.
- `--device=GPU` and TensorRT run modes require an exported model and a Paddle Inference build with the corresponding runtime. A CPU inference pass does not validate TensorRT.
- Export outputs need `infer_cfg.yml`, `model.pdmodel`, `model.pdiparams`, and usually `model.pdiparams.info`. Missing one of these files means deployment preflight should stop.
- ONNX conversion has model-specific opset/fixed-shape limits; confirm the model family in the export reference before converting.
- Paddle Serving requires both server/client model directories and a running service. Paddle Lite additionally requires a target ABI and optimizer; do not diagnose a host CPU failure as a mobile runtime failure.

## Data and pipeline

- COCO boxes use `[x, y, width, height]`; VOC boxes use corner coordinates; MOT `labels_with_ids` uses normalized center/width/height plus identity. Mixing schemas silently corrupts training.
- Paths in dataset configs are resolved relative to the configured dataset root. Validate image existence, annotation filenames, category IDs, and `num_classes` before launching workers.
- `tools/slice_image.py` requires optional `sahi`; if it is missing, use the bundled validation helper to confirm the input COCO contract and install `sahi` only when slicing is selected.
- Pipeline input priority is camera ID over video file, video directory, RTSP, image directory, and image file according to the actual parser; specify one input mode at a time to avoid ambiguous execution.
- PP-Human/PP-Vehicle configs may auto-download several models and require video codecs, tracking, ReID, OCR, or segmentation components. Use the pipeline config summarizer first, then run with a local model bundle and a short fixture.
