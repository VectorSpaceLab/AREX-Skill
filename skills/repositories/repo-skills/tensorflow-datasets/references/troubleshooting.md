# TensorFlow Datasets Troubleshooting

Use this root troubleshooting page for install/import, optional dependency, environment, and cross-workflow failures. For workflow-specific failures, route to the nearest sub-skill troubleshooting reference.

## First triage

1. Identify whether the task is loading, authoring/testing, CLI, external/community formats, or Beam/performance.
2. Run a non-mutating environment check:
   ```bash
   python scripts/check_tfds_environment.py --check-cli
   ```
3. Avoid full downloads, conversions, publishes, Dataflow/Flink jobs, or credentialed GCS operations until paths and optional dependencies are explicit.
4. If a command uses `tfds build`, start with an explicit staging `--data_dir` and `--max_examples_per_split=1` or `0`.
5. If a Python call uses `tfds.load`, remember that `download=True` is the default; use `tfds.builder` or `download=False` for metadata-first inspection.

## Common install/import failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: tensorflow_datasets` | Package not installed in the active environment. | Install `tensorflow-datasets` or `tfds-nightly`, then rerun `python -c "import tensorflow_datasets as tfds; print(tfds.__version__)"`. |
| `tfds` command missing | Console script not on `PATH` or package installed in a different environment. | Run `python -m pip show tensorflow-datasets`; activate the intended environment or call the environment's `tfds` executable. |
| `tfds --help` raises `ModuleNotFoundError` for `tensorflow`, `apache_beam`, or `mlcroissant` | Selected TFDS CLI modules import optional dependencies for TensorFlow-backed, Beam conversion, or Croissant paths. | Install only the dependency needed by the selected workflow: TensorFlow for `tf.data`/general CLI use, Beam for Beam/conversion paths, `mlcroissant` for Croissant. Use `scripts/check_tfds_environment.py --check-cli --json` to confirm. |
| Protobuf version conflict after adding TensorFlow/Beam | TensorFlow, Beam, TensorFlow Metadata, and generated proto packages require compatible protobuf ranges. | Prefer a consistent modern set; rerun `python -m pip check`. If a workflow does not need Beam or TensorFlow, remove the unnecessary extra instead of forcing broad installs. |
| Import succeeds without TensorFlow but a loading/CLI path fails later | TFDS supports some TensorFlow-less imports, but practical `tf.data`, conversion, visualization, and several CLI paths need optional deps. | Route to the sub-skill that owns the workflow and install the smallest documented extra for that path. |

## Optional dependency and dataset-specific failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| Dataset builder import fails for `pydub`, `Pillow`, `scipy`, `pandas`, `gcld3`, `tensorflow_io`, `envlogger`, or similar | The selected dataset has a dataset-specific extra. | Inspect the dataset's documented extra or setup metadata and install only that extra/dependency. Do not install every dataset extra by default. |
| Audio builder errors mention ffmpeg | Some audio datasets need both Python packages and a system `ffmpeg` binary. | Confirm `ffmpeg -version`; if absent, ask before host-level installation. |
| HuggingFace/community dataset import fails for `datasets` | HuggingFace wrapper dependency missing. | Install the HuggingFace extra/dependency only for that workflow and route to `formats-and-community`. |
| Beam/Dataflow workers fail after local command parses | Worker environment lacks packages, files, credentials, or options available locally. | Route to `beam-and-performance`; package worker requirements explicitly and validate `--beam_pipeline_options` before launch. |

## Download, data directory, and cloud failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `DatasetNotFoundError` or unexpected dataset version | Name/config/version mismatch or a newer TFDS release is required. | Inspect `tfds.list_builders()` and builder names/configs. Use exact `name/config:version` when needed. |
| Manual download instructions appear | Dataset license/source requires the user to download files manually. | Do not bypass the instruction; place files in `manual_dir` and pass it through `DownloadConfig` or CLI `--manual_dir`. |
| `NonMatchingChecksumError` | Upstream file changed, wrong manual file, stale checksum, or interrupted download. | Verify the source file and manual path. For authoring, register/update checksums only after confirming the intended source artifact. |
| GCS authentication warnings during local inspection | TFDS may probe public GCS or cloud metadata; credentials are not always required. | Ignore if local metadata succeeds and the task does not need private GCS. Configure credentials only for user-approved private/cloud operations. |
| Prepared dataset exists but `tfds.load` cannot read it | Wrong `data_dir`, wrong config/version/file format, incomplete metadata, or stale split info. | Use `data-loading/scripts/tfds_inspect_dataset.py` and route external layout issues to `formats-and-community`. |

## Routing after triage

- `sub-skills/data-loading/references/troubleshooting.md`: `tfds.load`, splits, metadata, decoding, `as_numpy`, GCS read checks, manual download and checksum load errors.
- `sub-skills/dataset-authoring/references/troubleshooting.md`: skeletons, builder registration, dummy data, feature schemas, checksums, dataset collections.
- `sub-skills/cli-workflows/references/troubleshooting.md`: `tfds` parser behavior, command construction, conversion/publish mutation safeguards, Croissant CLI options.
- `sub-skills/formats-and-community/references/troubleshooting.md`: external TFRecord metadata, `builder_from_directory`, folder datasets, community namespaces, HuggingFace, Croissant layout issues.
- `sub-skills/beam-and-performance/references/troubleshooting.md`: Beam runner options, Dataflow/Flink/GCS, sharding, file formats, high RAM, throughput, and worker dependency issues.
