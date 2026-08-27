# GeoSeg data formats

## General pairing contract

Acquire LoveDA, ISPRS Vaihingen/Potsdam, or UAVid from the dataset owner before
running these scripts; this skill does not download data. Use absolute paths or
paths relative to the current shell directory. The scripts sort inputs, pair by
stem, check image/mask dimensions, reject unknown labels, and refuse to replace
existing files unless `--overwrite` is explicit.

The dataset classes are not interchangeable. Do not use a mask converted for
one dataset with another dataset's config.

## LoveDA

The expected tree is:

```text
LoveDA/{Train,Val,Test}/{Urban,Rural}/
  images_png/<id>.png
  masks_png/<id>.png                 # source masks for Train/Val
  masks_png_convert/<id>.png         # indexed masks used by GeoSeg
  masks_png_convert_rgb/<id>.png     # visualization copy
```

`LoveDATrainDataset` reads `Train` or `Val`, joins both `Urban` and `Rural`,
and expects `images_png` and `masks_png_convert` to contain matching stems.
The validation dataset is instantiated at module import, so a missing external
`data/LoveDA/Val/...` tree can fail even before a dataloader is used. Test images
have no masks.

The source label encoding accepted by
[`convert_loveda_masks.py`](../scripts/convert_loveda_masks.py) is:

| Source value | Stored value | Class/meaning | RGB visualization |
|---:|---:|---|---|
| 0 | 7 | void/ignore | black |
| 1 | 0 | background | `(255,255,255)` |
| 2 | 1 | building | `(255,0,0)` |
| 3 | 2 | road | `(255,255,0)` |
| 4 | 3 | water | `(0,0,255)` |
| 5 | 4 | barren | `(159,129,183)` |
| 6 | 5 | forest | `(0,255,0)` |
| 7 | 6 | agricultural | `(255,195,128)` |

The indexed output is a single-channel PNG. Only source values 0 through 7
are accepted; a value such as 8 is an error rather than silently becoming
background. The RGB sibling is for inspection/visualization and is not the
mask directory used by the training dataset.

## Vaihingen and Potsdam

Both datasets produce the dataset-loader layout:

```text
<data-root>/{train,test}/
  images_1024/*.tif
  masks_1024/*.png
```

Vaihingen source images and masks are paired as `<stem>.tif`. With `--eroded`,
the mask is `<stem>_noBoundary.tif`. Potsdam source files are paired by their
base stem: `<stem>_RGB.tif` (or `<stem>_IRRG.tif`) with
`<stem>_label.tif`; `--eroded` selects `<stem>_label_noBoundary.tif`.
`--rgb-image` selects Potsdam RGB imagery; without it the script selects IRRG.

The color masks use these class values during conversion:

| Stored value | Class | Source RGB |
|---:|---|---|
| 0 | impervious surface (`ImSurf`) | `(255,255,255)` |
| 1 | building | `(255,0,0)` |
| 2 | low vegetation (`LowVeg`) | `(255,255,0)` |
| 3 | tree | `(0,255,0)` |
| 4 | car | `(0,255,255)` |
| 5 | clutter | `(0,0,255)` |
| 6 | boundary/ignore | `(0,0,0)` |

The normal output mask is single-channel PNG with values 0..6. Boundary (6)
is retained as the padding/ignore value; the dataset configurations commonly
use six foreground classes. `--gt` instead writes RGB visualization masks
(and an `origin/` copy), so do not point a training dataset at a GT output.
Output image patches are TIFF. A bottom/right pad is added before tiling;
image padding is zero and mask padding is boundary 6. Full patches only are
written. In `train` mode the adapted scripts emit source, horizontal-flip,
and vertical-flip variants with variant ids 0, 1, and 2. `--val-scale` applies
only outside train mode and uses bicubic image / nearest-neighbor mask resize.

## UAVid

Input is nested and must look like:

```text
uavid_train_val/<sequence>/
  Images/<frame>.png
  Labels/<frame>.png
```

The adapted splitter pairs `Images/<stem>.png` and `Labels/<stem>.png` by exact
stem, not by `zip(os.listdir(...))`. It accepts non-square source frames and
non-square tile sizes. Output is two flat directories:

```text
train_val/{images,masks}/<sequence>_<frame>_<mode>_<tile-index>.png
```

UAVid source RGB labels map to indexed values as follows:

| Stored value | Class | Source RGB |
|---:|---|---|
| 0 | Building | `(128,0,0)` |
| 1 | Road | `(128,64,128)` |
| 2 | Tree | `(0,128,0)` |
| 3 | LowVeg | `(128,128,0)` |
| 4 | Moving_Car | `(64,0,128)` |
| 5 | Static_Car | `(192,0,192)` |
| 6 | Human | `(64,64,0)` |
| 7 | Clutter | `(0,0,0)` |
| 255 | boundary/ignore | `(255,255,255)` |

Labels are written as single-channel PNGs. Image padding is black and mask
padding is 255. Full tiles only are emitted in sorted row/column order. The
`mode` flag is retained in output names and does not add augmentation; this is
consistent with the repository splitter's current behavior.
