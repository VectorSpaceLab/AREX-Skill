# Troubleshooting

This page covers the cross-cutting RoboSat failures that tend to block multiple workflows.

## Install and import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError` for `robosat` | Package not installed in the active environment, or import is resolving the wrong checkout. | Install the package into the active environment and rerun `python -c "import robosat"`. |
| `Could not find libspatialindex_c library file` | `rtree` is installed but the native `libspatialindex` library is missing. | Install `libspatialindex` in the same environment or OS prefix, then rerun the CLI check. |
| `Invalid projection: esri:54009 ... crs not found` | The environment has an incompatible pyproj/PROJ combination or missing CRS database support. | Use a pyproj 2.x/PROJ-data combination that resolves `ESRI:54009`; pyproj 2.6.x worked in the verified inspection environment. |
| `ImportError` from `torch` or `torchvision` | Old torch wheels not installed, or the environment uses an unsupported Python build. | Install the historical CPU wheel pair for Python 3.6 or a compatible torch/torchvision combination before using model commands. |

## CLI and config mistakes

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `rs train` exits because CUDA is unavailable | `model.common.cuda = true` but the environment has only CPU torch or no supported GPU backend. | Set `cuda = false` for CPU work, or install and verify a compatible CUDA torch build before rerunning. |
| `Error: The loss function used, need dataset weights values` | Dataset TOML uses `CrossEntropy`, `mIoU`, or `Focal` without `[weights].values`. | Run `rs weights --dataset dataset.toml` and copy the printed list into the dataset TOML. |
| `image resolution has to be divisible by 32 for resnet` | `model.common.image_size` is not a multiple of 32. | Adjust the tile size / resize setting to a multiple of 32. |
| `same number of tiles in all images` or tile mismatch assertions | Image and label Slippy Map trees are out of sync. | Run `scripts/validate_slippy_map.py` and `scripts/check_training_layout.py`, then fix the missing or extra tiles. |
| Empty or tiny batches during training | `batch_size` is larger than the split or `drop_last=True` removes too many tiles. | Use `scripts/check_training_layout.py --batch-size ... --drop-last` to estimate the risk, then lower batch size or enlarge the split. |

## Data and geometry problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `rs rasterize` produces empty masks | Feature GeoJSON does not overlap the tile set, the zoom is wrong, or the dataset colors/classes do not match the expected binary layout. | Check `--zoom`, the tile CSV, and the `dataset.toml` class/color order. |
| `rs features --type parking` produces nothing | The mask class index does not match the `parking` class, or the segmentation mask is empty. | Confirm the dataset class order and the probability/mask conversion step. |
| `rs merge` returns invalid or skipped polygons | Input shapes are self-intersecting or the buffer/merge threshold is too aggressive. | Reduce the threshold or inspect the mask source before merging. |
| `rs dedupe` keeps too many predictions or removes too many | The IoU threshold does not match the desired deduplication strictness. | Remember that `--threshold` is IoU, not distance. |

## Network and credential problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `rs download` fails or stalls | Tile endpoint is unreachable, rate limited, or the URL template is wrong. | Verify the `{z}`, `{x}`, and `{y}` placeholders, reduce the rate, or test the endpoint separately. |
| `rs serve` exits asking for a map token | `MAPBOX_ACCESS_TOKEN` is missing. | Export the token in the environment before starting the server, or use batch prediction instead of the demo tile server. |
| Serving or download behavior is inconsistent | Network access is unavailable or filtered. | Keep the command generic in the skill and do not use network-backed smoke tests without an explicit endpoint and token policy. |

## CPU/CUDA strategy

- Use CPU for the smallest reliable environment-inspection and smoke path.
- Treat CUDA as optional unless the task explicitly needs GPU training, prediction, or serving.
- Do not claim GPU verification unless `torch.cuda.is_available()` and a tiny device operation have passed in the target environment.
- If the legacy torch wheel family does not support the current GPU architecture, document that as a backend limitation rather than downgrading it silently.

## Good first checks

1. `python scripts/check_robosat_env.py --check-cli`
2. `python sub-skills/model-lifecycle/scripts/unet_cpu_smoke.py`
3. `python sub-skills/data-preparation/scripts/validate_slippy_map.py <slippy-root> --tiles-csv <tiles.csv>`
4. `python sub-skills/feature-postprocessing/scripts/validate_feature_collection.py <geojson>`

If these pass, move on to the workflow-specific sub-skill reference for the exact command sequence.
