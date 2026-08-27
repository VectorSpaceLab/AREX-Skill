# TFDS CLI reference

This reference summarizes safe TensorFlow Datasets command-line workflows. It is self-contained and intentionally avoids depending on the original repository docs or tests at runtime.

## Global command layout

```bash
tfds [--version] [--dry_run=True] {build,new,convert_format,build_croissant} ...
```

Important parser rules:

- `--dry_run` is a **top-level** flag. Put it before the subcommand:
  ```bash
  tfds --dry_run=True build --data_dir /tmp/tfds-build-data mnist --max_examples_per_split=1
  ```
- Boolean flags can be written explicitly (`--overwrite=True`, `--overwrite=False`). Explicit booleans are easier for generated commands and reviews than relying on parser shorthand.
- Check the installed package before relying on flag names:
  ```bash
  tfds --version
  tfds --help
  tfds build --help
  ```
- The installed CLI help for the inspected package exposed the subcommands `build`, `new`, `convert_format`, and `build_croissant`.

## `tfds new`: skeleton creation

Purpose: create a new dataset source directory from a template.

Basic safe form:

```bash
tfds --dry_run=True new my_dataset --dir /tmp/tfds-authoring
# After reviewing the parsed args:
tfds new my_dataset --dir /tmp/tfds-authoring
```

Key facts:

- `dataset_name` is positional and must be a valid dataset/Python class-style name; invalid examples include names with hyphens or names starting with digits.
- `--dir` is the parent directory where the dataset folder will be created.
- `--data_format` choices are `standard`, `conll`, and `conllu`.
- The command writes a dataset directory and fails if that target already exists.
- It creates files such as builder Python, builder test, `README.md`, `CITATIONS.bib`, `TAGS.txt`, `checksums.tsv`, `dummy_data/`, and `__init__.py`.
- Details of how to complete the builder internals are outside this sub-skill; route that to `dataset-authoring`.

## `tfds build`: generation command reference

Purpose: download and prepare TFDS datasets from registered names, imported modules, local dataset folders, or local builder scripts.

### Dataset selectors

`tfds build` accepts datasets in two ways:

```bash
# Positional datasets
tfds --dry_run=True build --data_dir /tmp/tfds-build-data mnist cifar10 --max_examples_per_split=1

# Keyword dataset list
tfds --dry_run=True build --data_dir /tmp/tfds-build-data --max_examples_per_split=1 --dataset mnist cifar10
```

Accepted dataset values include:

- A registered dataset name, optionally with config/version syntax such as `mnist` or `trivia_qa/rc`.
- A local dataset folder containing `<name>_dataset_builder.py` or legacy `<name>.py`.
- A local builder script such as `my_dataset.py`.
- No dataset argument from inside a dataset directory, meaning "build the current directory".
- A registered dataset made visible by imports, e.g. `--imports=my_package.datasets`.

When `--imports` is set, the build code expects dataset registration through those imports and does not treat the dataset selector as a local path first.

### Path flags

Use explicit locations while prototyping:

```bash
tfds --dry_run=True build my_dataset \
  --data_dir /tmp/tfds-build-data \
  --download_dir /tmp/tfds-downloads \
  --extract_dir /tmp/tfds-downloads/extracted \
  --manual_dir /tmp/tfds-downloads/manual \
  --max_examples_per_split=1
```

- `--data_dir` controls prepared dataset output and should be explicit.
- `--download_dir` defaults under the data directory if omitted.
- `--extract_dir` defaults under the download directory if omitted.
- `--manual_dir` is required for datasets whose source files must be downloaded manually.
- `--add_name_to_manual_dir=True` appends the dataset name under the manual directory to avoid collisions when generating multiple datasets.

### Debug and safety flags

- `--max_examples_per_split=1`: generate only a tiny sample per split; this is the default safe prototype limit used by the bundled helper.
- `--max_examples_per_split=0`: run split generation and downloads but skip `_generate_examples`; useful when checking metadata/split setup without writing record shards.
- `--overwrite=True`: deletes an already prepared dataset version before rebuilding. Use only on disposable/staging directories.
- `--fail_if_exists=True`: fail if the target prepared dataset already exists; useful for CI/staging checks.
- `--download_only=True`: download source files but do not prepare examples. It cannot be combined with `--register_checksums=True`.

### Config selection

Use exactly one config selector:

```bash
# In the dataset name
tfds --dry_run=True build trivia_qa/rc --data_dir /tmp/tfds-build-data --max_examples_per_split=1

# By config name
tfds --dry_run=True build trivia_qa --config rc --data_dir /tmp/tfds-build-data --max_examples_per_split=1

# By config index
tfds --dry_run=True build trivia_qa --config_idx=0 --data_dir /tmp/tfds-build-data --max_examples_per_split=1
```

