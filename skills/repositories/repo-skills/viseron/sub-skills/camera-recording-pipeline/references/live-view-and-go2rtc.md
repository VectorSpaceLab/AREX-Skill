# Live View, MJPEG Streams, and go2rtc

Use this reference when configuring Viseron camera viewing, MJPEG stream endpoints, or go2rtc-based WebRTC/MSE live relay. It does not cover webserver authentication or reverse-proxy setup; route that to the deployment/configuration sub-skill.

## Live View modes

Viseron Live View can show cameras through:

1. **MJPEG fallback** from the frames Viseron is already processing.
2. **go2rtc WebRTC or MSE** for higher-quality, lower-latency live streams and optional camera restreaming.

Without the go2rtc component, Live View is limited to MJPEG. If a camera uses FFmpeg `record_only: true`, MJPEG is not available because Viseron is not decoding frames for processing; configure a `still_image` if the UI still needs a preview.

## Dynamic MJPEG stream endpoint

Every camera can expose a dynamic MJPEG stream:

```text
http://<viseron-host>:8888/<camera_identifier>/mjpeg-stream
```

Query parameters can resize or annotate the stream:

| Parameter | Effect |
|---|---|
| `width`, `height` | Resize output. |
| `draw_objects` | Draw detected objects. |
| `draw_object_mask` | Draw configured object masks. |
| `draw_motion` | Draw detected motion. |
| `draw_motion_mask` | Draw configured motion masks. |
| `draw_zones` | Draw zones. |
| `draw_post_processor_mask` | Draw post-processor masks. |
| `mirror` | Mirror horizontally when truthy. |
| `rotate` | Rotate by degrees; positive clockwise, negative counter-clockwise. |

Example:

```text
http://<viseron-host>:8888/front_door/mjpeg-stream?width=640&draw_objects=true&draw_zones=true
```

Each dynamic MJPEG stream processes frames independently. If multiple consumers need the same view, configure a static stream instead.

## Static MJPEG streams

Static streams define the query-parameter work in `config.yaml` so the processed result can be reused.

```yaml
ffmpeg:
  camera:
    front_door:
      host: camera-lan
      port: 554
      path: /Streaming/Channels/101/
      mjpeg_streams:
        annotated_small:
          width: 640
          height: 360
          draw_objects: true
          draw_zones: true
          draw_motion: true
        clean_small:
          width: 640
          height: 360
```

Static endpoints follow this shape:

```text
http://<viseron-host>:8888/front_door/mjpeg-streams/annotated_small
```

Static MJPEG stream names should use lowercase letters, numbers, and underscores.

## Still images

The camera domain can use a still image URL for UI previews. This is useful for `record_only` cameras or cameras whose live stream is temporarily unavailable.

```yaml
ffmpeg:
  camera:
    front_door:
      host: camera-lan
      port: 554
      path: /Streaming/Channels/101/
      still_image:
        url: http://camera-lan/snapshot.jpg
        username: !secret front_door_user
        password: !secret front_door_pass
        authentication: digest
        refresh_interval: 10
        use_last_snapshot_on_error: true
```

`authentication` can be `basic` or `digest`. `use_last_snapshot_on_error` uses extra memory and should be enabled only when a stale preview is better than no preview.

## go2rtc component shape

go2rtc is an optional relay component. Viseron passes the `go2rtc` config through to the go2rtc service, restarts the service, and uses the local go2rtc API to learn which camera stream names are available. A camera's live-stream availability is true when go2rtc reports a stream whose name matches the Viseron camera identifier.

The stream names under `go2rtc.streams` must match Viseron camera identifiers:

```yaml
go2rtc:
  streams:
    front_door:
      - rtsp://camera-user:camera-pass@camera-lan:554/Streaming/Channels/101/
  webrtc:
    candidates:
      - 192.0.2.10:8555
      - stun:8555
  log:
    level: debug
```

Treat go2rtc ports, NAT traversal candidates, camera codec support, and browser WebRTC/MSE selection as target-host behavior unless explicitly verified on that host.

## Restream cameras through go2rtc

Restreaming reduces the number of direct connections to a camera. Point Viseron's FFmpeg camera at the local go2rtc RTSP listener and place the physical camera URL under `go2rtc.streams`.

```yaml
ffmpeg:
  camera:
    front_door:
      name: Front Door
      host: localhost
      port: 8554
      path: /front_door
      stream_format: rtsp

go2rtc:
  streams:
    front_door:
      - rtsp://camera-user:camera-pass@camera-lan:554/Streaming/Channels/101/
```

If other devices outside Viseron should consume go2rtc streams, expose the go2rtc service ports in the target container/deployment. Do not assume those ports are exposed by default.

## Live-view troubleshooting quick checks

- If Live View shows only MJPEG or low quality, check whether `go2rtc` is configured and whether stream names exactly match camera identifiers.
- If MJPEG is unavailable, check whether the camera is `record_only`, disconnected, or lacks processed frames.
- If annotations are missing from MJPEG, verify the query/static stream draw flags and route detector mask/zone semantics to the detector sub-skill.
- If WebRTC fails but MSE works, suspect browser/NAT/candidate issues rather than the camera config.
- If go2rtc restart or stream discovery fails, inspect go2rtc service availability on the target host; the component talks to a local go2rtc API and logs connection failures.
