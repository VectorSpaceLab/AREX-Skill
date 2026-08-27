# MMOCR Data Preparation Workflows

## Safe preflight first

Use the bundled helper before a conversion, config edit, or training handoff:

```bash
python scripts/mmocr_dataset_preflight.py --list
python scripts/mmocr_dataset_preflight.py --dataset wildreceipt --task kie
python scripts/mmocr_dataset_preflight.py --dataset-zoo-path <dataset_zoo> --dataset private_receipts --task textspotting
python scripts/mmocr_dataset_preflight.py --annotation-task textdet --validate-json <annotation.json>
```

The helper never imports MMOCR, never downloads data, and never writes outputs.
It can inspect a dataset-zoo directory, fall back to a bundled official coverage
snapshot, and perform lightweight structure checks for MMOCR JSON, recognition
line labels, or WildReceipt-style KIE lines.

## Unified dataset preparer CLI semantics

The public preparer accepts this argument shape:

```text
prepare_dataset datasets... [--nproc N] [--task textdet|textrecog|textspotting|kie]
                        [--splits train test val] [--lmdb] [--overwrite-cfg]
                        [--dataset-zoo-path <dataset_zoo>]
```

Argument meanings:

| Argument | Meaning | Data-prep decision |
| --- | --- | --- |
| `datasets` | one or more dataset-zoo folder names | verify the folder exists and the requested task file exists before running |
| `--nproc` | worker count for parsing/packing; default is 4 | keep small on shared hosts; increase only for large local conversions |
| `--task` | `textdet`, `textrecog`, `textspotting`, or `kie`; default is `textdet` | choose from the task decision map, not from model family alone |
| `--splits` | split names to prepare; valid values are `train`, `test`, `val`; default requests all three | request only splits present in the dataset-zoo config to avoid silent skips/confusion |
| `--lmdb` | force LMDB output | only with `--task textrecog`; requires loader/config changes |
| `--overwrite-cfg` | allow generated base dataset config to overwrite an existing file | require explicit approval when preserving local config edits matters |
| `--dataset-zoo-path` | alternate dataset-zoo root | use for private dataset-zoo entries or copied official metadata |

The preparer may download, extract, move, delete, and generate config files.
Before allowing it to run, confirm dataset license, network access, cache space,
expected `data_root`, chosen splits, and whether existing configs can be
overwritten.

## What a dataset-zoo task config does

A task config describes the complete conversion plan. A typical split preparer
contains:

```python
train_preparer = dict(
    obtainer=dict(...),
    gatherer=dict(...),
    parser=dict(...),
    packer=dict(...),
    dumper=dict(...))
config_generator = dict(type='TextDetConfigGenerator')
```

Conceptual roles:

- `obtainer`: ensures raw archives/files are present, extracts them, and maps
  files into task directories. The common obtainer creates `data_root`,
  `<task>_imgs`, and `annotations` directories.
- `gatherer`: returns either parallel image/annotation lists (`PairGatherer`) or
  one image directory plus one annotation file (`MonoGatherer`).
- `parser`: normalizes raw annotation syntax into tuples containing image paths
  and instances.
- `packer`: converts parsed instances into MMOCR JSON or KIE line objects.
- `dumper`: writes JSON, LMDB, or WildReceipt open-set text output.
- `delete`: removes temporary extraction/annotation folders after conversion.
- `config_generator`: writes a base dataset config under
  `configs/<task>/_base_/datasets/<dataset>.py` unless overwriting is disabled.

A split with no preparer is skipped. A preparer with only some of gatherer,
parser, packer, and dumper is invalid; they must be all present or all absent.

## Output layouts and generated configs

Typical generated layouts:

```text
# text detection
<data_root>/
  textdet_imgs/train/
  textdet_imgs/test/
  textdet_train.json
  textdet_test.json

# text recognition JSON
<data_root>/
  textrecog_imgs/train/
  textrecog_imgs/test/
  textrecog_train.json
  textrecog_test.json

# text recognition LMDB
<data_root>/
  textrecog_train.lmdb/
  textrecog_test.lmdb/

# KIE WildReceipt-style
<data_root>/
  image_files/
  class_list.txt
  dict.txt
  openset_train.txt
  openset_test.txt
```

