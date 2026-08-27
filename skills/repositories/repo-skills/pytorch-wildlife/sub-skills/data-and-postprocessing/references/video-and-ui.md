# Video, Gradio, and deployment guidance

## Frame processing

`PytorchWildlife.utils.process_video(source_path, target_path, callback,
target_fps=1, codec="mp4v")` reads video metadata with supervision, samples
frames when the source FPS is above `target_fps`, and writes a new video with
`VideoSink`. The callback contract is exactly:

```python
def callback(frame: numpy.ndarray, index: int) -> numpy.ndarray:
    ...
```

`frame` is an RGB NumPy frame and `index` is the index of the sampled frame,
not necessarily the original source frame number when stride is greater than
one. Return an RGB NumPy frame suitable for the sink and preserve the frame
height/width. The utility converts RGB to BGR before writing. If source FPS is
less than or equal to the requested target FPS, it uses every frame; otherwise
its integer stride is `int(source_fps / target_fps)`, so the effective output
rate can be approximate. `target_fps` should be a positive integer.

`codec="mp4v"` is the conservative default. A browser may fail to render an
otherwise valid output; try `avc1` with an OpenCV build that includes the
encoder (the project documentation specifically suggests a conda-forge
OpenCV install after removing the pip OpenCV wheel). Codec availability is
platform/build dependent. A missing ffmpeg/OpenCV codec or malformed input
usually fails at metadata or sink creation, not in the callback. Test a tiny
local fixture, not a downloaded video, before processing a large collection.

A detector/classifier callback can call detection on the frame, crop each
animal box using `supervision.crop_image`, classify the crop, then draw boxes
and labels with supervision annotators. Keep model construction outside the
callback so weights are not repeatedly loaded. Route model selection and
threshold semantics to the detection/classification sub-skills.

## Gradio capabilities and safe boundaries

The demonstration UI provides controls for:

- single-image detection with detector and classifier thresholds;
- ZIP batch image detection, optionally emitting detection or TimeLapse JSON;
- folder-path detection followed by Animal/No_animal separation; and
- uploaded video processing with output FPS and `mp4v`/`avc1` codec choices.

It may load detector weights and classifier weights on demand. It is a demo,
not a hardened multi-tenant service: large ZIPs/videos consume local disk and
memory, uploads may fail on Windows for large files, and browser playback is
codec-sensitive. Validate ZIP extraction and do not accept untrusted archives
without defending against archive path traversal and resource exhaustion.

Never expose a demo server directly to an untrusted network. The application
has no user authentication. Keep it on loopback, use `share=False`, isolate
scratch files in a per-process temporary directory, and put any remote
access behind an authenticating reverse proxy with upload limits. Do not
publish local model paths or permit arbitrary file-serving paths. Do not
launch the UI as part of routine skill verification.

## Install and Docker overview

For the public 1.3.0 distribution, use Python >=3.10 and install the package
with `pip install PytorchWildlife` in an isolated environment. CPU is a
supported execution path; CUDA is optional and requires a compatible PyTorch
installation and host driver. Video work may additionally need a working
OpenCV/ffmpeg codec stack. Prefer the PyTorch installation command appropriate
for the host rather than copying a fixed CUDA command into an automated
workflow.

The project also publishes a Docker-based demo workflow: use a trusted,
version-pinned image, map only the required local port, and pass the intended
command explicitly. Treat image pulls and container execution as deployment
operations requiring user approval; this skill does not pull images, launch a
server, or ship a Docker runner. Pin and review the image provenance before
using it, and do not assume an old image tag has the current package security
posture.
