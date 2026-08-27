# Dataset Layout Reference

This reference describes the dataset roots expected by pytorch-semseg loaders. Paths are shown relative to the value configured as `data.path`; no loader should be instantiated until the config has passed static checks.

## Summary table

| Dataset key | `data.path` should point to | Train/val split spelling | Main image/mask expectation |
| --- | --- | --- | --- |
| `pascal` | VOC2012 directory | `train`, `val`, `trainval`, `train_aug`, `train_aug_val` | `JPEGImages`, `SegmentationClass`, `ImageSets/Segmentation`; SBD data for augmented splits |
| `camvid` | CamVid root | `train`, `val`, `test` | image dirs `train`, `val`, `test`; mask dirs `trainannot`, `valannot`, `testannot` |
| `ade20k` | ADE20K root | `training`, `validation` | images under `images/<split>`; labels as sibling `*_seg.png` files |
| `mit_sceneparsing_benchmark` | ADEChallenge/scene parsing root | `training`, `validation` | `images/<split>/*.jpg` and `annotations/<split>/*.png` |
| `cityscapes` | Cityscapes root | `train`, `val`, `test` | `leftImg8bit/<split>/<city>/*_leftImg8bit.png` and matching `gtFine` labels |
| `nyuv2` | NYUv2 root | config `training`, `val` | image folders `train`, `test`; annotation folders `train_annot`, `test_annot` |
| `sunrgbd` | SUNRGBD root | config `training`, `val` | image folders `train`, `test`; annotation folders `annotations/train`, `annotations/test` |
| `vistas` | Mapillary Vistas root | usually `training`, `validation` | `<split>/images/*.jpg`, `<split>/labels/*.png`, and `config.json` |

## Pascal VOC / SBD (`data.dataset: pascal`)

`data.path` should point to the VOC2012 directory:

```text
VOC2012/
  JPEGImages/
    <id>.jpg
  SegmentationClass/
    <id>.png
    pre_encoded/
      <id>.png
  ImageSets/
    Segmentation/
      train.txt
      val.txt
      trainval.txt
```

For SBD augmented training, `data.sbd_path` should point to the benchmark release root:

```text
benchmark_RELEASE/
  dataset/
    train.txt
    cls/
      <id>.mat
```

Important Pascal behavior:

- The loader builds `train_aug` by combining VOC train ids with SBD train ids.
- It writes or reuses `SegmentationClass/pre_encoded` masks. Treat this as a dataset preparation side effect, not as a static validation action.
- The unmodified training/validation entry points do not pass `data.sbd_path` to the loader. If you need Pascal SBD behavior, route command adaptation to `training-and-evaluation`.
- `img_rows: same` and `img_cols: same` are explicitly supported by the Pascal transform.

## CamVid (`data.dataset: camvid`)

Expected root:

```text
CamVid/
  train/
    <frame>.png
  trainannot/
    <frame>.png
  val/
    <frame>.png
  valannot/
    <frame>.png
  test/
    <frame>.png
  testannot/
    <frame>.png
```

Notes:

- The image and annotation file names must match within each split.
- The loader lists image files directly from the split directory.
- The loader ignores the config `img_size` and uses an internal transform size.

## ADE20K (`data.dataset: ade20k`)

Expected root:

```text
ADE20K_ROOT/
  images/
    training/
      <image>.jpg
      <image>_seg.png
    validation/
      <image>.jpg
      <image>_seg.png
```

Notes:

- The loader expects each label to be next to its image with `_seg.png` replacing `.jpg`.
- Use split names `training` and `validation`.
- Use numeric `img_rows` and `img_cols`.

## MIT Scene Parsing Benchmark (`data.dataset: mit_sceneparsing_benchmark`)

Expected root:

```text
SCENE_PARSING_ROOT/
  images/
    training/
      <image>.jpg
    validation/
      <image>.jpg
  annotations/
    training/
      <image>.png
    validation/
      <image>.png
```

Notes:

- Annotation basenames must match image basenames.
- Split names are `training` and `validation`.
- The transform explicitly accepts `img_rows: same` and `img_cols: same`.

## Cityscapes (`data.dataset: cityscapes`)

Expected root:

```text
CITYSCAPES_ROOT/
  leftImg8bit/
    train/
      <city>/
        <city>_<seq>_<frame>_leftImg8bit.png
    val/
      <city>/
        <city>_<seq>_<frame>_leftImg8bit.png
  gtFine/
    train/
      <city>/
        <city>_<seq>_<frame>_gtFine_labelIds.png
    val/
      <city>/
        <city>_<seq>_<frame>_gtFine_labelIds.png
```

Notes:

- The loader derives the label name by replacing the image suffix with `gtFine_labelIds.png` under the corresponding city directory.
- Use numeric `img_rows` and `img_cols`; `same` is not handled in this transform.
- The `test` split may lack labels in normal Cityscapes distributions, so it is usually not suitable for supervised validation.

## NYUv2 (`data.dataset: nyuv2`)

Expected root:

```text
NYUV2_ROOT/
  train/
    <prefix>_<####>.png
  train_annot/
    new_nyu_class13_<####>.png
  test/
    <prefix>_<####>.png
  test_annot/
    new_nyu_class13_<####>.png
```

Config split mapping:

- `train_split: training` -> image folder `train`
- `val_split: val` -> image folder `test`

Notes:

- Do not use `validation` for NYUv2; the loader split map expects `val`.
- Labels are matched by a four-digit image id extracted from the image filename.
- Use numeric `img_rows` and `img_cols`.

## SUNRGBD (`data.dataset: sunrgbd`)

Expected root:

```text
SUNRGBD_ROOT/
  train/
    <image>.jpg
  test/
    <image>.jpg
  annotations/
    train/
      <mask>.png
    test/
      <mask>.png
```

Config split mapping:

- `train_split: training` -> image folder `train`
- `val_split: val` -> image folder `test`

Notes:

- The loader sorts image and annotation file lists independently, then pairs them by index. Keep file naming/order consistent.
- Do not use `validation` for SUNRGBD; the loader split map expects `val`.
- Use numeric `img_rows` and `img_cols`.

## Mapillary Vistas (`data.dataset: vistas`)

Expected root:

```text
VISTAS_ROOT/
  config.json
  training/
    images/
      <image>.jpg
    labels/
      <image>.png
  validation/
    images/
      <image>.jpg
    labels/
      <image>.png
```

Notes:

- `config.json` must contain a `labels` list used for names and colors.
- Image and label basenames must match except for `.jpg` versus `.png`.
- The transform explicitly accepts `img_rows: same` and `img_cols: same`.
- If using `testing`, verify whether labels exist before treating it as validation data.

## Static path-checking strategy

Use the validator's path mode for lightweight checks:

```bash
python scripts/validate_config.py --config CONFIG.yml --strict-paths --print-summary
```

`--strict-paths` checks directory and split-file existence where predictable. It intentionally does not import dataset loaders, read images, read masks, download data, or create `pre_encoded` masks.
