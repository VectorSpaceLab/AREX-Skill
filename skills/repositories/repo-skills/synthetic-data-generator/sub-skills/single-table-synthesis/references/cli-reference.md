# CLI reference

## Commands

`sdgx` exposes:

```text
fit
sample
list-models
list-data-connectors
list-data-processors
list-cachers
list-data-exporters
```

List commands are useful after installing extension packages.

## `sdgx fit`

Purpose: initialize or load a synthesizer, fit/continue training, and save the synthesizer directory.

Important options:

- `--save_dir TEXT` required output directory.
- `--model TEXT` required model name, usually `CTGAN`.
- `--model_path TEXT` path to model weights/state when loading a model by class/name.
- `--load_dir TEXT` load an existing synthesizer; overrides `model_path` if both are set.
- `--metadata_path TEXT` load metadata JSON.
- `--data_connector TEXT` and `--data_connector_kwargs TEXT` choose and configure a registered connector such as `csvconnector`.
- `--raw_data_loaders_kwargs TEXT` and `--processed_data_loaders_kwargs TEXT` are JSON strings for loader/cache kwargs.
- `--data_processors TEXT` comma-separated processor names.
- `--data_processors_kwargs TEXT` JSON mapping for processor kwargs.
- `--inspector_max_chunk INTEGER`, `--metadata_include_inspectors TEXT`, `--metadata_exclude_inspectors TEXT`, and `--inspector_init_kwargs TEXT` control metadata inference.
- `--model_fit_kwargs TEXT` JSON kwargs for `model.fit`.
- `--dry_run BOOLEAN` initializes without fitting/saving.
- `--json_output BOOLEAN` prints structured JSON success/failure.
- `--log_to_file BOOLEAN` enables log file handler.
- `--torchrun BOOLEAN` and `--torchrun_kwargs TEXT` launch through PyTorch `torchrun`.

Example:

```bash
sdgx fit \
  --save_dir model-dir \
  --model CTGAN \
  --model_kwargs '{"epochs":1,"batch_size":10,"device":"cpu"}' \
  --data_connector csvconnector \
  --data_connector_kwargs '{"path":"input.csv"}' \
  --raw_data_loaders_kwargs '{"cacher_kwargs":{"cache_dir":"cache/raw"}}' \
  --processed_data_loaders_kwargs '{"cacher_kwargs":{"cache_dir":"cache/processed"}}' \
  --json_output true
```

## `sdgx sample`

Purpose: load a synthesizer directory and export sampled data.

Important options:

- `--load_dir TEXT` required saved synthesizer directory.
- `--model TEXT` required model name/class name for load logic.
- `--count INTEGER` number of rows to sample.
- `--chunksize INTEGER` chunk size for large output.
- `--model_sample_args TEXT` JSON kwargs passed to model sampling.
- `--data_exporter TEXT` defaults to `CsvExporter`.
- `--data_exporter_kwargs TEXT` JSON kwargs for the exporter.
- `--export_dst TEXT` output path; defaults to a timestamped CSV path if omitted.
- `--dry_run BOOLEAN`, `--json_output BOOLEAN`, `--log_to_file BOOLEAN`, and `--torchrun` wrapper flags.

Example:

```bash
sdgx sample \
  --load_dir model-dir \
  --model CTGAN \
  --count 1000 \
  --chunksize 200 \
  --export_dst synthetic.csv \
  --json_output true
```

## JSON and boolean caveats

Click options are typed as strings/booleans, not repeated structured flags. Use valid JSON strings for nested options and pass boolean values explicitly as `true` or `false`.
