# Troubleshooting Norfair video, drawing, and camera-motion workflows

Use this guide before changing detector or tracker logic. If the failure is about `Tracker` parameters, distance functions, initialization, ReID, or `Detection` construction beyond drawable shape, route to `../../tracking-core/SKILL.md`. If the failure is about MOTChallenge metrics or benchmark files, route to `../../evaluation/SKILL.md`.

## Fast triage

1. Can Python import OpenCV and Norfair video/drawing modules?
2. Can OpenCV open the input source and read at least one frame?
3. Can OpenCV create the output writer for the requested file suffix/fourcc?
4. Do the drawables have the shape expected by the chosen drawer?
5. If camera motion is enabled, does `MotionEstimator.update(frame, mask)` return a usable transform or should you reuse identity/last-good transform?

## OpenCV and import issues

| Symptom | Likely cause | Recovery and validation |
| --- | --- | --- |
| `ImportError` mentioning Norfair video features or OpenCV | `opencv-python` is not installed. Minimal Norfair installs do not include the `video` extra. | Install the video extra (`pip install norfair[video]`) or install a compatible OpenCV package in the active environment. Then run `python scripts/video_smoke.py`. |
| Import works but `Video.show(...)` fails, hangs, or opens no window | Headless session or no OpenCV GUI backend. | Do not use `show` in headless jobs. Write video with `Video.write(frame)` and inspect the output file. |
| `cv2` imports from a different environment than Norfair | Mixed Python interpreters or notebooks/kernels. | Print `python -c "import sys, cv2, norfair; print(sys.version); print(cv2.__version__, norfair.__version__)"` from the runtime that will process the video. |

## Bad input paths and video sources

| Symptom | Likely cause | Recovery and validation |
| --- | --- | --- |
| `ValueError: You must set either 'camera' or 'input_path'` | `Video()` was called with neither source or with both. | Use exactly one: `Video(input_path="input.mp4")` or `Video(camera=0, output_fps=30)`. |
| `Argument 'camera' ... must be an int` | Camera id was passed as a string or device path. | Use an integer device id for Norfair's `camera` argument. If OpenCV needs a non-integer source URL/path, open it with OpenCV directly and use Norfair drawing helpers on those frames. |
| `File '...' does not exist` | Relative path is wrong for the current working directory, or the file was not copied into the runtime. | Resolve the path before constructing `Video`; `Path(path).expanduser().is_file()` should be true. Use a full file path in scripts/CI. |
| `does not seem to be a video file supported by OpenCV` or zero frames | OpenCV cannot decode the container/codec, file is corrupt, or the path points to a non-video file. | Validate with a tiny `cv2.VideoCapture(path).read()` check. Re-encode to `.mp4`/`mp4v` or `.avi`/`XVID`, or install an OpenCV build with the needed codec support. |
| Video loop stops early | `VideoCapture.read()` returned `False`/`None` due to end-of-file, corrupt frame, unsupported stream, or an interrupted camera. | Count frames with OpenCV before the Norfair loop. For cameras, handle reconnects outside `Video` or use a direct OpenCV loop. |

## Output writer and codec issues

| Symptom | Likely cause | Recovery and validation |
| --- | --- | --- |
| No output file appears until late in processing | `Video.write(frame)` opens the writer lazily on the first write; if no frame is written, no file is created. | Ensure the loop reaches `video.write(frame)`. Write the first resized/annotated frame only after you know the intended output size. |
| Output exists but has zero frames or cannot be opened | OpenCV `VideoWriter` failed for the suffix/fourcc or frame size. | Use `.mp4` with `mp4v` or `.avi` with `XVID`; avoid odd frame sizes if codecs reject them. In custom code, check `video.output_video.isOpened()` after the first `write`. |
| Runtime says it cannot determine codec | Output filename suffix is neither `.mp4` nor `.avi`, and `output_fourcc` was not supplied. | Use a supported suffix or pass `output_fourcc="mp4v"`, `"XVID"`, `"avc1"`, or another fourcc supported by the local OpenCV build. |
| Output dimensions are wrong | The first frame passed to `Video.write` had a different size than later frames. | Resize/crop all frames consistently before the first write. `Video.write` configures the writer from the first frame shape. |

## `VideoFromFrames` missing-frame problems

| Symptom | Likely cause | Recovery and validation |
| --- | --- | --- |
| `Couldn't find 'seqLength'` or another variable | `seqinfo.ini` is missing a required MOT-style key. | Check `frameRate`, `imWidth`, `imHeight`, `seqLength`, `imExt`, and `imDir`; values must match the actual frame folder. |
| Iteration yields `None` frames | `cv2.imread` could not read `input_path/<imDir>/<000001><imExt>` or later files. | Verify six-digit filenames, extension case, and image readability. Add `if frame is None: raise ...` before drawing. |
| Output under `save_path/videos/` is missing | `update(frame)` was not called, `make_video` was disabled, or the writer failed. | Use `make_video=True`, call `sequence.update(frame)` on each processed frame, and check codec support. |

