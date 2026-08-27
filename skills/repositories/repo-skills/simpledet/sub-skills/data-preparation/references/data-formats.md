# SimpleDet roidb data formats

This reference documents the behavior of the bundled
`sub-skills/data-preparation/scripts/convert_roidb.py`. The converter does not
infer a dataset layout, download data, or choose an output filename: callers
must provide the input arguments and an explicit `--output` path.

## Records produced by the converter

Each converted image is a dictionary containing:

| field | produced type | meaning |
| --- | --- | --- |
| `gt_class` | NumPy `int32` array, shape `(N,)` | The class values supplied by the format converter. COCO values are contiguous IDs beginning at `1`; VOC values come directly from the label map (the helper does not validate them); CrowdHuman uses `1` for `person` and `-2` for non-person/ignored boxes. |
| `gt_bbox` | NumPy `float32` array, shape `(N, 4)` | Box coordinates in xyxy order. |
| `flipped` | `False` (Python bool) | The converter does not create flipped records. |
| `h`, `w` | Python `int` | Image dimensions. |
| `image_url` | `str` | The string form of the path passed or constructed by the converter. It is not made absolute. |
| `im_id` | Python `int` | The format-specific integer image/record ID described below. |

The optional `gt_poly` key is always created by the COCO converter (its value
is a per-image list), and is created for custom JSON only when the input
`gt_poly` value is non-`None`. Values are not normalized. The converter does
not add a CrowdHuman `id` field, even though the source record has an `ID`.

All four formats require NumPy because the output contains NumPy arrays.

## Common caveats

- Coordinates are stored in xyxy order, not COCO's input xywh order.
- The converter does not perform a general record validation pass. It only
  applies the format-specific checks described below.
- `image_url` can be relative or absolute. For COCO and VOC it is derived from
  the paths supplied to the command; only the CrowdHuman image-size lookup
  requires opening the image during conversion.
- The output file is exactly the path passed to `--output`. There is no output
  basename derivation, automatic `data/cache` placement, or split-based naming
  in this helper. Choose a basename that matches `DatasetParam.image_set` when
  handing the result to a model workflow.

## COCO JSON

Invoke the converter with `--format coco --input ANNOTATIONS.json
--image-root IMAGE_ROOT --output OUTPUT.roidb`. The annotation path is used
directly by `pycocotools.COCO`; the converter does not construct an
`annotations/` path from a dataset name, inspect a split, or switch between
`instances_` and `image_info_` files.

For every image returned by `COCO.getImgIds()`/`loadImgs()` and every
non-crowd annotation returned for that image:

1. `COCO.getCatIds()` is enumerated in the order returned. Each source category
   ID is mapped to the next contiguous value beginning at `1`. This is the
   only category remapping; there are no special aliases or hard-coded COCO
   class names.
2. The input `bbox` is read as `[x, y, width, height]`. `x` and `y` are first
   clamped at zero. The right and bottom values are computed with the
   converter's historical `width - 1`/`height - 1` adjustment and clipped to
   `image width - 1`/`image height - 1`.
3. An annotation is skipped when `area` is missing or `<= 0`, or the resulting
   right/bottom corner is less than its left/top corner. Annotations with
   `iscrowd` true are not selected.
4. `im_id` is the source COCO image `id`, and `image_url` is
   `str(Path(image_root) / image["file_name"])`.
5. For every retained annotation, `annotation.get("segmentation")` is
   appended to `gt_poly`. Thus a missing segmentation produces `None`; a
   polygon list remains a polygon list, and an RLE/dict remains that dict.

The converter does not decode RLE, turn RLE into polygons, reject RLE, or
validate polygon lengths. Whether a downstream mask loader accepts a given
`gt_poly` value is a separate contract and must not be inferred from this
conversion step.

## VOC XML

Invoke with `--format voc --input VOC_ROOT --label-map LABEL_MAP.json
--output OUTPUT.roidb`. `--label-map` is required for VOC; it has **no default
value**. The JSON is loaded as a class-name-to-ID mapping, and an object whose
class name is absent raises an error. The helper does not verify that IDs are
contiguous or 1-based, so the supplied map must satisfy the model's class
contract.

If `--split SPLIT` is supplied, names are read in the order of
`VOC_ROOT/ImageSets/Main/SPLIT.txt`, and the corresponding XML files are used.
Without `--split`, all `VOC_ROOT/Annotations/*.xml` files are selected in
sorted pathname order. Each XML's `size/height`, `size/width`, and `filename`
are read; `image_url` is `str(VOC_ROOT / "JPEGImages" / filename)`, preserving
whether the supplied root was relative or absolute. The XML `bndbox` values
are copied as `[xmin, ymin, xmax, ymax]` floats without clipping or geometric
validation. `im_id` is the zero-based enumeration index in the selected XML
sequence. No VOC cache basename is derived by the converter.

## CrowdHuman ODGT

Invoke with `--format crowdhuman --input ANNOTATION.odgt --image-root
IMAGE_ROOT --output OUTPUT.roidb`. Each nonblank line is decoded as one JSON
source record. Its `ID` determines the image path
`str(Path(image_root) / (str(ID) + ".jpg"))`; Pillow opens that path to obtain
the width and height. `im_id` is the zero-based source-record enumeration
index. The source `ID` is **not** copied into an output `id` key.

For each `gtboxes` item, non-positive `fbox` width or height is skipped. Other
boxes are written as `[x, y, x + width, y + height]`. A box is class `1` only
when `tag == "person"` and `extra.ignore` is zero or absent. All other boxes
are class `-2`. Items are kept in their input order: there is no shuffle,
including no CrowdHuman-specific shuffle of boxes or records.

## Native/custom JSON

Invoke with `--format json --input RECORDS.json --output OUTPUT.roidb`. The
top-level value may be a list, or a dictionary containing a `records` or
`roidb` list. Every item must contain `gt_class`, `gt_bbox`, `flipped`, `h`,
`w`, `image_url`, and `im_id`. The converter casts `gt_class` to NumPy
`int32`, `gt_bbox` to NumPy `float32` with shape `(-1, 4)`, converts `im_id`,
`h`, and `w` to Python integers, converts `image_url` to a string, and copies
`flipped` through `bool(...)`. An optional `gt_poly` is passed through
unchanged. Other input keys are not retained. The explicit `--output` path
is used verbatim; the input JSON basename is never transformed.

## Segmentation values

This converter is a transport step, not a mask encoder. It preserves the
COCO `segmentation` object exactly as a per-instance `gt_poly` value (or
stores `None` when the key is absent), and passes custom JSON `gt_poly`
through unchanged. It performs no polygon/RLE conversion or validation. If a
downstream mask workflow requires raw polygon lists, provide and validate
those lists separately; do not claim that this helper makes RLE compatible.

## Handoff to model workflows

Model configurations may expect conventional names such as
`data/cache/coco_val2017.roidb` or `data/cache/voc2007_test.roidb`, but those
names are conventions of the consuming workflow. The converter creates no
cache directory or alias automatically. After conversion, run
`sub-skills/data-preparation/scripts/validate_roidb.py` and ensure the chosen
output path and record fields match the consuming configuration.
