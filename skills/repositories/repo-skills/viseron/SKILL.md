---
name: viseron
description: "Guides Viseron self-hosted NVR deployment, camera recording,
  computer-vision detection, integrations, and backend extension workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Viseron Repo Skill

Use this skill when a task involves Viseron, the self-hosted local NVR and AI computer-vision application, especially when the user needs to configure cameras, recording, storage, object/motion/face/license-plate detection, notifications, automations, or backend components.

## First checks

- Viseron is normally operated as a containerized service with a YAML `config.yaml` and optional `secrets.yaml` mounted into the runtime config directory.
- The Python distribution is named `viseron` and the primary import package is `viseron`; source checkouts also rely on a top-level `manager.py` helper for some subprocess modules.
- Treat live cameras, Docker images, PostgreSQL, MQTT brokers, notification credentials, detector services, GPU/EdgeTPU/Hailo devices, and model downloads as target-host requirements unless the user explicitly asks to verify them.
- Run bundled scripts from this skill only against user-provided config snippets or an already prepared Viseron runtime/development environment; they are preflight helpers and do not replace Viseron startup validation.

## Route by task

- **Install, deploy, or validate global configuration**: load [configuration-and-deployment](sub-skills/configuration-and-deployment/SKILL.md) for Docker/container setup, `config.yaml`, `secrets.yaml`, webserver/auth/API, logging, safe mode, and startup validation.
- **Configure camera streams, NVR, recording, storage tiers, snapshots, timelapse, or live view**: load [camera-recording-pipeline](sub-skills/camera-recording-pipeline/SKILL.md) for FFmpeg/GStreamer/go2rtc, stream URLs, FFprobe metadata, recorder/NVR behavior, retention, and storage troubleshooting.
- **Choose or debug motion/object/post-processing AI components**: load [detection-and-ai-components](sub-skills/detection-and-ai-components/SKILL.md) for MOG2/background subtraction, MQTT external motion, YOLO, Darknet, EdgeTPU, Hailo, CodeProject.AI, DeepStack, dlib, CompreFace, labels, masks, zones, filters, and training/post-processing touchpoints.
- **Automate events or control integrations**: load [automation-and-integrations](sub-skills/automation-and-integrations/SKILL.md) for MQTT/Home Assistant, webhooks, Discord/Gotify/Telegram notifications, Telegram commands, ONVIF PTZ, data-stream events, and Jinja templates.
- **Modify or extend Viseron source code**: load [developer-extension](sub-skills/developer-extension/SKILL.md) for component/domain lifecycle, config schemas, reload behavior, entities, docs generation, tests, and source-root import caveats.

## Root references and scripts

- Read [component capability index](references/component-capability-index.md) when deciding which component/domain owns a user request before loading a sub-skill.
- Read [cross-cutting troubleshooting](references/troubleshooting.md) for install/import, optional dependency, Docker, config, service, and source-root failures that span multiple sub-skills.
- Read [repo provenance](references/repo-provenance.md) when checking whether this skill is stale relative to a newer Viseron checkout.
- Run [scripts/check_viseron_imports.py](scripts/check_viseron_imports.py) in a Viseron Python environment to probe core imports and optional dependency availability without contacting cameras or services.
- Run [scripts/extract_config_schema_summary.py](scripts/extract_config_schema_summary.py) in a Viseron source/runtime environment to list available component schemas and setup hooks.

## Common workflow skeletons

### Review a user configuration

1. Load `configuration-and-deployment` and validate YAML/secrets syntax first.
2. Route each top-level component to the owning sub-skill using the component capability index.
3. Check cross-component dependencies: cameras must load before NVR, object/motion detectors are optional or required depending on the component, and post-processors need object-detector labels that can trigger them.
4. For every external service, credential, device, model, or camera URL, separate static config review from target-host runtime verification.

### Diagnose missing recordings or detections

1. Load `camera-recording-pipeline` to check camera connectivity, stream metadata, recorder/NVR settings, storage tiers, and live-frame availability.
2. Load `detection-and-ai-components` to check whether motion/object labels, zones, masks, `scan_on_motion_only`, `trigger_event_recording`, `store`, and post-processor labels can produce the expected event.
3. Load `automation-and-integrations` only if the event exists in Viseron but an MQTT/webhook/notification/Telegram side effect is missing.

### Add or modify a backend component

1. Load `developer-extension` before editing code.
2. Keep `setup_domains()` hot-reload safe: register domain instances only, and avoid expensive shared initialization there.
3. Put component-level resources in `setup()`, declare `CONFIG_SCHEMA`, and model domain dependencies with `RequireDomain` or `OptionalDomain`.
4. After code changes, select focused native tests from the relevant sub-skill's candidate list rather than running hardware, container, or external-service checks by default.

## Who owns what

| User request signal | Owning route | Why |
|---|---|---|
| `config.yaml`, `secrets.yaml`, startup error, safe mode, web UI, API token, auth, or logging | `configuration-and-deployment` | These are global deployment concerns and should be checked before any camera or detector tuning. |
| RTSP/MJPEG URL, FFmpeg command, FFprobe timeout, recorder, NVR, live view, snapshots, timelapse, storage tier | `camera-recording-pipeline` | These concerns are tied to frame acquisition, recordings, and retained media. |
| Motion detected but no recording, label mismatch, zone/mask issue, model/device choice, EdgeTPU/Hailo/YOLO/Darknet, face or plate recognition | `detection-and-ai-components` | These are AI pipeline and post-processing choices. |
| MQTT entity/topic, webhook, Telegram, Discord, Gotify, PTZ, event topic, Jinja template | `automation-and-integrations` | These are side effects or control surfaces layered on top of Viseron events. |
| Setup hook, config schema, reload diff, domain dependency, entity class, docs generation, tests, or import caveat in source code | `developer-extension` | These are repo-maintenance and backend-extension tasks. |

## How to use the bundled scripts

- `scripts/check_viseron_imports.py` prints a compact import/probe report for core modules and selected optional groups. Use it when you need to know whether a Viseron environment is ready for source inspection or which optional backend is missing.
- `scripts/extract_config_schema_summary.py` summarizes which components expose `CONFIG_SCHEMA`, `setup()`, and `setup_domains()`. Use it when choosing which component-owned sub-skill should own a new configuration branch.
- The sub-skill scripts are intentionally narrow and safe. They should fail fast on malformed local input instead of starting Viseron or contacting live hardware/services.

## Verification boundaries

This skill was constructed from source, docs, tests, generated component explorer config, and CPU-safe installed-package inspection. It does **not** claim that this construction host verified live cameras, Docker images, PostgreSQL services, MQTT brokers, notification endpoints, YOLO/Darknet inference, EdgeTPU, Hailo, GStreamer/PyGObject, or CUDA/VA-API/Jetson/Raspberry Pi acceleration. Those remain explicit target-host checks.
