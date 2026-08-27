# Troubleshooting

Use this reference when a Raster Vision pipeline config, URI, or bundle does not behave as expected.

## Fast triage
1. Run [scripts/summarize_pipeline_config.py](../scripts/summarize_pipeline_config.py) against the config.
2. Confirm `root_uri`, derived output URIs, and command lists.
3. Confirm the runner matches the target environment.
4. Confirm every URI in the pipeline is readable by the same file-system layer you will use at runtime.

## Config loading errors
### `There must be a get_config() or get_configs() function`
Cause:
- the module path is wrong, or the module does not expose the expected function

Fix:
- add `get_config()` or `get_configs()`
- pass the correct `.py` file path or import path

### `All objects returned by get_configs ... must be PipelineConfigs`
Cause:
- the function returned a plain object or a non-pipeline config

Fix:
- return only `PipelineConfig` / `RVPipelineConfig` instances
- if you need helper objects, keep them inside the config builder

### `--arg` values look like strings
Cause:
- CLI arguments arrive as strings unless they are `true` / `false`

Fix:
- convert inside `get_config()` / `get_configs()`
- use lowercase `true` / `false` for booleans

## Output URI errors
### `root_uri` is missing or derived URIs fail to build
Cause:
- the config never set `root_uri`
- or some stage URI is unset and cannot be derived

Fix:
- set `root_uri`
- or explicitly set every stage URI you need
- re-run the config summary helper before launching the pipeline

### Unexpected output paths
Cause:
- explicit stage URIs override the `root_uri` defaults

Fix:
- check `analyze_uri`, `chip_uri`, `train_uri`, `predict_uri`, `eval_uri`, and `bundle_uri`
- inspect the serialized config, not just the config module

## Runner and split issues
### `--splits` does nothing
Cause:
- the chosen command is not in `split_commands`
- or the runner/backend filters it out

Fix:
- check the pipeline's `split_commands`
- verify the command signature accepts `split_ind` and `num_splits`
- use `inprocess` or `local` to confirm the split logic first

### `run_command` split index problems
Cause:
- `split-ind` was not passed, or the runner does not implement split discovery

Fix:
- pass `--split-ind` explicitly when needed
- confirm your custom runner implements `get_split_ind()` if it depends on environment routing

### `local` runner fails on `make`
Cause:
- GNU make is missing, or the shell environment cannot launch the generated Makefile

Fix:
- install make
- try `inprocess` to isolate the config from the runner
- inspect the generated Makefile next to `pipeline-config.json`

## Prediction and bundle issues
### `predict` cannot read the bundle or image
Cause:
- URI scheme mismatch
- file-system plugin missing
- bundle or image path not accessible in the current environment

Fix:
- confirm the URI scheme is supported by Raster Vision in this runtime
- use local/HTTP/S3/GDAL-VSI paths consistently
- make sure the bundle and image are both reachable

### Channel-order errors
Cause:
- the image band order differs from the bundle's training-time expectation

Fix:
- pass `--channel-order`
- verify the order against the source imagery

### StatsTransformer or scene-group warnings
Cause:
- the bundle contains stats for a different scene group

Fix:
- use `--scene-group`
- or rebuild the bundle with the intended stats

### `predict_scene` fails on a `SceneConfig`
Cause:
- the serialized scene config does not match the bundle expectations

Fix:
- confirm the `SceneConfig` contains the correct raster source and label store URIs
- use `predict` first if you only need one image and one output label path

## Remote runner URI issues
### Batch or SageMaker jobs cannot find local paths
Cause:
- remote runners cannot see your workstation file system

Fix:
- move inputs and outputs to remote-readable URIs such as S3
- keep local paths for local or in-process runs only

## Bundle regeneration issues
### Bundle exists but inference still fails
Cause:
- the bundle was produced from stale training artifacts or an older config shape

Fix:
- regenerate the bundle from the matching training output
- ensure the config upgrader path still matches the installed package versions

## Good debugging order
When a pipeline fails, debug in this order:
1. config load
2. config update and derived output URIs
3. runner choice
4. split behavior
5. model bundle contents
6. image or scene URI accessibility
