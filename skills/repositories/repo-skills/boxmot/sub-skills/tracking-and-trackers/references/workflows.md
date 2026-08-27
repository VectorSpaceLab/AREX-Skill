# Tracking Workflows

## Direct tracking from the CLI

Use `track` when the user already has a video, webcam, image folder, or stream and wants annotated output immediately.

```bash
boxmot track \
  --detector yolov8n \
  --reid osnet_x0_25_msmt17 \
  --tracker botsort \
  --source video.mp4 \
  --save
```

Common source values:

- `0` for webcam
- `video.mp4` for a local video
- `path/to/images` for an image directory
- `path/*.jpg` for a glob
- `rtsp://...` or `http://...` for a stream

## Python facade path

```python
from boxmot import BoxMOT

model = BoxMOT(detector="yolov8n", reid="osnet_x0_25_msmt17", tracker="botsort")
run = model.track(source="video.mp4", save=True)
print(run)
```

## Direct tracker path

Use a direct tracker class when the user wants to feed precomputed detections or embeddings.

```python
from boxmot.trackers import OccluBoost

tracker = OccluBoost(reid_model=None, with_reid=False)
tracks = tracker.update(dets, image=frame)
```

## Typical decision points

- Use `BoxMOT.track(...)` for full detector + tracker pipelines.
- Use `create_tracker(...)` when the user knows the tracker name but wants default YAML loading.
- Use a direct class import when the user wants to tune constructor parameters explicitly.
- Use `tracker_backend='cpp'` only for supported native trackers.

## OBB and AABB behavior

BoxMOT infers the geometry from the detection tensor shape.

- 6 columns -> AABB path
- 7 columns -> OBB path

The same tracker instance should not switch shapes mid-run. If the shape changes, create a fresh tracker or reset the sequence-local state before continuing.

## Per-class tracking

If the user wants class-separated tracking, set `per_class=True` or use `BoxMOT(..., classes=[...])` for class filtering.

## Output handling

`TrackResults` supports array-style slicing and named accessors. When debugging downstream code, check these fields first:

- `tracks.xyxy` or `tracks.xywha`
- `tracks.id`
- `tracks.conf`
- `tracks.cls`
- `tracks.det_ind`

If the user wants MOT-style export, use `save_mot()` or the CLI `--save-txt` path.
