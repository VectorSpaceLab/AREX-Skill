# Inference workflows

These procedures describe the behavior of the checked-in scripts without
copying their GPU implementations. They assume a prepared CUDA environment,
a config/model pair, and an external checkpoint. See
[CLI reference](cli-reference.md) for flags and
[troubleshooting](troubleshooting.md) for failure recovery.

## 1. Benchmark tile evaluation

### Input contract

Use data prepared by the data-preparation route and the config for the same
dataset/model family. The default dataset constructors expect these roots:

- Vaihingen: `data/vaihingen/test/images_1024` and
  `data/vaihingen/test/masks_1024` (or the configured `img_dir`/`mask_dir`).
  Images are `.tif`, masks are `.png`, and six class ids are expected.
- Potsdam: `data/potsdam/test/images_1024` and
  `data/potsdam/test/masks_1024`, also six classes with `.tif` images and `.png`
  masks.
- LoveDA test: `data/LoveDA/Test/Urban/images_png` and
  `data/LoveDA/Test/Rural/images_png`. LoveDA validation additionally needs
  matching `masks_png_convert` trees under `data/LoveDA/Val`. LoveDA has seven
  classes and the dataset returns an `img_type` of `Urban` or `Rural`.

Vaihingen/Potsdam dataset constructors enumerate mask filenames and derive
image ids from mask stems, then load `<stem>.tif` and `<stem>.png`. Equal file
counts do not prove matching stems, so check pairing before a run. LoveDA
enumerates image filenames by region; test prediction has no ground truth.

### Execution and metrics

Each script parses a Python config, constructs the configured Lightning model,
loads exactly:

```text
<config.weights_path>/<config.test_weights_name>.ckpt
```

It moves the model to CUDA, calls `eval()`, wraps it in the selected `ttach`
TTA adapter, predicts batches of two with four workers, applies softmax over
classes, and takes `argmax(dim=1)`.

Vaihingen and Potsdam add every prediction/ground-truth pair to
`tools.metric.Evaluator`, write one output per tile, and print class-level F1
and IoU followed by aggregate F1, mIoU, and OA. The aggregate mIoU/F1 means
exclude the last class in these two scripts. LoveDA only evaluates when
`--val` is set; its validation metrics include all seven classes and its
prediction results are written beneath the region directory. Do not compare
metrics from an indexed mask to a palette visualization as if they were the
same representation: evaluate class ids before color conversion.

### TTA compositions

The flag names are not interchangeable across scripts:

| Route | `lr` | `d4` |
|---|---|---|
| Vaihingen | horizontal + vertical flips | horizontal + vertical flips, 90° rotation, scales 0.5/0.75/1.0/1.25/1.5 |
| Potsdam | horizontal + vertical flips | horizontal + vertical flips, scales 0.75/1.0/1.25/1.5 (no rotation in source) |
| LoveDA | horizontal + vertical flips | horizontal flip, scales 0.75/1.0/1.25/1.5 (vertical flip and rotation are commented out) |

Omitting `-t` leaves the base model unwrapped. TTA increases memory and
runtime; first prove the no-TTA route with a small data slice if resources are
limited.

## 2. UAVid sequence inference

### Input and output layout

`--image_path` is a directory containing arbitrary sequence directory names.
For each sequence, the script searches only:

```text
<input>/<sequence>/Images/*.{tif,png,jpg}
```

It sorts the matching paths, predicts each image independently, and creates:

```text
<output>/<sequence>/Labels/<original-image-basename>
```

The output parent and `Labels` folders are created automatically. The source
preserves the input filename, including its extension, and always writes the
8-class UAVid RGB palette; there is no indexed-output flag. A test-only UAVid
root may legitimately omit `Labels` on input. Empty sequences produce empty
output folders and should be treated as a data-layout warning, not a successful
inference.

### Padding, tiling, and restoration

For each image of shape `(H, W, 3)` and patch `(PH, PW)`, the script pads only
on the bottom and right with black pixels:

```text
height_pad = (PH - H % PH) % PH
width_pad  = (PW - W % PW) % PW
padded shape = (H + height_pad, W + width_pad)
```

It creates tiles in row-major order (`x` increasing, then `y` increasing),
collects predictions in the same DataLoader order, and places them back into a
padded `uint8` mask. It restores the original shape with a bottom/right crop;
no overlap blending is performed. A shape error generally indicates that a
custom model returned non-patch output or that tile ordering/batch collection
was changed.

The script uses `model.cuda(config.gpus[0])`. Confirm that `config.gpus` is an
indexable device selection before starting; the README's training-oriented
`gpus='auto'` can be incompatible with this inference-specific access.

### TTA compositions

`lr` is horizontal+vertical flip TTA. `d4` is a horizontal flip plus scales
0.75/1.0/1.25/1.5/1.75; the source does not enable vertical flips or rotations
in this branch. The default is `lr`, so explicitly omit or choose a mode rather
than inheriting it accidentally in a reproducibility record.

## 3. Huge-image inference

### Input and output layout

`--image_path` must be a flat existing folder. The script scans only the first
level for `.tif`, `.png`, and `.jpg`, sorts paths, and writes each result to:

```text
<output>/<same-basename-as-input>
```

It creates the output root if necessary. It does not recurse into sequence
folders; use the UAVid route for `sequence/Images` trees. The `-d` value picks
the output conversion: `pv` for Vaihingen/Potsdam's six classes,
`landcoverai` for four classes, `uavid` for eight classes, and `building` for
two classes.

### Padding, tiling, stitching, and crop

The exact source behavior is:

1. Read BGR with OpenCV and convert to RGB.
2. Compute bottom/right black padding using the same remainder formula as the
   UAVid route.
3. Cut a complete grid of `(patch-height, patch-width)` tiles in row-major
   order and normalize each tile.
4. Predict batches of `-b` tiles, apply softmax and argmax, and append results
   in DataLoader order.
5. Fill a padded output mask by iterating the same row-major grid.
6. Crop with `output_mask[-H:, -W:]`, where `(H, W)` is the original image
   shape. The restored mask must be exactly `(H, W)` before color conversion.
7. Convert class ids to the palette selected by `-d` and write with OpenCV.

There is no sliding-window overlap or seam blending. Padded black regions are
never part of the final output after the bottom/right crop. If a fork changes
padding placement, tile ordering, model output resolution, or batch filtering,
this negative-index crop is no longer safe.

### TTA compositions

`lr` is horizontal+vertical flip TTA. `d4` is a horizontal flip plus scales
0.75/1.0/1.25/1.5/1.75. No rotation or vertical flip is enabled in the source
`d4` branch. Start with `-b 1` when diagnosing memory or shape errors.

## Checkpoint and configuration pairing

The three tile scripts and huge-image script use
`Supervision_Train.load_from_checkpoint` and expect a Lightning checkpoint
whose model architecture and class count match the imported config. The
repository's examples include names such as:

- `model_weights/vaihingen/dcswin-small-1024-ms-512crop-e70.ckpt`
- `model_weights/potsdam/dcswin-small-1024-ms-512crop-e30.ckpt`
- `model_weights/loveda/dcswin-small-512crop-ms-epoch30.ckpt`
- `model_weights/uavid/last.ckpt`

These are naming conventions from configs, not files shipped with the checkout.
LoveDA's DCSwin config also references an external backbone file
`pretrain_weights/stseg_small.pth` while building its network. A missing
backbone or checkpoint must be fixed before inference; do not substitute a
checkpoint from another dataset merely because the filename loads.
