# Cross-cutting Troubleshooting

## Start with a safe diagnosis

From the generated skill root, run:

```bash
python scripts/check_sahi_env.py
python sub-skills/model-integrations/scripts/check_model_dependencies.py
python sub-skills/postprocess-backends/scripts/postprocess_backend_smoke.py --print-backend
```

These checks are deterministic and do not download model weights, use credentials, train models, or require GPUs.

## Install/import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'sahi'` | SAHI not installed in the active Python | Install with `pip install sahi`, then run `python -c "import sahi; print(sahi.__version__)"`. |
| `ModuleNotFoundError` for `ultralytics`, `transformers`, `torchvision`, `yolov5`, `mmdet`, `detectron2`, `inference`, or `rfdetr` | Optional detector framework not installed | Read [installation and optional dependencies](installation-and-optional-deps.md), install only the framework needed for the selected `model_type`, then rerun the model dependency checker. |
| `ImportError` mentioning `mmdet`, `mmcv`, `mmengine`, and `torch` | OpenMMLab stack not installed or incompatible | Use a dedicated environment with a compatible torch/CUDA/Python/OpenMMLab matrix. Do not fix this by installing broad extras into an unrelated environment. |
| `cv2` import errors or strange missing OpenCV attributes | Mixed OpenCV distributions or incompatible versions | Reinstall one OpenCV distribution or keep every installed `opencv-*` distribution at the same version. |
| A package imports from an unexpected checkout | Running with the wrong Python, `PYTHONPATH`, or editable install | Print `sahi.__version__` and `sahi.__file__` in the target Python. Switch environments rather than relying on shell activation assumptions. |

## Model loading failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `KeyError` or class lookup failure for `model_type` | Unsupported or misspelled model type, or a wrapper map mismatch in the installed SAHI release | Use `model-integrations/references/model-matrix.md` to choose a supported `model_type`. For YOLO variants, prefer documented aliases (`ultralytics`, `yoloe`, `yolo-world`, `yolov5`, `rtdetr`) and verify the installed release. |
| `model_path` works in the detector framework but not through SAHI | Missing `model_type`, `config_path`, `image_size`, category mapping, or optional package | Compare the wrapper-specific row in the model matrix. For MMDetection/Detectron2, provide both model weights and config where required. |
| HuggingFace/GroundingDINO returns unexpected classes or no categories | Missing `text_labels`, weak `text_threshold`, or gated/private model access | Supply stable `text_labels` for zero-shot categories, tune `text_threshold`, and provide a token only through runtime environment or arguments. |
| Roboflow route unexpectedly asks for credentials | A plain string is treated as a Universe model id; a local RF-DETR class-name string selects a local route | Use local RF-DETR class names such as `RFDETRBase`/`RFDETRSegMedium` for local models, and provide `category_mapping` for custom classes. |
| CUDA requested but torch says CUDA unavailable | CPU-only torch wheel, driver/container passthrough issue, or incompatible wheel | Verify torch CUDA with a tiny tensor allocation before loading SAHI models. Use `device="cpu"` until the target environment proves CUDA. |

## Prediction and slicing failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Too many duplicate boxes after sliced inference | Slice overlap or postprocess settings do not match object size/density | Read `sub-skills/sliced-inference/references/slicing-parameters.md` and `sub-skills/postprocess-backends/SKILL.md`; try `GREEDYNMM`, tune `postprocess_match_metric` (`IOS` for nested boxes), and adjust overlap. |
| Missing small objects | Slices too large, insufficient overlap, high confidence threshold, or class exclusion filters | Reduce slice size, keep overlap near documented defaults, lower confidence threshold for the call, and check `exclude_classes_by_name`/`exclude_classes_by_id`. |
| Large objects split or partially detected | Sliced-only inference misses full context | Keep standard+sliced mode enabled or include a standard pass. |
| Folder/video CLI produces no outputs | Wrong `--source`, disabled visual export, invalid project/name path, or model load failure occurred before export | Run a single-image command first, use `--novisual` only intentionally, and check the terminal error before inspecting output folders. |
| Progress callback counts look surprising | Sliced batches report per-slice or per-slice-group progress | Use the `sliced-inference` reference for `batch_size`, `progress_bar`, and callback expectations. |

## COCO/FiftyOne/evaluation failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| COCO images cannot be found | `images[*].file_name` does not resolve under the provided image directory | Validate the image directory and relative file names before slicing/evaluation. |
| Categories mismatch or appear remapped incorrectly | Inconsistent `category_id`/`category_name` mapping across annotations/results | Normalize categories with SAHI COCO helpers before splitting/export/evaluation. |
| Negative images disappear | `ignore_negative_samples` or filtering settings removed images without annotations | Preserve negative images explicitly when the dataset/task needs them. |
| `sahi coco evaluate` or `analyse` fails on import | `pycocotools` or evaluation plotting dependencies missing | Install the evaluation dependency set or fall back to JSON/schema validation until metrics are required. |
| FiftyOne does not launch | `fiftyone` missing or no suitable UI/session environment | Install FiftyOne and run in an environment that can open or expose the app session. |
| YOLO export symlink failures | OS permissions/symlink limitations | Use an elevated/admin shell when the platform requires it, or export/copy data using a platform-compatible path strategy. |

## Data object and visualization failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ValueError: box must be 4 non-negative floats` | Invalid bbox order or negative coordinates | Use `[minx, miny, maxx, maxy]` for `BoundingBox`/`ObjectPrediction`, and clip/validate before object construction. |
| `full_shape must be provided` for masks | Mask segmentation needs the original image shape | Pass `[height, width]` as `full_shape` for mask-bearing `ObjectPrediction` or `Mask`. |
| FiftyOne/imantics conversion import error | Optional conversion package absent | Install the optional package only when that conversion is needed, or export COCO dictionaries instead. |
| Visualization file is missing | Output directory/file name or export format mismatch | Use `PredictionResult.export_visuals(...)` and confirm the chosen `export_dir`, `file_name`, and format. |

## When to stop and ask for more context

Stop rather than guessing when the task requires private model weights, private datasets, HuggingFace/Roboflow credentials, a GPU-specific backend guarantee, large downloads, training-scale runs, or a particular benchmark score. Record which dependency, credential, hardware, or dataset is missing and offer a CPU/no-download smoke alternative when possible.
