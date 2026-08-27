# Tracking inference workflows

This reference gives self-contained operating recipes for PySOT inference. The paths in command examples are placeholders relative to the user's PySOT checkout or working directory; replace them with the user's actual config, snapshot, media, and dataset locations.

## Required inputs

| Input | Required for | Notes |
| --- | --- | --- |
| Config YAML | demo, test, API | Must merge into PySOT `cfg`; `TRACK.TYPE` must be one of `SiamRPNTracker`, `SiamMaskTracker`, `SiamRPNLTTracker`. |
| Snapshot (`.pth`) | demo, test, API | Use a snapshot trained for the same config/model family. State-dict mismatch is usually a config/snapshot family problem. |
| Video file | optional demo | Source demo recognizes `.avi` and `.mp4` by suffix. |
| Image directory | optional demo | Source demo treats non-video `--video_name` as a directory and reads `*.jp*` files sorted by numeric filename stem. |
| Webcam/display | default demo | If no media is supplied, the demo opens webcam 0 and uses OpenCV `selectROI` on the first frame. |
| Benchmark dataset | test | Full `test.py` expects datasets below `testing_dataset/<DATASET>` in the checkout. Dataset/result evaluation details belong to `evaluation-toolkit`. |

## Safe preflight

Use the bundled validator before running GUI or CUDA workflows:

```bash
python scripts/validate_tracking_inputs.py \
  --mode demo \
  --config path/to/config.yaml \
  --snapshot path/to/model.pth \
  --video-name path/to/video.mp4
```

For benchmark command construction:

```bash
python scripts/validate_tracking_inputs.py \
  --mode test \
  --config path/to/config.yaml \
  --snapshot path/to/model.pth \
  --dataset VOT2018 \
  --repo-root path/to/pysot-checkout
```

The validator only checks paths/config basics and prints a command skeleton. It never opens a window, captures a webcam, downloads a dataset, imports PyTorch, or loads model weights.

## Demo workflow

The native demo loads config, builds `ModelBuilder`, loads the snapshot with CPU map-location, moves the model to CUDA only when CUDA is available and `cfg.CUDA` is true, builds the tracker, asks for an initial ROI on the first frame, then draws `bbox` or `polygon`/`mask` on later frames.

### Webcam demo

```bash
PYTHONPATH=path/to/pysot-checkout:$PYTHONPATH \
python path/to/pysot-checkout/tools/demo.py \
  --config path/to/config.yaml \
  --snapshot path/to/model.pth
```

Expected side effects:

- Opens webcam 0.
- Opens an OpenCV window named `webcam`.
- Prompts the operator to draw the initial ROI with `cv2.selectROI`.
- Does not write benchmark result files.

### Video-file demo

```bash
PYTHONPATH=path/to/pysot-checkout:$PYTHONPATH \
python path/to/pysot-checkout/tools/demo.py \
  --config path/to/config.yaml \
  --snapshot path/to/model.pth \
  --video_name path/to/video.mp4
```

Use `.avi` or `.mp4` for the unmodified native demo. If OpenCV cannot decode the file, convert it to a common codec/container or supply an image sequence.

### Image-folder demo

```bash
PYTHONPATH=path/to/pysot-checkout:$PYTHONPATH \
python path/to/pysot-checkout/tools/demo.py \
  --config path/to/config.yaml \
  --snapshot path/to/model.pth \
  --video_name path/to/frames_dir
```

The frame directory must contain files matching `*.jp*` (`.jpg`, `.jpeg`, etc.) with numeric filename stems such as `0001.jpg`, because the native demo sorts with `int(stem)`.

## Benchmark test workflow

Use this only after the user supplies a matching snapshot and downloaded dataset. The source benchmark path calls:

```python
model = load_pretrain(model, snapshot).cuda().eval()
```

so a full unmodified benchmark run requires a working CUDA PyTorch environment. It is not a safe default CPU check.

### Command pattern

Run from the directory where the user wants the `results/` tree to be created. If running from an experiment directory, the source README pattern uses a relative path back to `tools/test.py`; if running from the checkout root, use `tools/test.py` directly.

```bash
PYTHONPATH=path/to/pysot-checkout:$PYTHONPATH \
python -u path/to/pysot-checkout/tools/test.py \
  --dataset VOT2018 \
  --config path/to/config.yaml \
  --snapshot path/to/model.pth
```

Optional flags:

- `--video VIDEO_NAME`: evaluate only one video whose dataset video name exactly matches `VIDEO_NAME`.
- `--vis`: open OpenCV windows while tracking; this adds GUI/display requirements.

### Dataset assumptions

`test.py` builds `dataset_root` as `testing_dataset/<DATASET>` under the PySOT checkout. Dataset adapters and JSON sidecars are owned by the evaluation toolkit; do not invent layouts here.

### Result output locations

`model_name` is the snapshot filename without its extension, and all paths are relative to the process working directory.

| Dataset family | Output path pattern | Contents |
| --- | --- | --- |
| `VOT2016`, `VOT2018`, `VOT2019` restart mode | `results/<DATASET>/<model_name>/baseline/<video>/<video>_001.txt` | Lines are `1` for initialization, `2` for lost, `0` for skipped frames, or predicted boxes/polygons. |
| `VOT2018-LT` long-term | `results/VOT2018-LT/<model_name>/longterm/<video>/<video>_001.txt` plus `<video>_001_confidence.value` and `<video>_time.txt` | Predicted boxes, per-frame confidence, and per-frame time. |
| `GOT-10k` | `results/GOT-10k/<model_name>/<video>/<video>_001.txt` plus `<video>_time.txt` | Predicted boxes and times. |
| Other OPE datasets such as OTB/UAV/NFS/LaSOT-style adapters | `results/<DATASET>/<model_name>/<video>.txt` | One predicted `[x,y,w,h]` line per frame after initialization conventions. |

Route metric computation, tracker-prefix selection, and `eval.py` use to `evaluation-toolkit` after results are written.

## Programmatic tracker API workflow

Use the API when the user wants to integrate PySOT into another script and already has frames and an initial bounding box.

```python
import cv2
import torch
from pysot.core.config import cfg
from pysot.models.model_builder import ModelBuilder
from pysot.tracker.tracker_builder import build_tracker

cfg.merge_from_file("path/to/config.yaml")
cfg.CUDA = torch.cuda.is_available() and cfg.CUDA
device = torch.device("cuda" if cfg.CUDA else "cpu")

model = ModelBuilder()
state = torch.load("path/to/model.pth", map_location=lambda storage, loc: storage.cpu())
if isinstance(state, dict) and "state_dict" in state:
    state = state["state_dict"]
state = {k.split("module.", 1)[-1] if k.startswith("module.") else k: v for k, v in state.items()}
model.load_state_dict(state, strict=False)
model.eval().to(device)

tracker = build_tracker(model)
first = cv2.imread("first_frame.jpg")  # BGR ndarray
tracker.init(first, [x, y, width, height])  # 0-based pixel box

next_frame = cv2.imread("next_frame.jpg")
outputs = tracker.track(next_frame)
print(outputs["bbox"], outputs.get("best_score"), outputs.get("polygon"))
```

Use the source `load_pretrain` helper only when CUDA is available, because it maps checkpoint tensors through the current CUDA device. For CPU-only demos, prefer the direct `torch.load(..., map_location=cpu)` pattern above.
