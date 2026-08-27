---
name: video-detection-workflows
description: "Operate ImageAI video and camera object detection workflows with
  callbacks for standard and custom models."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Video Detection Workflows

Use this sub-skill when the task is to run, script, debug, or explain ImageAI object detection over video files, explicit OpenCV camera/live-stream inputs, or custom ImageAI-trained video detection models.

## Route Here For

- Standard COCO video detection with `VideoObjectDetection` and RetinaNet, YOLOv3, or TinyYOLOv3 weights.
- Camera or live-stream detection through an explicitly created `cv2.VideoCapture` object.
- Standard-detector class filtering with `CustomObjects` for selected COCO classes.
- Custom video detection with `CustomVideoObjectDetection`, `.pt`/`.pth` weights, and the matching JSON detection config.
- Save/no-save operation, output path behavior, FPS, frame detection intervals, timeouts, progress logging, display flags, and video analytics callbacks.

## Route Elsewhere

- Still-image object detection, extraction, image arrays, or COCO class details belong to `object-detection-workflows`.
- Custom model training, dataset layout, Pascal VOC conversion, or interpreting newly trained artifacts belong to `custom-training-and-data`.
- Install/import/backend setup and model-asset acquisition policy belong to the root `image-ai` skill.

## Operating Checklist

1. Choose detector family:
   - Standard COCO: `VideoObjectDetection`; model type `retinanet`, `yolov3`, or `tiny-yolov3`.
   - Custom trained detector: `CustomVideoObjectDetection`; model type `yolov3` or `tiny-yolov3`, plus matching JSON config.
2. Choose exactly one input source. Prefer `input_file_path` for files. Open a camera only when the user explicitly requests a camera index or stream URL.
3. Decide saving. If `save_detected_video=True`, provide an output base path; ImageAI appends `.mp4` and returns that path string. If `save_detected_video=False`, use callbacks for useful output; the detection call returns `None`.
4. For cameras and long files, set `detection_timeout`, choose a practical `frames_per_second`, and raise `frame_detection_interval` on slow hardware.
5. Match callback arity to `return_detected_frame`. The complete-video callback never receives a frame argument.
6. Use the bundled helper when a safe command-line wrapper is enough: [`scripts/detect_video.py`](scripts/detect_video.py).

## References

- [`references/api-reference.md`](references/api-reference.md): verified class methods, signatures, inputs, return values, and callback parameter shapes.
- [`references/workflows.md`](references/workflows.md): file, camera, custom model, save/no-save, timeout, interval, and performance recipes.
- [`references/callbacks-and-analysis.md`](references/callbacks-and-analysis.md): callback data schemas and accumulator patterns.
- [`references/troubleshooting.md`](references/troubleshooting.md): OpenCV, codec, callback, threshold, timeout, model/config, and performance failures.
