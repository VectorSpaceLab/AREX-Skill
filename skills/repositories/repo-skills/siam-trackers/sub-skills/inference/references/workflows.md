# NanoTrack Inference Workflows

## 1. Preflight without weights

Run the bundled checker before importing NanoTrack:

```bash
python /path/to/inference/scripts/nanotrack_demo_check.py \
  --variant v1 --frame-shape 480 640 3 --bbox 20 30 80 60 --device cpu
```

This validates a synthetic frame declaration, box, variant profile, and device
policy without network, GUI, video, checkpoint deserialization, or NanoTrack
imports. Add `--json` for machine-readable output.

Generate a minimal inference YAML when no maintained config asset is available:

```bash
python /path/to/inference/scripts/nanotrack_demo_check.py \
  --variant v3 --write-config ./configs/nanotrack-v3-inference.yaml
```

The parent directory must already exist. The generated YAML includes only model,
point-grid, and tracker fields needed for inference. It deliberately excludes
historical dataset, training, resume, and path fields.

## 2. Build one matched runtime

Use one fresh process per variant. The following pattern patches the public head
registry in memory rather than editing package files:

```python
from pathlib import Path
import importlib
import torch

from nanotrack.core.config import cfg
import nanotrack.models.head as head_registry
from nanotrack.models.model_builder import ModelBuilder
from nanotrack.tracker.tracker_builder import build_tracker
from nanotrack.utils.model_load import load_pretrain


def build_runtime(*, variant, config_path, checkpoint_path, device_request="auto"):
    if variant not in {"v1", "v2", "v3"}:
        raise ValueError("variant must be v1, v2, or v3")

    config_path = Path(config_path).expanduser()
    checkpoint_path = Path(checkpoint_path).expanduser()
    if not config_path.is_file():
        raise FileNotFoundError(f"missing config: {config_path}")
    if not checkpoint_path.is_file():
        raise FileNotFoundError(f"missing checkpoint: {checkpoint_path}")

    # Do this before ModelBuilder() and NanoTracker().
    cfg.merge_from_file(str(config_path))
    head = importlib.import_module(f"nanotrack.models.head.ban_{variant}")
    head_registry.BANS["UPChannelBAN"] = head.UPChannelBAN
    head_registry.BANS["DepthwiseBAN"] = head.DepthwiseBAN

    if device_request == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA was required but torch.cuda.is_available() is false")
        device = torch.device("cuda")
    elif device_request == "cpu":
        device = torch.device("cpu")
    elif device_request == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        raise ValueError("device_request must be auto, cpu, or cuda")

    # Tracker crops and model parameters must use the same backend.
    cfg.CUDA = device.type == "cuda"
    model = ModelBuilder()  # no constructor arguments
    model = load_pretrain(model, str(checkpoint_path))
    model = model.to(device).eval()  # never unconditional .cuda()
    tracker = build_tracker(model)
    return tracker, device
```

Before returning the runtime, assert the expected effective profile if config
files are caller-controlled:

```python
EXPECTED = {
    "v1": ("mobilenetv3_small", 64, 16, 0.462, 0.148, 0.390),
    "v2": ("mobilenetv3_small", 64, 16, 0.490, 0.150, 0.385),
    "v3": ("mobilenetv3_small_v3", 96, 15, 0.455, 0.138, 0.348),
}
backbone, channels, output, window, penalty, lr = EXPECTED[variant]
assert cfg.BACKBONE.TYPE == backbone
assert cfg.ADJUST.KWARGS.in_channels == channels
assert cfg.BAN.KWARGS.in_channels == channels
assert cfg.POINT.STRIDE == 16
assert cfg.TRACK.OUTPUT_SIZE == output
assert abs(cfg.TRACK.WINDOW_INFLUENCE - window) < 1e-12
assert abs(cfg.TRACK.PENALTY_K - penalty) < 1e-12
assert abs(cfg.TRACK.LR - lr) < 1e-12
```

This catches a V3 head with a V2 config, a stale output size after a same-process
switch, and accidental use of core stride 8.

## 3. Validate frames and boxes

Keep adaptation explicit at the boundary:

```python
import math
import numpy as np


def require_bgr_u8(frame):
    frame = np.asarray(frame)
    if frame.ndim != 3 or frame.shape[2] != 3 or frame.size == 0:
        raise ValueError(f"expected nonempty HxWx3 frame, got {frame.shape}")
    if frame.dtype != np.uint8:
        raise TypeError(f"expected uint8 BGR frame, got {frame.dtype}")
    return np.ascontiguousarray(frame)


def require_init_box(box, frame):
    if len(box) != 4:
        raise ValueError("init box must be [x, y, width, height]")
    x, y, w, h = map(float, box)
    if not all(map(math.isfinite, (x, y, w, h))):
        raise ValueError("init box values must be finite")
    height, width = frame.shape[:2]
    if w <= 0 or h <= 0:
        raise ValueError("init box width and height must be positive")
    if x < 0 or y < 0 or x + w > width or y + h > height:
        raise ValueError("init box must be fully inside the first frame")
    return [x, y, w, h]
```

