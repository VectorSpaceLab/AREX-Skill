# Configuration Workflows

## Purpose

Use this reference to plan a Viseron deployment, create or review `config.yaml`/`secrets.yaml`, and perform safe pre-start validation. It distills the repository's Docker-first installation guidance, config loader behavior, and startup/reload semantics into a self-contained workflow.

## Deployment decision points

Viseron's user-facing deployment model is Docker/container based. A source checkout can expose Python entry points for development, but normal operation should be planned as a container with mounted configuration and media volumes.

### Choose the image class

| Target host need | Container choice | Requirements to verify on the target host |
| --- | --- | --- |
| Generic amd64/aarch64/armhf Linux | Multi-arch `roflcoopter/viseron:latest` or architecture-specific image | Docker/Compose available, enough RAM and disk, mounted volumes writable. |
| amd64 with NVIDIA CUDA decoding/inference | CUDA-specific amd64 image | NVIDIA driver and NVIDIA Container Toolkit; pass the runtime/device settings in Docker/Compose. |
| Intel/VA-API decoding | Generic image with render device access | `/dev/dri` device available and mounted into the container. |
| Raspberry Pi | Generic/RPi-oriented image with privileged/device mounts | Adequate RAM, camera substreams for lower load, required video/USB device mounts. |
| Jetson Nano | Jetson-specific image | NVIDIA runtime and privileged/device access for Jetson acceleration. |
| Home Assistant OS app/add-on | Viseron Home Assistant app flow | Home Assistant app store access and ingress/subpath behavior. |

Hardware acceleration, live cameras, Docker image execution, and external detector services are target-host requirements, not locally verified by this generated skill.

### Mount the important paths

Use stable host directories and mount them to the paths Viseron expects inside the container:

- `/config`: `config.yaml`, `secrets.yaml`, Viseron database/config state, auth/onboarding state, and `viseron.log`.
- `/segments`: continuous and event recording segments.
- `/snapshots`: object/motion/post-processor snapshots.
- `/thumbnails`: thumbnails for generated event clips.
- `/event_clips`: event clip outputs.
- `/timelapse`: timelapse output.
- `/etc/localtime:ro`: keeps container time aligned with the host.

Recommended container settings include `--shm-size=1024mb` or `shm_size: "1024mb"`. If host volume ownership causes permission errors, set `PUID` and `PGID` to the host user/group that owns the mounted directories. `VISERON_DISABLE_CHOWN=true` can skip recursive ownership changes on startup, but only use it when the host paths are already writable by the configured user/group.

### Port and reverse proxy model

Public container examples expose the Web UI on host port `8888`. Prefer changing the host-side port mapping or reverse-proxy listener rather than relying on the deprecated `webserver.port` option. If a reverse proxy serves Viseron under a subpath, configure `webserver.subpath` and the proxy path together; see [webserver, logging, and auth](webserver-logging-and-auth.md).

## Config directory and files

Viseron reads `config.yaml` and `secrets.yaml` from the container configuration directory. In normal containers this is `/config`, and source-level defaults use `/config/config.yaml` and `/config/secrets.yaml`. Advanced development/runtime contexts may change the config directory with `VISERON_CONFIG_DIR`, but generated skill guidance should stay portable and describe the container convention unless the user explicitly gives another runtime.

If no `config.yaml` exists at startup, Viseron creates a default walkthrough file and then treats that exact default content as an empty config. An empty YAML file also loads as an empty config. On startup Viseron always sets up core/default services such as the data stream, storage, and webserver; configured components are then loaded from top-level keys in `config.yaml`.

Top-level component entries with no value are normalized to empty dictionaries. These are accepted by Viseron, but explicit `{}` is clearer for humans and safer for automated edits:

```yaml
webserver: {}
logger: {}
```

## `!secret` behavior

`secrets.yaml` must live next to `config.yaml` in the same config directory. Any scalar value in `config.yaml` can use `!secret key_name`; Viseron replaces it with the matching value from `secrets.yaml` during config loading.

