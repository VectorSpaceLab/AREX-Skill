# Tracking and Solutions Troubleshooting

## Install and Import Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: ultralytics` | Package is not installed in the active Python environment | Install/activate the intended environment, then verify `python -c "import ultralytics; print(ultralytics.__version__)"` |
| Solutions fail while importing or constructing geometry | `BaseSolution` requires `shapely>=2.0.0` | Install `shapely>=2.0.0`; then retry a small local frame/video with `show=False` |
| Similarity search asks for FAISS | `VisualAISearch` calls `check_requirements("faiss-cpu")` | Install `faiss-cpu` or avoid similarity search |
| Similarity search asserts torch version | `VisualAISearch` requires `torch>=2.4` | Use a compatible torch build, preferably CPU first for validation |
| Streamlit inference fails on import | `solutions.Inference` requires `streamlit>=1.29.0` | Install Streamlit, then run only if an interactive server is acceptable |
| Search web app fails on Flask | `SearchApp` requires `flask>=3.0.1` | Install Flask or use `VisualAISearch` directly |

## CLI Argument Shape Problems

Ultralytics CLI uses `arg=value`, not normal argparse flags.

Correct:

```bash
yolo track model=yolo26n.pt source="video.mp4" tracker=botsort.yaml show=False
yolo solutions count source="video.mp4" region="[(10,200),(540,200)]" show=False
```

Incorrect:

```bash
yolo track --model yolo26n.pt --source video.mp4
```

For list-like values, quote them so the shell passes one argument. Examples: `classes=0,2`, `region="[(20,400),(1080,400),(1080,360),(20,360)]"`, `kpts=[6,8,10]`.

## Tracker YAML Errors

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Assertion says only supported trackers are allowed | Custom YAML has unsupported `tracker_type` | Copy a built-in YAML and keep `tracker_type` as one of `botsort`, `bytetrack`, `ocsort`, `deepocsort`, `fasttrack`, `tracktrack` |
| Tracks reset between frames in a manual loop | `persist=True` was omitted | Use `model.track(frame, persist=True, ...)` for sequential frame calls |
| IDs reset between videos or source changes | Tracker state resets when source path changes unless `persist` applies | Keep one continuous stream, use `persist=True` for manual frames, or expect reset between separate videos |
| Many false tracks | `conf`, `track_high_thresh`, or `new_track_thresh` too low | Raise thresholds gradually; avoid lowering detector confidence and tracker thresholds together |
| Objects disappear after occlusion | `track_buffer` too low or tracker not suited for occlusion | Try `fasttrack.yaml`, `tracktrack.yaml`, or increase `track_buffer` carefully |
| Moving-camera ID switches | Tracker lacks effective global motion compensation | Try `botsort.yaml` or `tracktrack.yaml` with `gmc_method=sparseOptFlow`; set `gmc_method=none` only for stable cameras |
| ReID guidance fails or is slow | `with_reid=True` adds model/backend/compute requirements | Start with `with_reid=False`; if ReID is needed, prefer `botsort`, `deepocsort`, or `tracktrack`, validate device and model format separately |

## Region, Geometry, and Counting Problems

- Use exactly two points for line-based in/out counting with `ObjectCounter`.
- Use at least three points for polygon regions; four points are common for rectangles.
- Use a dictionary of named polygons for multiple `RegionCounter` zones in Python.
- Ensure region coordinates match the actual frame size after resizing or letterboxing assumptions.
- `RegionCounter` counts current objects whose centers are inside regions; `ObjectCounter` counts crossing direction over time.
- Queue counts require a polygon region and previous track positions; a brand-new track may not count until it has history.
- If `shapely` is missing, all `BaseSolution`-derived solutions can fail before processing. Install it before debugging region coordinates.

## Source, Codec, and Media Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| OpenCV cannot read the video | Bad path, unsupported codec, or unavailable stream | Confirm `source` exists, test with a small MP4, or transcode to a common codec |
| CLI downloads a sample unexpectedly | Solutions CLI was run without `source` | Always pass `source="..."` in reproducible commands |
| YouTube/RTSP/HTTP fails | Network or backend availability | Prefer local files for verification; treat network URLs as non-deterministic |
| No window appears or process hangs on display | Headless environment or GUI not supported | Set `show=False`; write outputs or inspect returned `SolutionResults` |
| Large disk output | CLI solutions write processed videos; `save_frames` creates many files | Ask before enabling video outputs or frame exports; choose a project/name if outputs matter |

## Device and Backend Problems

- Use `device=cpu` for first reproducibility checks.
- Use `half=True` only on compatible CUDA devices; FP16 on CPU is usually invalid or unhelpful.
- If CUDA is unavailable, remove `device=0` or set `device=cpu`.
- ReID and similarity search can be memory-heavy; test with a tiny source and small `imgsz` before full videos.
- Exported engines or deployment formats are outside this sub-skill; route engine/runtime conversion and benchmark issues to `../export-and-deployment/SKILL.md`.

## Download and Network Risks

- Model names such as `yolo26n.pt` may trigger weight downloads if absent locally.
- Solutions CLI without `source` can download demo videos.
- Similarity search with a missing `data` directory can download sample images.
- Streamlit UI uses remote logo/assets and starts a server process.

When the user needs offline or deterministic behavior, require local model files, local media, existing image directories, and `show=False`.

## Expensive or Unsafe Side Effects

Do not silently start:

- Long training, validation, export, or benchmark jobs; route those to sibling sub-skills.
- Webcam, RTSP, Streamlit, Flask, or GUI loops.
- Media downloads from URLs.
- Per-frame saves or large output videos.
- Email/security/parking workflows that need credentials or external JSON files.

Ask first or provide a dry-run command with the expected side effects.