If a dataset has builder configs and no config is selected, `tfds build` generates all configs. For custom configs, `--config` can be a JSON object forwarded to the builder config constructor.

### Imports and registration

For datasets outside TFDS public registration:

```bash
tfds --dry_run=True build my_dataset \
  --imports=my_project.datasets \
  --data_dir /tmp/tfds-build-data \
  --max_examples_per_split=1
```

`--imports` is a comma-separated list of modules to import before resolving builder names. Ensure those modules are importable in the shell environment used to run `tfds`.

### Checksums

- `--register_checksums=True` records source file sizes/checksums during a build. It is intended for dataset development and should be reviewed before committing generated checksum records.
- `--force_checksums_validation=True` raises an error if checksums are absent instead of bypassing validation.
- Do not use `--register_checksums=True` together with `--download_only=True`; the build command rejects that combination.

### File format and shard controls

`--file_format` choices in the inspected CLI are:

- `tfrecord`
- `riegeli`
- `array_record`
- `parquet`

Related flags:

- `--max_shard_size_mb=<int>`: bound shard size.
- `--num_shards=<int>`: force a shard count.
- `--num-processes=<int>` or `--num_processes=<int>`: build multiple datasets/configs in parallel processes. Use cautiously because ordering is not guaranteed and resource use scales with process count.
- `--nondeterministic_order=True`: may be faster but can give nondeterministic example ordering; deterministic requirements belong in the task review.
- Beam pipeline options are syntactically accepted by `tfds build`, but runner semantics and cloud/Dataflow setup belong to `beam-and-performance`.

### Metadata and publishing

- `--update_metadata_only=True`: update existing `dataset_info.json` metadata from builder definitions. The dataset must already be prepared.
- `--publish_dir=<path>`: after successful generation, copy the prepared dataset under a publish root. Use a staging publish directory first.
- `--skip_if_published=True`: skip generation if that dataset version/config already exists in the publish directory.
- `--experimental_latest_version=True`: build the latest experimental version and cannot be combined with an explicit version in the dataset selector.

## `tfds convert_format`: mutation-aware conversion

Purpose: convert already prepared TFDS dataset shards between file formats.

Basic dry-run review:

```bash
tfds --dry_run=True convert_format \
  --dataset_version_dir /tmp/tfds-build-data/my_dataset/1.0.0 \
  --out_file_format array_record \
  --out_dir /tmp/tfds-converted/my_dataset/1.0.0 \
  --num_workers=1
```

Selectors: provide exactly one of:

- `--root_data_dir`: convert all datasets/configs/versions under a root data directory.
- `--dataset_dir`: convert all configs/versions of one dataset directory.
- `--dataset_version_dir`: convert one version directory, or a comma-separated list of version directories.

Safety and side effects:

- If `--out_dir` is omitted, converted shards are written in the input dataset directory and metadata may be updated to add the new alternative file format. Treat this as a mutation.
- If multiple `--dataset_version_dir` paths are given, `--out_dir` must be omitted; each input directory is converted in place.
- Use a copied fixture or explicit `--out_dir` for rehearsals.
- Use `--overwrite=True` only for disposable outputs; it permits overwriting existing converted data.
- `--only_log_errors=True` logs conversion errors instead of failing the whole conversion; use it only when partial conversion is acceptable and the final metadata/shard counts will be checked.
- `--use_beam=True` delegates conversion to Beam; runner design belongs to `beam-and-performance`.

## `tfds build_croissant`: JSON-LD backed generation

Purpose: prepare a Croissant dataset as TFDS data.

Safe review command:

```bash
tfds --dry_run=True build_croissant \
  --jsonld /tmp/croissant.json \
  --data_dir /tmp/tfds-croissant-data \
  --file_format array_record \
  --record_sets articles,authors \
  --mapping '{"document.csv": "/tmp/manual/document.csv"}'
```

Key facts:

- `--jsonld` is required and points to the Croissant JSON-LD file.
- `--data_dir` is required and should be a staging directory while testing.
- `--file_format` defaults to `array_record`; the same file-format choices as build are accepted.
- `--record_sets` is a comma-separated list. If omitted, all record sets in the metadata are used.
- `--mapping` is a JSON object mapping Croissant `FileObject` names to local file paths for manual downloads. Quote it so the shell passes valid JSON.
- `--download_dir`, `--publish_dir`, `--skip_if_published`, `--overwrite`, and `--overwrite_version` are available. Use overwrite/publish/version changes only after the JSON-LD and mapping have been validated.
- Croissant data model design and format-specific modeling decisions belong to `formats-and-community`.

## Optional dependency cautions

The inspected CLI import path loaded TensorFlow, Beam, and Croissant-related modules successfully. Downstream environments may not have those extras. If `tfds --help` or a subcommand import fails, install only the dependency needed for the requested command path rather than broad development/test extras.
