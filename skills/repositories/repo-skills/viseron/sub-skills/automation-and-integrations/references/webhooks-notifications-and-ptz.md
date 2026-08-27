# Webhooks, Notifications, and PTZ

Use this reference for outbound HTTP webhooks, Discord/Gotify/Telegram notifications, Telegram bot commands, and ONVIF PTZ control. Treat all delivery targets, bots, brokered credentials, and ONVIF cameras as external requirements unless the user explicitly authorizes live verification.

## Webhooks

A webhook component contains named hooks. Each hook listens to exactly one Viseron event name and then optionally renders a condition before sending an HTTP request.

```yaml
webhook:
  front_person_event:
    trigger:
      event: front_door/objects
      condition: >
        {{ event.camera_identifier == "front_door"
           and event.objects
           and (event.objects | selectattr("label", "equalto", "person") | list | length) > 0 }}
    url: "https://automation.example.invalid/hook/{{ event.camera_identifier }}"
    method: post
    headers:
      Authorization: "Bearer <redacted>"
      X-Viseron-Camera: "{{ event.camera_identifier }}"
    payload: >-
      {"camera":"{{ event.camera_identifier }}","matched_label":"person"}
    content_type: application/json
    timeout: 10
    verify_ssl: true
```

Schema and runtime behavior:

- Hook names are slugs under `webhook:`.
- `trigger.event` is an exact Viseron event name such as `front_door/objects`, `front_door/motion_detected`, or `front_door/recorder/complete`.
- `trigger.condition` is optional Jinja. The hook is skipped unless the rendered result is truthy according to Viseron's condition rules.
- `url`, `payload`, and each header value are rendered as Jinja templates with `event` and `states` context.
- Supported HTTP methods are `get`, `patch`, `post`, `put`, and `delete`; the schema lowercases the value.
- `content_type` defaults to `application/json` and is added as the `Content-Type` header when set.
- `payload` is UTF-8 encoded bytes when present; an omitted/empty payload is sent as no request body.
- `username` and `password` are an inclusive pair for basic authentication. Keep them static secrets or redacted values in examples; the runtime code passes the configured values to the HTTP client as basic auth.
- `verify_ssl` defaults to `true`. `ca_cert` may point to a target-runtime CA bundle or directory and takes precedence over the boolean `verify_ssl` value.
- Request exceptions are logged; the component does not implement retries or a dead-letter queue.

When a webhook should only fire for one camera/object label, combine an exact event name with a defensive condition. Avoid indexing `event.objects[0]` until checking that the list exists and is non-empty.

## Discord notifications

Discord sends webhook notifications for configured cameras on recorder start and recorder complete events.

Configuration shape:

```yaml
discord:
  webhook_url: "https://discord.example.invalid/webhook/<redacted>"
  detection_labels: [person]
  send_detection_thumbnail: true
  send_detection_video: true
  max_video_size_mb: 8
  cameras:
    front_door: {}
    driveway:
      webhook_url: "https://discord.example.invalid/webhook/<redacted-camera>"
      detection_labels: [car, truck]
      send_detection_thumbnail: false
      send_detection_video: true
      max_video_size_mb: 50
```

Behavior to preserve:

- The global `webhook_url` is required; a camera may override it.
- `detection_labels` defaults to `[person]`. The deprecated `detection_label` string is still accepted and split on commas. Camera-level labels override global labels.
- A recording with detected objects is skipped if none of the objects match the effective label list.
- A recording with no objects still matches in the Discord notifier, which is important for manual recordings.
- On recorder start, Discord sends a text message and may attach the thumbnail if enabled and available.
- On recorder complete, Discord sends the video when enabled and available. If the file exceeds `max_video_size_mb`, the implementation sends the first allowed bytes as a partial file. If video cannot be sent, it falls back to message and optional thumbnail.

## Gotify notifications

Gotify sends notifications when a configured camera starts a recording.

```yaml
gotify:
  gotify_url: "https://gotify.example.invalid"
  gotify_token: "<redacted>"
  priority: 5
  detection_label: "person,cat"
  send_thumbnail: true
  use_public_url: false
  image_max_size: 800
  image_quality: 95
  cameras:
    front_door: {}
    driveway:
      detection_label: "car,truck"
      send_thumbnail: false
```

Behavior to preserve:

- `gotify_url`, `gotify_token`, and `cameras` are required. The token is treated as sensitive.
- `priority` is 1-10 and defaults to `5`.
- `detection_label` is a comma-separated string and defaults to `person`; camera-level `detection_label` overrides the global value.
- Gotify skips recordings with no detected objects.
- `send_thumbnail` defaults to false. When true and a thumbnail exists, the image is resized to `image_max_size` unless that value is `0`, encoded at `image_quality`, and included in markdown.
- `use_public_url: true` creates a temporary public image URL through the webserver public-image mechanism. This requires a working webserver public base URL on the target deployment; otherwise the fallback URL is local-only.
- Gotify does not send videos; it sends text plus optional image markdown.

