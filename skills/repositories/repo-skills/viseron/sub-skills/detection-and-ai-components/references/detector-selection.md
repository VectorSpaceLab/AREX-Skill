# Detector Selection

This reference summarizes the detector components owned by this sub-skill. The strict construction scope verified CPU-safe imports and schema evidence only; live cameras, containers, GPUs, EdgeTPU, Hailo devices, external AI servers, model downloads, and credentials remain target-host requirements.

## Mental model

Viseron separates detection into domains:

- `motion_detector`: cheap motion state from frame scanning or an external source.
- `object_detector`: object boxes and labels from local models, accelerators, or external services.
- Post-processors: `face_recognition`, `image_classification`, and `license_plate_recognition`; these run after an object detector emits matching objects.

For most NVR deployments, combine a cheap motion detector with an object detector. Motion can start event recordings by itself when `trigger_event_recording: true`, or it can be used only to gate object detection via `scan_on_motion_only: true`.

## Motion detector choices

| Component | Best fit | Important settings | Notes |
|---|---|---|---|
| `background_subtractor` | Simple local OpenCV motion detection with low overhead. | per-camera `fps`, `area`, `width`, `height`, `mask`, `threshold`, `alpha`, `trigger_event_recording`, `recorder_keepalive`, `max_recorder_keepalive`. | Maintains a running average and compares the current frame to that average. Lower `threshold` and higher `alpha` are more sensitive but noisier. |
| `mog2` | Local OpenCV motion detection when background subtraction needs better shadow/background handling. | Same scanner settings as `background_subtractor`, plus `history`, `detect_shadows`, and `learning_rate`. | First frame initializes the model. `detect_shadows` can improve false positives at extra cost. `learning_rate` controls how quickly the model adapts. |
| `mqtt.motion_detector` | External motion source such as a PIR sensor, another camera system, or a custom automation. | global `mqtt` broker settings; per-camera `topic`, `payload_on`, `payload_off`, `max_motion_duration`, `trigger_event_recording`, `recorder_keepalive`. | Does not scan video frames. Payloads may be the configured on/off strings or JSON containing a boolean `detected` field. `max_motion_duration` is a safety auto-clear timer for missed off messages. |

Scanner motion detectors resize frames before detection. Use lower `fps` and smaller `width`/`height` first, then adjust `area`, `threshold`, or masks to reduce false positives.

## Object detector choices

| Component | Best fit | Model/device settings | Operational notes |
|---|---|---|---|
| `yolo` | Local Ultralytics YOLO models when the target host has enough CPU/GPU resources and a supplied `.pt` model. | required `model_path`; optional `min_confidence` default `0.25`, `iou` default `0.7`, `half_precision`, `device` such as `cpu`, `cuda:0`, or `0`. | Uses the model's labels and logs them at startup. The component-level `min_confidence` filters model results before Viseron's per-label filters. Limited model families were documented as tested; verify unfamiliar models on the target host. |
| `darknet` | Local YOLO/Darknet models, especially default container models or CPU/OpenCL/CUDA deployments. | `model_path`, `model_config`, `label_path`, `suppression`, `dnn_backend`, `dnn_target`, `half_precision`. Defaults point at container model paths. | Uses native Darknet when CUDA support is available and no explicit OpenCV backend/target is configured; otherwise uses OpenCV DNN. Tiny models reduce resource use at accuracy cost. |
| `edgetpu.object_detector` | Coral EdgeTPU or compatible TensorFlow Lite CPU models. | optional `model_path`; `device` may be `cpu`, `usb`, `usb:<N>`, `pci`, `pci:<N>`, `:<N>`, or a list; `label_path`. | If no device is set, Viseron chooses the first available EdgeTPU or CPU. Model must match selected device type. The implementation uses a subprocess and reloads after repeated inference failures. |
| `hailo` | Hailo-8/Hailo-8L accelerator object detection. | optional `model_path` as local HEF path or URL; `label_path`; `max_detections`; top-level `multi_process_service`. | Requires host Hailo runtime/driver compatibility and container access to the device. If no model is provided, Viseron may download/cache a default HEF model on startup. |
| `codeprojectai.object_detector` | External CodeProject.AI service with object-detection modules. | top-level `host`, `port` default `32168`, `timeout`; object `custom_model` default `ipcam-general`, optional square `image_size`. | Sends JPEG frames to the server. `image_size` uses letterbox resizing to preserve aspect ratio. Service errors return no detections rather than crashing the detector loop. |
| `deepstack.object_detector` | External DeepStack object detection service. | top-level `host`, required `port`, optional `api_key`, `timeout`; optional `image_width`, `image_height`, `custom_model`. | Sends JPEG frames to the server. If width/height are omitted, Viseron interprets returned boxes in the camera's native resolution. Service errors return no detections. |

