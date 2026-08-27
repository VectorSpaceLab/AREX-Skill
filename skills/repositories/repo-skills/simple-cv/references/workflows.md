# SimpleCV Workflow Router

## Purpose

Use this reference to choose the right SimpleCV sub-skill for a user request and to avoid reopening original source examples. Runtime instructions should point to bundled references and scripts in this generated skill tree.

## Choose the workflow owner

| User intent | Load this owner | Why |
|---|---|---|
| Install SimpleCV, fix `import SimpleCV`, check `cv`/`cv2.cv`, start the `simplecv` shell | Root `SKILL.md` + `install-and-runtime.md` | Setup and compatibility are shared across all workflows. |
| Load a sample image, crop/resize/rotate/warp/save/draw/filter, compute histograms/DFT/line scans | `sub-skills/image-processing-basics/` | Static image transformations are core Image/ImageSet work. |
| Use webcams, virtual cameras, display windows, streams, shell, calibration, headless/SDL behavior | `sub-skills/acquisition-display-shell/` | These are interactive or hardware-sensitive. |
| Find blobs, lines, corners, templates, Haar objects, keypoints, barcode/OCR features | `sub-skills/feature-detection/` | These return `FeatureSet`/feature objects and need detector-specific thresholds. |
| Segment frames, build masks, track objects over time, reason about motion | `sub-skills/segmentation-tracking/` | These maintain state across frames or depend on masks/tracker objects. |
| Train/test KNN, NaiveBayes, Tree, or SVM wrappers with feature extractors | `sub-skills/machine-learning-legacy/` | These use SimpleCV's legacy classifier API and optional Orange. |

## Common route patterns

### Static image plus detector

If the request says “load a sample image, detect a blob, annotate it, and save the result,” start at `feature-detection` for the detector and cross-link to `image-processing-basics` for the save/transform steps.

### Camera plus detector or tracker

If the request says “track an object from a webcam” or “detect faces from camera frames,” start at `acquisition-display-shell` to decide whether a physical camera/display is safe, then use `feature-detection` or `segmentation-tracking` for the algorithm.

### Image features plus classifier

If the request says “classify images using blob area/height/width,” start at `machine-learning-legacy` and link to `feature-detection` for feature extraction and to `image-processing-basics` for dataset/image loading.

### Install issue before workflow

If import fails, do not continue to sub-skill steps until the root `scripts/check_env.py` check succeeds or the user accepts a documented partial/optional limitation.

## Bundled script map

| Task | Bundled helper |
|---|---|
| Import and optional module diagnostics | `scripts/check_env.py` |
| Headless display check | `scripts/check_display_headless.py` |
| Finite image-transform sample | `sub-skills/image-processing-basics/scripts/image_recipe.py` |
| Blob/template/corner/line recipe | `sub-skills/feature-detection/scripts/feature_recipe.py` |
| Static segmentation recipe | `sub-skills/segmentation-tracking/scripts/segmentation_recipe.py` |
| Tiny classifier recipe | `sub-skills/machine-learning-legacy/scripts/ml_recipe.py` |
| Camera/display/shell environment probe | `sub-skills/acquisition-display-shell/scripts/env_probe.py` |

Each helper accepts `--help`. If the target package is not installed but a checkout is available, most helpers accept `--repo-root` to add that checkout to `sys.path` explicitly.

## Verification-friendly examples

Use these finite patterns rather than original interactive examples:

```bash
python scripts/check_env.py
python sub-skills/image-processing-basics/scripts/image_recipe.py --recipe rotate --output-dir /tmp/simplecv-image
python sub-skills/feature-detection/scripts/feature_recipe.py --recipe blobs --output-dir /tmp/simplecv-features
python sub-skills/segmentation-tracking/scripts/segmentation_recipe.py --output-dir /tmp/simplecv-segmentation
python sub-skills/machine-learning-legacy/scripts/ml_recipe.py
```

In headless sessions, prefix display-sensitive commands with:

```bash
SDL_VIDEODRIVER=dummy
```

## Avoid these routes

- Do not send OpenCV-only or scikit-image-only requests here unless the user explicitly asks for SimpleCV.
- Do not run original `SimpleCV/examples/*` camera, web, Kinect, or display loops as automated checks.
- Do not claim optional hardware or OCR/barcode/Orange integrations are verified unless the target environment specifically proves them.
