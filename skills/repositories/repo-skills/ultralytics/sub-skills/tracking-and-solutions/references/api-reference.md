# Tracking API and Tracker Reference

## Direct Tracking APIs

Ultralytics exposes tracking through the Python API and the `yolo` CLI.

```python
from ultralytics import YOLO

model = YOLO("yolo26n.pt")
results = model.track(source="video.mp4", tracker="botsort.yaml", conf=0.25, iou=0.7, show=False)
```

The verified installed signature is:

```text
Model.track(source=None, stream=False, persist=False, **kwargs) -> list[Results]
```

Use `stream=True` for memory-efficient iteration over videos or streams. Use `persist=True` only when the caller is feeding sequential frames manually and wants the tracker state reused across calls.

```python
for frame in frames:
    result = model.track(frame, persist=True, tracker="bytetrack.yaml", verbose=False)[0]
```

For CLI usage, keep the shape `yolo TASK MODE arg=value`:

```bash
yolo track model=yolo26n.pt source="video.mp4" tracker=botsort.yaml conf=0.25 iou=0.7 show=False
yolo detect track model=yolo26n.pt source="video.mp4" tracker=bytetrack.yaml classes=0,2
```

Do not use argparse-style flags such as `--source video.mp4` with `yolo track`; Ultralytics expects `source=video.mp4`.

## Supported Tracker YAMLs

Built-in tracker configs are selected by passing the YAML name or a custom YAML path in `tracker=`. Supported `tracker_type` values are `botsort`, `bytetrack`, `ocsort`, `deepocsort`, `fasttrack`, and `tracktrack`.

| YAML | Best first use | Notable knobs | Optional dependencies/compute |
| --- | --- | --- | --- |
| `botsort.yaml` | Default stable video tracking, moving cameras | `gmc_method`, `track_buffer`, `match_thresh`, `with_reid`, `appearance_thresh` | ReID adds model/compute; GMC methods use OpenCV features |
| `bytetrack.yaml` | Fast, simple MOT and low-confidence recovery | `track_high_thresh`, `track_low_thresh`, `new_track_thresh`, `track_buffer`, `match_thresh` | No ReID-specific dependency |
| `ocsort.yaml` | Observation-centric association without ReID | `delta_t`, `inertia`, `use_byte`, common thresholds | No ReID-specific dependency |
| `deepocsort.yaml` | OC-SORT plus optional appearance features | `with_reid`, `model`, `gmc_method`, `alpha_fixed_emb`, thresholds | ReID model/features and more compute if enabled |
| `fasttrack.yaml` | Lightweight occlusion-aware ByteTrack-style tracking | `reset_velocity_offset_occ`, `enlarge_bbox_occ`, `occ_reappear_window`, `init_iou_suppress` | No ReID-specific dependency |
| `tracktrack.yaml` | Multi-cue association, long occlusion, Track-Aware Initialization | `iou_weight`, `reid_weight`, `conf_weight`, `lost_match_thr`, `with_reid`, `gmc_method` | Optional ReID; more tuning-sensitive |

Run the bundled helper for a recommendation:

```bash
python sub-skills/tracking-and-solutions/scripts/choose_tracker.py --goal occlusion --moving-camera
python sub-skills/tracking-and-solutions/scripts/choose_tracker.py --goal reid --prefer-stable-ids --needs-exported-reid
```

## Custom Tracker YAML Rules

1. Copy a built-in YAML and edit the copy.
2. Keep `tracker_type` unchanged; changing it to an unsupported value raises an assertion.
3. Tune thresholds gradually and record the source video conditions used for the decision.
4. Use higher `track_buffer` for temporary occlusions, but expect more stale tracks and possible ID switches.
5. Lower `track_high_thresh` or `conf` only when missed detections are the main issue; lowering both can increase false tracks.
6. Use `with_reid=True` only for `botsort`, `deepocsort`, or `tracktrack`, and only when the environment/model/backend can support the extra appearance model work.

## Track Outputs

Tracking updates `Results` boxes or OBB entries with track-aware data. For detection boxes:

```python
result = model.track("video.mp4", tracker="botsort.yaml", show=False)[0]
boxes = result.boxes
if boxes is not None and boxes.is_track:
    ids = boxes.id.int().cpu().tolist()
    xyxy = boxes.xyxy.cpu().tolist()
```

For oriented bounding boxes, use `result.obb` instead of `result.boxes`. Route detailed result object parsing to `../inference-and-results/SKILL.md`.

## Safety Defaults

- Prefer local videos/images over implicit downloads or network URLs when writing examples.
- Set `show=False` in headless agents and CI.
- Avoid `save_frames=True` unless the user explicitly wants per-frame media output.
- Do not start training, export, benchmarks, webcam loops, or GUI apps unless the user asked for those side effects.
