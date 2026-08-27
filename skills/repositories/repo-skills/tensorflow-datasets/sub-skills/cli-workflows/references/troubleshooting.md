# TFDS CLI troubleshooting

Use this page to triage command construction and parser/runtime failures before attempting full downloads, conversions, or publishes.

## `tfds` command is missing or help fails

Symptoms:

- `tfds: command not found`
- `ModuleNotFoundError` or optional dependency import error while running `tfds --help`
- subcommands missing from `tfds --help`

Actions:

1. Confirm the environment has `tensorflow-datasets` installed.
2. Run the bundled reference check:
   ```bash
   python sub-skills/cli-workflows/scripts/tfds_cli_reference.py --json
   ```
3. If the console script is not on `PATH`, pass its location with `--tfds-bin` or activate the package environment.
4. Install only the optional dependency needed for the command path: TensorFlow for TensorFlow-backed dataset operations, Beam for Beam-based conversion/generation paths, and Croissant support for `build_croissant`.

## `tfds build` cannot find the dataset

Common causes:

- The dataset name is not registered in the installed TFDS package.
- A custom dataset module was not imported with `--imports`.
- A local dataset path does not contain `<name>_dataset_builder.py` or legacy `<name>.py`.
- The command is run from the wrong current directory with no dataset argument.
- `--imports` is set, so the selector is resolved through registration rather than local path discovery.

Checks:

```bash
tfds --dry_run=True build my_dataset --imports=my_project.datasets --data_dir /tmp/tfds-build-data --max_examples_per_split=1
python -c "import my_project.datasets"
```

If the task is to fix builder source code, route to `dataset-authoring`.

## Config selection errors

Symptoms:

- `Config should only be defined once`
- `Dataset ... does not have config`
- `--config_idx ... greater than number of configs`

Actions:

- Use exactly one of `dataset/config`, `--config`, or `--config_idx`.
- Do not use `--config_idx` for datasets without builder configs.
- If no config is selected for a multi-config dataset, expect all configs to be built.
- Prefer named configs over indexes in user-facing commands; indexes are less stable/readable.

## Existing data, overwrite, and metadata-only surprises

Symptoms:

- Build silently reuses or skips an existing prepared dataset.
- `--fail_if_exists=True` fails because the output version already exists.
- `--overwrite=True` deletes an existing prepared dataset version.
- `--update_metadata_only=True` fails or has no useful effect because the dataset was not already prepared.

Actions:

- Use disposable `--data_dir` paths while prototyping.
- Use `--fail_if_exists=True` when a CI/staging job must prove it produced fresh output.
- Use `--overwrite=True` only with explicit confirmation and only on staging data.
- Use `--update_metadata_only=True` only for existing prepared datasets.

## Download, extraction, manual-data, and checksum failures

Symptoms:

- manual-download instructions or missing local source files;
- checksum mismatch or missing checksum entries;
- unexpected sharing of manual files across datasets;
- `--download_only=True` combined with checksum registration error.

Actions:

```bash
tfds --dry_run=True build my_dataset \
  --data_dir /tmp/tfds-build-data \
  --download_dir /tmp/tfds-downloads \
  --extract_dir /tmp/tfds-downloads/extracted \
  --manual_dir /tmp/tfds-manual \
  --add_name_to_manual_dir=True \
  --max_examples_per_split=1
```

- Place manually acquired files under the effective manual directory.
- Use `--register_checksums=True` only when intentionally generating checksum records.
- Use `--force_checksums_validation=True` only when checksum files are expected to be complete.
- Never combine `--download_only=True` with `--register_checksums=True`.

## Parallel builds and nondeterminism

Symptoms:

- resource exhaustion after setting `--num-processes`;
- different processing order across runs;
- faster Beam-like generation requested from a CLI command.

Actions:

- Keep `--num-processes=1` while debugging.
- Increase process count only after the command is bounded and output/download directories are isolated.
- Avoid `--nondeterministic_order=True` when reproducible example ordering matters.
- Route Beam runner options, Dataflow/Flink configuration, and cloud execution planning to `beam-and-performance`.

## `convert_format` mutates input directories

Symptoms:

- new shards appear beside existing shards;
- `dataset_info.json` changes to record an alternative file format;
- conversion skips because the target format already exists;
- multiple version dirs plus `--out_dir` fails.

Actions:

- For safe rehearsals, always set `--out_dir` for a single input:
  ```bash
  tfds --dry_run=True convert_format \
    --dataset_version_dir /tmp/tfds-data/my_dataset/1.0.0 \
    --out_file_format array_record \
    --out_dir /tmp/tfds-converted/my_dataset/1.0.0 \
    --num_workers=1
  ```
- If converting multiple `--dataset_version_dir` values, copy inputs first because `--out_dir` is not allowed and conversion is in-place.
- Use `--overwrite=True` only on disposable converted outputs.
- Inspect shard counts and metadata after conversion, especially when using `--only_log_errors=True`.

## Croissant JSON-LD and mapping issues

Symptoms:

- `build_croissant` import fails;
- mapping JSON parse error;
- record set not found;
- unexpected dataset version;
- output written to the wrong data directory.

Actions:

```bash
tfds --dry_run=True build_croissant \
  --jsonld /tmp/croissant.json \
  --data_dir /tmp/tfds-croissant-data \
  --file_format array_record \
  --record_sets records \
  --mapping '{"document.csv": "/tmp/manual/document.csv"}'
```

- Ensure the environment has Croissant support installed.
- Quote `--mapping` as valid JSON; keys should match Croissant `FileObject` names.
- If `--record_sets` is omitted, all record sets are generated.
- If the Croissant metadata lacks a version, TFDS uses `1.0.0`; set `--overwrite_version` only when that is intentional.
- Route Croissant data modeling and format decisions to `formats-and-community`.

## Publishing and credentials

Publishing with `--publish_dir` copies generated data to another root. Use a staging root for dry runs and prototypes. Cloud credentials, GCS access policy, release processes, and external service failures are outside this CLI-construction sub-skill; route cloud/performance questions to `beam-and-performance` or the project's release procedures.
