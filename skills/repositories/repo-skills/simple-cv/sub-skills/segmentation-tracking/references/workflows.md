# Segmentation and Tracking Workflows

## When to read this

Read this for foreground/background masks, frame differences, running background models, motion detection, and track sets.

## Segmentation model selection

| Model | Use | Inputs | Output |
|---|---|---|---|
| `ColorSegmentation()` | Segment colors learned from sample pixels or crops. | `addToModel(data)` then `addImage(img)`. | Binary/threshold image and blobs. |
| `DiffSegmentation(grayOnly=False, threshold=(10,10,10))` | Compare consecutive frames. | Two or more images via `addImage`. | Difference mask. |
| `RunningSegmentation(alpha=0.7, thresh=(20,20,20))` | Smooth background subtraction over time. | Sequence of frames. | Running foreground mask. |
| `MOGSegmentation(history=200, nMixtures=5, backgroundRatio=0.7, noiseSigma=15, learningRate=0.7)` | Mixture-of-Gaussians background model. | Sequence of frames. | Foreground mask. |

## Color segmentation recipe

```python
from SimpleCV import Image
from SimpleCV.Segmentation import ColorSegmentation
img = Image('greenscreen.png', sample=True)
seg = ColorSegmentation()
model_crop = img.crop(0, 0, min(40, img.width), min(40, img.height))
seg.addToModel(model_crop)
seg.addImage(img)
mask = seg.getSegmentedImage()
mask.save('color_mask.png')
```

Model quality depends on the crop or color samples. If a crop is not known to represent the foreground/background class, expose that uncertainty.

## Difference segmentation recipe

```python
from SimpleCV import Image
from SimpleCV.Segmentation import DiffSegmentation
seg = DiffSegmentation()
seg.addImage(Image('tracktest0.jpg', sample=True))
seg.addImage(Image('tracktest1.jpg', sample=True))
if seg.isReady():
    seg.getSegmentedImage().save('diff_mask.png')
```

Use this pattern instead of live camera examples when verifying behavior.

## Tracking route

`Image.track(method='CAMShift', ts=None, img=None, bb=None, **kwargs)` creates or updates tracking state. The task must define:

- frame sequence or previous/current images
- starting bounding box
- tracker method
- whether a display/camera loop is needed
- how to handle lost tracks or empty feature matches

`TrackSet` supports paths, bounding boxes, track length, pixel velocity, background extraction, and Kalman prediction/correction display helpers.

## Segmentation to blobs

Use `getSegmentedBlobs()` when the user needs objects rather than masks. Then route blob geometry questions to `../feature-detection/`.

```python
blobs = seg.getSegmentedBlobs()
if blobs:
    blobs.draw()
```

## Source example replacement map

| Source repo artifact | Runtime replacement |
|---|---|
| `examples/detection/ColorSegmentation.py` | ColorSegmentation recipe here and `scripts/segmentation_recipe.py --recipe color`; no mouse/camera loop. |
| `examples/detection/MOGSegmentation.py` | MOG model selection notes; verify only with finite frame sequences. |
| `examples/detection/MotionTracker.py` | Tracking route notes; live camera/display path is optional. |
| `examples/tracking/camshift.py`, `lk.py`, `mftrack.py`, `surftest.py` | Tracker concepts here; do not run interactive camera demos by default. |
| `tests/tests.py` segmentation cases | Final native verification candidates. |

## Validation checklist

- Are there enough frames for the selected model?
- Is `isReady()` true?
- Is `isError()` false?
- Does the mask contain foreground before extracting blobs?
- Is a physical camera/display truly required, or can a static frame sequence validate the workflow?
- Are tracker-specific OpenCV features available?
