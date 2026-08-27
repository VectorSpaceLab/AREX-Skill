# Data Formats And Batch Contracts

## Loader Selection

`open_clip_train.data.get_data(args, preprocess_fns, epoch=0, tokenizer=None, naflex_data_config=None)` returns a dictionary of `DataInfo` objects keyed by split:

- `train` when `--train-data` is present or dataset type is `synthetic`/`synthetic-audio`.
- `val` when `--val-data` is present.
- `imagenet-val` and `imagenet-v2` when their flags are present.

A command must provide at least one train, validation, ImageNet, or audio zero-shot data source. Otherwise task-era `main` asserts that no data was specified.

## CSV And TSV

Use `--dataset-type csv` or `--dataset-type auto` with `.csv`/`.tsv` paths.

Default CSV flags:

```bash
--csv-separator $'\t'
--csv-img-key filepath
--csv-caption-key title
```

The CSV loader reads the file with pandas, stores image paths and captions as pandas Series, opens image paths with PIL, applies the train/eval transform, stringifies captions with `str(caption)`, tokenizes them, and emits dict samples:

```python
sample = {"image": image_tensor, "text": token_tensor}
```

Training dataloaders use `drop_last=True`; validation dataloaders keep partial final batches.

Use the bundled validator before running real training:

```bash
python sub-skills/training/scripts/validate_csv_dataset.py DATA/train.tsv --separator tab --image-key filepath --caption-key title
```

The validator checks required columns, empty values, numeric captions that OpenCLIP will stringify, and image path existence. It does not load OpenCLIP, tokenize text, transform images, or train.

## CSV Failure Patterns

- Wrong separator: a TSV read with comma separator usually appears as one wide or one malformed column; pass `--csv-separator $'\t'` or validate with `--separator tab`.
- Wrong image key: parser default is `filepath`; many caption datasets use `image`, `path`, or `file_name`.
- Wrong caption key: parser default is `title`; many examples use `caption`.
- Relative image paths: OpenCLIP passes paths directly to `Image.open(str(path))`; resolve relative paths in the CSV or run training from the intended working directory.
- Numeric captions: OpenCLIP converts them to strings before tokenization. This is supported but often indicates the wrong caption column was selected.

## WebDataset Image/Text

Use `--dataset-type webdataset` for tar shards containing image and text members with matching basenames.

Minimal shape:

```text
sample-000001.jpg
sample-000001.txt
sample-000002.png
sample-000002.txt
```

Accepted image suffixes are `jpg`, `png`, `jpeg`, and `webp`. Caption source can be:

- A text member selected by `--text-key`, default `txt`; semicolon-separated alternatives are allowed, such as `--text-key 'txt;caption'`.
- A JSON member selected by `--json-text-key FIELD`, which takes precedence over `--text-key`.

Training WebDataset requires a known epoch size. Provide `--train-num-samples` unless shard metadata can provide a count. If the count is unknown, training raises with guidance to set `--train-num-samples`.

## Multiple WebDataset Sources

Combine shard specs with `::`:

```bash
--train-data 'DATA/a/{000000..000999}.tar::DATA/b/{000000..000099}.tar'
```

Use `--dataset-resampled` for large or mixed sources. If `--train-data-upsampling-factors` is set, `--dataset-resampled` is required and the factors must match the number of `::` sources:

```bash
--dataset-resampled --train-data-upsampling-factors '1::2'
```

For non-resampled training, the number of shards must be at least `workers * world_size`.

## Modern WebDataset Pipeline Order

The task-era WebDataset path tokenizes caption text before image decode and transform:

```text
shards -> split/shuffle -> sample filter/rename -> tokenize -> optional length bucketing -> decode -> transform -> batch
```

This keeps bucket pools full of raw compressed samples rather than decoded images/waveforms. `legacy_main` uses `legacy_data`, which preserves the older decode-first pipeline and does not support bucketing or NaFlex.

## Dict Batch Contract

Task-era training uses named dict batches instead of tuples.

Image/text fixed-shape batch:

```python
batch = {
    "image": FloatTensor[B, C, H, W],
    "text": LongTensor[B, context_length],
}
```

Variable text adds a boolean validity mask:

```python
batch = {
    "image": FloatTensor[B, C, H, W],
    "text": LongTensor[B, T_batch],
    "text_valid": BoolTensor[B, T_batch],
}
```

`T_batch` is the batch maximum caption length, optionally rounded by `--text-pad-multiple`. Padding is right-aligned as invalid suffix positions. Variable text requires a tokenizer with a reserved `pad_token_id`.

Image/text tasks still accept `task(images, texts)` and `task(image=..., text=...)` for backward compatibility, but dataloader consumers should use dict keys.

## NaFlex Image Batches

When a NaFlex image data policy is active, image batches are nested dicts:

```python
batch["image"] = {
    "patches": FloatTensor[B, N, patch_dim],
    "patch_coord": LongTensor[B, N, 2],
    "patch_valid": BoolTensor[B, N],
}
batch["text"] = LongTensor[B, T]
```

NaFlex CSV and WebDataset training require an OpenCLIP NaFlex transform factory. The parser enables NaFlex automatically for model names containing `genlip`, `genlap`, or `naflexclap`; `--use-naflex` enables compatible image NaFlex pipelines manually. Route detailed token-budget and patch configuration decisions to `../naflex-generative/SKILL.md`.

## Synthetic Image/Text

Use `--dataset-type synthetic` and set `--train-num-samples`.

Synthetic data creates a blank RGB image matching the transform image size and a dummy caption. It is useful for parser/model/training-loop smoke checks and CI-style tests, not for quality experiments.

A safe CPU-oriented shape:

```bash
python -m open_clip_train.main --dataset-type synthetic --train-num-samples 16 --batch-size 4 --epochs 1 --workers 0 --device cpu --model RN50
```

## Audio Data Routing

This sub-skill covers audio dataset routing at the training-command level. Use `../audio-clap/SKILL.md` for CLAP audio model setup, audio transform fields, audio zero-shot, and audio-specific troubleshooting.

Audio dataset types:

- `webdataset-audio`: audio-caption shards for fixed CLAP, NaFlexClap, and GenLAP.
- `synthetic-audio`: fixed CLAP smoke data.

Default audio flags include `--audio-ext flac`, `--audio-fill repeatpad`, `--audio-trunc rand_trunc`, and `--audio-multiprocessing-context forkserver` when workers are active.

Fixed CLAP audio batches use:

```python
batch = {
    "audio": {
        "waveform": FloatTensor[B, clip_samples],
        "longer": BoolTensor[B],
        # optional: "mel_fusion"
    },
    "text": LongTensor[B, context_length],
}
```

Variable-text audio batches can include `text_valid`. NaFlex audio batches use a nested `audio` patch dict analogous to image NaFlex. `synthetic-audio` intentionally rejects NaFlex audio transform factories; use `webdataset-audio` for NaFlexClap and GenLAP.

## Validation Without Training

Use these safe checks before launching a costly job:

1. `scripts/training_arg_report.py -- [args...]` to inspect parser-selected defaults, normalized model flags, and option families.
2. `scripts/validate_csv_dataset.py DATA/train.tsv --separator tab --image-key filepath --caption-key title` for CSV/TSV structure and paths.
3. For WebDataset, verify shard count is at least `workers * world_size` and set `--train-num-samples` explicitly unless metadata is known to be present.
4. For variable text, verify the selected model/tokenizer supplies a pad token; route model/tokenizer checks to `../model-inference/SKILL.md` when no training command is needed.
