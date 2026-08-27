# MQTT and Home Assistant

Use this reference for Viseron automation through an MQTT broker, Home Assistant MQTT discovery, MQTT-triggered external motion, and MQTT command topics.

## Component shape

A minimal MQTT integration needs a broker. Defaults and constraints from the component schema:

```yaml
mqtt:
  broker: mqtt-broker.local
  port: 1883
  username: !secret mqtt_user   # optional, but username/password must appear together
  password: !secret mqtt_pass
  client_id: viseron            # default
  base_topic: viseron           # optional; falls back to client_id
  publish_states_on_reconnect: true
  home_assistant:               # optional; enables discovery
    discovery_prefix: homeassistant
    retain_config: true
    publish_ha_config_on_reconnect: false
```

Important details:

- `username` and `password` are an inclusive pair. Supplying only one is a config error.
- `base_topic` controls all Viseron state and command topics. If absent, Viseron uses `client_id`.
- `last_will_topic` can override the LWT topic; otherwise Viseron uses `{base_topic}/lwt`.
- The component evidence exposes plain broker host/port/auth options. Treat broker TLS, client certificates, and network reachability as target-broker requirements unless a later implementation adds explicit MQTT TLS options.
- `publish_states_on_reconnect` republishes entity states after reconnect. Home Assistant discovery config is only republished after reconnect when `home_assistant.publish_ha_config_on_reconnect: true`.

## State, command, and availability topics

Viseron creates MQTT entities from internal Viseron entities.

| Viseron entity domain | MQTT topic pattern | Home Assistant domain |
| --- | --- | --- |
| `binary_sensor` | `{base_topic}/binary_sensor/{object_id}/state` | `binary_sensor` |
| `sensor` | `{base_topic}/sensor/{object_id}/state` | `sensor` |
| `image` | `{base_topic}/image/{object_id}/image` plus `{base_topic}/image/{object_id}/attributes` | `camera` |
| `toggle` | `{base_topic}/toggle/{object_id}/state` and `{base_topic}/toggle/{object_id}/command` | `switch` |

Regular sensor/binary/toggle state payloads are retained JSON:

```json
{"state":"on","attributes":{}}
```

Image entities publish JPEG bytes on the `image` topic and JSON attributes on the `attributes` topic.

Availability and client-state topics:

- `{base_topic}/state` is Viseron's MQTT client connection topic; source behavior publishes `online` on connect and `offline` during stop, retained.
- `{base_topic}/lwt` is the default Last Will topic; source behavior publishes `alive` on connect and sets the broker Last Will payload to `dead`, retained.
- Home Assistant discovery availability uses both topics: `payload_available`/`payload_not_available` are `alive`/`dead` for LWT and `online`/`offline` for client state.

## Home Assistant discovery

Home Assistant discovery is disabled until `mqtt.home_assistant` is present. Discovery config topics use:

```text
{discovery_prefix}/{home_assistant_domain}/{object_id}/config
```

The generated discovery payload includes:

- `name`, `unique_id`, and `default_entity_id` based on the Viseron entity.
- `state_topic` and `value_template: {{ value_json.state }}` for binary sensors, sensors, and switches.
- `json_attributes_topic` with `json_attributes_template: {{ value_json.attributes | tojson }}`.
- A `device` object when the source Viseron entity exposes a device name and identifiers.
- `payload_on`/`payload_off` and `state_on`/`state_off` as lowercase `on`/`off` for switches.
- `command_topic` for switches.
- For image entities, discovery uses `topic` for the JPEG image topic instead of `state_topic`/`value_template`.

Common generated entity families include:

- Camera connection and recorder binary sensors.
- Object-detected binary sensors for any configured label, a specific label, any object in a zone, or a specific label in a zone.
- Motion-detected, face-detected, and still-image-available binary sensors.
- Latest thumbnail camera entity.
- Operation-state and object-detector-FPS sensors.
- Camera connection and manual-recording switches.

If Home Assistant entities do not appear, check both the retained discovery config topic and the retained Viseron state topic. A discovery config without later state can leave an entity unavailable; a state topic without matching discovery prefix/object id can leave Home Assistant unaware of it.

## MQTT external motion detector

The MQTT component can also act as a motion detector by subscribing to camera-specific topics:

```yaml
mqtt:
  broker: mqtt-broker.local
  motion_detector:
    cameras:
      front_door:
        topic: sensors/front-door/motion
        payload_on: "on"
        payload_off: "off"
        trigger_event_recording: true
        recorder_keepalive: true
        max_recorder_keepalive: 30
        max_motion_duration: 60
```

Behavior to preserve:

- Each camera key must match a configured Viseron camera identifier.
- Viseron subscribes to the configured topic when the motion detector starts and unsubscribes during unload.
- A raw payload exactly equal to `payload_on` sets motion true; `payload_off` sets motion false.
- A JSON object with a boolean `detected` field overrides the string payload comparison. Examples: `{"detected": true}` and `{"detected": false}`.
- Undecodable payloads, JSON without a boolean `detected`, and unrecognized strings are ignored without changing the last motion state.
- `max_motion_duration` is a safety timer inherited from the external motion detector base. A value of `0` disables auto-clear.

## Command topics

Generic toggle commands are case-sensitive and compare against lowercase `on` and `off` in the implementation. Home Assistant discovery also advertises lowercase payloads.

Manual recording has a richer command parser on the manual-recording toggle command topic:

```text
{base_topic}/toggle/{camera_identifier}_manual_recording/command
```

Accepted manual recording payloads:

```text
on
```

```text
off
```

```json
{"action":"start","duration":120}
```

```json
{"action":"stop"}
```

Manual recording start is ignored when a manual recording is already active, when the payload is malformed, when `duration` is non-positive, or when the camera has no current frame. Stop is ignored when there is no active manual recording.

## Quick diagnosis: Home Assistant entities missing

1. Confirm `mqtt.home_assistant` exists in Viseron config; plain MQTT publishing alone does not enable discovery.
2. Confirm Home Assistant and Viseron use the same MQTT broker and `discovery_prefix`.
3. Check whether discovery config messages are retained. `retain_config: true` is the default; if false, Home Assistant can miss config messages during restarts.
4. Check whether entity state messages are retained on `{base_topic}/.../state`.
5. After a broker outage, either restart Viseron or set `publish_ha_config_on_reconnect: true` when Home Assistant needs discovery config republished on reconnect.
6. Verify `base_topic` and `client_id`: if `base_topic` is unset, topics start with `client_id`.
7. For switches, publish lowercase `on`/`off` to the command topic unless a generated Home Assistant switch handles it for you.
