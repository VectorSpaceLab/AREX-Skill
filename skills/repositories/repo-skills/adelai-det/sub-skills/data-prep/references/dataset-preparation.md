# Dataset preparation recipes

AdelaiDet reuses Detectron2 dataset registration patterns, but several model families need extra derived files.

## COCO/PIC thing semantic masks

Some basis-mask/segmentation workflows need semantic masks generated from instance annotations. Use the skill-owned converter with explicit paths:

```bash
python scripts/prepare_thing_semantic.py \
  --instance-json datasets/coco/annotations/instances_train2017.json \
  --output-dir datasets/coco/thing_train2017 \
  --category-mode coco
```

For PIC/person-only data:

```bash
python scripts/prepare_thing_semantic.py \
  --instance-json datasets/pic/annotations/train_person.json \
  --output-dir datasets/pic/thing_train \
  --category-mode person-only
```

Outputs are compressed `.npz` files with a `mask` array. Category ids are converted to contiguous thing ids plus 1; background/unlabeled is 0.

## PIC person conversion

The source PIC script expects hard-coded directories. Use the safer wrapper:

```bash
python scripts/gen_pic_person_coco.py \
  --pic-root /path/to/PIC \
  --phase train --phase val \
  --output-dir /path/to/PIC/pic/annotations
```

Expected input under `--pic-root`:

```text
pic/list5/train_id
pic/list5/val_id
instance/train/<id>.png
instance/val/<id>.png
semantic/train/<id>.png
semantic/val/<id>.png
```

The wrapper emits COCO-style JSON with category id 1 named `person`.

## LVIS semantic masks

The source has an LVIS semantic-mask converter. It requires the LVIS API/package and full LVIS annotation files. Treat this as optional until a task explicitly names LVIS. Use the COCO semantic converter as a template, but confirm category-id mapping from the LVIS metadata before writing outputs.

## MEInst mask components

MEInst configs may require mask encoding artifacts (`MODEL.MEInst.PATH_COMPONENTS`) generated from COCO masks. Before running MEInst training:

1. Confirm instance masks exist for the target split.
2. Decide component count/dimensionality from the config.
3. Use `scripts/meinst_mask_encoding.py --check-only` to validate input/output locations and dependency expectations.
4. Run the repository's MEInst/LME generation flow only when data is available and the run budget allows it.

## Text datasets

BAText/ABCNet needs text-specific annotations, not just COCO boxes. Route to `text-spotting` for Bezier/control-point fields, transcriptions, dictionaries, lexicons, and evaluator protocol.

## Visual validation

After conversion or registration, use the dataset visualization wrapper:

```bash
python ../demo-visualize/scripts/visualize_dataset.py --repo-root /path/to/AdelaiDet \
  --config <config.yaml> --source dataloader --output output/dataset-vis --dry-run
```

Remove `--dry-run` only when paths and config are correct.
