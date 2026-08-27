# Module dataset and data-format notes

Always verify the selected module tutorial/config before training. This reference gives the operating pattern and common failure points across PaddleX module families.

## Universal rule

Run dataset checking before training:

```bash
python scripts/run_module_smoke.py --config module_config.yaml --mode check_dataset --override Dataset.dataset_dir=./dataset
```

If `check_dataset` fails, fix the data or config before `train`. Do not try to bypass dataset validation by changing training hyperparameters.

## Common dataset shapes

| Family | Typical data | Common checks |
| --- | --- | --- |
| Image classification | image folders and label mapping / train-val split | class names, empty classes, unsupported image files, split ratio |
| Detection / instance segmentation / rotated detection | images plus COCO/VOC/rotated annotations | class ids, bbox polygons, missing image references, annotation file path |
| Semantic segmentation | images plus masks | mask classes, palette/label ids, same image-mask size |
| OCR text detection/recognition | image paths plus transcription/box annotations | encoding, text normalization, box order, cropped-image availability |
| Layout/table/formula/document | images/PDF-derived pages plus layout/table/formula labels | page/image mapping, table structure labels, HTML/XLSX targets, special tokens |
| Time series | CSV/tabular data | timestamp order, target columns, covariates, grouping ids, train/val/test splits |
| Speech | audio files plus transcript/metadata | sample rate, codec, transcript text, language/tokenizer dependency |
| Video | video files plus labels/frames | codec availability, frame extraction, clip length, label mapping |
| VLM/doc VLM/chart parsing | document/image inputs plus structured answers or table targets | large model dependencies, prompt/schema format, GPU/remote service expectations |
| 3D BEV | sensor/lidar/camera metadata | dataset-specific directory layout and calibration files |

## Config override hygiene

- Keep paths under dataset/output sections, not under model-definition sections.
- Override only keys that exist in the selected config.
- Use quoting for shell values that include spaces, commas, or JSON-like content.
- Prefer one override per `-o` argument:

```bash
python scripts/run_module_smoke.py --config config.yaml --mode check_dataset --override Dataset.dataset_dir=./dataset --override Global.output=./output
```

## Small dry-run strategy

When a dataset is large or remote:

1. Create a tiny local subset that preserves the directory/annotation format.
2. Run `check_dataset` on the subset.
3. Run one short train/evaluate smoke if the user has enough budget.
4. Only then run full training.

## When to stop and ask

Ask for more information when the user omits:

- target module family or model name.
- dataset directory and annotation format.
- desired mode (`check_dataset`, `train`, `evaluate`, `export`, `predict`).
- hardware/backends and runtime budget for training or large VLM modules.
- whether downloads are allowed for pretrained weights.
