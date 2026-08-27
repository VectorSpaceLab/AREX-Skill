# SimpleDet data-preparation workflows

Use these recipes to prepare and validate a tiny roidb before handing it to a
model workflow. The bundled helpers write only explicit output paths and never
download data.

## Bundled conversion helper

Use `scripts/convert_roidb.py` from this sub-skill. It supports `json`, `voc`,
`coco`, and `crowdhuman` formats and always requires an explicit `--output`:

```bash
python <skill-root>/sub-skills/data-preparation/scripts/convert_roidb.py \
  --format json --input path/to/records.json \
  --output data/cache/custom_train.roidb
```

For a COCO annotation file and image root:

```bash
python <skill-root>/sub-skills/data-preparation/scripts/convert_roidb.py \
  --format coco --input data/custom/annotations/instances_val.json \
  --image-root data/custom/images --output data/cache/custom_val.roidb
```

For VOC XML and a label map:

```bash
python <skill-root>/sub-skills/data-preparation/scripts/convert_roidb.py \
  --format voc --input data/voc/VOC2007 --split train \
  --label-map data/label_map.json --output data/cache/voc_train.roidb
```

For CrowdHuman ODGT:

```bash
python <skill-root>/sub-skills/data-preparation/scripts/convert_roidb.py \
  --format crowdhuman --input data/crowdhuman/annotations/annotation_train.odgt \
  --image-root data/crowdhuman/images --output data/cache/crowdhuman_train.roidb
```

The converter requires NumPy for array-valued roidb fields and requires
`pycocotools` for COCO or Pillow for CrowdHuman. It does not download either
package or dataset.

## Validate

```bash
python <skill-root>/sub-skills/data-preparation/scripts/validate_roidb.py \
  --input data/cache/custom_train.roidb --check-images --max-records 3
```

Use `--format jsonl` for a JSONL record list, and `--strict` when out-of-bounds
warnings should fail the check. Validate at least one record with polygons for
mask workflows.

## Layout and split handoff

Use an annotation tree with an image tree whose names match the paths supplied
to the converter. The converter does not recognize or remap COCO split aliases;
pass the exact annotation file and image root you intend to use. After
conversion, choose an output basename that equals the consuming
configuration's `DatasetParam.image_set` value, such as
`data/cache/coco_val2017.roidb`.

For a tiny fixture, keep one to three images, one foreground instance, and one
intentional invalid record for validator testing. Once the cache passes, use the
root workflow wrapper with the selected config path; do not begin a model run
from this route.

## Deferred native check

The source loader behavior is retained as a private review candidate, not a
runtime dependency. Run it only after the runtime backend and a tiny cache are
available; a validator pass alone does not prove a model loader can bind.
