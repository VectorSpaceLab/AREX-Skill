# Video troubleshooting

## Codec or reader problems

- Symptom: the demo cannot open an AVI/MP4 file or stops during reading.
- Likely cause: the input codec is unsupported or `imageio-ffmpeg` is missing.
- Recovery: install the video IO dependencies and test with the bundled sample
  video first.

## Short or irregular clips

- Symptom: the smoothing demo behaves oddly or drops most frames.
- Likely cause: the smoothing window is longer than the clip, or the start/end
  frame settings exclude too much of the video.
- Recovery: shrink `n_pre` and `n_next`, or start with the default values on the
  sample clip.

## Tracking drift

- Symptom: the rendered mesh jumps or the tracker re-detects frequently.
- Likely cause: the head pose changed too quickly or the face turned too far.
- Recovery: expect re-detection on difficult frames; for a more stable test,
  use a less aggressive motion sequence.

## Webcam display issues

- Symptom: the webcam demo opens no usable window or fails to access the camera.
- Likely cause: the host blocks the camera, or the machine has no GUI display.
- Recovery: treat webcam tracking as manual-only and test camera permissions
  outside the headless wrappers.
