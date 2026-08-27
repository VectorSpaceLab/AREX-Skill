# TorchGeo troubleshooting

## Import and installation

- `PackageNotFoundError: No package metadata was found for torchgeo` usually means the source tree is on `PYTHONPATH` but the package was not installed. Use an editable install (`python -m pip install -e .`) in a Python version satisfying `pyproject.toml`.
- Missing `rasterio`, `pyproj`, `shapely`, `geopandas`, or `pyogrio` blocks geospatial datasets even if pure-PyTorch code imports. Install the core package dependencies rather than only `torch`.
- Missing `lightning`, `kornia`, `timm`, `segmentation_models_pytorch`, or `torchmetrics` blocks datamodules/tasks/models. For broad development, install the package extras used by the repo tests.
- Many model weight constructors download checkpoints when `weights` are requested. Use `weights=None` or a tiny local smoke before relying on network/cache.

## Dataset and data layout

- `DatasetNotFoundError` means the dataset-specific expected files were not found under the configured `root`/`paths`. Re-open the dataset class and its corresponding `tests/datasets/test_<name>.py` fixture to confirm exact filenames and split files.
- Do not assume every dataset returns the same keys. Classification commonly returns `image` and `label`; segmentation returns `image` and `mask`; detection may return boxes/labels/masks; geospatial datasets may include CRS/bounds metadata.
- For GeoDatasets, the index is spatial/temporal. Query with a complete enough spatiotemporal slice or use a TorchGeo sampler instead of integer indices.
- Use `&` only when every query must exist in both datasets. Use `|` when either dataset may satisfy the query.

## Samplers and chip sizes

- `RandomPatchSampler`/batch samplers expect chips that fit inside indexed geometries. If iteration is empty or errors, check dataset bounds, resolution, `roi`, `toi`, and whether `size` is in pixels or CRS units.
- Prefer gridded samplers for evaluation/tiling. Use overlap/stride intentionally to avoid stitching artifacts in dense prediction.
- Keep ROI/TOI in the same coordinate/time assumptions as the dataset index.

## Lightning tasks and transforms

- Kornia augmentations operate on batched tensors; masks often need channel handling and dtype preservation. Inspect the task/datamodule test when adding a transform to a mask-bearing workflow.
- `SemanticSegmentation` supports SMP backbones for most models, but the TorchGeo `FCN` path is separate and does not support pretrained weights.
- If a pretrained TorchGeo weight enum is passed by string, use `get_weight` and check that the string exactly matches an enum value.
- For multispectral imagery, set `in_channels` and band ordering deliberately. RGB plotting utilities may raise `RGBBandsMissingError` when no RGB-compatible band set exists.

## Testing and contribution work

- Use targeted tests first, for example `pytest tests/datasets/test_<dataset>.py -q`. The project default skips `slow` tests and disables sockets.
- Fake data belongs under `tests/data/<dataset>/` and should be generated or minimal, never copied from real datasets.
- New public files need the TorchGeo copyright/license header and Google-style docstrings.
- Update API docs and dataset CSV tables when adding a dataset or datamodule.
