# Engine selection and inference data flow

This reference distills DAMO-YOLO demo inference behavior into engine-selection and data-flow rules. Use it with the bundled helper rather than reopening repo-local demo code.

## Required inputs

- **Config file**: a user-owned DAMO-YOLO Python config such as `/path/to/damoyolo_config.py`. Load it with `parse_config(config_file)` and make any relative TinyNAS/data paths resolvable from the chosen working directory.
- **Engine artifact**: one of `.pth` / `.pt`, `.onnx`, or `.trt`. The extension determines the runtime path.
- **Media source**: image path, video path, or `--camid` for a camera.
- **Inference size**: usually `640 640` for T/S/M/L models and `416 416` for nano variants; match the model/export.
- **Class names**: read from `config.dataset.class_names` when present; otherwise labels are stringified class ids from `0` to `num_classes - 1`.

## Engine choice

| Engine artifact | Runtime path | Strengths | Required packages | Device notes | Postprocess path |
| --- | --- | --- | --- | --- | --- |
| `.pth` / `.pt` | PyTorch model built with `build_local_model(config, device)`, checkpoint `ckpt['model']` loaded, `RepConv` switched to deploy, `model.eval()` | Most debuggable; best when config/checkpoint are available; CPU fallback is possible | `torch`, `torchvision`, base `damo` requirements | If CUDA is requested but unavailable, demo code uses CPU; slower but expected for Torch | Model returns `BoxList` detections, resized back to original image size |
| `.onnx` | `onnxruntime.InferenceSession(engine)` using the first input name and exported input shape | Portable inference artifact; no PyTorch checkpoint load | `onnxruntime` plus base image deps | Source demo does not expose ONNX provider selection; verify CUDA provider separately if GPU ONNX is required | Raw score and box tensors are converted to Torch tensors and passed through DAMO-YOLO `postprocess(...)` |
| `.trt` | TensorRT serialized engine deserialized with TensorRT runtime and CUDA Python buffers | Fast NVIDIA inference when an engine has already been exported for the target GPU/input size | `tensorrt`, CUDA Python package importable as `from cuda import cuda`, CUDA driver/runtime | Treat as CUDA-only. The optional TensorRT stack may be absent even when Torch CUDA works. | Non-`--end2end` uses raw scores/boxes + `postprocess(...)`; `--end2end` expects NMS outputs `(nums, boxes, scores, pred_classes)` |

If the extension is wrong or missing, do not guess. Rename/use the correct artifact or choose the right workflow. A checkpoint converted to ONNX or TensorRT must still match the config's architecture and class count.

## Preprocessing

The demo path applies the config's test transform through `transform_img(...)`:

1. Resize using `config.test.augment.transform.image_max_range` and the requested `--infer_size` target.
2. Apply the configured horizontal-flip probability, tensor conversion, and normalization (`image_mean`, `image_std`). For inference configs this is normally no random flip and mean `0`, std `1`.
3. Convert to `ImageList`, then pad the single image tensor to the requested inference size.
4. Move the padded `ImageList` to the selected Torch device. ONNX and TensorRT paths convert the tensor back to a NumPy array before engine execution.

Important details:

- `--infer_size` is height then width in the command examples (`640 640`). Keep it consistent with the exported engine; TensorRT engines are commonly fixed-shape.
- For ONNX, the source runtime updates `infer_size` from the ONNX input shape (`input_shape[2:]`). If a user-provided `--infer_size` disagrees with a fixed ONNX input, trust the exported shape or re-export.
- Image files are opened through Pillow and converted to RGB. Video/camera frames come from OpenCV. Preserve this convention unless you intentionally normalize color handling in custom code.

## Postprocessing and outputs

DAMO-YOLO uses `BoxList` to carry detections. After engine execution:

- Torch returns detections from the PyTorch model path.
- ONNX and non-end2end TensorRT produce class-score and box-prediction tensors and run DAMO-YOLO `postprocess(cls_scores, bbox_preds, num_classes, nms_conf_thre, nms_iou_thre, image)`.
- End-to-end TensorRT expects NMS to be inside the engine and wraps returned boxes/scores/classes in `BoxList`.
- The final `BoxList` is resized from model input dimensions back to the original `(width, height)` media shape.

`--conf` filters only visualization. It does **not** change model NMS; edit the config head thresholds only when you intentionally need different NMS behavior.

## Visualization and class names

Visualization draws `xyxy` boxes, class label text, and scores onto the source frame.

- `class_names` must align with `config.model.head.num_classes` and the checkpoint/export. For custom data, update both the model head class count and `dataset.class_names` during training/export.
- If class labels are outside `0 <= label < len(class_names)`, the visualizer can fail or draw shifted labels. This usually indicates a config/checkpoint/export mismatch or a TensorRT end-to-end class-index convention mismatch.
- Saved image output uses the input basename under `--output-dir`. Saved video output uses the video basename; camera output should use an explicit output name or a camera-derived filename.

## Device behavior

- Torch inference: `--device cuda` requests CUDA, but if `torch.cuda.is_available()` is false, the demo falls back to CPU. This is not proof that CUDA worked.
- ONNX inference: `--device` affects preprocessing tensor movement in source-style code, not provider selection. Check ONNX Runtime providers if GPU ONNX is required.
- TensorRT inference: requires a CUDA-capable runtime and TensorRT Python bindings. Do not expect CPU fallback.
- A verified GPU model-forward smoke returning a `BoxList` proves the PyTorch model path can execute on CUDA, but it does not prove ONNX Runtime or TensorRT are installed.
