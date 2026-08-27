# Training Data Formats

## Purpose

Read this when preparing Darkflow custom training data. Darkflow's training parser expects Pascal VOC style XML annotations plus an image directory.

## Required layout

You pass paths explicitly to the CLI:

```bash
flow --train --dataset <images_dir> --annotation <annotations_dir> --model <custom.cfg>
```

Darkflow expects:

- `<images_dir>`: image files referenced by annotation XMLs.
- `<annotations_dir>`: one or more Pascal VOC XML files.
- `<labels.txt>`: one class label per line for custom model names.

The XML `<filename>` values are joined with the dataset directory when batches are built.

## Label file format

Use one class name per line:

```text
person
bicycle
horse
```

The label count must match the config's final `[region]` `classes` value. If the config name is a recognized VOC or COCO model, Darkflow may load built-in labels instead of the default label file; read `../../../references/model-overview.md` before changing labels.

## Pascal VOC XML fields used by the parser

For each XML file, Darkflow reads:

- `filename`
- `size/width`
- `size/height`
- each `object/name`
- each `object/bndbox/xmin`, `ymin`, `xmax`, `ymax`

Minimal shape:

```xml
<annotation>
  <filename>image_001.jpg</filename>
  <size>
    <width>500</width>
    <height>375</height>
    <depth>3</depth>
  </size>
  <object>
    <name>person</name>
    <bndbox>
      <xmin>135</xmin>
      <ymin>25</ymin>
      <xmax>236</xmax>
      <ymax>188</ymax>
    </bndbox>
  </object>
</annotation>
```

## Validation helper

Run the bundled validator:

```bash
python scripts/check_voc_dataset.py --labels <labels.txt> --annotations <annotations_dir> --images <images_dir>
```

Use `--allow-missing-images` when the image directory is unavailable and you only want schema/label checks.

## Common data issues

- Unknown labels in XML files.
- Empty label file.
- Missing `filename`, `size`, or `bndbox` elements.
- Width or height equal to zero, which can surface during batching.
- XML filenames that do not exist under the image directory.
- Label count changed without updating config `classes` and `filters`.