## Drawing and drawable-shape issues

| Symptom | Likely cause | Recovery and validation |
| --- | --- | --- |
| `draw_boxes` draws a strange rectangle | Drawable points are not exactly two 2-D corners in `[[x0, y0], [x1, y1]]` order. | Convert center/width/height to top-left and bottom-right corners before wrapping in `Detection`; use `draw_points` for centroids/keypoints. |
| `draw_points` hides expected keypoints | `hide_dead_points=True` and a `TrackedObject.live_points` value is `False`; all dead points make the object disappear. | For debugging, set `hide_dead_points=False`, inspect `TrackedObject.live_points`, then route tracker point-life behavior to `tracking-core` if needed. |
| Labels or ids do not appear | `draw_labels`/`draw_ids` are disabled, label/id is `None`, or text is off-frame due to object position. | Enable `draw_labels=True`/`draw_ids=True`, set `text_size`/`text_thickness`, and ensure the drawable has `label` or a tracked object id. Detections never have ids. |
| Colors look swapped | OpenCV uses BGR, not RGB. | Use `Color` constants, BGR tuples, or hex strings parsed by Norfair. Do not assume `(255, 0, 0)` is red in OpenCV; it is blue. |
| Deprecated parameter warnings | Old code used `detections=`, `label_size=`, `line_color=`, `line_width=`, `color_by_label=`, `draw_tracked_objects`, or `draw_tracked_boxes`. | Prefer `drawables=`, `text_size=`, `color=`, `thickness=`, and the modern `draw_points`/`draw_boxes` functions. |

## Paths, absolute paths, and grid issues

| Symptom | Likely cause | Recovery and validation |
| --- | --- | --- |
| Relative trail drifts badly on moving-camera video | `Paths` records frame-relative positions and does not compensate for camera motion. | Use `AbsolutePaths` and pass the current `coord_transform` returned by `MotionEstimator.update(...)`. |
| `AbsolutePaths.draw(...)` raises because `coord_transform` is `None` | Motion estimation failed or has not produced a transform yet. | Use identity on the first frame or reuse the last good transformation. Do not call `AbsolutePaths.draw` with `coord_transform=None` in moving-camera mode. |
| Absolute paths are very slow | `AbsolutePaths` cost grows with `max_history * number_of_tracked_objects`. | Lower `max_history`, draw fewer points with a custom `get_points_to_draw`, or disable path drawing except on debug clips. |
| Absolute grid points vanish or drift | Estimated transform maps most grid points off-frame or is tracking moving objects/overlays instead of the background. | Call `MotionEstimator.update` before drawing overlays, mask moving boxes and static scoreboards/timestamps, increase background texture/features, and compare translation versus homography getters. |

## Camera-motion estimation issues

| Symptom | Likely cause | Recovery and validation |
| --- | --- | --- |
| `MotionEstimator.update(frame, mask)` returns `None` | Too few corners, optical flow failed, homography had fewer than four points, mask blocks too much, or frame is blank/low-texture. | Start with the bundled `camera_motion_smoke.py`, reduce `min_distance`, increase `max_points`, lower `quality_level`, verify the mask has nonzero background pixels, and use identity/last-good transform until estimation recovers. |
| Motion estimate follows players/cars instead of camera | Moving objects dominate sampled points. | Build a single-channel mask with zeros over detector/tracker boxes and other moving regions before calling `update`. Keep overlays out of the frame until after motion estimation. |
| Homography warnings about low amount of points | `HomographyTransformationGetter` needs at least four matched points and enough inliers. | Use more textured frames, increase `max_points`, lower `min_distance`, or switch to `TranslationTransformationGetter` if the camera only pans/tilts. |
| Optical-flow debug clutter hides detections | `draw_flow=True` draws lines and circles on the frame before later overlays. | Use `draw_flow` only on short debug clips, or write a separate debug video. Turn it off for final outputs. |

## Fixed-camera stabilization and cropping warnings

| Symptom | Likely cause | Recovery and validation |
| --- | --- | --- |
| Warning: `moving_camera_scale is not enough ... frame will be cropped` | The frame has moved outside the enlarged `FixedCamera` canvas. | Increase `FixedCamera(scale=...)`, shorten the clip, or crop intentionally. Run `python scripts/camera_motion_smoke.py --scale 2.5` as a known-good baseline.
| Stabilized output jumps or warps | `FixedCamera` was used with a homography transform or an unstable translation estimate. | Use only `TranslationTransformationGetter` with `FixedCamera`. For homography workflows, skip fixed-camera rendering and inspect with `draw_absolute_grid`/`AbsolutePaths`. |
| Overlays are scaled/offset incorrectly on stabilized video | Drawers were applied after `FixedCamera.adjust_frame(...)` using original-frame coordinates. | Draw detections, boxes, paths, grids, and flow first; call `FixedCamera.adjust_frame(...)` last; then write the stabilized frame. |
