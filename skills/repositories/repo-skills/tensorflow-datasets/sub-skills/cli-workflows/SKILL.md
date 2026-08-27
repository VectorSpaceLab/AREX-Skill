---
name: cli-workflows
description: "Construct and debug safe TensorFlow Datasets CLI commands for
  build, new, convert_format, and build_croissant workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# TensorFlow Datasets CLI workflows

Use this sub-skill when the task is to assemble, inspect, or debug `tfds` command lines for TensorFlow Datasets. It covers the `build`, `new`, `convert_format`, and `build_croissant` commands, with safe defaults for dry runs, temporary data locations, reduced example counts, and conversion/publishing safeguards.

## Operating protocol

1. **Start with parser inspection.** Prefer `tfds --help`, `tfds --version`, and `tfds <command> --help`, or run [`scripts/tfds_cli_reference.py`](scripts/tfds_cli_reference.py) to confirm the installed entry point and expected flags.
2. **Make side effects explicit.** Put global `--dry_run=True` before the subcommand while designing a command. Use explicit `--data_dir` for builds and Croissant output. Use explicit `--out_dir` for format conversion unless intentionally mutating an existing prepared dataset directory.
3. **Prototype before full work.** For `tfds build`, start with `--max_examples_per_split=1` or `0`; only remove it after paths, imports, configs, checksums, and optional dependencies are known.
4. **Keep generated artifacts isolated.** Use safe temporary or staging directories for `--data_dir`, `--download_dir`, `--extract_dir`, `--manual_dir`, `--publish_dir`, and conversion `--out_dir` until the command is proven.
5. **Check option interactions.** Do not combine incompatible or ambiguous selectors/flags: e.g. `--download_only=True` with `--register_checksums=True`; config in both `dataset/config` and `--config`; multiple `--dataset_version_dir` values with `--out_dir`.
6. **Escalate out-of-scope details.** Authoring builder code belongs to `dataset-authoring`; Beam runner semantics and Dataflow/Flink tuning to `beam-and-performance`; Croissant data modeling and community catalog details to `formats-and-community`; loading existing datasets in Python to `data-loading`.

## Command families at a glance

- **Top level:** `tfds [--version] [--dry_run=True] {build,new,convert_format,build_croissant} ...`. `--dry_run` is a top-level flag, so place it before the subcommand.
- **`tfds new`:** creates a dataset skeleton in `--dir`; it writes files and fails if the target dataset directory already exists. Data format templates are `standard`, `conll`, and `conllu`.
- **`tfds build`:** prepares datasets from registered names, imported modules, local dataset folders, or local dataset builder scripts. Critical safety flags are `--data_dir`, `--max_examples_per_split`, `--download_dir`, `--extract_dir`, `--manual_dir`, `--config`/`--config_idx`, `--imports`, `--file_format`, shard controls, and publishing/checksum options.
- **`tfds convert_format`:** converts prepared dataset shards to `tfrecord`, `riegeli`, `array_record`, or `parquet`. It can mutate the input dataset directory when `--out_dir` is omitted; use staging copies and explicit output directories for safety.
- **`tfds build_croissant`:** builds TFDS data from Croissant JSON-LD. Provide explicit `--jsonld`, `--data_dir`, optional `--record_sets`, JSON `--mapping`, and version/publish flags only after validating the metadata and files.

## Bundled references and scripts

- [`references/cli-reference.md`](references/cli-reference.md): distilled CLI layout, selectors, flags, side effects, and option interactions.
- [`references/build-command-recipes.md`](references/build-command-recipes.md): safe command recipes and staged workflows for build, conversion, Croissant, and skeleton creation.
- [`references/troubleshooting.md`](references/troubleshooting.md): error triage for CLI discovery, dataset lookup, configs, paths, checksums, conversions, Croissant mapping, and optional dependencies.
- [`scripts/build_command_helper.py`](scripts/build_command_helper.py): assembles safe `tfds build` commands without executing them.
- [`scripts/tfds_cli_reference.py`](scripts/tfds_cli_reference.py): checks the installed `tfds` entry point, version, help pages, and key command flags.

## Evidence distilled

The operating facts in this sub-skill are distilled from the TFDS CLI documentation notebook, the installed CLI help/version output for TensorFlow Datasets `4.9.10+nightly`, and source/test behavior for the command parser, `build`, `new`, `convert_format`, Croissant build, and CLI utilities. The inspection environment proved CPU CLI import/help checks with TensorFlow, Beam, and Croissant dependencies installed; do not assume every downstream user already has those optional packages unless their command path needs them.
