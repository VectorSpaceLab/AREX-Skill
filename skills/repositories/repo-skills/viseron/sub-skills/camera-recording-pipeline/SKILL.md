---
name: camera-recording-pipeline
description: "Guides Viseron camera ingestion, stream command construction,
  recorder/NVR behavior, storage tiers, recordings, snapshots, timelapse, live
  relay, and camera/NVR troubleshooting."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Camera Recording Pipeline

Use this sub-skill when the task is to configure or diagnose Viseron camera streams, FFmpeg/GStreamer command behavior, NVR coordination, recorder settings, retention tiers, snapshots, timelapse output, or live camera viewing.

## Route by task

- **Camera source, URL, FFmpeg/GStreamer, substream, FFprobe, hardware acceleration, raw command, or recoverable decode errors**: read [camera streams](references/camera-streams.md). Use [scripts/build_ffmpeg_url.py](scripts/build_ffmpeg_url.py) to safely construct and redact camera URLs without contacting a camera.
- **NVR coordination, event/continuous/manual recordings, recorder lookback and segments, storage tiers, snapshots, timelapse, event clips, or cleanup safety**: read [storage and recordings](references/storage-and-recordings.md).
- **Live View, MJPEG endpoints, static MJPEG streams, go2rtc/WebRTC/MSE, or restreaming through go2rtc**: read [live view and go2rtc](references/live-view-and-go2rtc.md).
- **Camera/NVR/storage/live-view failure diagnosis**: read [troubleshooting](references/troubleshooting.md) before changing config.

## Boundaries

This sub-skill owns camera ingestion, stream command construction, recorder/NVR operation, retention and cleanup planning, snapshots/timelapse storage, live camera relay, and camera/NVR failure modes.

Route detector labels, masks, zones, detector model/device choices, `trigger_event_recording` semantics beyond its recorder effect, and post-processor logic to `detection-and-ai-components`. Route Docker installation, global `config.yaml`/`secrets.yaml`, webserver/authentication/logging, and safe-mode startup to `configuration-and-deployment`. Route MQTT, webhooks, notifications, Telegram commands, Home Assistant discovery, and PTZ control surfaces to `automation-and-integrations`. Route component/domain implementation, tests, reload behavior, and source-code changes to `developer-extension`.

## Safe workflow defaults

1. Build or redact URLs locally; never print real camera passwords unless the user explicitly asks for raw output.
2. Treat live cameras, hardware acceleration, GStreamer system libraries, go2rtc ports, database services, containers, and network shares as target-host requirements unless separately verified on that host.
3. Prefer generated FFmpeg/GStreamer commands before using `raw_command`/`raw_pipeline`; raw overrides skip many safety defaults.
4. Keep recorder and snapshot retention separate: recorder tiers do not protect snapshots, and snapshot tiers do not protect event video.
5. Do not run destructive database reset helpers as a cleanup shortcut; use retention rules and normal Viseron cleanup behavior first.