## Telegram notifications and camera commands

Telegram can both notify chats and accept commands. Configuration starts a bot and registers recorder-complete listeners for each configured camera.

```yaml
telegram:
  telegram_bot_token: "<redacted>"
  telegram_chat_ids:
    - 123456789
  telegram_user_ids:
    - 123456789
  detection_labels: [person]
  send_detection_thumbnail: false
  send_detection_video: false
  send_detection_message: true
  telegram_log_ids: false
  cameras:
    front_door: {}
    driveway:
      detection_labels: [car, truck]
```

Behavior to preserve:

- `telegram_bot_token`, `telegram_chat_ids`, and `cameras` are required. Treat chat IDs and tokens as sensitive in handoffs.
- `telegram_user_ids` restricts bot commands in public chats. In private chats, a user is allowed when their user ID appears in `telegram_user_ids` or when the private chat ID appears in `telegram_chat_ids`.
- `telegram_log_ids: true` logs denied user IDs; keep it off unless the user needs diagnostics.
- `detection_labels` defaults to `[person]`. The deprecated comma-separated `detection_label` still works. Camera-level labels override global labels; camera-level deprecated `detection_label` has highest precedence for that camera.
- Telegram sends on recorder complete. If a recording has detected objects and none match the effective labels, nothing is sent. If a recording has no objects, the notifier still sends according to the enabled message/video/thumbnail options.
- Defaults are message on, thumbnail off, video off.

Core Telegram commands registered by the notifier:

| Command | Purpose |
| --- | --- |
| `/record` or `/r` | Start manual recording on the active camera; optional duration and count arguments. |
| `/stop_recorder` or `/sr` | Stop an active manual recording. |
| `/list`, `/li`, or `/select` | List registered cameras and select the active one through buttons. |
| `/which` or `/w` | Show the active camera identifier. |
| `/toggle` or `/t` | Start or stop the active camera. |
| `/snapshot` | Return a snapshot from the active camera. |
| `/help` | List commands or show details for one command. |

Recording commands require the active camera to be registered, the NVR domain to be enabled for that camera, and a current frame to be available before starting manual recording.

## ONVIF PTZ and Telegram PTZ commands

The `ptz` component exposes ONVIF pan/tilt/zoom control. Telegram adds PTZ commands only when the `ptz` component is configured and ready.

```yaml
ptz:
  cameras:
    front_door:
      onvif_port: 80
      onvif_username: "<redacted>"
      onvif_password: "<redacted>"
      camera_min_pan: -0.7
      camera_max_pan: 0.1
      presets:
        - name: home
          pan: 0.0
          tilt: 0.0
          zoom: 0.0
          on_startup: true
        - name: driveway
          pan: -0.4
          tilt: 0.1
```

Important PTZ requirements:

- PTZ camera keys must match Viseron camera identifiers.
- The ONVIF host is taken from the registered camera configuration, while the PTZ component supplies ONVIF port, username, password, optional pan bounds, and optional presets.
- The PTZ component creates the ONVIF client after the camera domain is registered. A camera identifier mismatch or unavailable camera domain prevents PTZ registration.
- Presets are Viseron-configured absolute pan/tilt/optional zoom positions, not automatically imported from the camera.
- `on_startup: true` moves to that named preset when the PTZ camera is registered.
- Relative pan/tilt/zoom moves may return false when the ONVIF service is missing or the camera reports an operation exception. The implementation logs many ONVIF operation exceptions as usually harmless because some cameras report limits this way.

Telegram PTZ commands, available when PTZ is active:

| Command | Purpose |
| --- | --- |
| `/left` or `/l`, `/right` or `/r` | Pan relative by optional step size, default `0.1`. |
| `/up` or `/u`, `/down` or `/d` | Tilt relative by optional step size, default `0.1`. |
| `/zi` or `/i`, `/zo` or `/o` | Zoom in/out by optional step size, default `0.1`. |
| `/pos` | Report current pan/tilt position. |
| `/patrol` or `/p` | Swing left/right for a duration with optional pause, step size, and step sleep. |
| `/stop` or `/st` | Stop the current patrol. |
| `/preset` or `/pr` | List presets or move to a named preset. |
| `/repeat` | Repeat a named preset path a requested number of times. |
| `/lissa` | Start a Lissajous-curve patrol and send a preview image to the chat. |

Use conservative step sizes first. Do not ask Viseron to move a real camera until the user confirms the active camera, command, and physical safety constraints.
