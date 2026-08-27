# Config and Dataset Troubleshooting

Use this guide when YAML validation fails, a dataset split cannot be found, or a loader path looks wrong. For command execution and checkpoints, route to `training-and-evaluation`; for model constructor details, route to `model-zoo-and-apis`.

## Quick triage checklist

1. Run static validation:

   ```bash
   python scripts/validate_config.py --config CONFIG.yml --print-summary
   ```

2. If paths should exist on this machine, add path checks:

   ```bash
   python scripts/validate_config.py --config CONFIG.yml --strict-paths --print-summary
   ```

3. Fix all `ERROR` messages before running training or validation.
4. Review `WARN` messages for legacy drift, private paths, missing optional files, and PyYAML compatibility.

## Symptoms, causes, and fixes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `KeyError` for `model`, `data`, `training`, `loss`, `lr_schedule`, or `resume` | The config omitted a key that the entry point indexes directly | Add the missing key. Use `loss: null`, `lr_schedule: null`, and `resume: null` when intentionally unset. |
| `KeyError` from `get_loader` | `data.dataset` is not a registry key | Use one of `pascal`, `camvid`, `ade20k`, `mit_sceneparsing_benchmark`, `cityscapes`, `nyuv2`, `sunrgbd`, `vistas`. |
| `NotImplementedError` from loss/optimizer/scheduler setup | Registry name is misspelled or unsupported | Validate `training.loss.name`, `training.optimizer.name`, and `training.lr_schedule.name`. |
| Augmentation setup fails with a key error | Unsupported augmentation key | Use only `gamma`, `hue`, `brightness`, `saturation`, `contrast`, `rcrop`, `hflip`, `vflip`, `scale`, `rsize`, `rsizecrop`, `rotate`, `translate`, `ccrop`. |
| Config works on one machine but fails elsewhere | Dataset path or checkpoint path is machine-specific | Replace absolute or placeholder-like paths with local project-relative or documented machine-local values. |
| `yaml.load()` raises a Loader-related error | Modern PyYAML requires an explicit loader | Adapt scripts to use `yaml.safe_load(fp)` or `yaml.load(fp, Loader=yaml.SafeLoader)`. The bundled validator already uses `safe_load`. |
| Loader reports no files for a split | Split spelling or directory layout does not match the loader | Check [data-formats.md](data-formats.md) for the selected dataset and run validator with `--strict-paths`. |
| Image file found but mask missing | Label directory or basename convention does not match loader logic | Check dataset-specific label naming rules in [data-formats.md](data-formats.md). |
| `img_rows`/`img_cols` cause resize/type errors | `same` used with a loader that expects numbers | Use positive integers except for Pascal, MIT Scene Parsing Benchmark, and Vistas where `same` is explicitly checked. |
| Legacy config has `l_rate` or `l_schedule` | Old key names are not read by the current training path | Move `l_rate` to `training.optimizer.lr`; change `l_schedule` to `training.lr_schedule`. |
| Optimizer ignores `momentum` or `weight_decay` | Those keys were placed directly under `training` | Move them under `training.optimizer`. |

## Private or placeholder paths

Example configs often contain paths that are valid only on the author's machine. Replace them before use.

Bad pattern:

```yaml
data:
  path: <path/to/data>
training:
  resume: <path/to/checkpoint>
```

Safer pattern:

```yaml
data:
  path: datasets/cityscapes
training:
  resume: null
```

When `resume` is not needed, keep the key and set it to `null`; do not remove it.

## Missing split/image/mask files

Static path validation can check predictable directories and split files, but it will not read images or masks. Common fixes:

- Pascal: ensure `ImageSets/Segmentation/train.txt`, `val.txt`, and/or `trainval.txt` exist under the VOC root; ensure `JPEGImages` and `SegmentationClass` exist.
- Pascal augmented splits: ensure SBD `dataset/train.txt` and `dataset/cls` exist, and plan for `SegmentationClass/pre_encoded` generation or reuse.
- CamVid: ensure `train` pairs with `trainannot`, `val` with `valannot`, and `test` with `testannot` using matching filenames.
- Cityscapes: ensure each `leftImg8bit/<split>/<city>` image has a matching `gtFine/<split>/<city>` `labelIds` mask.
- NYUv2 and SUNRGBD: use config split `training` for train folders and `val` for test folders; do not use `validation`.
- Vistas: ensure `<split>/images`, `<split>/labels`, and `config.json` exist.

## Pascal SBD and `pre_encoded`

Pascal is the most surprising loader:

- It reads VOC split lists from `ImageSets/Segmentation`.
- It can create `SegmentationClass/pre_encoded` masks by combining VOC masks and SBD `.mat` annotations.
- It asserts an expected augmented dataset size after setup.
- The stock training/validation scripts do not pass `data.sbd_path` into the loader, even if the YAML contains it.

If a Pascal config uses `train_aug`, plan an execution adapter that explicitly passes `sbd_path`, or prepare a workflow that avoids relying on the unmodified entry point for this specific constructor argument.

## `img_rows` / `img_cols: same`

Use both keys together:

```yaml
data:
  img_rows: same
  img_cols: same
```

Safe use:

- Pascal
- MIT Scene Parsing Benchmark
- Mapillary Vistas

Unsafe or not useful:

- Cityscapes, ADE20K, NYUv2, SUNRGBD: use numeric dimensions.
- CamVid: config dimensions are ignored by the loader.
- Any dataset: `img_rows: same` with numeric `img_cols` is invalid.

## Legacy drift repair example

Legacy-like config:

```yaml
training:
  optimizer:
    lr: 0.0001
  l_rate: 0.0001
  l_schedule:
  momentum: 0.99
  weight_decay: 0.0005
  resume: best_model.pkl
```

Safer modernized section:

```yaml
training:
  optimizer:
    name: sgd
    lr: 0.0001
    momentum: 0.99
    weight_decay: 0.0005
  loss:
    name: cross_entropy
  lr_schedule: null
  resume: best_model.pkl
```

Run the validator again after editing.
