---
name: configuration-and-deployment
description: "Guides Viseron installation, container deployment, configuration
  files, secrets, logging, webserver, authentication, and safe startup
  validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Configuration and Deployment

Use this sub-skill when the user needs to install or run Viseron, create or review `config.yaml` and `secrets.yaml`, enable safe debug logging, configure the Web UI/API/authentication surface, or diagnose startup/safe-mode behavior without tuning camera streams or detectors.

## Route by task

- **New deployment or container choice**: read [configuration workflows](references/configuration-workflows.md) for Docker image selection, volume conventions, default config creation, and safe startup checks.
- **Config/secrets validation before startup**: run [scripts/validate_config_yaml.py](scripts/validate_config_yaml.py) against a candidate YAML file before restarting or reloading Viseron.
- **Webserver, reverse proxy, public URLs, API, authentication, or logging**: read [webserver, logging, and auth](references/webserver-logging-and-auth.md).
- **Startup errors, missing secrets, safe mode, reverse-proxy subpaths, blank live view, auth lockouts, or noisy logs**: read [troubleshooting](references/troubleshooting.md).

## Boundaries

This sub-skill owns deployment, global configuration, webserver/auth/logger, safe validation, API access basics, live-view/snapshot configuration touchpoints, system event visibility, and templating context. Route camera stream URLs, FFmpeg/GStreamer command details, NVR/recording tiers, and storage-retention design to `camera-recording-pipeline`. Route detector labels, masks, zones, hardware detector choices, and post-processing to `detection-and-ai-components`. Route MQTT, webhooks, notifications, PTZ commands, and action templates to `automation-and-integrations`. Route component/domain implementation and tests to `developer-extension`.

## Safe workflow defaults

1. Validate YAML and secrets with the bundled script; it never starts Viseron.
2. Prefer explicit `{}` for enabled-but-default components such as `webserver: {}` or `logger: {}` even though Viseron normalizes null top-level entries to empty dictionaries.
3. Treat Docker, hardware acceleration, external services, cameras, and credentials as target-host requirements unless the user explicitly asks for live verification on that host.
4. For any config that could expose Viseron outside a trusted LAN, enable Viseron authentication and keep an independent reverse-proxy/VPN/access-control layer in front of the service.
