# Workflows

## 1. Interactive webcam demo

Use this when you want a live anchor-and-match loop.

1. Start with the default webcam input.
2. Let the first frame become the anchor, or press `n` on a better reference frame.
3. Adjust thresholds during the session if matches are too sparse or too noisy.
4. Press `k` to toggle keypoints, and `q` to exit.

Keyboard controls:
- `n`: set the current frame as the anchor
- `e` / `r`: decrease / increase the keypoint threshold
- `d` / `f`: decrease / increase the match threshold
- `k`: toggle keypoint rendering
- `q`: quit

## 2. IP camera or RTSP source

Use this when frames come from a remote camera endpoint.

- Pass the stream URL through `--input`.
- Keep `--no_display` off only if a GUI is available on the machine.
- If the stream stalls or returns no frames, switch to a local video file or directory sequence for debugging.
- The input is read through OpenCV, so camera permissions, authentication, and network reachability all matter.

## 3. Video file playback

Use this when you want a reproducible live-style sequence without a camera.

- Provide the video path via `--input`.
- Use `--skip` to thin dense videos.
- Use `--max_length` to keep the run short.
- Use `--resize` to trade off speed and match density.

## 4. Headless directory processing

Use this for remote servers, CI-style smoke checks, or offline sequence visualization.

```bash
python demo_superglue.py \
  --input assets/freiburg_sequence/ \
  --output_dir dump_demo_sequence \
  --resize 320 240 \
  --no_display
```

Notes:
- `--image_glob` controls which files are discovered in directory mode.
- `--skip` and `--max_length` bound the number of frames processed.
- `--output_dir` writes the rendered pair images even when no GUI is available.
- The smoke outputs are named with zero-padded anchor/live indices.

## 5. Safe bounded smoke helper

Use the bundled wrapper when you need a short, headless, directory-only run.

```bash
python scripts/run_headless_demo_smoke.py \
  --repo-root . \
  --input-dir assets/freiburg_sequence \
  --output-dir tmp/demo-smoke \
  --device cpu \
  --max-length 2 \
  --resize 320 240
```

Behavior:
- Always uses `--no_display`.
- Adds `--force_cpu` when `--device cpu` is selected.
- Keeps the run bounded so it is safe for validation and quick troubleshooting.
- `--device auto` prefers CUDA when available and otherwise falls back to CPU.

## 6. Tuning for weak matches

If the overlay is empty or nearly empty:

1. Lower `--keypoint_threshold` a little.
2. Lower `--match_threshold` a little.
3. Increase `--resize` if the scene was downscaled too much.
4. Use more keypoints with a larger `--max_keypoints` value.
5. Re-anchor on a more stable frame with `n`.

Visualization hints:
- `make_matching_plot_fast` colors matches by predicted confidence.
- Red lines are more confident; blue lines are less confident.
- `--show_keypoints` helps diagnose whether the detector is failing before matching does.