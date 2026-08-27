# Repo Maintenance Reference

## Core policy

Follow repository policy: less is more, Delete > Replace > Add, solve behavior in the owning code path, search and reuse first, and avoid speculative shims. Do not edit the primary checkout in normal PR work; create a git worktree and branch. The default branch is `master`.

## Style and compatibility

- Python support: `>=3.8`.
- PyTorch floor: `>=1.8.0`.
- Line length: 120; Ruff and docformatter are configured in `pyproject.toml`.
- Larger classes/functions should use Google-style docstrings.
- Keep dependency floors aligned between `requirements.txt` and `pyproject.toml`.
- Do not remove local helpers marked as intentionally different from upstream Ultralytics helpers.

## CI smoke surface

Repository CI covers practical scripts rather than a traditional pytest suite. Representative commands include:

```bash
python train.py --imgsz 64 --batch-size 32 --weights yolov3-tiny.pt --cfg yolov3-tiny.yaml --epochs 1 --device cpu --name smoke --exist-ok
python val.py --imgsz 64 --batch-size 32 --weights runs/train/smoke/weights/best.pt --device cpu
python detect.py --imgsz 64 --weights yolov3-tiny.pt --device cpu
python export.py --weights yolov3-tiny.pt --img 64 --include torchscript
python models/yolo.py --cfg yolov3-tiny.yaml
python hubconf.py --model yolov3-tiny
```

These may download official weights and coco128 assets. Use root `scripts/yolov3_repo_smoke_plan.py` to print a safety-classified plan before running them.

## Docs and provenance

- The repo is YOLOv3 detection-only. Keep README and docs evergreen and YOLOv3-focused.
- Historical upstream YOLOv5 issue/discussion links can be intentional provenance; do not rewrite them blindly to YOLOv3.
- TensorFlow rows in `export.py:export_formats()` are load-bearing for suffix detection and benchmarks even though TensorFlow export has been removed.