Example:

```yaml
# secrets.yaml
camera_one_host: 192.0.2.10
camera_one_username: viseron
camera_one_password: replace-this
```

```yaml
# config.yaml
ffmpeg:
  camera:
    camera_one:
      name: Front Door
      host: !secret camera_one_host
      username: !secret camera_one_username
      password: !secret camera_one_password
```

If `config.yaml` contains `!secret` but `secrets.yaml` is missing, startup fails into the safe-mode path. If a referenced key is absent from `secrets.yaml`, config loading raises an error naming the missing key. Validate before a restart:

```bash
# From this sub-skill directory, or by resolving the bundled script path from the loaded skill.
python scripts/validate_config_yaml.py /path/to/config.yaml --secrets /path/to/secrets.yaml
```

The validator prints secret key names only; it never prints secret values and never starts Viseron.

## Minimal safe configurations

### Camera-less debug/safe-mode triage

When the user wants the Web UI and logs without any camera, detector, or integration load, use a camera-less config like:

```yaml
webserver: {}
logger:
  default_level: debug
  logs:
    viseron.components: debug
```

This keeps the config focused on the critical webserver/storage/logger surfaces. It is suitable for parsing checks, web UI access, onboarding/auth triage, and safe-mode troubleshooting. Do not present it as an NVR configuration; it intentionally does not configure cameras or recording.

### Enable authentication from the start

```yaml
webserver:
  auth: {}
logger:
  default_level: info
```

On first access, the frontend prompts onboarding to create the initial admin user. Authentication should be combined with external network controls when exposing the service beyond a trusted LAN.

### Reverse proxy with subpath and auth

```yaml
webserver:
  subpath: /viseron
  auth:
    session_expiry:
      days: 30
logger:
  default_level: info
```

The proxy path must match `subpath`. For Nginx-style proxying, the upstream `proxy_pass` should strip the subpath by ending in `/`, and the proxy must support WebSocket upgrades for live updates.

## Editing and reload workflow

- The frontend Configuration Editor can edit `config.yaml`, syntax-highlight YAML, and trigger a config reload.
- The Camera Tuning page can edit some camera-specific settings, but camera tuning belongs to the camera/recording sub-skill.
- A command-line reload can be sent with `docker exec -it viseron viseron --reload`; this sends a SIGHUP to running Viseron processes.
- A SIGHUP starts a reload thread and does not exit the main process. If another SIGHUP arrives while reload is still running, it is ignored with a warning.
- Reload errors are reported through the Web UI/response path or logs. If a critical component cannot load, Viseron activates safe mode and loads the last known good critical-component config when available.

Before any reload or restart, run the bundled validator and inspect logs for config-loader errors. Full component schema validation still happens inside Viseron, so the validator is a preflight check rather than a complete substitute for startup.

## API, live view, snapshots, system events, and templating touchpoints

- **API and WebSocket**: the webserver serves the Web UI, REST API, and WebSocket API. When auth is enabled, API calls require valid authentication; personal access tokens are generated in the Profile page for API clients.
- **Live view**: the Live page can show MJPEG streams from frames Viseron is processing. WebRTC/MSE live viewing requires the `go2rtc` component and camera stream configuration, which is owned by `camera-recording-pipeline`. `record_only: true` disables decoded frames, so the default MJPEG live stream is not available.
- **Snapshots/public image URLs**: snapshots come from detector and post-processor events and are stored under the snapshot volume. Public image URLs are controlled by `webserver.public_base_url`, `public_url_expiry_hours`, and `public_url_max_downloads`.
- **System events**: admins can inspect dispatched events in the Web UI system-event viewer. Event payloads help users build webhook payloads and template conditions.
- **Templating**: Viseron uses Jinja2-style templates where supported by components. Template context can include `states` and event data. Template-heavy webhooks and notification actions are owned by `automation-and-integrations`; this sub-skill only covers where the context comes from and how to validate deployment prerequisites.
