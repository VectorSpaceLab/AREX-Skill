# Tracking and Solutions Workflows

## Choose Between Tracking and Solutions

Use direct tracking when the user needs IDs, trajectories, or per-frame `Results` objects. Use Solutions when the user wants a packaged video analytics behavior such as counts, heatmaps, queues, speed labels, region counts, similarity search, or Streamlit UI.

## Direct Tracking Workflow

1. Choose model weights that match the task: detection for standard boxes, OBB for oriented tracking, segmentation/pose only when their outputs are needed.
2. Choose a local source: video path, webcam index, image sequence, stream URL, or numpy frame loop.
3. Select a tracker YAML. Start with `botsort.yaml` for general tracking or `bytetrack.yaml` for a fast baseline.
4. Run with explicit inference options: `conf`, `iou`, `classes`, `imgsz`, `device`, `max_det`, `half`, `show=False`.
5. Inspect `result.boxes.is_track` or `result.obb.is_track` before reading IDs.

```bash
yolo track model=yolo26n.pt source="video.mp4" tracker=botsort.yaml conf=0.25 iou=0.7 classes=0 show=False
```

```python
from ultralytics import YOLO

model = YOLO("yolo26n.pt")
for result in model.track("video.mp4", stream=True, tracker="botsort.yaml", classes=[0], show=False):
    boxes = result.obb if result.obb is not None else result.boxes
    ids = [] if boxes is None or not boxes.is_track else boxes.id.int().cpu().tolist()
```

## Solutions CLI Map

The verified `yolo solutions` commands include these names. The CLI writes processed videos under a `runs/solutions/exp*` output directory for video-processing solutions.

| CLI solution | Python class | Use for |
| --- | --- | --- |
| `count` | `solutions.ObjectCounter` | In/out counts across a line or polygon region |
| `heatmap` | `solutions.Heatmap` | Accumulated movement intensity; can also count inside a region |
| `speed` | `solutions.SpeedEstimator` | Approximate object speed from track displacement, FPS, and scale |
| `queue` | `solutions.QueueManager` | Count tracked objects currently inside a polygon queue region |
| `region` | `solutions.RegionCounter` | Counts inside one or more named polygon regions |
| `trackzone` | `solutions.TrackZone` | Track only objects inside a polygonal zone mask |
| `inference` | `solutions.Inference` | Streamlit live inference UI with optional tracking for video/webcam |
| `analytics` | `solutions.Analytics` | Track-based charts; route non-tracking chart-only needs carefully |
| `crop`, `blur`, `isegment`, `visioneye`, `security`, `parking`, `workout` | Other solution classes | Related solutions; some need task-specific models, files, or credentials |

Use `yolo solutions help` to show the solution command overview.

## Shared Solutions Arguments

Most Solutions classes inherit shared configuration. Frequently useful keys are:

- `source`: input video/stream path for CLI solutions.
- `model`: model path or known Ultralytics asset name; defaults to `yolo26n.pt` when omitted.
- `region`: line or polygon coordinates for spatial solutions.
- `classes`: class indices to keep, e.g. `classes=0,2` in CLI or `classes=[0, 2]` in Python.
- `tracker`: tracker YAML, default `botsort.yaml`.
- `conf`, `iou`, `imgsz`, `device`, `max_det`, `half`: forwarded to tracking/inference.
- `show`, `show_conf`, `show_labels`, `line_width`, `verbose`: display/log controls.

Every `BaseSolution` uses `model.track(source=frame, persist=True, classes=..., verbose=False, tracker=..., conf=..., iou=..., device=..., max_det=..., half=..., imgsz=...)` internally.

## Object Counting

Line counting distinguishes direction by horizontal/vertical crossing. Polygon counting uses the tracked centroid entering the region.

```bash
yolo solutions count source="video.mp4" model=yolo26n.pt region="[(10,200),(540,200)]" tracker=bytetrack.yaml show=False
```

```python
from ultralytics import solutions

counter = solutions.ObjectCounter(
    model="yolo26n.pt",
    region=[(10, 200), (540, 200)],
    tracker="bytetrack.yaml",
    show=False,
)
result = counter(frame)
print(result.in_count, result.out_count, result.classwise_count)
```

