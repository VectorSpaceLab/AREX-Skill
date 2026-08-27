# Safe data/config tooling reference

This reference explains safe ways to inspect MMAction2 configs and make data-preparation decisions without training, testing, downloading datasets, scanning large media trees, or mutating user data by default.

## 1. Bundled config inspector

Use the local helper linked from this sub-skill:

```shell
python scripts/mmaction2_config_inspector.py --config CONFIG.py --show-dataloaders --show-pipelines
```

Add model summary:

```shell
python scripts/mmaction2_config_inspector.py --config CONFIG.py --show-model
```

Apply safe in-memory overrides before printing:

```shell
python scripts/mmaction2_config_inspector.py \
  --config CONFIG.py \
  --show-dataloaders --show-pipelines \
  --cfg-options \
    model.cls_head.num_classes=5 \
    train_dataloader.batch_size=4 \
    train_pipeline.0.num_clips=8 \
    model.data_preprocessor.mean="[127.5,127.5,127.5]"
```

What the inspector does:

- Loads a trusted config with MMEngine.
- Merges `--cfg-options` into memory.
- Prints top-level keys, default scope, dataloader summaries, pipeline transform names, and optional model summary.
- Does not instantiate datasets, build models, import checkpoints, open media files, scan annotation entries, train, test, or write outputs.

Limitations:

- Config files are Python; inspect only trusted config files.
- Missing `_base_` files, syntax errors, or missing MMEngine are reported as dependency/config failures.
- The helper cannot prove that media files exist or that a custom transform is importable; use it as the first safe step before any runtime job.

## 2. Data utility safety decisions

MMAction2-style data utilities fall into several risk classes. Apply these decisions before using or reimplementing utility behavior in a user workspace.

| Utility intent | Risk | Safe default | Escalation requirements |
| --- | --- | --- | --- |
| Print/inspect config | Low | Use the bundled inspector. | None beyond trusted config file. |
| Build file lists | Writes annotation files and may traverse large trees. | First validate intended schema on a tiny subset; write to a new output file. | Confirm source root, output path, dataset family, split naming, shuffle/seed, and overwrite policy. |
| Check videos | Scans media files; can be slow and may have destructive delete options in some utilities. | Scan a small split/sample; write only a report of invalid files. | Explicit user confirmation for full scan, worker count, decoder, report path, and any deletion. Do not delete by default. |
| Browse/visualize dataset | Builds dataset and reads media; writes visualization files. | Limit to a small number of samples and a fresh output directory. | Confirm phase, sample count, output directory, FPS/rescale, and optional label file. |
| Extract raw frames or optical flow | Large CPU/GPU work and large writes. | Do not run from this sub-skill by default; provide schema/config guidance. | Confirm input root, output root, extension, level, workers, expected size, overwrite/resume policy, and hardware. |
| Encode videos from frames | Large writes and codec dependencies. | Do not run by default. | Confirm frame template, start index, FPS, codec, output root, and sample dry run. |
| Extract audio or build audio features | Requires codecs and optional audio libraries; large writes. | Do not run by default; verify `AudioDataset` schema first. | Confirm source/destination roots, extension, worker count, partitioning, and feature format. |
| Download dataset annotations/videos/features | Network-heavy and may require credentials/licenses. | Never run automatically. | Require explicit user request, license/credential readiness, destination, quota, and resume policy. |
| AVA proposal conversion/denormalization | Mutates or creates proposal files whose coordinate convention matters. | Keep original proposal files untouched; write converted files separately. | Confirm normalized vs pixel coordinate convention, frame sizes, and evaluator expectation. |

## 3. Safe annotation validation snippets

Use these lightweight checks in a user-owned workspace when the user asks to validate annotation text. They read only annotation files and do not scan media directories.

### Video list shape

Expected fields: `filename label` or `filename label_1 label_2 ...` for multi-label.

```shell
python - <<'PY' video_train.txt
import sys
path = sys.argv[1]
for lineno, line in enumerate(open(path, encoding='utf-8'), 1):
    parts = line.strip().split()
    if not parts:
        continue
    if len(parts) < 2:
        print(f'{lineno}: unlabeled/inference-style line: {line.strip()}')
        continue
    bad = [x for x in parts[1:] if not x.lstrip('-').isdigit()]
    if bad:
        print(f'{lineno}: non-integer label(s): {bad}')
PY
```

