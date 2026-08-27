# Camera Streams, FFmpeg, and GStreamer

This reference covers Viseron camera ingestion through the `ffmpeg` and `gstreamer` components. It is for configuration and troubleshooting, not for implementing new camera domains.

## Minimal stream shape

FFmpeg and GStreamer both expose cameras under a component-level `camera` map keyed by the camera identifier. The identifier must be reused by `nvr` and by live relay definitions.

```yaml
ffmpeg:
  camera:
    front_door:
      name: Front Door
      host: camera-lan
      port: 554
      path: /Streaming/Channels/101/
      username: !secret front_door_user
      password: !secret front_door_pass

nvr:
  front_door:
```

Required camera-source fields are `host`, `port`, and `path`. Optional auth fields are `username` and `password`. Set both auth fields when the camera requires credentials; Viseron only inserts credentials into the URL when both values are present.

## URL construction model

Viseron builds the stream URL from the selected stream config:

```text
{protocol}://{username}:{url-encoded-password}@{host}:{port}{path}
```

- `stream_format: rtsp` defaults to protocol `rtsp` and supports `rtsp_transport: tcp`, `udp`, `udp_multicast`, or `http` in FFmpeg.
- `stream_format: rtmp` defaults to protocol `rtmp`.
- `stream_format: mjpeg` is an FFmpeg source format that defaults to protocol `http`; it is not currently a GStreamer source format.
- `protocol` can override the protocol when needed, for example `rtsps` or `https`.
- Passwords are URL-encoded before command construction, so characters such as `@`, `:`, `/`, and `#` must not be pasted into raw URLs unescaped.

Use the bundled helper to build a redacted URL without touching the camera:

```shell
python scripts/build_ffmpeg_url.py \
  --host camera-lan --port 554 --path /Streaming/Channels/101/ \
  --username admin --password 'example:secret'
```

Add `--substream --sub-port 554 --sub-path /Streaming/Channels/102/` to show a matching substream URL. The helper defaults to redacted output and only prints raw credentials with `--show-secret`.

## FFmpeg command construction

The generated FFmpeg decoder command follows this order:

```text
ffmpeg + global_args + -loglevel + input_args + hwaccel_args + decoder_codec + rtsp_transport + -i URL + recorder segment args + video_filters + rawvideo output args
```

Important options:

| Option | Use |
|---|---|
| `global_args` | Arguments before input args; default includes `-hide_banner`. |
| `input_args` | Full replacement for the default low-latency input args and stream-format timeout option. Leave unset unless a camera requires specific FFmpeg input behavior. |
| `hwaccel_args` | Decoder hardware-acceleration arguments. Defaults may be injected for target container/hardware support. |
| `codec` | Decoder codec override, for example a CUDA/RPi/Jetson decoder. Leave `unset` to let FFprobe plus target env mapping choose. |
| `audio_codec` | Source audio codec metadata. Set to `null` when the stream has no audio and FFprobe is unreliable. |
| `rtsp_transport` | Usually `tcp`; switch only when the camera does not support TCP or the network requires another transport. |
| `video_filters` | Filters applied before Viseron receives frames. If rotating 90 degrees, also set the swapped `width` and `height`. |
| `pix_fmt` | Defaults to `nv12`; use `yuv420p` only when the decoder cannot produce `nv12`. |
| `frame_timeout` | Seconds without a frame before FFmpeg is restarted. Valid range is 1 to 60. |
| `record_only` | Records only; no frame processing and no MJPEG Live fallback unless `still_image` is configured. |

FFmpeg writes short fragmented MP4/HLS segments for the recorder. When no substream is configured, one process reads the main stream, writes segments, and pipes frames to Viseron. With a substream, Viseron starts one process for main-stream segments and one process that pipes the substream to detection/processing.

## Main stream plus substream

Use a lower resolution and lower FPS substream to reduce CPU/GPU work for detectors while keeping full-resolution recordings from the main stream.

```yaml
ffmpeg:
  camera:
    front_door:
      name: Front Door
      host: camera-lan
      port: 554
      path: /Streaming/Channels/101/
      username: !secret front_door_user
      password: !secret front_door_pass
      width: 1920
      height: 1080
      fps: 25
      codec: h264
      audio_codec: aac
      substream:
        port: 554
        path: /Streaming/Channels/102/
        stream_format: rtsp
        width: 640
        height: 360
        fps: 5
        codec: h264
        audio_codec: null
      recorder:
        idle_timeout: 10
```

