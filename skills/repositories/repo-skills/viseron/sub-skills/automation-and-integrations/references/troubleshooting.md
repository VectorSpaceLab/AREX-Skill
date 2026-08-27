# Troubleshooting Automation and Integrations

Use this reference for failure modes owned by MQTT/Home Assistant, webhooks, notification integrations, Telegram commands, ONVIF PTZ, events, data-stream topics, and Jinja templates.

## MQTT entities missing in Home Assistant

Checklist:

1. Confirm Viseron MQTT itself connects to the intended broker. Broker return codes map to protocol/version, client ID, availability, bad credentials, or authorization failures.
2. Confirm both `username` and `password` are provided when either is needed. Supplying only one violates the schema.
3. Confirm `mqtt.home_assistant` is present. Without it, Viseron publishes MQTT state but does not publish discovery config.
4. Confirm Home Assistant listens on the same `discovery_prefix` that Viseron publishes. The default is `homeassistant`.
5. Inspect retained discovery messages. `retain_config: true` is the default; if it was false or changed after Home Assistant was offline, restart Viseron or enable `publish_ha_config_on_reconnect`.
6. Compute the expected state topic from `base_topic` or `client_id`. If `base_topic` is omitted, topics start with `client_id`.
7. Check retained state payloads on `{base_topic}/binary_sensor/.../state`, `{base_topic}/sensor/.../state`, `{base_topic}/toggle/.../state`, or image topics. Discovery without state may show unavailable entities.
8. For availability, expect source behavior of `{base_topic}/state` as `online`/`offline` and `{base_topic}/lwt` as `alive`/`dead`.
9. Unsupported Viseron entity domains are skipped by the MQTT/Home Assistant mapping. Supported domains are binary sensors, sensors, images, and toggles.
10. For switch commands, use lowercase `on`/`off`; generic toggle command handling is case-sensitive.

## MQTT external motion is not triggering

- The camera key under `mqtt.motion_detector.cameras` must exactly match a configured camera identifier.
- The detector subscribes only to the configured topic. Check the external sensor publishes to that exact topic.
- Raw payloads must exactly match `payload_on` or `payload_off`, unless using JSON with a boolean `detected` field.
- JSON examples that work: `{"detected": true}` and `{"detected": false}`.
- Unrecognized payloads are ignored and do not clear the previous state.
- If motion never clears, configure `max_motion_duration` as a safety timer or verify the external source publishes the off payload.
- If the recorder does not start, check the external motion detector's `trigger_event_recording`, `recorder_keepalive`, and camera/NVR configuration in the relevant camera and detector sub-skills.

## Webhook fires too often, not at all, or sends the wrong payload

- `trigger.event` must be an exact event name. `front_door/objects` and `front_door/zone/porch/objects` are different events.
- Webhook triggers do not use wildcard event names.
- The condition sees event data as `event`. For object events, check `event.objects` before indexing it.
- Missing state references raise `KeyError`. Test with the bundled renderer before deploying a condition.
- Viseron-style condition truth treats positive numbers and `true`/`yes`/`on`/`enable` as true; `0`, negative numbers, random text, and false-like strings are false.
- `url`, `payload`, and header values are rendered. If the rendered URL is empty, the hook is skipped.
- `username` and `password` must appear together for basic auth. Keep credentials in secrets and redact them in logs/handoffs.
- `content_type` defaults to `application/json` and is added as `Content-Type`; set it deliberately for non-JSON payloads.
- `ca_cert` takes precedence over `verify_ssl`. Use a target-runtime CA bundle rather than disabling SSL verification whenever possible.
- Request exceptions are logged. There is no built-in retry, queue, or backoff for failed webhook sends.
- Payloads are encoded as UTF-8 bytes. This avoids non-ASCII payload failures, but the receiver must accept the declared content type and charset.

## Difficult webhook case: one camera and one object label

Use this pattern:

1. Choose the narrowest event, usually `{camera_identifier}/objects` or `{camera_identifier}/zone/{zone_name}/objects`.
2. Write a condition that checks the camera identifier, checks that `event.objects` is non-empty, and uses `selectattr` or a loop to match labels.
3. Redact credentials in examples and store real tokens outside chat-visible output.
4. Test the condition locally with representative event JSON.
5. Only then enable the live webhook.

Safe condition pattern:

