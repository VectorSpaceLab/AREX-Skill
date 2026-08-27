# Inference troubleshooting

Use this reference for image/video/camera demo failures before changing the model config or reinstalling broad dependency sets.

## Engine and artifact problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Unsupported engine extension` or engine type is not selected | Engine path does not end in `.pth`, `.pt`, `.onnx`, or `.trt` | Use the correct artifact or rename only if the file truly is that format. Do not feed a Torch checkpoint to ONNX/TensorRT paths. |
| `KeyError: 'model'` when loading a `.pth` | Checkpoint does not use DAMO-YOLO's expected `{'model': state_dict}` layout | Use a DAMO-YOLO release/training checkpoint or adapt a conversion step outside this inference sub-skill. |
| Shape mismatch or many missing/unexpected keys | Config architecture does not match checkpoint/export | Pair the engine with the config used for training/export. Check model family, input size, and class count. |
| TensorRT output indexing errors with `--end2end` | `--end2end` does not match the TensorRT engine export layout | Use `--end2end` only for `.trt` engines exported with NMS included; omit it for raw-score/raw-box TensorRT engines. |
| ONNX input-size conflict | User `--infer-size` disagrees with fixed ONNX input shape | Trust the exported ONNX shape or re-export. Source-style ONNX inference derives `infer_size` from the ONNX input shape. |

## Device and backend problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Requested CUDA but run is slow or logs CPU | Torch CUDA is unavailable, so demo code fell back to CPU | Run a separate CUDA probe before claiming GPU inference. Install a CUDA-capable Torch build only if GPU inference is required. |
| TensorRT import fails: `ModuleNotFoundError: tensorrt` | TensorRT Python bindings are not installed | Treat TensorRT as optional. Use Torch/ONNX, or install TensorRT matching the target CUDA/driver stack before using `.trt`. |
| TensorRT import fails: `ModuleNotFoundError: cuda` or CUDA allocation failures | CUDA Python bindings/runtime/driver are missing or incompatible | Install the CUDA Python package/runtime expected by the TensorRT stack and verify driver visibility. Torch CUDA success alone does not prove TensorRT readiness. |
| ONNX import fails: `ModuleNotFoundError: onnxruntime` | ONNX Runtime is missing | Install `onnxruntime` for CPU, or the appropriate GPU package/provider if GPU ONNX is required. |
| ONNX runs on CPU despite `--device cuda` | Source-style ONNX session does not configure providers | Inspect `onnxruntime.get_available_providers()` and create a custom session/provider config if GPU ONNX is required. |
| Torchvision NMS error, missing compiled ops, or `torchvision::nms` not found | `torch` and `torchvision` binaries are incompatible | Install matching Torch/Torchvision builds for the chosen CPU/CUDA runtime. DAMO-YOLO postprocess uses `torchvision.ops.batched_nms`. |

## Python package/import problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: cv2` | OpenCV is missing | Install `opencv-python` or the environment's approved OpenCV package. Needed for video/camera IO and drawing. |
| `ModuleNotFoundError: PIL` or `Pillow` errors | Pillow is missing or cannot decode the image | Install Pillow and verify the input file is a real image. |
| `ModuleNotFoundError: loguru`, `omegaconf`, `easydict`, `timm`, or similar | DAMO-YOLO base requirements are incomplete | Install the repository/package requirements in the inference environment instead of relying on an unrelated Python environment. |
| Importing demo code from a copied checkout fails | Path-sensitive invocation or missing package install | Use the bundled helper with explicit paths and an installed `damo` package. Avoid assuming the current working directory is a DAMO-YOLO checkout. |

## Input media problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Image path is required` or `No such file` | Missing/incorrect `--path` | Pass an existing image path for `image` or video path for `video`; use `--camid` for `camera`. |
| Pillow `UnidentifiedImageError` | File extension is image-like but contents are not decodable | Validate the file with a basic image viewer or convert to `.jpg`/`.png`. |
| `cv2.VideoCapture` cannot open video | Wrong path, unsupported codec, or missing OpenCV video backend | Check the path, transcode to a common codec/container, or install OpenCV with video support. |
| Video writer creates an empty/corrupt file | Capture width/height/FPS are zero or codec unavailable | Use `--fps`, verify `CAP_PROP_FRAME_WIDTH/HEIGHT`, and choose an output extension/container supported by OpenCV. |
| Camera opens black frames or fails | Wrong camera id or permissions | Try another `--camid`, release other camera users, and verify OS/device permissions. |

## Visualization and class-name problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Class label ... does not fit class_names length` or `IndexError` in visualization | Config `dataset.class_names` length does not match model/export labels, or TensorRT end-to-end class indexing differs | Use the config from the same training/export run. For custom classes, verify `model.head.num_classes` and class-name order. If only TensorRT end-to-end is affected, confirm the NMS plugin's class-index convention. |
| Boxes are drawn but labels are shifted | Class-name order differs from the checkpoint's training labels | Recreate the config class-name list in the exact training order and re-export if needed. |
| No boxes visible at `--conf 0.6` | Display threshold filters low-score boxes | Lower `--conf` for visualization. If postprocess removed boxes before visualization, inspect config `model.head.nms_conf_thre` and `nms_iou_thre`. |
| Output image/video path is not where expected | `--output-dir` and input basename determine the default filename | Pass `--output-dir` and, with the bundled helper, `--output-name` to control the final path. Ensure the directory is writable. |
| GUI window never appears or job hangs | `cv2.imshow` used in headless environment | Save results instead. Only pass `--show-window` when a GUI display exists. |

## Source-style `--save_result` caveat

The original demo parser treats `--save_result` as `type=bool` with default `True`. In standard argparse, values such as `False` can still parse truthy because non-empty strings are true in Python. Prefer the bundled helper's `--no-save-result` for disabling saves, or use a direct Python API where `save_result=False` is an actual boolean.

## Quick triage checklist

1. Confirm config path exists and matches the engine family/class count.
2. Confirm engine extension and optional runtime: Torch (`.pth`/`.pt`), ONNX Runtime (`.onnx`), or TensorRT + CUDA Python (`.trt`).
3. Confirm media source opens: Pillow for images, OpenCV for video/camera.
4. Confirm `--infer-size` matches model/export shape.
5. Confirm class names align with `num_classes` and label indexing.
6. Save outputs first; only use display windows after the saved path works.