Every object detector uses the same per-camera object-detector schema for `fps`, `scan_on_motion_only`, `labels`, `max_frame_age`, `log_all_objects`, `mask`, and `zones`; see [labels, masks, zones, and filters](labels-masks-zones-and-filters.md).

## Face recognition choices

| Component | Best fit | Key settings | Notes |
|---|---|---|---|
| `dlib.face_recognition` | Local face recognition from a trained face folder. | `model: hog` or `model: cnn`; shared face settings such as `face_recognition_path`, `save_faces`, `save_unknown_faces`, `expire_after`, labels and masks. | `hog` is faster on CPU; `cnn` is more accurate and can use CUDA when available. Training happens from the face folder during setup. |
| `compreface.face_recognition` | External CompreFace service with subject management and optional plugins. | `host`, `port`, `recognition_api_key`, `train`, `det_prob_threshold`, `similarity_threshold`, `limit`, `prediction_count`, `face_plugins`, `status`, `use_subjects`. | `similarity_threshold` decides whether a low-similarity subject becomes `unknown`. `use_subjects` can use service subjects rather than the folder structure. |
| `codeprojectai.face_recognition` | External CodeProject.AI face recognition. | top-level server settings; `train`, `min_confidence`, face folder, save/expire settings. | Training reads the configured face folder, deletes existing faces for each subject, and registers images with exactly one detected face. |
| `deepstack.face_recognition` | External DeepStack face recognition. | top-level server settings; `api_key`, `train`, `min_confidence`, face folder, save/expire settings. | Training requires per-person directories and images where exactly one face is detected. |

Face recognition is a post-processor. It only receives objects whose labels are tracked and passed by the object detector.

## Image classification and license plate recognition

- `edgetpu.image_classification` runs an EdgeTPU/TFLite classifier as a post-processor. Use `labels` to decide which detected object labels trigger classification, set `model_path`, `device`, `label_path`, `expire_after`, and tune `crop_correction` if object crops are too tight.
- `codeprojectai.license_plate_recognition` runs license plate recognition as a post-processor. Configure server settings, `labels` such as vehicle-related object labels, optional `known_plates`, `min_confidence`, `save_plates`, and `expire_after`.

## Local versus external detector decision checklist

Choose a **local model or accelerator** when privacy/offline behavior matters, the target host has known hardware and model files, and you can mount model/device paths into the Viseron runtime. Prefer `background_subtractor`/`mog2` for cheap motion, `darknet` or `edgetpu` for lower-power object detection, `yolo` for flexible modern models, and `hailo` only when the Hailo runtime/device setup is already planned.

Choose an **external service detector** when the Viseron host should stay light, the service is easier to maintain separately, or face/LPR services are already deployed. Prefer CodeProject.AI when one service should cover object, face, and license plate workflows; prefer DeepStack when its object/face API and model set already fit the deployment; prefer CompreFace when face recognition subject management and plugins are the main requirement.

Before committing to either path, answer:

1. Which camera labels are needed, and does the chosen model expose those exact label names?
2. Can the model or service meet the desired `fps` without starving camera decoding and recording?
3. Are model paths, label files, device nodes, server hostnames, ports, API keys, and container volume/device mappings available on the target host?
4. Is a motion detector available if `scan_on_motion_only`, `require_motion`, or `require_motion_overlap` will be used?
5. Is the workflow strict recording, metadata-only detection, or post-processing after object detection? Configure `trigger_event_recording`, `store`, and post-processor `labels` accordingly.
