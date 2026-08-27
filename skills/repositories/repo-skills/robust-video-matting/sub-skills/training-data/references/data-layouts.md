# Data Layouts and `DATA_PATHS`

## When to read

Read this before editing a training checkout's `DATA_PATHS` mapping or launching
`train.py`. RVM expects several independent matte, background, and segmentation
datasets.

## `DATA_PATHS` keys

The training source uses this mapping shape:

```python
DATA_PATHS = {
    "videomatte": {"train": "...", "valid": "..."},
    "imagematte": {"train": "...", "valid": "..."},
    "background_images": {"train": "...", "valid": "..."},
    "background_videos": {"train": "...", "valid": "..."},
    "coco_panoptic": {"imgdir": "...", "anndir": "...", "annfile": "..."},
    "spd": {"imgdir": "...", "segdir": "..."},
    "youtubevis": {"videodir": "...", "annfile": "..."},
}
```

Paths are ordinary filesystem paths used by the training process. Avoid relying
on relative paths unless the launch working directory is fixed and documented.

## VideoMatte240K layout

`VideoMatteDataset` expects foreground and alpha clips with matching clip names
and frame names:

```text
VideoMatte train-or-valid root/
  fgr/
    0001/
      00000.jpg
      00001.jpg
  pha/
    0001/
      00000.jpg
      00001.jpg
```

The training docs recommend JPEG SD for stages 1-2 and JPEG HD for stages 3-4,
with selected clips moved from training into validation.

## ImageMatte layout

`ImageMatteDataset` expects foreground and alpha files with matching filenames:

```text
ImageMatte train-or-valid root/
  fgr/
    sample1.jpg
    sample2.jpg
  pha/
    sample1.jpg
    sample2.jpg
```

The docs describe ImageMatte as a merge of Distinctions-646 and Adobe Image
Matting human samples. Some datasets require contacting authors; do not automate
credentialed acquisition.

## Background images

`background_images.train` and `.valid` are directories of image files:

```text
Backgrounds/train/
  sample1.png
  sample2.jpg
```

For ImageMatte or VideoMatte samples, a background image may be repeated across
the sequence.

## Background videos

`background_videos.train` and `.valid` are directories of clip subdirectories,
each containing sorted image frames:

```text
BackgroundVideos/train/
  clip_0001/
    0000.jpg
    0001.jpg
```

The training docs also describe DVM-derived background videos and public
preprocessed downloads. Treat those downloads as large external data.

## COCO panoptic

`CocoPanopticDataset` needs:

- `imgdir`: COCO image directory, for example train2017 JPEGs.
- `anndir`: panoptic annotation PNG directory.
- `annfile`: panoptic annotation JSON.

The dataset filters annotations containing person category id `1`, and includes
person/backpack/tie category ids in the binary segmentation mask.

## Supervisely Person Dataset (SPD)

`SuperviselyPersonDataset` needs:

```text
SPD root/
  img/
    ...image files...
  seg/
    ...matching segmentation files...
```

The source asserts the sorted image and segmentation file counts match. The docs
mention a preprocessing script for Supervisely encodings; treat that as
reference material because raw SPD acquisition/preprocessing is dataset-version
specific.

## YouTubeVIS

`YouTubeVISDataset` needs:

- `videodir`: root containing frame paths referenced by `file_names` in the
  annotation JSON.
- `annfile`: instances JSON.

The dataset builds masks for person category id `26` and decodes RLE
segmentations.

## Validate layout safely

The bundled validator catches common missing-root and fgr/pha mismatch errors:

```bash
python scripts/rvm_validate_data_layout.py \
  --imagematte-train /data/ImageMatte/train \
  --background-images-train /data/Backgrounds/train \
  --background-videos-train /data/BackgroundVideos/train \
  --strict --json
```

It does not verify image decodability, dataset licensing, full train/valid
splits, or GPU readiness. Use it before, not instead of, a carefully scoped
training dry run.
