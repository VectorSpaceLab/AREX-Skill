# Events and Templates

Use this reference to choose event names for webhooks, understand data-stream topics, and render Jinja templates with Viseron's state/event context.

## Event delivery model

Viseron dispatches an `Event` object with:

- `name`: event name string.
- `data`: event-specific data object.
- `timestamp`: Unix timestamp.

A listener registered for event `front_door/motion_detected` receives the wrapper event. Webhook templates receive the inner event data as `event`, not the wrapper fields.

Data-stream topic mapping:

- Viseron events are published on `event/{event_name}`.
- `listen_event("front_door/objects", callback)` subscribes to `event/front_door/objects`.
- The lower-level data stream supports wildcard subscriptions such as `event/front_door/*`, but webhook triggers use exact event names.
- Core signals use data-stream topics `viseron/signal/shutdown`, `viseron/signal/last_write`, and `viseron/signal/stopping`.

The data-stream component is an internal pub/sub mechanism. It accepts callbacks, standard queues, and Tornado queues, and it runs callback work in threads or the supplied I/O loop. Do not treat it as a network API.

## Common event names for automation

Replace placeholders with configured identifiers.

| Area | Event name | Typical template fields |
| --- | --- | --- |
| Object detection | `{camera_identifier}/objects` | `event.camera_identifier`, `event.objects`, `event.zone` (`None` for field-of-view events) |
| Zone object detection | `{camera_identifier}/zone/{zone_name}/objects` | `event.camera_identifier`, `event.objects`, `event.zone.name`, `event.zone.coordinates` |
| Motion detection | `{camera_identifier}/motion_detected` | `event.camera_identifier`, `event.motion_detected`, `event.max_area` |
| Recorder start | `{camera_identifier}/recorder/start` | `event.camera.identifier`, `event.camera.name`, `event.recording.id`, `event.recording.objects`, `event.recording.thumbnail_path` |
| Recorder stop | `{camera_identifier}/recorder/stop` | same recorder data, with end fields when available |
| Recorder complete | `{camera_identifier}/recorder/complete` | same recorder data, including clip path when available to the component |
| Camera status | `{camera_identifier}/camera/status` | status event data; use the system event viewer on the target host for exact fields |
| Camera lifecycle | `{camera_identifier}/camera/start`, `{camera_identifier}/camera/stop`, `{camera_identifier}/camera/started`, `{camera_identifier}/camera/stopped` | lifecycle-specific data |
| Still image | `{camera_identifier}/still_image/available` | still-image availability data |
| Face recognition | `{camera_identifier}/face/detected/{face}` and `{camera_identifier}/face/expired/{face}` | `event.camera_identifier`, `event.face.name`, `event.face.confidence`, `event.face.coordinates` |
| Image classification | `{camera_identifier}/image_classification/result` and `{camera_identifier}/image_classification/expired` | classification result/expiry data |
| License plates | `{camera_identifier}/license_plate_recognition/detected/{plate}` and `{camera_identifier}/license_plate_recognition/expired/{plate}` | plate-recognition result/expiry data |
| MQTT internal | `mqtt/entity_added`, `mqtt/broker_reconnect` | MQTT entity or reconnect metadata; mainly useful for debugging integrations |
| Core entity/domain setup | `entity_added`, `state_changed`, `domain/registered/{domain}`, `domain/unregistered/{domain}`, `domain/setup/{status}/{domain}/{identifier}`, `component/setup/{status}/{component}` | setup/state metadata |

Detector scan/result constants such as `motion_detector/{camera_identifier}/scan`, `motion_detector/{camera_identifier}/result`, `object_detector/{camera_identifier}/scan`, and `object_detector/{camera_identifier}/result` are data-stream topics used by internal components. Use system events above for user-facing webhook triggers unless you are writing component code.

## Object and recording data in templates

Object event payloads expose `objects` as a list. Each object dictionary normally includes:

- `label`
- `confidence`
- `rel_width`, `rel_height`
- `rel_x1`, `rel_y1`, `rel_x2`, `rel_y2`

Defensive label condition:

```jinja2
{{ event.camera_identifier == "front_door"
   and event.objects
   and (event.objects | selectattr("label", "equalto", "person") | list | length) > 0 }}
```

Payload that includes all labels without assuming a first object:

```jinja2
{"camera":"{{ event.camera_identifier }}","labels":[{% for object in event.objects %}"{{ object.label }}"{% if not loop.last %},{% endif %}{% endfor %}]}
```

Recorder events expose `event.camera` and `event.recording`. A common payload is:

```jinja2
{"camera":"{{ event.camera.identifier }}","recording_id":{{ event.recording.id }},"trigger":"{{ event.recording.trigger_type }}"}
```

## State access in templates

Viseron passes `states` as a namespace backed by the current entity-state mapping.

Supported patterns from the helper implementation:

```jinja2
{{ states.binary_sensor.front_door_motion_detected.state }}
{{ states["binary_sensor.front_door_motion_detected"].state }}
{{ states.sensor["front_door_operation_state"].state }}
```

Rules and cautions:

- State keys are entity IDs in the form `domain.object_id`.
- Attribute-style access first selects the domain, then the object id: `states.sensor.front_door_operation_state` resolves `sensor.front_door_operation_state`.
- Use item access when an object id contains characters that are awkward in Jinja attribute syntax.
- Missing state keys raise `KeyError` in the helper. Pre-test templates and avoid missing-state references in webhook conditions.

## Condition truthiness

The webhook condition helper renders a template and converts the rendered result to boolean. Preserve these source-supported rules:

- `true`, `yes`, `on`, and `enable` are true, case-insensitive after trimming.
- Positive numeric rendered values are true; `0` and negative rendered numbers are false.
- Boolean values rendered by Jinja become strings such as `True` or `False` and follow the string rules.
- Empty templates, `None`, `false`, `no`, `off`, `disable`, random text, and missing/invalid numeric conversions are false.

Examples:

```jinja2
{{ event.motion_detected }}
```

```jinja2
{{ states.binary_sensor.front_door_motion_detected.state == "on" }}
```

```jinja2
{{ event.objects and event.objects[0].confidence > 0.85 }}
```

The last example is safe because it checks `event.objects` before indexing. Without that guard, an empty object list can break rendering.

## Local rendering helper

Use the bundled helper to render templates and conditions without network access:

```bash
python scripts/render_template_condition.py \
  --condition \
  --template '{{ event.camera_identifier == "front_door" and event.objects and (event.objects | selectattr("label", "equalto", "person") | list | length) > 0 }}' \
  --event '{"camera_identifier":"front_door","objects":[{"label":"person","confidence":0.91}]}' \
  --states '{"binary_sensor.front_door_motion_detected":{"state":"on","attributes":{}}}'
```

Expected JSON output includes the rendered string and the Viseron-style boolean result. Use `--sample` for a self-contained sample input and `--help` for all options.
