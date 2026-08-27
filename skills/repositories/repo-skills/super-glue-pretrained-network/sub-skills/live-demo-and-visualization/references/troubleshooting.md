# Troubleshooting

## No frames or first-frame failure

**Symptoms**: `Error when reading the first frame`, `Could not read camera`, or `VideoStreamer: Cannot get image from camera`.

**Likely causes**
- The webcam id is wrong or the device is busy.
- The IP/RTSP stream is unreachable or unauthorized.
- A video file path is incorrect.
- A directory input does not contain matching files.

**Fixes**
- Recheck `--input` and prefer an explicit directory or video file for debugging.
- Try a different webcam id if more than one camera is attached.
- For remote servers, skip live capture and use directory or video playback with `--no_display`.
- If the stream is IP-based, confirm the URL, credentials, and network reachability.

## No images found in directory mode

**Symptoms**: `No images found (maybe bad 'image_glob' ?)`.

**Likely causes**
- The directory path is wrong.
- The filename extension is not covered by the default glob patterns.
- `--skip` or `--max_length` reduced the usable list to zero.

**Fixes**
- Confirm the directory exists and contains images.
- Adjust `--image_glob` to match the files you actually have.
- Reduce `--skip` or raise `--max_length`.

## GUI or keyboard problems

**Symptoms**: the window does not appear, the preview is blank, or keyboard input is unreliable.

**Likely causes**
- The machine is headless.
- OpenCV GUI support is missing or unstable in the current build.
- The OpenCV window does not have focus.

**Fixes**
- Use `--no_display` on remote servers.
- Prefer the headless directory workflow or the bundled smoke helper.
- If you must use the live window, use a GUI-capable OpenCV build; the repository README notes that OpenCV 4.1.2.30 behaved well for keyboard interaction, while newer Qt-based builds can be less responsive or buggy on some hosts.
- Click the OpenCV window before testing `n`, `e`, `r`, `d`, `f`, `k`, or `q`.

## Too few or zero matches

**Symptoms**: the overlay is nearly empty or keypoints are detected but almost nothing matches.

**Likely causes**
- The keypoint threshold is too high.
- The match threshold is too high.
- The image was resized too aggressively.
- The scene needs the outdoor weights rather than the indoor weights.
- The current anchor frame is poor or too different from the live frame.

**Fixes**
- Lower `--keypoint_threshold` a bit.
- Lower `--match_threshold` a bit.
- Increase the resize size so more detail survives preprocessing.
- Use `--superglue outdoor` for outdoor or wide-baseline scenes.
- Re-anchor with `n` on a steadier frame.
- Turn on `--show_keypoints` to check whether the detector is producing usable points.

## Slow performance

**Symptoms**: the demo is sluggish on CPU or on large images.

**Likely causes**
- The run is on CPU.
- The frame size is too large.
- Too many keypoints are being kept.
- The sinkhorn loop is taking longer than needed for a smoke run.

**Fixes**
- Use CUDA when available and do not set `--force_cpu` unless you need it.
- Reduce `--resize` for quick debugging.
- Lower `--max_keypoints` if the scene is dense.
- Keep smoke runs short with a small `--max_length`.

## Resize warnings

**Symptoms**: the console warns that the input resolution is very small or very large.

**Likely causes**
- The requested resize is below the practical lower bound for feature matching.
- The requested resize is far above the practical upper bound for interactive demo work.

**Fixes**
- Stay in a moderate range, roughly between 160 and 2000 on the larger dimension.
- For webcam use, the common starting point is 320x240 or 640x480.

## Output files missing

**Symptoms**: the demo runs but no images appear in the output directory.

**Likely causes**
- `--output_dir` was not set.
- The directory is not writable.
- The run ended before any frames were written.

**Fixes**
- Create a writable output directory first.
- Confirm that the run processed at least one live frame after the anchor frame.
- Use the bundled smoke helper to verify the headless path end to end.

## Quick recovery checklist

1. Verify the input source first.
2. Switch to `--no_display` if the environment is remote.
3. Reduce resize and threshold aggressiveness.
4. Re-anchor with `n` when the scene changes.
5. Fall back to the bundled smoke helper for a bounded reproduction.