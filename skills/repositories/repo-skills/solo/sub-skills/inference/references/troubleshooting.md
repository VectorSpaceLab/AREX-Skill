# Inference troubleshooting

Use this matrix to classify the failure before changing a config, checkpoint,
or environment. Preserve the original exception and the exact command.

## Install and import

| Symptom | Likely cause | Recovery |
|---|---|---|
| `No module named mmdet` or imports resolve to another MMDetection | Package is not installed in the active environment or `PYTHONPATH` points at a different checkout. | Activate the intended environment; run a read-only `python -c "import mmdet; print(mmdet.__file__)"`; use a temporary explicit path choice only if required. Do not edit source or assume a current MMDetection release is compatible. |
| `No module named mmcv` or missing old MMCV symbol | MMCV is absent or too new for this API. | Use the repository's documented `mmcv==0.2.16` compatibility target and matching legacy PyTorch; do not fix by importing modern `mmcv` APIs into this skill. |
| `ImportError` for `pycocotools`, `cv2`, `scipy`, or `matplotlib` | Runtime dependency is missing. `show_result_ins` uses OpenCV/SciPy; mask decoding uses pycocotools; pyplot uses Matplotlib. | Install/activate dependencies through the approved environment process, then rerun an import smoke. Do not download dependencies from the inference helper or claim a renderer is available when it is not. |
| Error while importing `mmdet.ops` or a missing `.so`/CUDA symbol | Legacy custom extensions were not built, were built against a different ABI, or require CUDA. | Check the package build and PyTorch/CUDA compatibility. A CPU import may isolate a Python issue, but CPU success does not validate custom CUDA kernels. Avoid rebuilding from an unapproved source mutation during a runtime trial. |
| Setup asks for a compiler or CUDA toolkit | The legacy `setup.py` builds CUDA extensions and Cython/C++ components. | Stop and report the missing build toolchain. The documented environment requires CUDA 9+ and old compiler compatibility; a host with a CUDA runtime but no `nvcc` cannot be treated as a proven extension build. |
| Python syntax/API errors under a current runtime | The source targets Python 3.5+ and PyTorch 1.1-era dependencies; newer NumPy/Pillow/PyTorch can remove old names or behavior. | Reproduce in a version-matched legacy environment. Do not “modernize” runtime code as part of an inference request. |

## Optional dependencies and renderers

| Symptom | Likely cause | Recovery |
|---|---|---|
| `show_result_pyplot` fails or hangs | Matplotlib backend/display is missing, or the environment is headless. | Use `show_result(..., show=False, out_file=...)` or `show_result_ins(..., out_file=...)`; save an image instead of opening a figure. |
| OpenCV window cannot connect to X server | `show=True`, webcam rendering, or `mmcv.imshow_det_bboxes` requested a GUI in a headless session. | Rerun headlessly with `show=False` and an explicit output path. Do not set up or invoke a webcam for a smoke test. |
| `cv2.VideoCapture` opens but frames are empty | Camera id, permissions, driver, or GUI build is wrong. | Treat webcam as a manual hardware workflow; check `ret_val` before inference and provide a stop path. It is outside automated verification. |
| `albumentations` or `imagecorruptions` is missing | These are optional extras, not required by the basic image inference API. | Install optional extras only for a config/pipeline that names them. Do not add optional packages to a baseline inference command without evidence they are needed. |
| Mask visualization fails in `show_result_ins` but bbox rendering works | The result is a conventional bbox/mask tuple, not the SOLO tensor tuple expected by `show_result_ins`, or a mask dependency is missing. | Route conventional outputs to `show_result`; route SOLO-family outputs to `show_result_ins`; inspect the result structure before rendering. |

## Data and config validation

| Symptom | Likely cause | Recovery |
|---|---|---|
| Bundled helper says config/checkpoint/image is missing | A required local prerequisite is absent. | Supply an existing explicit path. The helper intentionally does not download or infer source-relative paths. |
| `Config.fromfile` or config execution fails | Config path is wrong, config has unavailable custom imports, or the config belongs to another code version. | Validate the file, package version, and any registered model components. Use a config from this SOLO/MMDetection family; do not silently replace it. |
| `KeyError` for `model`, `test_cfg`, or `data.test.pipeline` | The selected config is not compatible with the v1 inference API or was edited incompletely. | Check that the config defines the legacy detector model, test settings, and test pipeline. Preserve the pipeline's resize/normalize/pad/collect stages. |
| Model builds but checkpoint load reports missing/unexpected keys or shape mismatch | Config and checkpoint do not describe the same architecture, class count, or variant. | Pair exact family and schedule (for example SOLO vs Decoupled SOLO, R50 vs R101). Record the mismatch; do not force-load or ignore keys for a result claim. |
| Class labels are wrong or `model.CLASSES` is absent | Checkpoint metadata lacks `CLASSES`, so initialization falls back to COCO classes. | Confirm the checkpoint's dataset/classes and pass an explicit class list only in a deliberate custom integration. The fallback warning is not proof of custom-label correctness. |
| Image read returns `None`, has an unexpected shape, or colors look wrong | File is not a supported readable image, or a BGR/RGB array was supplied incorrectly. | Validate the local image with a read-only image probe; pass a path or the BGR array expected by MMCV/OpenCV. Do not bypass configured normalization. |
| Result is empty on every image | Thresholds, checkpoint, class metadata, image preprocessing, or model family may be wrong. | Inspect config `test_cfg` (`score_thr`, `mask_thr`, `update_thr`, `max_per_img`), visualization threshold, class names, and checkpoint provenance. Do not claim model failure from one threshold. |