```jinja2
{{ event.camera_identifier == "front_door"
   and event.objects
   and (event.objects | selectattr("label", "equalto", "person") | list | length) > 0 }}
```

## Discord notifications not sent

- Discord listens to recorder start and recorder complete events for each configured camera.
- `webhook_url` is required globally; a camera can override it. Redact both global and camera URLs.
- Effective labels are resolved in this order: camera deprecated `detection_label`, camera `detection_labels`, global deprecated `detection_label`, global `detection_labels`, then default `[person]`.
- Recordings with objects are skipped if no object label matches. Recordings with no objects still match in the Discord notifier.
- Start notifications may include a thumbnail if `send_detection_thumbnail` is true and the thumbnail file exists.
- Complete notifications send video only when `send_detection_video` is true and a clip path exists. Oversized videos are truncated to the configured byte limit; otherwise the notifier falls back to message and optional thumbnail.
- HTTP failures are logged from the underlying request; no delivery retry is implemented.

## Gotify notifications not sent

- Gotify listens to recorder start events only.
- `gotify_url`, `gotify_token`, and `cameras` are required.
- Gotify skips recordings with no objects.
- Effective labels use camera `detection_label` when set, otherwise global `detection_label`, otherwise default `person`. The value is comma-separated.
- `send_thumbnail` defaults to false. Enable it and confirm a thumbnail exists if image messages are expected.
- `use_public_url: true` depends on the webserver's public base URL and public-image token mechanism. Without a reachable public base URL, links may only work locally.
- Gotify cannot upload videos through this integration; it sends text and optional image markdown.
- Check token permissions and target URL reachability from the Viseron runtime host.

## Telegram notifications or commands not working

- Telegram sends notifications on recorder complete events, not recorder start.
- `telegram_bot_token`, `telegram_chat_ids`, and `cameras` are required. Redact tokens and chat IDs.
- In public chats, add the command user's ID to `telegram_user_ids`. In private chats, a matching private `telegram_chat_ids` entry can also allow commands.
- If the bot does not see group messages, review the bot privacy setting in Telegram and ensure commands are sent in a way the bot receives.
- `telegram_log_ids: true` can help identify denied users, but it logs IDs and should be used deliberately.
- Effective labels follow the same precedence as Discord. If objects exist and none match, no notification is sent. If there are no objects, Telegram still sends according to enabled message/video/thumbnail options.
- Defaults are `send_detection_message: true`, `send_detection_thumbnail: false`, and `send_detection_video: false`.
- `/record` requires an active camera, NVR enabled for that camera, no active manual recording, and a current frame.
- `/snapshot` requires an active camera and current frame.
- Use `/list` or `/select` before commands that depend on the active camera.

## PTZ does not move

- The `ptz` component must be configured and ready before Telegram PTZ starts. If Telegram starts while PTZ is configured but unavailable, startup can be delayed by a component-not-ready condition.
- PTZ camera keys must match configured Viseron camera identifiers.
- The PTZ component creates ONVIF clients when the camera domain is registered. If the camera never registers, PTZ never obtains a service/token.
- ONVIF host comes from the camera configuration; PTZ supplies ONVIF port, username, password, pan bounds, and presets.
- Verify ONVIF credentials and port on the target camera. Many cameras use a separate ONVIF user or disabled ONVIF service.
- Preset names are configured in Viseron. `/preset list` only lists those configured presets.
- Pan/tilt/zoom step sizes are relative; large steps can hit camera limits. Start with the default `0.1` or smaller.
- Some ONVIF operation exceptions are logged as usually harmless when a movement hits limits. Repeated service-missing errors indicate configuration or camera availability, not harmless limits.
- Always confirm physical safety before running `/patrol`, `/repeat`, or `/lissa` against a real camera.

## Event and template surprises

- Webhook conditions receive inner event data, while direct event listeners receive the `Event` wrapper.
- Event data in the system event viewer is the best target-host truth for exact fields.
- `states.domain.object_id.state` resolves `domain.object_id`; use bracket access for awkward entity IDs.
- Negative rendered numbers are false in current condition behavior, despite common shorthand descriptions of non-zero numbers.
- Data-stream wildcard topics are internal. Webhooks need exact event names.
- If `data_stream` is not loaded, event listeners and signal handlers cannot be registered. In normal Viseron startup it is a core component.
