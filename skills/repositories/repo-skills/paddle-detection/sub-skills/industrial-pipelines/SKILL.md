---
name: industrial-pipelines
description: "Configures PaddleDetection PP-Human, PP-Vehicle, PP-Tracking,
  ReID, plate, attribute, action, violation, and video/RTSP industrial
  pipelines."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Industrial Pipelines

Use this route when the task names PP-Human, PP-Vehicle, PP-Tracking, pedestrian or vehicle analysis, ReID/MTMCT, tracking, attribute recognition, plate recognition, action/fall/fight/smoking/phoning/intrusion detection, illegal parking, vehicle press-line/retrograde, image/video/RTSP input, or `deploy/pipeline`.

## Workflow

1. Choose a pipeline family: PP-Human, PP-Vehicle, or PP-Tracking-like MOT deployment.
2. Summarize the selected YAML with [`scripts/summarize_pipeline_config.py`](scripts/summarize_pipeline_config.py). Confirm enabled modules, model directories, visual output, and input type.
3. Stage local model directories before running. Many pipeline configs use URLs/auto-downloads; treat them as explicit network operations.
4. Choose one input mode: `--image_file`, `--image_dir`, `--video_file`, `--video_dir`, `--rtsp`, or `--camera_id`. Avoid specifying multiple modes unless testing parser priority.
5. Start CPU/paddle mode on a short local image/video fixture. Promote to GPU/TensorRT or multi-camera only after model/input preflight passes.
6. For counting or region-based tasks, set `--region_type`, `--region_polygon`, and related flags deliberately and record the coordinate system.

## References

- [`references/pipeline-configuration.md`](references/pipeline-configuration.md): parser flags, config override semantics, module names, and input priority.
- [`references/pphuman-ppvehicle-workflows.md`](references/pphuman-ppvehicle-workflows.md): PP-Human and PP-Vehicle feature routing.
- [`references/troubleshooting.md`](references/troubleshooting.md): pipeline dependency, model download, video, RTSP, tracking, and region errors.
