# Dataset and Augmentation API Reference

## When to read

Read this when mapping user data to RVM training classes or explaining what a
training sample contains.

## Matting datasets

### `VideoMatteDataset`

Constructor responsibilities:

- Reads `videomatte_dir/fgr/<clip>/<frame>` and matching
  `videomatte_dir/pha/<clip>/<frame>`.
- Randomly chooses either an image background or video background.
- Builds clip/frame indices in steps of `seq_length`.
- Uses a frame sampler to select temporal offsets.
- Returns transformed `(fgrs, phas, bgrs)`.

With training transforms, returned tensors are shaped like:

```text
fgrs: [T, 3, H, W]
phas: [T, 1, H, W]
bgrs: [T, 3, H, W]
```

### `ImageMatteDataset`

Reads still `fgr`/`pha` files with matching filenames, repeats the chosen image
for `seq_length`, and composites it with either image or video backgrounds after
augmentation. It is used in the official stage 4 recipe.

## Segmentation datasets

### `CocoPanopticDataset`

Loads COCO panoptic annotations JSON, filters annotations that contain person
category id `1`, and builds a binary mask from person, backpack, and tie
segments. It returns `(img, seg)` after transform.

### `SuperviselyPersonDataset`

Reads sorted image files and sorted segmentation files from separate directories
and asserts their counts match. Each sample returns an RGB image and grayscale
segmentation mask after transform.

### `YouTubeVISDataset`

Reads frame paths and RLE segmentations from a YouTubeVIS instances JSON. It
keeps person category id `26`, decodes masks, samples temporal sequences, and
returns `(imgs, segs)` after transform.

## Augmentation classes

`MotionAugmentation` is the base for VideoMatte and ImageMatte matting
augmentation. It can apply foreground/background motion affine transforms,
static affine, random resized crop, horizontal flips, noise, temporal color
jitter, grayscale, sharpness, blur, and pause effects before returning stacked
tensors.

`VideoMatteTrainAugmentation` uses moderate foreground/background affine,
color/noise/blur, horizontal flip, and pause probabilities. The valid variant
sets these probabilities to zero.

`ImageMatteAugmentation` uses a high foreground affine probability to create
motion from still mattes.

`CocoPanopticTrainAugmentation` and `YouTubeVISAugmentation` apply segmentation
appropriate affine/crop/color/flip transforms and return image/mask tensors.

## Frame samplers

`TrainFrameSampler` can speed up, shift, and reverse temporal frame indices.
Its default speed choices are `[0.5, 1, 2, 3, 4, 5]`.

`ValidFrameSampler` returns `range(seq_length)` for deterministic validation
sampling.

## Shape implications for training

The dataloaders add a batch dimension, so matting batches used by `train.py`
are shaped approximately:

```text
true_fgr: [B, T, 3, H, W]
true_pha: [B, T, 1, H, W]
true_bgr: [B, T, 3, H, W]
```

The training loop constructs source frames as:

```python
true_src = true_fgr * true_pha + true_bgr * (1 - true_pha)
```

Then it calls the model for matting and segmentation passes. This is distinct
from inference, where the user provides source RGB frames directly.

## Dataset API caveats

- The datasets list directories during initialization. Missing roots fail before
  training starts.
- File ordering is lexicographic; use zero-padded frame names.
- Large images may be downsampled when their minimum side exceeds the configured
  size.
- Background video roots are expected to contain frame directories, not only
  compressed video files, for training.
- Segmentation datasets are always part of the training loop even when the main
  matting dataset is `videomatte` or `imagematte`.
