# MMAction2 inference troubleshooting

Use this reference when an MMAction2 inference, inferencer, label, visualization, or optional pose/detection workflow fails. Keep fixes local and bounded: do not start training, dataset conversion, or model customization from this sub-skill.

## Install and import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'mmaction'` | MMAction2 is not installed in the active Python environment. | Activate the intended environment and install MMAction2 plus its runtime dependencies. Then run `python scripts/mmaction2_inference_smoke.py --print-signatures`. |
| `ModuleNotFoundError: No module named 'mmcv'` or `No module named 'mmengine'` | Required OpenMMLab runtime packages are missing or installed in the wrong environment. | Install compatible MMEngine and MMCV versions for the installed MMAction2 release and backend. Re-run a build-only smoke check before media inference. |
| Import succeeds in one shell but fails in another | Different Python interpreter or environment. | Compare `python -c "import sys; print(sys.executable)"` in both shells and run all checks in the intended environment. |
| `ImportError` mentioning CUDA or custom ops | MMCV/PyTorch/backend mismatch. | Use `device="cpu"` for the first smoke check. If CUDA is required, install a CUDA-compatible PyTorch/MMCV pair that matches the host driver and Python environment. |

## Config, checkpoint, and model selection

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `TypeError: config must be a filename or Config object` | `init_recognizer` received a list, dict, or other unsupported config type. | Pass a local config path, `pathlib.Path`, or `mmengine.Config` object. |
| Shape mismatch when loading checkpoint | Checkpoint and config disagree, commonly in class count, head type, modality, or backbone. | Use the config that produced the checkpoint, or adjust the model config in the model-extension skill before inference. For build-only checks, use `checkpoint=None`. |
| Alias/name unexpectedly tries to fetch weights | High-level inferencer received a model alias or metadata model name with no local weights. | For offline work, pass `model="CONFIG.py"` and `weights="CHECKPOINT.pth"` to `ActionRecogInferencer`, or `rec="CONFIG.py"` and `rec_weights="CHECKPOINT.pth"` to `MMAction2Inferencer`. |
| `ValueError: rec algorithm should provided.` | `MMAction2Inferencer()` was constructed without `rec`. | Provide `rec` as a local config path, short alias, or known model/config name. |
| Build succeeds but predictions are meaningless | Inference ran with `checkpoint=None` or random weights. | Treat this only as a pipeline smoke check. For real predictions, provide a trained local checkpoint that matches the config. |

## Device and backend failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| CUDA error on a CPU-only machine | Several public APIs default to `device="cuda:0"`. | Pass `device="cpu"` explicitly to `init_recognizer`, `detection_inference`, and `pose_inference`; pass `device="cpu"` to inferencer constructors. |
| `AssertionError` or backend error after switching to CUDA | CUDA-enabled PyTorch/MMCV stack is not compatible or GPU is unavailable to the process. | First prove `python -c "import torch; print(torch.cuda.is_available())"`. If false, stay on CPU. If true but MMCV fails, reinstall backend-compatible packages. |
| CPU inference is slow | Large video model, long clip, high resolution, or expensive decoding. | Use a shorter input clip for smoke checks, reduce output resolution, and avoid visualization until the model/pipeline is proven. For performance work, switch only after backend verification. |

## Input format and decode failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| ``RuntimeError: The type of argument `video` is not supported`` | `inference_recognizer` received a non-existing path or unsupported object. | Use an existing local video path, existing `.npy` audio feature path, or an already-packed dict. For rawframes/arrays, prefer `ActionRecogInferencer` with `input_format`. |
| `Please run "pip install decord" to install Decord first.` | Default video pipeline uses Decord and Decord is missing. | Install Decord in the active environment or switch to a config/pipeline that uses another decoder. Re-run a small local video smoke. |
| `Please install decord to load video file.` | The visualizer is loading a video path and Decord is missing. | Install Decord or pass already-decoded frames/arrays to the visualizer. |
| Video path has no extension and cannot be opened | Decord initialization may append `.mp4` to extensionless paths. | Use a real file path with the correct extension. |
| Last frames look duplicated or wrong with OpenCV decode | The OpenCV decoder path falls back to the previous frame when a requested frame is `None`. | Validate the input video with an external media tool; re-encode corrupt videos before inference. |
| Rawframe directory produces zero frames or file-not-found errors | Default rawframe template is `img_{:05}.jpg` with `start_index=1`. | Pass `pack_cfg={"filename_tmpl": ..., "start_index": ..., "modality": ...}` to `ActionRecogInferencer`, or rename frames to match the default template. |
| Array input fails or has wrong colors/modality | `input_format="array"` expects a 4D array; channel dimension `3` means RGB and `2` means Flow. | Ensure shape is `T x H x W x C`, dtype is compatible with the transforms, and the model/config matches RGB or Flow. |
| Audio `.npy` path produces nonsensical output | Wrong audio feature shape, wrong config, or no trained audio checkpoint. | Use an audio-recognition config whose test pipeline expects audio features. Confirm the `.npy` file exists and has the expected feature dimensions. |
| Missing audio feature path does not fail loudly | Some audio feature loaders can synthesize dummy features when the feature file does not exist. | Validate feature file existence before inference; do not rely only on model output to detect missing audio data. |

