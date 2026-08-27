# Inference troubleshooting

## `source` does not resolve

The detector cannot read a source that does not exist or is not readable by OpenCV.

Recovery:

- Check the file or directory path.
- If you are using a source list, make sure each line is valid.
- Classify the source before running the detector.

## Webcam or stream capture fails

Webcam and RTSP/HTTP capture depends on the local OpenCV build and network reachability.

Recovery:

- Test with a local image directory first.
- Verify the camera index or stream URL.
- Reduce the problem to a simpler source before changing model settings.

## GUI windows do not open

`view_img` requires a display-capable environment.

Recovery:

- Disable `view_img` in headless environments.
- Save images or text labels instead.
- Use the inference helper to decide whether a GUI run is even appropriate.

## Output folder surprises

The detector recreates the output directory before writing results.

Recovery:

- Never point it at a directory full of files you want to keep.
- Treat the output path as scratch space.
- Check the output path before starting a long run.

## `--update` changed the checkpoint

The update mode strips optimizer state after running inference.

Recovery:

- Do not use `--update` on a checkpoint you intend to preserve untouched.
- Keep a separate copy of the weights if you need the original file.

## Unexpectedly empty detections

A bad confidence threshold, a wrong checkpoint, or a source that does not match the model can all lead to no visible outputs.

Recovery:

- Lower the confidence threshold.
- Confirm that the checkpoint was trained for the data you are testing.
- Try a simpler source and the bundled helper first.
