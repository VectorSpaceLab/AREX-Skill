# Cross-Cutting Troubleshooting

Use this root troubleshooting guide when a Viseron failure spans several components or when the correct owner is not yet clear. Then route to the nearest sub-skill for workflow-specific recovery.

## Import and packaging problems

| Symptom | Likely cause | What to do |
|---|---|---|
| `ModuleNotFoundError: manager` while importing subprocess-related modules | Some Viseron source modules import the top-level `manager.py` helper. Commands run from a directory that is not the source root can hide that helper. | For development tasks, run import/test commands from the Viseron source root or ensure the source root is on `PYTHONPATH`. For installed application use, prefer the repository's container/runtime path rather than importing subprocess internals from an arbitrary directory. |
| `ModuleNotFoundError: gi` | GStreamer component needs PyGObject/GStreamer system libraries. | If the task uses GStreamer, prepare host/container system packages and Python bindings. If not, route to FFmpeg camera guidance and keep GStreamer unverified. |
| `ModuleNotFoundError: hailo_platform`, EdgeTPU interpreter errors, CUDA/OpenCL target errors | Optional accelerator runtime, drivers, devices, or container device mappings are missing or incompatible. | Decide whether the accelerator is required. If required, verify vendor runtime/device access on the target host; otherwise choose a CPU/service detector and record the accelerator as unverified. |
| Detector service client imports work but detections fail at runtime | External CodeProject.AI, DeepStack, or CompreFace server is unavailable, wrong host/port/API key, or model is missing. | Validate network reachability and service health separately from static YAML review. Check the component's `timeout`, `host`, `port`, `api_key`, model name, and train settings. |

## Configuration problems

| Symptom | Likely cause | What to do |
|---|---|---|
| Startup enters safe mode | `config.yaml` failed to load or validate, or a critical component failed. | Load `configuration-and-deployment`, run the bundled YAML/secret preflight, check logs for the first validation error, and simplify to a minimal config before re-adding components. |
| `!secret` error | `secrets.yaml` is missing or does not define the requested key. | Add the key to `secrets.yaml`, remove the `!secret` tag for non-secret values, or replace the value during tests with a placeholder secret file. |
| A top-level component appears enabled but does nothing | YAML null/empty value, wrong component name, or schema validation stripped/failed the intended settings. | Prefer explicit `{}` for default components and check spelling against the component capability index. Use component docs/schema summaries for required nested keys. |
| Changing config does not update a camera/detector as expected | Reload classification differs for component-level, domain-level, and identifier-level changes. | For user operations, restart when unsure. For development, load `developer-extension` and inspect reload diff rules and dependency unload ordering. |

## Runtime service problems

| Symptom | Likely cause | What to do |
|---|---|---|
| Camera connects but no recordings are saved | NVR not enabled for that camera, recorder disabled, storage tier prevents writes, event trigger not set, or detector/motion conditions never trigger. | Load `camera-recording-pipeline` for stream/recorder/storage checks, then load `detection-and-ai-components` if recordings depend on motion/object labels. |
| Object detections appear in logs but no event starts | Per-label `trigger_event_recording`, zone, `require_motion`, `require_motion_overlap`, `scan_on_motion_only`, or NVR optional dependency behavior is blocking the event. | Load `detection-and-ai-components` and trace label filters, zones/masks, motion state, and recording trigger flags. |
| MQTT/webhook/notification does not fire | Event name/topic mismatch, template condition false, label/camera override mismatch, credentials missing, or external endpoint unreachable. | Load `automation-and-integrations`; first prove the Viseron event exists, then test the template/payload and service connection separately. |
| Web UI works locally but fails behind a reverse proxy | `subpath`, websocket forwarding, public base URL, TLS headers, or auth/session settings do not match the proxy. | Load `configuration-and-deployment` and check webserver `subpath`, public URL, reverse-proxy path stripping, websocket upgrade headers, and auth rate limits. |

## Verification and safety boundaries

- Do not treat a successful Python import as proof that live camera streams, Docker containers, GPUs, accelerators, or external services work.
- Do not run destructive database reset or storage cleanup helpers unless the user explicitly asks and the target data is backed up.
- Do not run network/model-download/training/container-build tests as part of ordinary config review.
- When a required target-host backend is unavailable, narrow the task scope or report the backend block instead of silently substituting CPU behavior.

## Quick routing after triage

- YAML, secrets, startup, webserver, auth, logging: `configuration-and-deployment`.
- Camera URLs, FFprobe/FFmpeg/GStreamer, NVR, storage, recordings, live view: `camera-recording-pipeline`.
- Motion/object/face/LPR/classification detection, labels, masks, zones, models, devices: `detection-and-ai-components`.
- MQTT, webhooks, Telegram, Discord, Gotify, PTZ, events, templates: `automation-and-integrations`.
- Code changes, schemas, reload, domains, docs generation, focused tests: `developer-extension`.
