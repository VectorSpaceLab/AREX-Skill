---
name: segmentation-tracking
description: "Guides SimpleCV color, difference, running, MOG segmentation,
  motion, and tracking workflows across images or frames."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Segmentation and Tracking

Use this sub-skill when the task needs foreground/background masks, segmentation state, frame differencing, or object tracking across frames.

## Read first

Read `references/workflows.md` for segmentation model setup, track routing, and finite static-image recipes.
Read `references/troubleshooting.md` for empty masks, unstable models, tracker availability, and hardware/display traps.
Read the root `../../references/api-reference.md` for verified constructor and method signatures.
Run `scripts/segmentation_recipe.py --help` for a finite static-image segmentation helper.

## Use this for

- `ColorSegmentation`, `DiffSegmentation`, `RunningSegmentation`, and `MOGSegmentation`.
- `Image.findMotion(...)` and `Image.track(...)`.
- `Track`, `TrackSet`, `CAMShiftTrack`, `LKTrack`, `SURFTrack`, and `MFTrack` concepts.
- Turning segmented masks into blobs and trackable regions.
- Explaining live camera tracking workflows without accidentally running infinite loops.

## Route elsewhere

- Image preprocessing, masks as static transforms, or DFT/filter operations → `../image-processing-basics/SKILL.md`.
- One-shot object detection with blobs/templates/lines/keypoints → `../feature-detection/SKILL.md`.
- Camera/display setup required to acquire frames → `../acquisition-display-shell/SKILL.md`.
- Classifier training/testing → `../machine-learning-legacy/SKILL.md`.

## Core segmentation workflow

1. Start with two or more non-empty `Image` frames or a static image plus a color model.
2. Choose the state model:
   - `ColorSegmentation` for learned foreground/background colors.
   - `DiffSegmentation` for frame-to-frame differences.
   - `RunningSegmentation` for running-average background subtraction.
   - `MOGSegmentation` for mixture-of-Gaussians background modeling.
3. Call `addImage(...)` for each frame.
4. Check `isReady()` and `isError()` before reading results.
5. Use `getSegmentedImage(...)`, `getRawImage()`, or `getSegmentedBlobs()` depending on whether the user needs a mask, raw diff, or blob objects.

## Core tracking workflow

Use tracking only after the input source and bounding box are clear:

```python
track_set = img.track(method='CAMShift', ts=track_set, img=previous_img, bb=bounding_box)
```

The old source examples often require a live camera and display loop. For automation, convert them into finite frame sequences or use `VirtualCamera` from `../acquisition-display-shell/`.

## Important decisions

- Tracking asks usually need frame sequences; do not solve them with a single static detector unless the user asked for a one-shot detection.
- SURF/LK/MF trackers rely on old OpenCV feature or optical-flow APIs; verify the OpenCV build before promising a specific tracker.
- Segmentation thresholds are image- and lighting-dependent; output masks must be inspected before turning them into blob claims.
- If the request needs camera frames, decide hardware availability before using `Camera`.

## Bundled helper

```bash
python sub-skills/segmentation-tracking/scripts/segmentation_recipe.py --recipe diff --output-dir /tmp/simplecv-segmentation
python sub-skills/segmentation-tracking/scripts/segmentation_recipe.py --recipe color --output-dir /tmp/simplecv-segmentation
```

## Verification hooks

Good final candidates include `test_segmentation_diff`, `test_segmentation_running`, `test_segmentation_color`, movement-related native tests, and static image-pair segmentation checks. Live tracking demos remain optional/hardware-gated unless explicitly requested.