Generated base configs use a task-specific variable such as
`icdar2015_textdet_data_root = 'data/icdar2015'` and dataset variables such as
`icdar2015_textdet_train` or `icdar2015_textrecog_test`. If a config generator
uses `dataset_postfix`, the variable becomes
`<dataset>_<postfix>_<task>_<split>`; for example, alternate recognition test
labels may produce an additional `icdar2015_1811_textrecog_test` variable.

For training/evaluation, the model config imports the generated base dataset
config and assigns the task pipeline before placing the dataset in dataloaders.
Route the final training config work to the training sub-skill.

## Data root, prefixes, annotation files, and loaders

Before handing data to training/evaluation, verify these relationships:

1. `data_root` is the root used to resolve `ann_file` and relative image paths.
2. `ann_file` points to a generated JSON, LMDB directory, or KIE annotation file
   under that `data_root`.
3. Generated JSON `img_path` values are relative to `data_root` unless a custom
   dataset config intentionally adds a `data_prefix`.
4. Text detection and spotting pipelines load image files with
   `LoadImageFromFile` and load geometry/text via `LoadOCRAnnotations`.
5. Recognition JSON pipelines use `LoadImageFromFile` plus
   `LoadOCRAnnotations(with_text=True)`.
6. Recognition LMDB pipelines use `RecogLMDBDataset` and `LoadImageFromNDArray`.
7. KIE pipelines use `WildReceiptDataset`-style annotations and KIE annotation
   loading/packing; class and dictionary metadata must match the model.

A minimal data handoff to training should include dataset name, task, splits,
`data_root`, generated annotation files, dataset variable names, loader type,
and whether the pipeline must ignore image orientation or consume LMDB arrays.

## Private dataset path selection

### Private text detection

Use this path when labels locate text but transcripts are missing, ignored, or
not needed by the model. Normalize raw annotations into polygons/boxes and
boolean ignore flags. For line-level private data, keep each line polygon as one
instance; for word-level data, keep each word as one instance.

### Private text recognition

Use this path when each sample is a cropped word/line image with one label, or
when you intentionally crop recognition samples from full images. Check labels
against the intended dictionary before training. Use LMDB only when the dataset
is large enough to justify a different storage and loader path.

### Private text spotting

Use this path when a full image contains multiple text regions and each region
has a transcript. It is often the right choice for receipts/forms when the
immediate target is OCR output rather than semantic key-value extraction.

### Private KIE

Use this path when semantic fields matter: store name, date, total, tax,
address, product items, quantities, prices, and similar key/value fields. Verify
that every OCR token has a box, text, and semantic label. If key-value relations
are supervised, produce consistent edge IDs. Do not reuse WildReceipt label
numbers unless the class list is truly the same.

## Visualization as reference-only sanity check

Dataset browsing is useful after conversion but should not be the first or only
validation step. It can build datasets, run pipelines, and open display windows.
For headless environments, use output-only/no-display settings, limit the number
of samples, and prefer `original` mode when checking annotation geometry before
expensive transforms. Treat failures here as visualization/config diagnostics,
not proof that raw conversion is wrong until JSON/paths are checked.

## Handoff checklist before training/evaluation

- Dataset/task/split names selected and supported by dataset-zoo or private
  metadata.
- No accidental download is pending, or the user approved network/cache/storage.
- Generated annotations exist and pass structure checks.
- Image paths resolve from `data_root` and any `data_prefix`.
- `--overwrite-cfg` decision is explicit.
- Recognition LMDB status is known; loader and dataset type match storage.
- Dictionary and text charset risks are flagged.
- KIE class list, dictionary, label mapping, and edge policy are documented.
- Visualization, if requested, is output-only/headless-safe and sample-limited.
