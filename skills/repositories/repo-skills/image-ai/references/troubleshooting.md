# ImageAI Troubleshooting

## Purpose

Use this cross-cutting reference for install/import/backend/model-asset failures that affect multiple ImageAI workflows. Use the nearest sub-skill troubleshooting file for workflow-specific errors.

## Install and import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Dependency error!!! PyTorch and TorchVision are not installed` | ImageAI imported without required PyTorch dependencies. | Install compatible `torch` and `torchvision` in the same Python environment that runs ImageAI. Then rerun `python scripts/check_imageai_env.py`. |
| Import works in one shell but fails in another | Different Python interpreter or environment. | In the failing shell run `python -c "import sys; print(sys.executable)"`; install dependencies into that environment or activate the intended environment. |
| `No broken requirements found` but ImageAI import still fails | Package is installed but a transitive import such as OpenCV, Pillow, NumPy, torch, or torchvision fails. | Run `python scripts/check_imageai_env.py` for targeted import output; reinstall the missing or incompatible dependency pair. |
| OpenCV import errors involving GUI libraries | `opencv-python` wheel/system GUI dependency mismatch. | For servers, consider `opencv-python-headless` only if the task does not need GUI/camera display features. Keep video encoding support requirements in mind. |
| Repeated torchvision `pretrained` deprecation warnings | ImageAI 3.x source uses older torchvision model constructor arguments. | Treat as warning noise if imports and model loading succeed. Do not confuse it with a fatal model-weight error. |

## Model file failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Error says TensorFlow model or ImageAI now uses PyTorch | A `.h5` file was supplied to ImageAI 3.x. | Use `.pt`/`.pth` PyTorch weights, retrain in ImageAI 3.x, or run a separate legacy ImageAI 2.1.6-or-earlier environment for `.h5` assets. |
| `Invalid model file ... parse in a '.pt' and '.pth' model file` | Model path has the wrong extension. | Supply an existing `.pt` or `.pth` file. |
| `invalid path, path not pointing to a valid file` | Path does not exist from the process current working directory. | Use an absolute path or resolve the path before calling `setModelPath(...)`. |
| `Invalid weights!!!`, `missing keys`, `unexpected keys`, or tensor size mismatch | Model type setter does not match the checkpoint architecture, or custom JSON class count does not match the model head. | Verify the architecture used to produce the weights. Pair custom models with their generated JSON from the same training run. |

## Backend and performance failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Code unexpectedly uses GPU | ImageAI defaults to CUDA when `torch.cuda.is_available()` is true. | Call `useCPU()` before `loadModel()`, or use the bundled helpers' `--cpu` option. |
| CUDA requested but unavailable | CPU-only PyTorch wheel, missing driver passthrough, incompatible driver/wheel, or no GPU. | Run `python scripts/check_imageai_env.py --require-cuda`; install a matching CUDA-enabled PyTorch wheel or remove the CUDA requirement. |
| Video/training is extremely slow | CPU execution or large model/video/dataset. | Use CUDA where available, lower FPS/frame interval for video, use TinyYOLOv3 for speed, reduce batch size or epochs for training smoke checks. |
| CUDA out of memory during training | Batch size/model/dataset image size too large for GPU memory. | Lower `batch_size`, use TinyYOLOv3/MobileNetV2 when appropriate, or move to a larger GPU. |

## Stale ImageAI 2.x guidance

Older examples may mention TensorFlow backend, `.h5` weights, speed modes, `enhance_data`, `loadModel(num_objects=...)`, `num_objects` for classification training, or standalone detection `evaluateModel()`. For ImageAI 3.x PyTorch workflows in this skill:

- Use `.pt`/`.pth` weights only.
- `CustomImageClassification.loadModel()` takes no `num_objects` argument.
- `ClassificationModelTrainer.trainModel(...)` uses `num_experiments`, `batch_size`, `model_directory`, `transfer_from_model`, and `verbose`.
- `DetectionModelTrainer.setTrainConfig(...)` uses `object_names_array`, `batch_size`, `num_experiments`, and `train_from_pretrained_model`.
- Detection training uses YOLO-format text annotations, not Pascal VOC directly.

## Where to go next

- Classification-specific issues: [classification troubleshooting](../sub-skills/classification-workflows/references/troubleshooting.md).
- Still-image detection issues: [object detection troubleshooting](../sub-skills/object-detection-workflows/references/troubleshooting.md).
- Video/camera/callback issues: [video detection troubleshooting](../sub-skills/video-detection-workflows/references/troubleshooting.md).
- Dataset/training/conversion issues: [custom training troubleshooting](../sub-skills/custom-training-and-data/references/troubleshooting.md).
