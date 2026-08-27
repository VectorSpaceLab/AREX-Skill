# Gradio Interface Reference

Evidence labels used for this reference: README.md, gradio_demo.py,
mmaudio/eval_utils.py, mmaudio/model/sequence_config.py.

## Launch command
```bash
python gradio_demo.py --port 7860
```

## Launch behavior
- The module resolves the default model (`large_44k_v2`) and downloads missing assets during import.
- The model and feature stack are loaded before the UI launches.
- The app writes outputs under `./output/gradio`.
- The launcher exposes only that output directory via `allowed_paths`.
- The default port is `7860`; change it with `--port` when the port is busy or when tunneling through SSH.

## Tabs and controls

| Tab | Inputs | Output | Notes |
| --- | --- | --- | --- |
| Video-to-Audio | Video, prompt, negative prompt, seed, num steps, guidance strength, duration | `playable_video` | Uses `load_video(...)` and reconstructs an MP4 with audio. The negative prompt defaults to `music`. |
| Text-to-Audio | Prompt, negative prompt, seed, num steps, guidance strength, duration | `audio` | No video input. Saves a `.flac` file. |
| Image-to-Audio (experimental) | Image filepath, prompt, negative prompt, seed, num steps, guidance strength, duration | `playable_video` | Uses `load_image(...)`, sets `image_input=True`, and treats the image path as an experimental conditioning source. |

## Default widget values
- Seed: `-1` means random in the UI.
- Num steps: `25`
- Guidance strength: `4.5`
- Duration: `8` seconds
- Negative prompt on the video tab: `music`

## What each tab actually does

### Video-to-Audio
- Calls `load_video(video, duration)`.
- Uses the returned `duration_sec` after any truncation.
- Adds a batch dimension to the clip and sync tensors.
- Generates audio with `generate(...)`.
- Writes an MP4 composite with `make_video(...)`.

### Text-to-Audio
- Passes `clip_frames=None` and `sync_frames=None` to `generate(...)`.
- Uses the empty conditioning paths in the model.
- Writes a timestamped `.flac` file.

### Image-to-Audio
- Calls `load_image(image)`.
- Uses `image_input=True`, which expands the clip features instead of running sync-video encoding.
- Rebuilds a display video with a 1 FPS image-backed `VideoInfo` wrapper.
- This path is explicitly experimental and should not be treated as a trained image-to-audio benchmark mode.

## UI and performance notes
- High-resolution images and videos are slower to process because the decode/encode path dominates runtime.
- The input resolution does not improve quality beyond the model's conditioning resize.
- The UI examples are disabled from caching.
- Generated files remain in `./output/gradio` and are the only local files the browser can access through the app.

## Operational checklist
1. Start the app from the repository root.
2. Verify the model downloads complete before the browser opens.
3. If the port is occupied, relaunch with another `--port` value.
4. For remote use, forward the selected port through SSH or your tunnel tool.
5. If you only need audio, use the text tab or the CLI instead of the video tab.