If an application deliberately permits a partial box, clip it to the frame and
reject zero-area intersection before initialization. Do not silently interpret
four values as corners.

For RGB input, use an explicit conversion such as
`cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)`. For BGRA or grayscale, use the matching
OpenCV conversion. Do not infer color order from array shape.

## 4. Run a headless image-sequence loop

The tracker consumes decoded arrays, not filenames. Keep decode and lifecycle
outside the model wrapper:

```python
import math
import torch


def run_sequence(tracker, frames, init_box):
    frames = iter(frames)
    try:
        first = require_bgr_u8(next(frames))
    except StopIteration as exc:
        raise ValueError("frame sequence is empty") from exc

    init_box = require_init_box(init_box, first)
    with torch.inference_mode():
        tracker.init(first, init_box)

    yield {"frame_index": 0, "bbox": init_box, "best_score": None}

    for index, raw_frame in enumerate(frames, start=1):
        frame = require_bgr_u8(raw_frame)
        with torch.inference_mode():
            result = tracker.track(frame)

        if not {"bbox", "best_score"} <= set(result):
            raise RuntimeError("tracker result lacks bbox or best_score")
        bbox = [float(v) for v in result["bbox"]]
        score = float(result["best_score"])
        if len(bbox) != 4 or not all(map(math.isfinite, bbox)):
            raise RuntimeError(f"invalid predicted bbox at frame {index}")
        if bbox[2] <= 0 or bbox[3] <= 0:
            raise RuntimeError(f"non-positive predicted size at frame {index}")
        if not math.isfinite(score) or not 0.0 <= score <= 1.0:
            raise RuntimeError(f"invalid best_score at frame {index}")
        yield {"frame_index": index, "bbox": bbox, "best_score": score}
```

The first emitted score is `None` because `init` is template setup, not a
prediction. Preserve floats in records. Apply visualization clipping and
rounding only when drawing.

## 5. Adapt image directories safely

A library workflow should accept an explicit ordered list or sort with a clear
rule. Avoid assuming every filename stem is an integer.

```python
from pathlib import Path
import cv2


def decoded_frames(paths):
    for path in paths:
        path = Path(path)
        frame = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError(f"failed to decode frame: {path}")
        yield frame

paths = sorted(input_directory.glob("*.jpg"), key=lambda p: p.name)
results = run_sequence(tracker, decoded_frames(paths), init_box)
```

Lexicographic sorting requires zero-padded names (`000001.jpg`). If names are
numeric but not padded, parse and validate stems before numeric sorting. Reject
duplicates and gaps when they violate the caller's temporal contract.

## 6. Adapt video decoding without GUI

Open an explicit path, check it, and release it in `finally`:

```python
import cv2


def video_frames(video_path):
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        cap.release()
        raise ValueError(f"cannot open video: {video_path}")
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            yield frame
    finally:
        cap.release()
```

Do not skip warm-up frames from a file unless the caller explicitly requests a
seek. The initialization box belongs to the actual first yielded frame. Do not
call `namedWindow`, `imshow`, `waitKey`, `selectROI`, open a webcam, or create a
writer in a default inference path. Put all such side effects behind explicit
application flags.

## 7. Reinitialize or process scene cuts

Call `init` again when the target identity or reference box changes. Reusing the
same tracker is sequentially valid because `init` overwrites target state and
model template state, but a fresh tracker is easier to audit when geometry
config also changes.

Do not seek backward and continue with old state. At a seek/scene cut:

1. decode the new reference frame;
2. obtain a new box on that exact frame;
3. validate frame and box;
4. call `tracker.init` again;
5. resume chronological `track` calls.

## 8. Multi-target policy

The model owns `zf`, so this is unsafe:

```python
tracker_a = build_tracker(shared_model)
tracker_b = build_tracker(shared_model)
tracker_a.init(frame, box_a)
tracker_b.init(frame, box_b)  # overwrites shared_model.zf used by tracker_a
```

Default to a separate model/tracker pair per concurrently active target. An
advanced shared-weight implementation must externalize each template feature,
restore the right one under a lock before each call, and test interleaving. That
is an adaptation beyond the maintained single-object API.

## 9. Asset and verification policy

No config path, checkpoint path, video path, or initialization box should be
hard-coded in reusable code. Resolve them from explicit arguments or caller
configuration. Never download a checkpoint as a side effect of inference.

For a newly supplied checkpoint, verification is staged:

1. checker validates profile, declared frame, box, device, and file existence;
2. construction verifies key overlap and reviews missing/unused keys;
3. a tiny real fixture performs one `init` plus one `track` on the requested
   backend;
4. output schema/finiteness and state progression are asserted;
5. benchmark or speed claims are routed to their owning workflows.

Without weights and decoded frames, stop after stage 1 and state the limitation.
