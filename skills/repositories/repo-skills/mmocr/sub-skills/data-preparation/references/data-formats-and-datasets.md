# MMOCR Data Formats and Dataset Coverage

## Task decision map

| Need | MMOCR task | Dataset shape | Main fields to verify |
| --- | --- | --- | --- |
| Locate text regions in full images | `textdet` | one image may contain many text instances | `img_path`, `height`, `width`, per-instance `polygon` or `bbox`, `bbox_label`, `ignore` |
| Recognize a single cropped word/line image | `textrecog` | each image is one recognition sample, or text is cropped from full-image boxes | `img_path`, one `instances[].text`, recognition dictionary compatibility, optional LMDB |
| Detect and transcribe text in full images | `textspotting` | text detection geometry plus transcript per instance | `polygon` or `bbox`, `text`, `ignore`, `height`, `width` |
| Extract receipt/document key information from OCR tokens | `kie` | token boxes and texts with node labels, optional edge groups | `file_name`, `height`, `width`, `annotations[].box`, `text`, `label`, optional `edge`, class list/metainfo |

Choose the smallest task that matches the user goal. A private receipt dataset
with only polygons and transcripts is usually `textspotting`; the same receipt
data with semantic labels such as total/date/store fields is `kie`. Cropped
word or line images with only a transcript are `textrecog`.

## Unified MMOCR JSON for OCRDataset

The generated JSON used by `OCRDataset` is a dictionary with `metainfo` and
`data_list`:

```json
{
  "metainfo": {
    "dataset_type": "TextDetDataset",
    "task_name": "textdet",
    "category": [{"id": 0, "name": "text"}]
  },
  "data_list": [
    {
      "img_path": "textdet_imgs/train/img_1.jpg",
      "height": 720,
      "width": 1280,
      "instances": [
        {
          "polygon": [10, 20, 110, 20, 110, 60, 10, 60],
          "bbox": [10, 20, 110, 60],
          "bbox_label": 0,
          "ignore": false,
          "text": "optional for textspotting"
        }
      ]
    }
  ]
}
```

Key conventions:

- `img_path` is stored relative to the dataset `data_root` by the official
  packers. Keep generated JSON image paths and config `data_root` aligned.
- `polygon` is a flat coordinate list `[x1, y1, x2, y2, ...]`. It must contain
  an even number of coordinates and at least four points for text detection and
  spotting.
- `bbox` is axis-aligned `[x1, y1, x2, y2]`. Detection and spotting packers can
  derive a `bbox` from a polygon or a polygon from a box.
- `bbox_label` is normally `0` with category name `text` for text detection and
  spotting.
- `ignore` removes invalid or don't-care regions from training/evaluation.
  Common raw ignore markers are `###` for detection/spotting and `#` for some
  recognition annotations.
- `text` is required for `textrecog` and `textspotting`; it is not needed for a
  pure detector target but may be present in raw annotations.

## Text detection preparation concepts

The official preparer breaks conversion into these conceptual stages:

1. obtain image and annotation files into a task layout such as
   `textdet_imgs/<split>/` and `annotations/<split>/`;
2. gather images and annotations either one-to-one (`PairGatherer`) or one
   annotation file to many images (`MonoGatherer`);
3. parse raw files into instances with `poly` or `box`, optional `text`, and
   `ignore`;
4. pack samples into MMOCR JSON with height/width, `polygon`, `bbox`,
   `bbox_label`, and `ignore`;
5. dump `textdet_<split>.json` and generate a base dataset config.

For private detection data, decide first whether raw annotations are polygons,
quadrilateral boxes, or axis-aligned boxes. Configure parsing to normalize them
into flat polygons or `[x1, y1, x2, y2]` boxes. If annotations were created on
raw pixels for datasets with EXIF orientation quirks, make the downstream image
loader ignore orientation so that pixels and polygons stay aligned.

## Text recognition data and dictionaries

Recognition data has two common forms:

- Already-cropped images: raw annotations map an image name to one transcript.
  The packed MMOCR item contains `instances: [{"text": "..."}]`.
- Full-image annotations with boxes and transcripts: a crop packer can create
  `textrecog_imgs/<split>/...` patches and write recognition JSON.

MMOCR also has a legacy `RecogTextDataset` for `.txt` or JSONL labels. Prefer
new unified JSON for new data unless the user is maintaining a legacy config.

A recognition dataset can be syntactically correct but incompatible with a
model dictionary. Check the intended model dictionary before training:

