# Camera Recording Pipeline Troubleshooting

Start with the symptom, then isolate source URL, stream metadata, decoder process, NVR coordination, retention tiers, or live relay. Avoid changing detector labels/zones or deployment/authentication settings here unless the symptom directly points to camera/NVR ownership.

## Source URL and authentication

| Symptom | Likely cause | Checks and fixes |
|---|---|---|
| Camera never connects; logs show auth or 401-like failures | Bad username/password or password characters not URL-encoded | Rebuild the URL with `scripts/build_ffmpeg_url.py`; keep credentials in secrets; ensure both `username` and `password` are configured. |
| URL has the wrong scheme | `stream_format` and `protocol` mismatch | For RTSP use `stream_format: rtsp`; for secure RTSP set `protocol: rtsps`; for MJPEG/HTTP use FFmpeg `stream_format: mjpeg` with `protocol: http` or `https`. |
| RTSP connects on one client but not Viseron | Transport mismatch | Try `rtsp_transport: udp` or `http` only after confirming TCP is unsupported. Keep one transport change per test. |
| Camera path looks right but Viseron probes a bad URL | Missing leading slash or copied full URL into `path` | `path` should be only the path portion, for example `/Streaming/Channels/101/`; put host/port/protocol in their own fields. |

## FFprobe and metadata

| Symptom | Likely cause | Checks and fixes |
|---|---|---|
| Startup waits on FFprobe or retries camera setup | FFprobe timeout | Configure all of `width`, `height`, `fps`, `codec`, and `audio_codec` for the main stream; do the same in `substream` if used. |
| Stream-information error | FFprobe returned no video stream, no dimensions, no FPS, or no codec | Manually set metadata; verify the camera path and selected stream actually contain video. |
| Wrong aspect ratio after 90-degree rotation | Width/height were not swapped | If using `transpose`/rotation for 90 degrees, set `width` to the rotated width and `height` to the rotated height. |
| Audio causes segment warnings | Source audio codec is unsupported by MP4 copy path | Set recorder `audio_codec` to `aac` to transcode, or `null` to drop audio. |

## FFmpeg/GStreamer decoder process

| Symptom | Likely cause | Checks and fixes |
|---|---|---|
| `Did not receive a frame` or frame reader restarts repeatedly | Camera stream stalls, wrong pixel format, bad decoder, or too-low `frame_timeout` | Confirm metadata, use generated command before raw mode, keep `pix_fmt: nv12` unless decoder requires `yuv420p`, and increase `frame_timeout` only after fixing source issues. |
| Logs contain non-fatal H264/H265 decode noise | Noisy camera bitstream | Add a stable substring to `ffmpeg_recoverable_errors` or `gstreamer_recoverable_errors` only after confirming frames continue to arrive. |
| Command exits immediately after adding `raw_command` | Raw command does not output what Viseron expects | Processing raw commands must write raw video to `pipe:1`; main-stream raw commands used with a substream must write segments; raw mode ignores many normal options. |
| GStreamer component cannot import or start | Missing system-backed PyGObject/`gi` or GStreamer plugins | Treat GStreamer as optional target-host capability; use FFmpeg unless the host has the GStreamer stack and needed plugins. |
| Hardware acceleration makes the camera worse | Wrong decoder args/codecs for target image/device | Revert to software decoding, then add only one target-specific change at a time (`hwaccel_args`, decoder `codec`, recorder encoder args). |

## NVR and recording behavior

| Symptom | Likely cause | Checks and fixes |
|---|---|---|
| Camera appears configured but Viseron does not do anything useful | Missing `nvr` entry for the camera identifier | Add `nvr: {camera_id: {}}` using the exact camera identifier. |
| No event recordings | Detector did not trigger recording, event schedule is inactive, or NVR has no relevant detector | Confirm NVR exists; confirm detector-owned trigger settings in the detector sub-skill; check `recorder.schedule.events`; remember manual recording is not blocked by schedule. |
| Recording stops too soon after motion/object disappears | `idle_timeout` is too low | Increase camera `recorder.idle_timeout`; keep `max_recording_time` bounded. |
| Pre-event context is missing | `lookback` is too low or segments were cleaned before use | Increase `recorder.lookback`; ensure first-tier continuous/event retention leaves room for lookback plus segment duration. |
| Manual recording interrupts event recording | Expected NVR behavior | Manual recording forces the current event recording to stop, then starts manual recording. Plan user workflows accordingly. |
| Scanner FPS warning | Detector FPS exceeds camera output FPS | Lower detector FPS or raise processing output capacity; NVR clamps scan interval so it cannot scan more frames than the camera produces. |

## Storage tiers and cleanup

| Symptom | Likely cause | Checks and fixes |
|---|---|---|
| Validation rejects tier path | Reserved path, missing mount, duplicate tier path, or invalid age progression | Avoid `/tmp`; ensure category folders/mounts exist; use unique tier paths; make later `max_age` greater than earlier `max_age` for the same type. |
| Files disappear sooner than expected | Tier `max_age` is not additive | Calculate retention from original file creation time. A 7-day archive tier means 7 total days, not first-tier age plus archive age. |
| Event clips retained but snapshots disappear | Recorder tiers do not govern snapshots | Configure `storage.snapshots` or per-camera snapshot tiers separately from `storage.recorder`. |
| Continuous recordings consume all disk | Continuous retention enabled without adequate `max_size`/`max_age` | Add `continuous.max_size` or `continuous.max_age`; remember size is per camera. |
| Event recordings do not move to archive | First tier did not enable `events`, or later event tier violates validation | Enable `events` in the first recorder tier and add a later tier with greater event `max_age`. |
| First tier on NAS/NTFS misses files | File events/metadata unreliable | Move first tier to local disk/RAM disk. Use network/NTFS only for later tiers, and set `poll: true` when needed. |
| Storage database mismatch after manual file deletion | Files were removed outside Viseron | Prefer UI/API deletion and tier retention. Let cleanup jobs handle orphaned files; avoid manual deletion while running. |
| Temptation to recreate database to fix storage | Destructive workaround | Do not run database-recreate helpers unless the user explicitly accepts losing DB state. They drop tables and are not bundled in this skill. |

## Snapshots and timelapse

| Symptom | Likely cause | Checks and fixes |
|---|---|---|
| Too many object snapshots | Stationary objects or low store interval | Detector-owned `store_interval`/label behavior controls creation; this sub-skill controls snapshot retention tiers. |
| Snapshot domain override has no effect | Override placed under wrong category/camera | Use `storage.snapshots.<domain>.tiers` globally or camera `storage.snapshots.<domain>.tiers` for one camera. |
| Timelapse frames are missing | No `storage.timelapse` tiers, no segments available, or FFmpeg extraction failure | Configure timelapse tiers with an interval and verify target-host FFmpeg/segment availability. |

## Live view and go2rtc

| Symptom | Likely cause | Checks and fixes |
|---|---|---|
| Live View falls back to MJPEG | go2rtc not configured or stream name mismatch | Ensure `go2rtc.streams` keys exactly match camera identifiers. |
| MJPEG endpoint is unavailable | Camera is `record_only`, disconnected, or no processed frames are flowing | Disable `record_only` for live processing or configure `still_image`; then debug stream/NVR. |
| Static MJPEG stream consumes unexpected CPU | Multiple dynamic streams instead of one static stream | Move repeated query parameters into `mjpeg_streams` so processing can be reused. |
| WebRTC/MSE fails outside the host | go2rtc ports/candidates not exposed or NAT/browser issue | Treat candidates and exposed ports as deployment requirements; start simple on the same LAN before changing camera source config. |