Use two points for a line and three or more points for a polygon. For multiple named zones, use `RegionCounter` instead.

## Region Counting

`RegionCounter` accepts one polygon or a dictionary of named polygons and returns `region_counts`.

```python
from ultralytics import solutions

regions = {
    "Door": [(20, 400), (1080, 400), (1080, 360), (20, 360)],
    "Queue": [(100, 100), (400, 100), (400, 300), (100, 300)],
}
region_counter = solutions.RegionCounter(model="yolo26n.pt", region=regions, tracker="botsort.yaml", show=False)
result = region_counter(frame)
print(result.region_counts)
```

The CLI can pass one polygon directly:

```bash
yolo solutions region source="video.mp4" model=yolo26n.pt region="[(20,400),(1080,400),(1080,360),(20,360)]" show=False
```

## Heatmaps

`Heatmap` builds an accumulated heatmap from tracked object boxes. Add `region` when the user also needs in/out counts.

```bash
yolo solutions heatmap source="video.mp4" model=yolo26n.pt colormap=cv2.COLORMAP_INFERNO tracker=botsort.yaml show=False
```

```python
import cv2
from ultralytics import solutions

heatmap = solutions.Heatmap(model="yolo26n.pt", colormap=cv2.COLORMAP_PARULA, region=None, show=False)
result = heatmap(frame)
processed = result.plot_im
```

## Speed Estimation

Speed is an estimate from pixel displacement, `fps`, and `meter_per_pixel`. It is not a calibrated measurement unless the scene scale and camera geometry are known.

```bash
yolo solutions speed source="video.mp4" model=yolo26n.pt meter_per_pixel=0.05 fps=30 tracker=botsort.yaml show=False
```

```python
from ultralytics import solutions

speed = solutions.SpeedEstimator(model="yolo26n.pt", meter_per_pixel=0.04, fps=30, max_speed=120, show=False)
result = speed(frame)
```

## Queue and Track Zone

Use `QueueManager` when the user needs a per-frame count of tracked objects inside a polygon. Use `TrackZone` when detections outside the polygon should be masked before tracking.

```bash
yolo solutions queue source="video.mp4" model=yolo26n.pt region="[(20,400),(1080,400),(1080,360),(20,360)]" show=False
```

```bash
yolo solutions trackzone source="video.mp4" model=yolo26n.pt region="[(150,150),(1130,150),(1130,570),(150,570)]" show=False
```

## Similarity Search

Similarity search is owned here because it is exposed through `ultralytics.solutions`. Use it when the user asks for image retrieval by text query, not object tracking.

```python
from ultralytics.solutions.similarity_search import VisualAISearch

searcher = VisualAISearch(data="images", device="cpu")
print(searcher.search("red car", k=5, similarity_thresh=0.2))
```

Important side effects and requirements:

- Requires `torch>=2.4` and `faiss-cpu`.
- Builds or loads `faiss.index` and `paths.npy` in the working directory.
- If `data` does not exist, it may attempt to download sample images.
- `SearchApp` additionally requires `flask>=3.0.1` and starts a web server.

## Streamlit Live Inference

Use this only when the user wants an interactive browser UI. It requires `streamlit>=1.29.0` and launches a server process.

```bash
yolo solutions inference model=yolo26n.pt
```

```python
from ultralytics import solutions

app = solutions.Inference(model="yolo26n.pt")
app.inference()
```

The app supports image/video/webcam inputs, class selection, confidence/IoU sliders, and a video/webcam option to enable tracking.

## Media and Side-Effect Notes

- CLI solutions may use a default sample video when `source` is omitted; provide `source` to avoid network downloads.
- GUI windows require display support; keep `show=False` for agents, servers, and CI.
- Video writers create media output; ask before enabling large output, per-frame saves, webcam loops, or web apps.
- Example GUI/video scripts from the source repository are reference-only here because they require media files, display interaction, mouse callbacks, network assets, or long-running UI loops.
