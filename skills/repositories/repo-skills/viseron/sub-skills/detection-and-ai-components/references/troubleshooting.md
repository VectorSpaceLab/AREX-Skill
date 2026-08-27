# Troubleshooting Detection and AI Components

This reference covers detector and post-processor failures owned by `detection-and-ai-components`. Treat live hardware, services, model downloads, cameras, containers, and credentials as target-host requirements unless separately verified in the user's environment.

## Object is detected but event recording does not start

Most causes are filter or gate mismatches:

1. The model label does not exactly match the configured `label`.
2. Detector-level `min_confidence` dropped the raw detection before label filters ran.
3. Per-label `confidence` is too high. Viseron requires detected confidence to be strictly greater than the configured threshold.
4. Relative `width_min`, `width_max`, `height_min`, or `height_max` exclude the box.
5. The object's lower portion is inside an object-detector mask.
6. The object is only configured inside a zone and the lower-center point of the object box is outside that zone.
7. The matching label or zone label has `trigger_event_recording: false`.
8. `scan_on_motion_only: true` delayed object scanning until motion was active.
9. `require_motion` or `require_motion_overlap` is set and the motion detector is absent, false, or has insufficient contour overlap.
10. Camera/NVR schedule or recorder settings block event recording; route those checks to `camera-recording-pipeline` after detector filters are ruled out.

Run the bundled checker against the relevant snippet:

```bash
python skills/disco/viseron/sub-skills/detection-and-ai-components/scripts/check_detection_config.py path/to/snippet.yaml
```

Use `--strict` if warnings, such as missing same-camera motion detector for motion overlap, should fail a CI-style check.

## Object detector never scans

- If `scan_on_motion_only: true`, ensure a motion detector for the same camera is configured and motion is actually becoming active.
- If no motion detector is configured, Viseron disables `scan_on_motion_only` and logs a warning; that may increase load rather than prevent scanning.
- Check `fps`; `0` is not a useful active scan rate even though non-negative numbers pass schema-style validation.
- Check `max_frame_age`; stale frames are discarded before inference.
- If there are no `labels` or `zones`, Viseron warns that no objects will be detected for that camera.

## Masks and zones behave unexpectedly

- Coordinate polygons need at least three `x`/`y` points.
- Coordinates are absolute pixels in the camera frame used by detection.
- Zone inclusion uses the object's lower-center point, not any overlap with the polygon.
- Motion masks ignore movement inside the polygon; object masks can discard objects whose lower portion is inside the polygon; post-processor masks hide pixels before face/classifier/LPR processing.
- If coordinates came from a screenshot, confirm the screenshot resolution matches the stream being analyzed.

## Motion detector false positives or missed motion

- For `background_subtractor`, lower `threshold` increases sensitivity; higher `alpha` adapts faster but can make small changes trigger motion. Large stationary changes may need time to settle into the background.
- For `mog2`, tune `history`, `threshold`, `detect_shadows`, and `learning_rate`. Shadow detection can help accuracy but costs resources.
- For both scanners, lower `fps` and smaller `width`/`height` reduce cost; increase them only if missed motion is unacceptable.
- Use masks for moving trees, roads, screens, timestamps, or lights.
- For MQTT external motion, confirm `topic`, `payload_on`, `payload_off`, and JSON `{"detected": true|false}` behavior. Unknown payloads are ignored. Set `max_motion_duration` when the off message might be lost.

## YOLO local detector issues

- `model_path` is required and must be readable inside the Viseron runtime, not merely on the host.
- Verify the model's labels. If the model emits `vehicle` but config tracks `car`, the label filter will never match.
- If detections are missing, lower detector `min_confidence` first, then tune per-label `confidence`.
- If performance is poor, reduce object-detector `fps`, use `scan_on_motion_only`, choose a smaller model, or move inference to an appropriate `device`.
- `half_precision` should only be enabled when the target GPU/model path supports FP16.
- Treat documented model compatibility notes as target-host requirements for unfamiliar YOLO versions.

## Darknet local detector issues

