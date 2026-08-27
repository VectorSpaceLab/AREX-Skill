# Pipeline configuration

Raster Vision pipeline execution starts with a `PipelineConfig` object.
For the standard Raster Vision tasks, that object is usually an `RVPipelineConfig` subclass such as `SemanticSegmentationConfig`, `ObjectDetectionConfig`, or `ChipClassificationConfig`.

## Config module shape
A config module should expose one of these:
- `get_config(runner, **kwargs)`
- `get_configs(runner, **kwargs)`

The CLI passes the runner name as the first argument and forwards every `--arg KEY VALUE` pair as keyword arguments.

## Build/update flow
A normal `run` invocation follows this sequence:
1. load configs from a Python module, local `.py` file, or `.json` file
2. convert boolean `--arg` values from strings to Python `bool`
3. call `update()` on each config
4. validate and serialize the config to `pipeline-config.json`
5. call `build(tmp_dir)` to create the pipeline object
6. hand the pipeline and command list to the chosen runner

The generated helper script in this sub-skill follows the same update/build pattern but does not execute commands.

## Core pipeline fields
These fields matter most for CLI work:
- `root_uri`: experiment root
- `dataset`: train/validation/test scene config
- `backend`: ML backend config
- `analyzers`: optional analysis stage configs
- `evaluators`: optional evaluation stage configs
- `chip_options`: training chip settings
- `predict_options`: sliding-window prediction settings
- `source_bundle_uri`: optional pre-trained bundle for fine-tuning

## Derived output URIs
For `RVPipelineConfig`, `update()` fills in stage outputs when they are unset:
- `analyze_uri` → `<root_uri>/analyze`
- `chip_uri` → `<root_uri>/chip`
- `train_uri` → `<root_uri>/train`
- `predict_uri` → `<root_uri>/predict`
- `eval_uri` → `<root_uri>/eval`
- `bundle_uri` → `<root_uri>/bundle`

Related paths:
- `get_config_uri()` → `<root_uri>/pipeline-config.json`
- `get_model_bundle_uri()` → `<bundle_uri>/model-bundle.zip`

## Command categories
Raster Vision pipelines expose three command groupings:
- `commands`: the ordered command list for the pipeline
- `split_commands`: commands that can be partitioned across splits
- `gpu_commands`: commands that should prefer GPU-capable runners or resources

For standard Raster Vision pipelines, the command set is usually:
- `analyze`
- `chip`
- `train`
- `predict`
- `eval`
- `bundle`

If a pipeline has no analyzers, `analyze` is removed from the runnable command list.

Typical split-capable commands are `chip` and `predict`.
Typical GPU-aware commands are `train` and `predict`.
Backends may filter either list.

## Runner behavior
### `local`
- builds a Makefile in the output tree
- launches `make -j`
- fans out split commands as separate `run_command` invocations

### `inprocess`
- runs commands sequentially in one Python process
- good for debugging config or path issues

### `batch`
- submits AWS Batch jobs for each command
- uses array jobs for split commands
- routes GPU commands to GPU-capable Batch resources

### `sagemaker`
- creates a SageMaker Pipeline
- maps each command to a pipeline step
- expands split commands into parallel step branches

## Config patterns that matter
- Keep `root_uri` stable so derived URIs stay predictable.
- If your config branches on runner, inspect the runner name inside `get_config()` / `get_configs()`.
- If you emit multiple configs, each one gets its own pipeline output tree.
- If you set stage URIs explicitly, the defaults from `root_uri` are skipped for that field.

## Practical checklist
Before running a pipeline, verify:
1. the config loads
2. `root_uri` is correct
3. `commands` and `split_commands` are what you expect
4. `predict_options` matches the model bundle you intend to use
5. remote runners point at remote-readable URIs