Set all five metadata fields (`width`, `height`, `fps`, `codec`, `audio_codec`) on both streams when FFprobe is slow or incomplete. If any required field remains unset, Viseron calls FFprobe during camera initialization.

## FFprobe metadata

FFprobe is used to discover stream width, height, FPS, video codec, and audio codec. A recurring FFprobe timeout or incomplete metadata response should be handled by explicitly configuring all of these values. This also speeds startup because Viseron can skip probing.

FFprobe command behavior:

- Viseron requests JSON stream entries for `codec_type`, `codec_name`, `width`, `height`, and `avg_frame_rate`.
- RTSP probes include the configured `rtsp_transport`.
- Probe timeout grows with setup retry attempt, but repeated failures still leave the camera in a retry/not-ready state.
- If no video stream or no usable FPS is returned, Viseron cannot size frame buffers and raises a stream-information error.

## Hardware acceleration decision notes

Hardware acceleration support is target-host and container dependent. This generated skill did not verify live decoding on any accelerator.

- FFmpeg can use decoder mappings for CUDA/NVIDIA, VA-API, Raspberry Pi 3/4, and Jetson Nano when the runtime environment advertises support.
- FFmpeg defaults to VA-API args only when VA-API is supported and CUDA is not preferred.
- Jetson Nano FFmpeg support is limited; GStreamer may be a better target if the host has the required GStreamer stack.
- GStreamer imports require system-backed PyGObject/`gi`. Absence of `gi` means the GStreamer component is unavailable even if the rest of Viseron imports.
- GStreamer has a Jetson-specific pipeline; otherwise it builds a generic pipeline around `rtspsrc`/`rtmpsrc`, depay/parse/decode, optional output elements, raw `NV12` appsink, and `splitmuxsink` segments.

When changing hardware acceleration, change only one layer at a time: source metadata first, then transport, then decoder args/codecs, then recorder encoder args/codecs.

## GStreamer-specific notes

GStreamer camera config is similar to FFmpeg but has component-specific options:

| Option | Use |
|---|---|
| `stream_format` | `rtsp` or `rtmp`; MJPEG is not currently a GStreamer source format. |
| `output_element` | Additional GStreamer element(s) before conversion to raw frames; useful for rotation/filtering. |
| `audio_pipeline` | Optional custom audio path; default audio path re-encodes audio to AAC when audio is present. |
| `raw_pipeline` | Full replacement pipeline. It must output raw frames to the named appsink and create recorder segments via split-mux behavior. |
| `gstreamer_loglevel` | Debug only; default is `error`. |
| `gstreamer_recoverable_errors` | Substrings filtered as non-fatal noisy messages. |
| `recorder.*` | Recorder filters/codecs are still FFmpeg-style for recording-related settings in this component. |

GStreamer does not implement FFmpeg-style substreams in the inspected code path. If you need a low-resolution processing stream plus high-resolution recordings, prefer FFmpeg substreams unless you have a target-host reason to use GStreamer.

## Recoverable errors

Viseron filters known non-fatal FFmpeg/GStreamer log substrings so noisy camera bitstreams do not stop processing. Add only stable substrings that you have confirmed are non-fatal for the camera.

```yaml
ffmpeg:
  camera:
    front_door:
      # ... source config ...
      ffmpeg_recoverable_errors:
        - error while decoding MB
        - non-existing PPS 0 referenced
```

Do not use recoverable errors to hide connection failures, authentication failures, invalid codecs, missing binaries, or commands that exit immediately. If the frame reader exits or Viseron logs repeated empty frames, fix transport/metadata/codec first.

## Raw commands and raw pipelines

Use `raw_command` or `raw_pipeline` only when generated commands cannot represent the source.

- A processing FFmpeg raw command must write raw video to `pipe:1` in the configured pixel format and dimensions.
- A main-stream FFmpeg raw command used with `substream` must write recorder segments rather than raw frames.
- A GStreamer raw pipeline must feed an appsink named `sink` with raw frames and provide split-mux segments for recordings.
- Most schema options are ignored once raw mode is used; document the full command in the config and keep secrets in `secrets.yaml` where possible.

## Source-script decisions

The container-specific FFmpeg and FFprobe wrapper scripts were treated as reference-only and were not bundled. They only adjust container `LD_LIBRARY_PATH` and executable names; copying them into a generic generated skill would imply container-specific paths and binaries that may not exist on the target host.