## API and CLI misuse

| Symptom | Likely cause | Recovery |
|---|---|---|
| `init_detector` raises `TypeError` for config | `config` is neither a filename nor an `mmcv.Config`. | Pass an explicit config path or construct the matching legacy `mmcv.Config`. |
| `inference_detector` gets a video path or a batch/list and fails | This API's implementation is one image path or one loaded array at a time. | Decode video/image streams yourself and call the API per BGR frame, reusing the model. Do not assume modern batch semantics. |
| `show_result` receives SOLO `(masks, labels, scores)` output | Wrong renderer for the detector family. | Use `show_result_ins` for SOLO-style instance outputs; use `show_result` for bbox-only or conventional `(bbox_result, segm_result)` outputs. |
| `show_result` returns `None` unexpectedly | `show=True` or `out_file` was supplied. | This is documented behavior: use the output file, or set both `show=False` and `out_file=None` when an array return is desired. |
| `show_result_ins` returns an image but no file exists | `out_file` was omitted, or the result was empty. | Pass an explicit writable `out_file`; inspect for `None`/`[None]` and ensure the input image is valid. |
| Bundled helper rejects `--device cuda` | The helper requires an explicit CUDA index to avoid ambiguous device selection. | Use `--device cuda:0` (or another visible index) or explicitly choose `--device cpu`; no automatic CPU fallback is performed. |
| Bundled helper rejects an output path | Parent directory does not exist, is unwritable, or output equals input. | Create the destination directory explicitly and keep output separate. The helper does not create arbitrary directories or overwrite the input. |
| `tools/test_ins.py` exits on its operation assertion | None of `--out`, `--show`, or `--json_out` was supplied. | For a planned dataset run choose an explicit output operation, but do not start it here without local dataset/checkpoint approval. `--show` is GUI-dependent. |
| `--eval` fails or output is not the expected type | Evaluation needs the configured dataset, annotations, pycocotools, and compatible result serialization. | Use `--help` for a CLI smoke; reserve actual `bbox`/`segm` evaluation for a separately approved dataset experiment. |
| `--json_out result.json` behaves as a prefix | The script removes a trailing `.json` and writes one or more result files from the prefix. | Supply a deliberate prefix and inspect the generated names; do not assume one exact file. |

## Workflow-specific failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| CUDA device requested but `torch.cuda.is_available()` is false | CPU-only PyTorch, no visible GPU, driver mismatch, or environment mismatch. | Stop and report the environment. Use CPU only as a limited diagnostic if the selected model/extensions support it; do not reinterpret it as a CUDA validation. |
| `CUDA error`, illegal memory access, or custom op launch failure | Extension/PyTorch/CUDA ABI mismatch, unsupported model op, bad GPU selection, or memory pressure. | Record the first CUDA error, verify the legacy stack and visible device, then retry a smaller approved local case only after environment repair. Do not run a full dataset or distributed job to “test around” it. |
| CPU inference fails with missing `roi_align`/NMS/DCN op | The model requires an extension or a CPU-compatible fallback is not present. | Classify CPU as unsupported for this model. Use a verified CUDA environment; do not claim the CPU path is equivalent. |
| Inference is extremely slow or memory-heavy | Large image, high `nms_pre`/`max_per_img`, model variant, or CPU execution. | Use a small local fixture for a smoke, inspect test config and device, and report resource limits. Do not lower thresholds in a way that changes the intended result without recording it. |
| Async call raises `NotImplementedError` or loop/stream errors | Async support is Python 3.7+ oriented, requires an event loop and explicit CUDA streams, and does not support arbitrary augmentation/batching. | Use synchronous inference first. If async is required, follow the documented queue/concurrency design and verify one image/one augmentation at a time. |
| Image-stream loop leaks windows or never stops | GUI/webcam side effects were used in an automated context. | Stop the process, switch to headless per-frame output, and keep webcam verification manual. |
| `tests/test_forward.py` passes CPU portions but final CUDA case is unavailable | The native candidate has optional CUDA coverage and CPU branches/skips. | Report the CUDA case as unverified/blocked. Never promote CPU success to custom-kernel evidence. |
| A visualization appears valid but the model was initialized with no checkpoint | `init_detector` permits `checkpoint=None` and constructs randomly initialized weights. | Treat the image as a pipeline-only smoke, not a pretrained inference result; rerun with an existing compatible checkpoint for meaningful output. |

## Stop conditions

Stop rather than guess when the config/checkpoint family is uncertain, class
metadata is incompatible with the requested labels, a required CUDA extension
cannot be proven, a dataset/evaluation path would require downloads, or a
webcam/GUI/distributed action would be needed for acceptance. Report the exact
missing prerequisite and the next safe read-only check.
