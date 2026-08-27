# Component Capability Index

Use this index to map a Viseron task to the nearest generated sub-skill before reading deeper references.

## Core runtime and deployment

| Surface | Components or modules | Route | Notes |
|---|---|---|---|
| Global configuration | `config.yaml`, `secrets.yaml`, `viseron.config`, default config | `configuration-and-deployment` | YAML is loaded with `ruamel.yaml`; `!secret` values come from `secrets.yaml`; null top-level components are normalized to `{}`. |
| Startup and safe mode | `viseron.__main__`, `setup_viseron`, critical components | `configuration-and-deployment` | Config load failures activate safe mode instead of normal component setup. |
| Web UI/API/auth | `webserver` | `configuration-and-deployment` | Owns auth, tokens, rate limits, subpath/public URL, static files, and API handlers. |
| Logging | `logger`, Viseron logging helpers | `configuration-and-deployment` | Controls logger levels, duplicate/sensitive filters, and file rotation. |
| Source maintenance | component/domain/reload/docs/test modules | `developer-extension` | Use for code changes, not ordinary YAML support. |

## Camera, recording, live view, and storage

| Surface | Components or modules | Route | Notes |
|---|---|---|---|
| Camera ingestion | `ffmpeg.camera`, `gstreamer.camera` | `camera-recording-pipeline` | FFmpeg is the common camera backend; GStreamer needs system PyGObject/GStreamer support and is useful on some platforms such as Jetson. |
| Stream probing/commands | `ffmpeg.stream`, `FFprobe`, recorder command builders | `camera-recording-pipeline` | Manual width/height/fps/codecs can bypass repeated FFprobe failures. |
| Recording/NVR | `nvr`, camera recorder/fragmenter | `camera-recording-pipeline` | NVR depends on camera and can optionally incorporate motion/object detector domains. |
| Storage tiers | `storage`, SQLAlchemy models, tier handlers | `camera-recording-pipeline` | Separate recorder, snapshot, and timelapse categories; be careful with retention and cleanup. |
| Live relay | `go2rtc`, MJPEG stream options, public image URLs | `camera-recording-pipeline` with `configuration-and-deployment` for webserver URL/auth | go2rtc relays streams; webserver settings affect how users access live views and public URLs. |

## Detection and post-processing

| Surface | Components or modules | Route | Notes |
|---|---|---|---|
| Frame-based motion | `background_subtractor`, `mog2` | `detection-and-ai-components` | CPU OpenCV motion detectors; tune fps, resize dimensions, masks, thresholds, and recording triggers. |
| External motion | `mqtt.motion_detector` | `detection-and-ai-components` plus `automation-and-integrations` for broker topics | Uses MQTT messages instead of frame scanning. |
| Object detection | `yolo`, `darknet`, `edgetpu.object_detector`, `hailo`, `codeprojectai.object_detector`, `deepstack.object_detector` | `detection-and-ai-components` | All share per-camera labels/masks/zones/fps settings but have different model/device/service requirements. |
| Face recognition | `dlib`, `compreface`, `codeprojectai.face_recognition`, `deepstack.face_recognition` | `detection-and-ai-components` | Post-processor triggered by selected object labels; training/folders/services are component specific. |
| Image classification | `edgetpu.image_classification` | `detection-and-ai-components` | Post-processor requiring compatible TFLite/EdgeTPU model and labels. |
| License plate recognition | `codeprojectai.license_plate_recognition` | `detection-and-ai-components` | Post-processor for vehicle/plate workflows with service-side requirements. |

## Automation and external integrations

| Surface | Components or modules | Route | Notes |
|---|---|---|---|
| MQTT/Home Assistant | `mqtt`, MQTT entities, Home Assistant discovery | `automation-and-integrations` | Covers base topics, discovery prefixes, state/command topics, retained config, and external motion payloads. |
| Webhooks | `webhook` | `automation-and-integrations` | Triggered by event names and optional Jinja conditions; supports headers, auth, payload, TLS/CA settings. |
| Notifications | `discord`, `gotify`, `telegram` | `automation-and-integrations` | Camera-level overrides and detection labels decide when notifications are sent. |
| Camera control | `ptz`, Telegram PTZ helpers | `automation-and-integrations` | ONVIF PTZ and Telegram commands require matching camera identifiers and credentials. |
| Events/templates | `events`, `data_stream`, template helpers | `automation-and-integrations`; use `developer-extension` for code-level event changes | Distinguish event names/topics from rendered Jinja conditions. |

## Developer surfaces

| Surface | Components or modules | Route | Notes |
|---|---|---|---|
| Component lifecycle | `viseron.components.Component`, `setup_component`, `setup_components` | `developer-extension` | Components may define `setup()` and/or `setup_domains()`; config schema validation happens before setup. |
| Domain lifecycle | `viseron.domains`, `DomainRegistry`, domain base classes | `developer-extension` | Use `RequireDomain`/`OptionalDomain`; `DomainNotReady` retries with backoff. |
| Reload | `viseron.reload`, config diff dataclasses | `developer-extension` | Reload distinguishes component-level, domain-level, and identifier-level changes. |
| Docs generation | generated component explorer config, `scripts/gen_docs` behavior | `developer-extension` | Schema descriptions feed component documentation; generated docs writing is not a runtime skill task. |
| Tests | `tests/` | relevant workflow sub-skill plus `developer-extension` | Prefer focused unit/mocked tests; avoid live hardware/services unless explicitly selected. |