### Rawframe list shape

Expected fields without offset: `frame_dir total_frames label...`; with offset: `frame_dir offset total_frames label...`.

```shell
python - <<'PY' rawframes_train.txt no-offset
import sys
path, mode = sys.argv[1], sys.argv[2]
with_offset = mode == 'with-offset'
for lineno, line in enumerate(open(path, encoding='utf-8'), 1):
    parts = line.strip().split()
    if not parts:
        continue
    min_fields = 4 if with_offset else 3
    if len(parts) < min_fields:
        print(f'{lineno}: expected at least {min_fields} fields, got {len(parts)}')
        continue
    numeric = parts[1:] if with_offset else parts[1:]
    bad = [x for x in numeric if not x.lstrip('-').isdigit()]
    if bad:
        print(f'{lineno}: non-integer numeric field(s): {bad}')
PY
```

### AVA CSV shape and normalized boxes

```shell
python - <<'PY' ava_train.csv
import csv, sys
path = sys.argv[1]
for lineno, row in enumerate(csv.reader(open(path, newline='', encoding='utf-8')), 1):
    if not row:
        continue
    if len(row) != 8:
        print(f'{lineno}: expected 8 columns, got {len(row)}')
        continue
    try:
        ts = int(row[1]); coords = [float(x) for x in row[2:6]]; label = int(row[6]); entity = int(row[7])
    except ValueError as exc:
        print(f'{lineno}: parse error: {exc}')
        continue
    if not all(0.0 <= x <= 1.0 for x in coords):
        print(f'{lineno}: bbox not normalized: {coords}')
    if coords[0] > coords[2] or coords[1] > coords[3]:
        print(f'{lineno}: invalid bbox corner order: {coords}')
PY
```

## 4. Safe config review workflow

1. Parse config with the bundled inspector using no overrides.
2. Re-run with intended `--cfg-options` and compare the printed model/dataloader/pipeline summaries.
3. Confirm dataset class and `data_prefix` keys match the annotation schema.
4. Confirm train/val/test pipeline names match the data modality and split purpose.
5. Confirm class counts and evaluator type match the task.
6. Only after the config summary is coherent should work route to training/testing or inference sub-skills.

## 5. Override examples by task

### Custom video classification

```shell
python scripts/mmaction2_config_inspector.py \
  --config CONFIG.py \
  --show-dataloaders --show-model \
  --cfg-options \
    model.cls_head.num_classes=12 \
    train_dataloader.dataset.ann_file=train.txt \
    val_dataloader.dataset.ann_file=val.txt \
    test_dataloader.dataset.ann_file=test.txt \
    train_dataloader.dataset.data_prefix.video=videos/train \
    val_dataloader.dataset.data_prefix.video=videos/val \
    test_dataloader.dataset.data_prefix.video=videos/test
```

### Rawframe conversion of a video config

Use a config-file edit when changing multiple pipeline steps, because switching `VideoDataset` to `RawframeDataset` also changes prefixes, decode transforms, `filename_tmpl`, and usually `start_index`.

Minimal fields to inspect after editing:

```text
train_dataloader.dataset.type = RawframeDataset
train_dataloader.dataset.data_prefix.img = <rawframe-root>
train_dataloader.dataset.filename_tmpl = img_{:05}.jpg
train_pipeline includes SampleFrames before RawFrameDecode
```

### AVA custom class subset

Check these fields together:

```text
model.roi_head.bbox_head.num_classes = len(custom_classes) + 1
dataset.num_classes = len(custom_classes) + 1
dataset.custom_classes excludes 0
dataset.label_file points to the matching label map
evaluator label/exclude files match the validation split
proposal file uses normalized boxes keyed by video_id,timestamp
```

## 6. When to route away

- If the user asks to launch `train.py`, `test.py`, distributed jobs, metric tools, or checkpoint evaluation, route to training-and-evaluation.
- If the user asks to run inference on a video/frames or to use an inferencer/demo, route to inference-and-demos.
- If the user asks to implement/register a new dataset class, transform class, model, head, or export path, route to models-and-extension after summarizing the data/config requirements.