- common built-in character files include lowercase English+digits, English
  digits+symbols, English digits+symbols+space, Chinese+English+digits, Korean
  English+digits+symbols, and an SDMGR dictionary;
- if labels contain spaces, punctuation, mixed case, CJK, Korean, or currency
  symbols, choose or create a dictionary that contains those characters;
- dictionary wiring inside recognition/KIE models belongs to the component
  sub-skill, but data preparation should flag out-of-vocabulary transcripts
  before training.

## Recognition LMDB

`--lmdb` is only valid for `textrecog`. It forces each prepared split to be
dumped as `textrecog_<split>.lmdb` and makes the generated dataset config use
`RecogLMDBDataset` with a dataset name suffixed by `_lmdb`.

LMDB records contain:

- `num-samples`: total number of valid samples;
- `image-000000001`, `image-000000002`, ...: encoded image bytes;
- `label-000000001`, `label-000000002`, ...: transcript bytes.

Because `RecogLMDBDataset` loads an image into `results['img']` directly, the
recognition pipeline must use `LoadImageFromNDArray`, not `LoadImageFromFile`.
A JSON recognition config and an LMDB recognition config are not
interchangeable without changing both dataset type and loader.

## Text spotting

Text spotting uses the same image/layout assumptions as text detection but each
instance must also include `text`. The standard packer writes:

- `metainfo.dataset_type = TextSpottingDataset`;
- `metainfo.task_name = textspotting`;
- `category = [{"id": 0, "name": "text"}]`;
- per-instance `polygon`, `bbox`, `bbox_label`, `ignore`, and `text`.

Many official spotting entries reuse a text detection dataset-zoo config and
swap the packer/config generator to spotting. For private datasets, use
textspotting when the model needs both regions and transcripts in full images;
use textrecog when each sample is already a cropped word/line image.

## KIE receipt/document format

MMOCR's built-in KIE path is WildReceipt-style. Raw close-set lines are JSON
objects like:

```json
{
  "file_name": "image_files/example.jpeg",
  "height": 1200,
  "width": 1600,
  "annotations": [
    {"box": [550, 190, 937, 190, 937, 104, 550, 104], "text": "SAFEWAY", "label": 1},
    {"box": [1048, 211, 1074, 211, 1074, 196, 1048, 196], "text": "TM", "label": 25}
  ]
}
```

Open-set KIE lines add an `edge` group and use coarse node labels such as
background, key, value, and others. Built-in WildReceipt metadata includes
receipt classes such as store name/address, telephone, date, time, product
item/quantity/price, subtotal, tax, tips, total, ignore, and others. For a
private receipt/document dataset, do not assume the WildReceipt label numbers
match your labels; define the class list and mapping before conversion.

## Dataset-zoo metadata and supported tasks

Each dataset-zoo folder may contain:

- `metafile.yml`: display name, paper/citation, website, language, scene,
  granularity, tasks, license, format, and keywords;
- `sample_anno.md`: raw annotation examples for human inspection;
- one or more task config files named `textdet.py`, `textrecog.py`,
  `textspotting.py`, or `kie.py`.

The unified preparer checks that the requested dataset folder exists and that
`metafile.yml`, when present, lists the requested task. License metadata may
trigger a warning and delay before the actual data operation.

Official task coverage distilled from the bundled dataset-zoo:

| Dataset | Supported tasks |
| --- | --- |
| `cocotextv2` | `textdet`, `textrecog`, `textspotting` |
| `ctw1500` | `textdet`, `textrecog`, `textspotting` |
| `cute80` | `textrecog` |
| `funsd` | `textdet`, `textrecog`, `textspotting` |
| `icdar2013` | `textdet`, `textrecog`, `textspotting` |
| `icdar2015` | `textdet`, `textrecog`, `textspotting` |
| `iiit5k` | `textrecog` |
| `mjsynth` | `textrecog` |
| `naf` | `textdet`, `textrecog`, `textspotting` |
| `sroie` | `textdet`, `textrecog`, `textspotting` |
| `svt` | `textdet`, `textrecog`, `textspotting` |
| `svtp` | `textrecog` |
| `synthtext` | `textdet`, `textrecog`, `textspotting` |
| `textocr` | `textdet`, `textrecog`, `textspotting` |
| `totaltext` | `textdet`, `textrecog`, `textspotting` |
| `wildreceipt` | `textdet`, `textrecog`, `textspotting`, `kie` |

Other dataset-specific converter modules exist for legacy/manual workflows.
Treat them as reference-only unless the user explicitly approves adapting one:
most assume a particular external dataset layout, may download or move large
files, and are less stable than the unified dataset-zoo path.
