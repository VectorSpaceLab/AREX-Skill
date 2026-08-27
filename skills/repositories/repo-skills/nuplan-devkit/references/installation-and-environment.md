# Installation and environment

## When to read

Read this before importing nuPlan, running a Hydra entry point, or deciding
whether a missing dependency is relevant to the requested route.

## Compatibility point

The source package declares Python `>=3.9`, version `1.2.2`, and the
`nuplan_cli` console entry point. The source requirements split a base/runtime
set from a Torch/model set:

- Base data/planning dependencies include NumPy 1.23.4, GeoPandas/Fiona/
  Rasterio/Shapely, SQLAlchemy 1.4.27, Hydra 1.1.0rc1, Ray, Bokeh, Typer,
  SQLite helpers, and test utilities.
- Model dependencies include PyTorch 1.9.0 (+cu111 on Linux), torchvision
  0.10.0+cu111, torch-scatter 2.0.9, PyTorch Lightning 1.3.8, torchmetrics
  0.7.2, and TIMM. The exact wheel must match Python, platform, driver, and
  extension ABI.
- Submission dependencies are a smaller container-oriented set; Docker and
  gRPC are submission concerns, not prerequisites for geometry or local DB
  queries.

Prefer an isolated environment. Install only the route's needed dependency
variant; do not blindly combine all lock files or optional groups. For a source
checkout, an editable install is convenient during development, but the
runtime skill itself must not depend on that checkout remaining available.

## Data-root contract

Set explicit roots rather than relying on defaults:

```bash
export NUPLAN_DATA_ROOT="$HOME/nuplan/dataset"
export NUPLAN_MAPS_ROOT="$NUPLAN_DATA_ROOT/maps"
export NUPLAN_EXP_ROOT="$HOME/nuplan/exp"
export NUPLAN_MAP_VERSION="nuplan-maps-v1.0"
```

`NUPLAN_DATA_ROOT` should contain `nuplan-v1.1/splits/mini` or another selected
split and, for sensor workflows, `nuplan-v1.1/sensor_blobs`. `NUPLAN_MAPS_ROOT`
contains `<map-version>.json` plus location/version `map.gpkg` files. The
experiment root must be writable; dataset and maps can be read-only.

Run the bundled data validator before a data-backed command. It is local-only,
read-only, and returns nonzero for missing required layout. A missing dataset is
not repaired by changing the map version or switching to another split.

## Backend decisions

CPU is sufficient for state, geometry, DB, map-layer, configuration, mock
scenario, and most metric checks. CUDA is optional for model/training paths.
An observed compatibility environment used PyTorch 1.9.0+cu111 on an NVIDIA
A100, but that is not a universal hardware guarantee. Verify:

```bash
python -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available())"
```

A CPU import does not prove CUDA behavior or training performance. If a model
workflow needs CUDA extensions, match the Torch and CUDA tags before installing
extensions. If the package's old pins conflict with a newer interpreter or
wheel, preserve the documented version boundary instead of silently upgrading
Hydra/Torch and claiming compatibility.

## Safe gates

1. `python -c "import nuplan"` and `python -m pip check` pass.
2. `nuplan_cli --help` and `nuplan_cli db --help` pass without a dataset.
3. The route's bundled validator passes `--help` and a tiny valid/invalid case.
4. A data-backed route verifies roots before opening DBs or maps.
5. A training route validates YAML before model construction and starts with
   sequential workers, a tiny filter, and FP32.
6. A simulation route validates config paths and overrides before launching.
7. Submission preflight remains static until Docker, data, and credentials are
   explicitly available.

Never include credentials, private cache paths, environment activation names,
or machine-specific interpreter paths in a generated command or report.
