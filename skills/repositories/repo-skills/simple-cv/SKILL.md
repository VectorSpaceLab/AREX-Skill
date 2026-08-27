---
name: simple-cv
description: "Routes SimpleCV users to legacy install, image processing,
  acquisition/display, feature detection, segmentation/tracking, and
  machine-learning workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# SimpleCV

Use this skill for the legacy `SimpleCV` computer-vision package when a future agent needs to install it, inspect its API, or route a user question to the right workflow.

## Start here

Read `references/repo-provenance.md` when you need to check whether this skill still matches the current checkout or before refreshing it.
Read `references/install-and-runtime.md` when the user needs install, import, or shell-start guidance.
Read `references/workflows.md` when the request is broad and you need to choose a sub-skill.
Read `references/troubleshooting.md` when the user is blocked by OpenCV, pygame, Python 2, or sample-image issues.
Read `references/api-reference.md` when you need verified constructor and method signatures.

## Quick install and import check

SimpleCV is a legacy Python 2 package. The verified runtime profile for this repo is:

- Python 2.7
- `SimpleCV` 1.3 / `SimpleCV.__version__ == '1.3.0'`
- OpenCV 2.4-era bindings that expose both `cv2` and `cv` / `cv2.cv`
- `numpy`, `scipy`, `Pillow`, `pygame`, `svgwrite`, `IPython`, `nose`

Minimal smoke check:

```bash
python -c "import SimpleCV; print(SimpleCV.__version__)"
```

If the shell needs to run headless, use `SDL_VIDEODRIVER=dummy` before the `simplecv` command or before a script that touches `Display`.

## Route map

### `image-processing-basics`
Use this for image loading and saving, sample images, transforms, masks, drawing, scanlines, DFT, color utilities, and simple image analysis.

Typical requests:
- open, crop, resize, rotate, warp, or save an image
- compare two images or annotate a sample image
- compute a histogram, DFT, or line scan
- use `ImageSet`, `Color`, or `ColorModel`

Read `sub-skills/image-processing-basics/SKILL.md` and `sub-skills/image-processing-basics/references/workflows.md`.

### `acquisition-display-shell`
Use this for cameras, virtual cameras, the interactive shell, display windows, stream helpers, and calibration or headless runtime issues.

Typical requests:
- start or explain the `simplecv` shell
- work with `Camera`, `VirtualCamera`, `Display`, or `Stream`
- understand calibration or live display behavior
- diagnose SDL/headless or webcam failures

Read `sub-skills/acquisition-display-shell/SKILL.md` and `sub-skills/acquisition-display-shell/references/workflows.md`.

### `feature-detection`
Use this for corners, blobs, lines, templates, Haar features, keypoints, barcodes, OCR hooks, and feature objects.

Typical requests:
- find blobs or lines in a sample image
- compare template-matching methods
- inspect feature geometry or return values
- understand keypoint or Haar usage

Read `sub-skills/feature-detection/SKILL.md` and `sub-skills/feature-detection/references/workflows.md`.

### `segmentation-tracking`
Use this for segmentation models, motion, and tracker objects.

Typical requests:
- build a color, diff, running, or MOG segmentation mask
- explain `TrackSet`, `CAMShift`, `LK`, `SURF`, or `MF`
- reason about mask stability, motion tracking, or frame-to-frame inputs

Read `sub-skills/segmentation-tracking/SKILL.md` and `sub-skills/segmentation-tracking/references/workflows.md`.

### `machine-learning-legacy`
Use this for the legacy classifier wrappers and feature-extractor workflows.

Typical requests:
- train or test a `KNNClassifier`, `NaiveBayesClassifier`, `TreeClassifier`, or `SVMClassifier`
- understand feature-extractor inputs and save/load behavior
- diagnose Orange-dependent or synthetic-data classifier issues

Read `sub-skills/machine-learning-legacy/SKILL.md` and `sub-skills/machine-learning-legacy/references/workflows.md`.

## Common constraints

- Do not assume modern Python 3 wheels or OpenCV 3/4 bindings are enough; the package source expects older APIs.
- Do not tell the user to run original repo examples from this checkout. Use the bundled scripts in this skill tree instead.
- Do not rely on hardware-only examples unless the user explicitly wants camera or device guidance.
- Do not treat a successful import alone as proof that camera, display, or optional integrations work.

## Bundled helpers

- `scripts/check_env.py` — run this for import, version, and optional module diagnostics.
- `scripts/check_display_headless.py` — run this to verify the display path in a dummy SDL session.
- `sub-skills/*/scripts/*.py` — run the workflow-specific helper that matches the user request.

## Refresh signal

If the repository commit, branch, package version, or evidence paths no longer match `references/repo-provenance.md`, refresh this skill before reusing it.
