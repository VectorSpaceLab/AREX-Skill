# Safe TFDS CLI command recipes

Use these recipes to build commands incrementally. Keep `--dry_run=True` until the parsed arguments, directories, imports, and side effects are correct.

## Helper script quick start

The bundled helper assembles `tfds build` commands without executing them:

```bash
python sub-skills/cli-workflows/scripts/build_command_helper.py mnist
```

Default output is safe for review:

- includes top-level `--dry_run=True`;
- includes explicit `--data_dir` under a temporary location;
- includes `--max_examples_per_split=1`;
- never runs `tfds` itself.

Examples:

```bash
# Positional dataset, one config, explicit file format
python sub-skills/cli-workflows/scripts/build_command_helper.py trivia_qa \
  --config rc \
  --file-format array_record

# Use --dataset keyword list instead of positional datasets
python sub-skills/cli-workflows/scripts/build_command_helper.py mnist cifar10 \
  --use-dataset-flag

# Build current directory after reviewing parser output
python sub-skills/cli-workflows/scripts/build_command_helper.py \
  --current-dir \
  --data-dir /tmp/tfds-current-dir-build
```

To produce an execution-ready command, pass `--no-dry-run`. The helper keeps the sample limit unless `--full-build --allow-full-build` is explicitly requested.

## Recipe 1: verify the installed CLI

```bash
tfds --version
tfds --help
tfds build --help
python sub-skills/cli-workflows/scripts/tfds_cli_reference.py --json
```

If the shell cannot find `tfds`, activate the environment that installed `tensorflow-datasets` or pass `--tfds-bin` to the reference script.

## Recipe 2: prototype a public registered dataset

Dry-run first:

```bash
tfds --dry_run=True build mnist \
  --data_dir /tmp/tfds-build-data \
  --max_examples_per_split=1
```

Then run the bounded prototype only if the parsed arguments are correct:

```bash
tfds build mnist \
  --data_dir /tmp/tfds-build-data \
  --max_examples_per_split=1
```

Remove `--max_examples_per_split` only when a full build is intended, required optional dependencies are installed, and output/download directories have enough space.

## Recipe 3: build a local dataset folder or current directory

From a dataset folder containing a builder file:

```bash
cd /path/to/my_dataset
tfds --dry_run=True build \
  --data_dir /tmp/tfds-local-build \
  --max_examples_per_split=1
```

From a parent directory or another working directory:

```bash
tfds --dry_run=True build /path/to/my_dataset \
  --data_dir /tmp/tfds-local-build \
  --max_examples_per_split=1
```

The local folder is expected to contain either `<dataset_name>_dataset_builder.py` or legacy `<dataset_name>.py`. If `--imports` is present, the build command resolves the dataset through imported registration instead of local path discovery.

## Recipe 4: build a registered dataset from a custom module

```bash
tfds --dry_run=True build my_dataset \
  --imports=my_project.datasets \
  --data_dir /tmp/tfds-import-build \
  --max_examples_per_split=1
```

Use a comma-separated import list if multiple modules are required:

```bash
tfds --dry_run=True build my_dataset \
  --imports=my_project.datasets,my_project.extra_datasets \
  --data_dir /tmp/tfds-import-build \
  --max_examples_per_split=1
```

The shell environment must be able to `import my_project.datasets` before this command can work.

## Recipe 5: choose a single config safely

Use only one of the following forms:

```bash
# Dataset selector embeds config
tfds --dry_run=True build trivia_qa/rc --data_dir /tmp/tfds-config-build --max_examples_per_split=1

# Config by name
tfds --dry_run=True build trivia_qa --config rc --data_dir /tmp/tfds-config-build --max_examples_per_split=1

# Config by index
tfds --dry_run=True build trivia_qa --config_idx=0 --data_dir /tmp/tfds-config-build --max_examples_per_split=1
```

If the dataset has builder configs and no config is given, all configs are built. That can multiply work and disk use.

## Recipe 6: isolate downloads, extraction, and manual files

```bash
tfds --dry_run=True build my_dataset \
  --data_dir /tmp/tfds-staging/data \
  --download_dir /tmp/tfds-staging/downloads \
  --extract_dir /tmp/tfds-staging/downloads/extracted \
  --manual_dir /tmp/tfds-staging/manual \
  --add_name_to_manual_dir=True \
  --max_examples_per_split=1
```

Use `--manual_dir` for datasets with license-gated/manual files. With `--add_name_to_manual_dir=True`, the effective manual directory is `<manual_dir>/<dataset_name>`.

## Recipe 7: checksum registration and validation

Checksum registration is a dataset-authoring/development step, not a generic loading step.

```bash
tfds --dry_run=True build my_dataset \
  --data_dir /tmp/tfds-checksum-build \
  --download_dir /tmp/tfds-checksum-downloads \
  --register_checksums=True \
  --max_examples_per_split=1
```

Rules:

- Do not combine `--download_only=True` and `--register_checksums=True`.
- `--force_checksums_validation=True` makes missing checksums fail instead of being bypassed.
- Review generated checksum records before treating them as authoritative.

## Recipe 8: update metadata without rebuilding examples

Use only when a dataset has already been prepared in the selected data directory:

```bash
tfds --dry_run=True build my_dataset \
  --data_dir /tmp/tfds-existing-data \
  --update_metadata_only=True
```

This updates existing metadata from builder definitions. It is not a substitute for preparing missing shards.

## Recipe 9: file format and shard controls

```bash
tfds --dry_run=True build my_dataset \
  --data_dir /tmp/tfds-array-record-build \
  --file_format array_record \
  --num_shards=8 \
  --max_examples_per_split=1
```

Alternative using shard size:

```bash
tfds --dry_run=True build my_dataset \
  --data_dir /tmp/tfds-sized-shards \
  --file_format tfrecord \
  --max_shard_size_mb=256 \
  --max_examples_per_split=1
```

Avoid setting both forced shard count and shard-size policy unless the builder/task explicitly requires it.

## Recipe 10: publishing to a staging root

```bash
tfds --dry_run=True build my_dataset \
  --data_dir /tmp/tfds-build-data \
  --publish_dir /tmp/tfds-publish-staging \
  --skip_if_published=True \
  --max_examples_per_split=1
```

Publishing copies a successfully generated dataset under the publish root. Use a staging publish directory first; credentials, permanent object stores, and release policy are outside this sub-skill.

## Recipe 11: convert prepared data without mutating inputs

```bash
tfds --dry_run=True convert_format \
  --dataset_version_dir /tmp/tfds-build-data/my_dataset/1.0.0 \
  --out_file_format array_record \
  --out_dir /tmp/tfds-converted/my_dataset/1.0.0 \
  --num_workers=1
```

For multiple version directories:

```bash
tfds --dry_run=True convert_format \
  --dataset_version_dir /tmp/tfds-data/a/1.0.0,/tmp/tfds-data/b/1.0.0 \
  --out_file_format riegeli \
  --num_workers=1
```

Multiple `--dataset_version_dir` paths cannot be combined with `--out_dir`; each input is converted in place. Use copies if in-place mutation is not acceptable.

## Recipe 12: build Croissant JSON-LD with a manual file mapping

```bash
tfds --dry_run=True build_croissant \
  --jsonld /tmp/croissant.json \
  --data_dir /tmp/tfds-croissant-data \
  --file_format array_record \
  --record_sets articles,authors \
  --mapping '{"document.csv": "/tmp/manual/document.csv"}'
```

Review the JSON-LD record sets and mapping before removing `--dry_run=True`. If Croissant version metadata is absent, TFDS uses `1.0.0` unless `--overwrite_version` is provided.
