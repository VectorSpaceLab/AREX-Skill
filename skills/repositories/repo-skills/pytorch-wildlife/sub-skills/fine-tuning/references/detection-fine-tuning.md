# Detection fine-tuning contract

This is the legacy/experimental Ultralytics-based detection companion
workflow. It describes dataset and configuration contracts without running
training, validation, inference, or weight acquisition.

## Dataset layout

Use one dataset root with parallel image and label trees:

```text
<dataset-root>/
  images/
    train/
    val/
    test/
  labels/
    train/
    val/
    test/
```

The dataset YAML sits alongside the dataset directory. Its `path` identifies
the dataset root; `train`, `val`, and `test` identify image subdirectories
(or otherwise valid Ultralytics image sources), and `names` maps each numeric
class id to a class name. Keep YAML path resolution explicit: a relative
`path` is interpreted relative to the process/YAML convention, and the
companion launcher rewrites a non-absolute `path` to an absolute path. That
mutation is one reason to use a copied YAML and review the diff afterward.

For each image, the matching label file uses the same stem and a `.txt`
extension in the corresponding split. Each non-empty line is:

```text
class x_center y_center width height
```

`class` is an integer in the range of the YAML class mapping. The four box
values are normalized YOLO `xywh` values in `[0, 1]`; they are not pixel
coordinates and are not `x_min y_min x_max y_max`. Empty label files can be
valid for negative images, but a missing file and an incorrectly named file
should be treated as a dataset error until verified.

Check that train/val/test image stems do not accidentally overlap when the
same camera burst or source sequence was copied into multiple partitions.
Detection YAML validation should also confirm every declared split exists and
that labels are paired with the intended split, not merely that a few images
can be opened.

## Model and config contract

The general YAML keys are:

- `model`: `YOLO` or `RTDETR` (case-sensitive in the launcher).
- `model_name`: one of `MDV6-yolov9-c`, `MDV6-yolov9-e`,
  `MDV6-yolov10-c`, `MDV6-yolov10-e`, or `MDV6-rtdetr-c`.
- `data`: dataset YAML path.
- `test_data`: image directory/source for inference.
- `task`: `train`, `validation`, or `inference`.
- `exp_name`: experiment identifier.

The model table associates the first four names with Ultralytics YOLO
variants and `MDV6-rtdetr-c` with the RTDETR variant. The companion README
also records AGPL-3.0 licensing for these listed fine-tuning model variants;
review licensing and redistribution obligations before deployment.

Training keys are `epochs`, `batch_size_train`, `imgsz`, `device_train`,
`workers`, `optimizer`, `lr0`, `patience`, `save_period`, `val`, `resume`, and
`weights`. Validation keys are `save_json`, `plot`, `device_val`, and
`batch_size_val`. The launcher currently forwards only a subset of those
values directly to the Ultralytics calls. In particular, inspect the version
of the launcher before assuming `optimizer`, `lr0`, or every plotting key is
honored.

There is a known config/code naming hazard: the documented YAML uses `plot`,
while the validation branch reads `plots`. A validation run can therefore
fail with a missing key unless the launcher/config is reconciled in a copied
configuration. Treat this as a preflight error, not as a reason to invent a
new key silently.

## Launcher behavior

The command accepts a config path (default conceptually `./config.yaml`) and
loads it with YAML/Munch. If `resume` is true, `weights` is used; otherwise
`model_name` is passed through the companion's model-path resolver. Missing
cached weights cause a network download, so never call this path during a
safe check.

- `task: train` calls the selected YOLO/RTDETR model with the dataset YAML,
  epochs, image size, device, save period, workers, batch size, validation
  toggle, patience, and resume setting.
- `task: validation` calls model validation with JSON/plot/device/batch
  settings and exposes mAP50-95, mAP50, mAP75, and per-class maps.
- `task: inference` evaluates `test_data` and saves rendered results under
  `inference_results/<exp_name>` using indexed image filenames.

Use an explicit local checkpoint and an isolated output directory for any
approved run. A device id of `0` means the first accelerator in the source
configuration; confirm `torch.cuda.is_available()` and the Ultralytics device
syntax before choosing it. CPU can be useful for YAML and label preflight but
is not performance-equivalent to a full fine-tuning run.

## Run outputs and handoff

The launcher directs training projects to `runs/train_<exp_name>/exp` and
validation projects to `runs/val_<exp_name>/exp` (the exact Ultralytics
artifacts below those roots depend on the installed version). Inference
images are directed to `inference_results/<exp_name>`. The README's generic
reference to `runs/detect` should not override the actual launcher project
arguments.

Record the best checkpoint, model family/name, class names, image size,
source YAML, and Ultralytics version. The companion README says direct core
PytorchWildlife/Gradio integration is still future work. Core detection
wrappers may require a particular checkpoint family, class ordering, or
loader format; test with a local weight and the detection sub-skill before
claiming integration. Do not route a failed companion checkpoint into core
inference by changing only its extension.

The companion's model resolver downloads named MegaDetector weights to a
Torch cache when they are absent. That helper is intentionally excluded from
this runtime skill: acquire weights only under an explicit user-approved
network/credential policy, verify checksums/provenance where available, and
keep downloaded artifacts outside the generated skill tree.
