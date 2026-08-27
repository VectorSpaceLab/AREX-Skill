# CLI reference

This sub-skill covers the Raster Vision `rastervision` CLI for pipeline execution and prediction.

## Entry points
- `rastervision` is the user-facing CLI.
- It maps to `python -m rastervision.pipeline.cli` when run from source or inside a package environment.

## Top-level options
- `-p, --profile`: select an Everett profile.
- `-v, --verbose`: increase verbosity.
- `--tmpdir`: set the root temporary directory used by Raster Vision.

## `run`

Run one or more pipeline commands from a config module or JSON file.

```bash
rastervision run RUNNER CFG_MODULE [COMMANDS...]
```

### Arguments
- `RUNNER`: `local`, `inprocess`, `batch`, or `sagemaker`.
- `CFG_MODULE`: a Python module path, a local `.py` file, or a `.json` config file.
- `COMMANDS`: optional command names in pipeline order. If omitted, all commands run.

### Options
- `-a, --arg KEY VALUE`: pass arguments into `get_config()` / `get_configs()`.
- `-s, --splits N`: split splittable commands into `N` parallel parts.
- `--pipeline-run-name NAME`: label the run.

### Notes
- The config builder receives `runner` as its first argument.
- Boolean strings are converted by the CLI layer: `true` → `True`, `false` → `False`.
- `--arg` values otherwise arrive as strings; convert numbers or enums inside your config builder.
- `get_config(runner, **kwargs)` may return a single config.
- `get_configs(runner, **kwargs)` may return a list of configs for parallel runs.

### Examples
```bash
rastervision run local tiny_spacenet.py
rastervision run inprocess tiny_spacenet.py -a use_gpu true -s 4
rastervision run batch tiny_spacenet.py -a root_uri s3://bucket/experiment/
```

## `run_command`

Run one command from a serialized `pipeline-config.json`.

```bash
rastervision run_command CFG_JSON_URI COMMAND
```

### Options
- `--split-ind`: split index for a splittable command.
- `--num-splits`: total number of splits.
- `--runner`: runner name used to determine split routing when needed.

### Notes
- This is the low-level entry point used by custom runners.
- `local` uses it from a generated Makefile.
- `batch` and `sagemaker` use it inside remote jobs or steps.

## `predict`

Predict on one image using a model bundle.

```bash
rastervision predict MODEL_BUNDLE IMAGE_URI LABEL_URI
```

### Options
- `-a, --update-stats`: recompute stats for this image before prediction.
- `--channel-order`: override the channel order used by the bundle.
- `--scene-group`: choose the stats group used by `StatsTransformer`.

### Notes
- `LABEL_URI` is the output location for predicted labels.
- `IMAGE_URI` and `MODEL_BUNDLE` can be local, HTTP, S3, or other supported file-system URIs.
- `--channel-order` takes a space-separated list of band indices.

## `predict_scene`

Predict on a scene config using a model bundle.

```bash
rastervision predict_scene MODEL_BUNDLE_URI SCENE_CONFIG_URI
```

### Options
- `--predict_options_uri`: optional serialized `PredictOptions` config.

### Notes
- Use this when you already have a serialized `SceneConfig`.
- This path is the cleanest way to override sliding-window prediction settings for a single scene.

## Runner routing at a glance
- `local`: builds a Makefile and runs commands on the host with `make -j`.
- `inprocess`: runs each command sequentially in one process.
- `batch`: submits a DAG of AWS Batch jobs, including split array jobs.
- `sagemaker`: maps commands to SageMaker pipeline steps.