## Prediction and label issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Output class names are missing | No `label_file` was supplied to the inferencer, or direct API result was not mapped manually. | For inferencers, pass a one-label-per-line recognition class file. For direct API, map `result.pred_score` indices yourself. |
| Label names are shifted or wrong | Label file order does not match checkpoint training classes. | Use the class list associated with the checkpoint and config. Do not mix recognition one-label-per-line files with spatio-temporal `id: label` maps. |
| `pred_out_file` is empty or not created | The directory does not exist, extension unsupported, or the run failed before postprocess. | Create the parent directory first and use `.json`, `.yaml`/`.yml`, or `.pkl`. Keep `return_datasamples=False` for serializable prediction dumps. |
| Need raw tensors but only dict predictions are returned | High-level wrappers serialize predictions by default. | Use direct `inference_recognizer` for `ActionDataSample`, or use `ActionRecogInferencer(...)(..., return_datasamples=True)` when no serialized dump is needed. |

## Visualization failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| No visualization output | `show=False`, `vid_out_dir=""`, and `return_vis=False`; the inferencer intentionally skipped visualization. | Set `vid_out_dir` to a writable output directory, or set `return_vis=True` in code. |
| GUI window does not appear on server/SSH | Headless environment or disabled display forwarding. | Use `show=False` and save to `vid_out_dir`; do not depend on pop-up display for verification. |
| `Please install moviepy to enable output file` | Demo-style output path needs MoviePy. | Install MoviePy only if output video composition is required; otherwise use prediction dumps or inferencer `vid_out_dir` output. |
| Output video/GIF path not where expected | Inferencer writes inside `vid_out_dir` using the input basename or generated array name. | Check `results["visualization"]` and list the output directory. For decoded array input, generated names may look like `00000000.mp4`. |
| Multi-input visualization only saves part of a batch | The unified wrapper visualization path is most predictable for one input at a time. | Run visualization one input per call, or use `ActionRecogInferencer` directly for more control. |

## Optional detection and pose paths

| Symptom | Exact or likely error | Recovery |
| --- | --- | --- |
| Human detection helper fails to import | ``Failed to import `inference_detector` and `init_detector` from `mmdet.apis`. These apis are required in this inference api! `` | Install a compatible `mmdet` stack in the active environment, or skip skeleton/spatio-temporal workflows. Clip-level recognition does not require `mmdet`. |
| Pose helper fails to import | ``Failed to import `inference_topdown` and `init_model` from `mmpose.apis`. These apis are required in this inference api! `` | Install a compatible `mmpose` stack in the active environment, or skip pose/skeleton workflows. RGB clip recognition does not require `mmpose`. |
| Detection returns no boxes | Threshold too high, wrong detector class ID, poor detector/checkpoint, or input frames unsuitable. | Lower `det_score_thr` for diagnosis, confirm `det_cat_id` for the detector label map, and visualize detections before action recognition. |
| Pose results lack `keypoints` or `keypoint_scores` | Pose model output or dependency version is incompatible with the expected top-down pose API. | Verify `pose_results[0].keys()` and use compatible detector/pose package versions. |
| Skeleton prediction fails after pose | Skeleton config expects a different keypoint layout or image shape. | Confirm the skeleton checkpoint/config pair and pass `img_shape=(height, width)` from the original frames. |
| Spatio-temporal detection is much slower than clip recognition | It runs frame extraction, human detection, action model prediction for timestamp windows, and visualization. | Use a short clip and CPU only for functional checks; move to GPU only after backend verification. |

## When to route away

- If the fix requires changing annotation files, rawframe lists, data roots, or config inheritance, use `../data-and-configs/SKILL.md`.
- If the user wants to evaluate a checkpoint on a dataset, launch training/testing, or compute metrics, use `../training-and-evaluation/SKILL.md`.
- If the fix requires registering a new model, changing heads/backbones, exporting, or deployment, use `../models-and-extension/SKILL.md`.
