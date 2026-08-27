---
name: tracking-and-trackers
description: "Use BoxMOT for live tracking, tracker construction, tracker
  selection, and AABB/OBB output schema debugging."
metadata:
  disco-role: operating
disable-model-invocation: true
license: AGPL 3.0
---

# Tracking and Trackers

Use this sub-skill when the task is about `boxmot track`, direct tracker instantiation, tracker registry lookup, output schemas, or explaining how AABB and OBB detections flow through the tracker API.

## Covers

- `boxmot track` and `BoxMOT.track(...)`
- `boxmot.trackers.registry.create_tracker(...)`
- direct tracker imports such as `boxmot.trackers.OccluBoost`
- tracker selection by name or class
- AABB and OBB detection layouts
- track result accessors such as `xyxy`, `xywha`, `id`, `conf`, `cls`, and `det_ind`
- per-class tracking and tracker output debugging

## Does not cover

- benchmark cache generation or replay (`generate`, `eval`, `tune`, `research`)
- ReID training, evaluation, comparison, or export
- native C++ build steps and `boxmot build`

Use the sibling sub-skills for those routes.

## Read first

- [API reference](references/api-reference.md)
- [Tracking workflows](references/workflows.md)
- [Detection and output formats](references/data-formats.md)
- [Troubleshooting](references/troubleshooting.md)
- [Smoke test script](scripts/tracker_contract_smoke.py)

## Good prompts for this route

- "Track this video with ByteTrack and save the output."
- "Why does my tracker expect 7 columns instead of 6?"
- "How do I instantiate OccluBoost directly in Python?"
- "Why did my OBB track output lose the angle column?"
- "Which tracker objects support OBB input?"

## Typical workflow

1. Identify the detector/tracker inputs and whether the user is working with AABB or OBB tensors.
2. Decide whether the user wants the CLI, the high-level `BoxMOT` facade, or a direct tracker class.
3. Use the tracker registry or the direct package export to construct the tracker.
4. Check the input tensor shape before asking the user to run a long command.
5. Confirm the returned `TrackResults` schema and the `det_ind` mapping when debugging downstream consumers.

## Entry points

### CLI tracking

```bash
boxmot track --detector yolov8n --reid osnet_x0_25_msmt17 --tracker botsort --source video.mp4 --save
```

### Python facade

```python
from boxmot import BoxMOT

model = BoxMOT(detector="yolov8n", reid="osnet_x0_25_msmt17", tracker="botsort")
run = model.track(source="video.mp4", save=True)
```

### Direct tracker class

```python
from boxmot.trackers import OccluBoost

tracker = OccluBoost(reid_model=None, with_reid=False)
tracks = tracker.update(dets, image=frame)
```

## What to hand off to nearby references

- Column and shape details belong in `references/data-formats.md`.
- API signatures and registry details belong in `references/api-reference.md`.
- Concrete workflow examples belong in `references/workflows.md`.
- Shape errors, OBB support checks, and tracker misuse belong in `references/troubleshooting.md`.

When a user asks for a smoke test or contract check, use `scripts/tracker_contract_smoke.py` instead of hand-writing a one-off snippet.