- `model_path`, `model_config`, and `label_path` must be consistent; mismatched labels or model dimensions produce bad labels/boxes or startup failures.
- Defaults point at container model paths. If using a custom model, mount weights/config/labels into those paths or update the config.
- If CUDA support is available and no explicit OpenCV backend/target is set, Viseron uses native Darknet; otherwise it uses OpenCV DNN.
- To force OpenCV/OpenCL behavior, set `dnn_backend` and `dnn_target` explicitly.
- Tiny models reduce CPU/RAM use but may significantly reduce accuracy.
- `suppression` is non-max suppression; too low or too high can change duplicate-box behavior.

## EdgeTPU detector or classifier issues

- Device values must be `cpu`, `usb`, `usb:<N>`, `pci`, `pci:<N>`, `:<N>`, or a list of those values.
- If `device` is omitted, Viseron selects an EdgeTPU when available, otherwise CPU. The selected model must be compatible with the selected device.
- Ensure the model and label file belong to the same training set.
- The implementation uses a subprocess and reloads after repeated failures. Repeated reload messages usually mean a model/device/runtime mismatch or unstable accelerator access.
- `image_classification.crop_correction` affects classifier crops; too little padding can crop out context, too much can include distracting background.

## Hailo detector issues

- Hailo support requires a compatible Hailo-8/Hailo-8L accelerator, host runtime/driver setup, and container access to the device.
- If a container is used, the Hailo device must be passed through to the Viseron runtime.
- `model_path` must point to a valid HEF model or a URL that the runtime can download; downloads are a startup/network requirement.
- The Hailo runtime version on the host must be compatible with the runtime expected by the Viseron image.
- `label_path` must match the HEF model's class ordering.
- `multi_process_service` is only useful when multiple processes need to share the Hailo device.

## External AI service issues

For CodeProject.AI, DeepStack, and CompreFace:

- `host`, `port`, API keys, and service-specific modules must be reachable from the Viseron runtime network namespace.
- Increase `timeout` only after confirming the service is healthy; long timeouts can stall detector loops.
- A connection or timeout error usually returns no detections/faces/plates and logs an error, while the rest of Viseron may continue.
- Service model labels must match Viseron label filters.
- If the service runs in another container, check service name resolution and exposed ports from Viseron's container, not from the user's shell alone.

Provider-specific checks:

- CodeProject.AI object detection uses `custom_model` and optional square `image_size` letterboxing. Use a model whose labels match the requested objects.
- DeepStack object detection requires `image_width` and `image_height` together if resizing is desired.
- CompreFace `similarity_threshold` determines known versus unknown faces; too high creates many unknowns, too low creates false matches.
- CodeProject.AI and DeepStack face training skip images with zero or multiple faces.

## Face recognition training problems

- The face folder must contain subdirectories named by person/subject; images directly under the root are invalid.
- The reserved `unknown` subject should not be used as a training identity.
- Each training image should contain exactly one clear face.
- If no classifier or service subjects are available, Viseron may still start but faces will be unknown or no results will be emitted.
- `save_unknown_faces` can collect examples; move only good samples into the correct person's folder before retraining.
- When using CompreFace `use_subjects`, entity creation comes from service subjects rather than local directories.

## License plate recognition problems

- LPR is post-processing: it needs an object detector to detect source labels such as `car`, `truck`, or the model-specific vehicle label first.
- `known_plates` only affects known/unknown sensor status; it does not make plates detectable.
- If plates are cropped poorly, check the source object detector label and bounding box quality before changing LPR thresholds.
- `min_confidence` too high suppresses plates; too low increases false positives.

## Quick triage questions

Ask these before making broad detector changes:

1. Which component owns this camera's motion detector, object detector, and post-processors?
2. Is the problem missing scans, missing model detections, filtered detections, no recording trigger, no database/snapshot storage, or no post-processor result?
3. Are optional devices/services/model files available inside the Viseron runtime, not only on the host?
4. Does a small YAML/JSON snippet pass the bundled checker for labels, polygons, and motion-overlap settings?
5. If the problem crosses detector decisions into recorder scheduling/storage, route to `camera-recording-pipeline` with the detector findings attached.
