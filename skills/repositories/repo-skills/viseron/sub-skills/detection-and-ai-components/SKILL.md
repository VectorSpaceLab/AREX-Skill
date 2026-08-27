---
name: detection-and-ai-components
description: "Guides Viseron motion detection, object detection,
  post-processing, labels, masks, zones, and AI detector hardware or service
  choices."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Detection and AI Components

Use this sub-skill when the user is configuring or diagnosing Viseron's AI pipeline: motion detectors, object detectors, face recognition, image classification, license plate recognition, labels, filters, masks, zones, post-processing triggers, model paths, detector devices, or external AI services.

## Route by task

- **Choose a detector or backend**: read [detector selection](references/detector-selection.md) before editing component blocks such as `background_subtractor`, `mog2`, `mqtt`, `yolo`, `darknet`, `edgetpu`, `hailo`, `codeprojectai`, `deepstack`, `dlib`, or `compreface`.
- **Explain why detections do or do not trigger recordings**: read [labels, masks, zones, and filters](references/labels-masks-zones-and-filters.md), then check the candidate config with [scripts/check_detection_config.py](scripts/check_detection_config.py).
- **Configure face recognition, image classification, license plate recognition, training folders, or object-triggered post-processors**: read [post-processing and training](references/post-processing-and-training.md).
- **Diagnose optional hardware, service, model, payload, motion-overlap, mask, or label failures**: read [troubleshooting](references/troubleshooting.md).

## Boundaries

This sub-skill owns detector and post-processor behavior only. Route camera URL acquisition, FFmpeg/GStreamer stream construction, NVR storage tiers, recordings, snapshots, timelapse, and live relay to `camera-recording-pipeline`. Route Docker installation, config-file basics, secrets, logging, webserver, and safe startup to `configuration-and-deployment`. Route MQTT entity publication, Home Assistant discovery, webhooks, notifications, PTZ commands, and template delivery to `automation-and-integrations`. Route writing new components/domains/tests or changing Viseron source to `developer-extension`.

## Safe workflow defaults

1. Treat GPU, EdgeTPU, Hailo, external AI services, camera streams, containers, model downloads, and credentials as target-host requirements unless the user explicitly asks for live verification on that host.
2. Validate small detector snippets with the bundled checker before restarting Viseron; it parses YAML/JSON and never imports Viseron, OpenCV, ML frameworks, or service clients.
3. For recording-related questions, inspect the full path: object detector scanning gate, label/zone filters, `trigger_event_recording`, `scan_on_motion_only`, motion detector presence, and motion-overlap requirements.
4. For post-processors, first ensure the object detector tracks the source object labels; post-processors only receive objects that passed object-detector filtering.
