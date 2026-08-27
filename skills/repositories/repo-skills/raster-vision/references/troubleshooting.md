# Raster Vision troubleshooting

Use this cross-cutting reference before drilling into workflow-specific troubleshooting files.

## Install and import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: rastervision...` | Only one subpackage is installed, or the environment is not the one running the command | Run `python scripts/check_rastervision_install.py`; install `rastervision` or the missing plugin package in the active environment. |
| `rastervision` CLI is missing | `rastervision_pipeline` entry point is absent or scripts are not on `PATH` | Try `python -m rastervision.pipeline.cli --help`; reinstall `rastervision_pipeline` or activate the correct environment. |
| Rasterio/GDAL data errors | Geospatial wheels cannot find GDAL data | Prefer Docker or conda-forge geospatial packages; set `GDAL_DATA` only after confirming the installed rasterio/GDAL paths. |
| `rastervision.gdal_vsi` fails to import | Optional GDAL VSI plugin or `gdal==3.6.3` is missing | Install `rastervision_gdal_vsi` plus compatible GDAL, or avoid `/vsi...` URIs. |
| Albumentations or torch import warning/noise | Optional package update checks or CPU/GPU wheel mismatch | Disable update checks for noninteractive smoke tests; verify `torch.__version__`, `torch.version.cuda`, and `torch.cuda.is_available()` when GPU matters. |

## Config and data failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `get_config()` receives unexpected strings | `--arg` passes strings except boolean values converted by the CLI | Convert numeric/enumerated args inside `get_config()` and document expected values. |
| Scene build fails on labels | Missing `class_id`, wrong label source type, missing rasterization, or missing `ClassConfig` | Use `sub-skills/data-and-models/scripts/check_scene_config.py` on serialized scene JSON; inspect label-source choice. |
| `channel_order` errors | Band indices do not exist or the model bundle expects a different order | Check the raster band count and the bundle's training assumptions; override `--channel-order` only when the new imagery matches the expected semantics. |
| `RandomWindowGeoDataset` cannot sample | AOI/window size/negative-sampling constraints are too strict | Shrink `size`, relax AOIs, increase attempts, or use sliding sampling for debugging. |
| Output URI exists with incompatible files | Label stores or score files from a previous run conflict with current settings | Use a fresh `root_uri` or remove stale prediction/eval outputs after confirming they are not needed. |

## Runtime and backend failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Training is extremely slow | CPU-only torch or Docker missing GPU passthrough | Check torch CUDA and `nvidia-smi`; rerender Docker command with `--gpu` if using containers. |
| macOS dataloader crash/hang | Python multiprocessing issue with workers | Set `num_workers=0` in the PyTorch data config. |
| External model/loss download fails | `ExternalModuleConfig` uses GitHub/URI and needs network/cache access | Use built-in models for smoke tests; pre-stage external definitions or run with network access. |
| DDP/fork CUDA error | CUDA initialized before process fork or incompatible DDP start method | Use the default spawn path unless rasterio pickling issues force fork; avoid CUDA calls before worker startup. |
| Batch/SageMaker cannot access local files | Remote runners cannot see local paths | Use S3 or another remote filesystem for `root_uri`, raw data, processed data, and training roots. |

## Where to go next

- CLI/runners/config modules: `sub-skills/pipeline-cli/references/troubleshooting.md`.
- Scene/data/label/model-bundle APIs: `sub-skills/data-and-models/references/troubleshooting.md`.
- PyTorch task recipes and example-specific failures: `sub-skills/pytorch-workflows/references/troubleshooting.md`.
- Docker/AWS/S3/GDAL VSI setup: `sub-skills/cloud-and-filesystems/references/troubleshooting.md`.
