# Data formats and config connections

## Detectron2-style datasets

AdelaiDet configs refer to registered dataset names, not raw paths. A dataset must be registered before launch, and the config must list names in:

```yaml
DATASETS:
  TRAIN: ("my_train",)
  TEST: ("my_val",)
```

For custom data, register via Detectron2 dataset catalogs in a small launcher or importable registration module before calling training/evaluation.

## COCO instance annotations

COCO-style instance JSON should contain:

- `images`: `file_name`, `height`, `width`, `id`
- `annotations`: `image_id`, `bbox`, `segmentation`, `area`, `category_id`, `iscrowd`, `id`
- `categories`: `id`, `name`

Semantic-mask conversion consumes instance `segmentation` fields and writes one `.npz` mask per image.

## Thing semantic masks

Generated `.npz` files contain:

```python
np.load(path)["mask"]  # uint8 HxW, 0 background, 1..N contiguous thing ids
```

File stems are based on the source image filename stem. Keep output root consistent with the config's semantic-supervision path.

## PIC person data

PIC conversion expects separate instance and semantic grayscale masks. Instance masks encode object instance ids; semantic masks encode category labels. The converter keeps only category id `1` (`person`) and emits COCO polygons from contours.

## Text spotting data

Text annotations need more than boxes:

- Text geometry as Bezier/control-point-compatible fields.
- Transcription strings.
- Ignore/legibility labels.
- Dictionary/lexicon protocol alignment.

Use `text-spotting` before training BAText/ABCNet on custom data.

## MEInst components

MEInst uses encoded mask components referenced by `MODEL.MEInst.PATH_COMPONENTS`. If that path is missing, training can fail even when COCO annotations exist. Generate or point to components matching the mask size/dimension expected by the config.

## Common validation checks

- All image paths referenced by annotations exist.
- Category IDs match the config's class count and mapping.
- Semantic masks have same height/width as source images.
- Text records include transcription and Bezier geometry.
- Output directories are separate from raw annotations to avoid accidental overwrite.
