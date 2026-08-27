# Backend and environment verification plan

## Dependency surfaces

TorchGeo is CPU-first for most dataset, sampler, transform, model-construction, and Lightning-task smoke checks, but it depends on geospatial and ML packages that are not part of the Python standard library.

Core runtime dependencies from `pyproject.toml` include:

- Geospatial/data: `geopandas`, `pyogrio`, `pyproj`, `rasterio`, `shapely`, `pandas`, `numpy`, `pillow`, `requests`, `tqdm`.
- ML/training: `torch`, `torchvision`, `lightning`, `kornia`, `timm`, `segmentation-models-pytorch`, `torchmetrics`, `einops`, `lightly`.
- Optional dataset extras: `h5py`, `laspy`, `netcdf4`, `rioxarray`, `scipy`, `tokenizers`, `webdataset`, `xarray`.
- Optional model extras: `microsoft-aurora`, `olmoearth-pretrain-minimal`.

## Minimum verification target

For routine Researcher use and code changes, prepare a Python `>=3.12` environment with an editable TorchGeo install and the core runtime dependencies. CPU is sufficient for:

- importing `torchgeo.datasets`, `torchgeo.samplers`, `torchgeo.datamodules`, `torchgeo.transforms`, `torchgeo.models`, and `torchgeo.tasks`;
- constructing lightweight dataset/sampler/task/model objects without downloads;
- running targeted unit tests that use fake fixtures and are not marked slow.

CUDA/MPS/ROCm are optional accelerators for training throughput. They are not required to validate API wiring unless a task explicitly claims accelerator-specific behavior.

## Commands for a future verifier

```bash
python -m pip install -e ".[all]"
python skills/disco/torchgeo/scripts/probe_torchgeo_install.py
python skills/disco/torchgeo/scripts/minimal_geodataset_smoke.py
pytest tests/datasets/test_geo.py tests/samplers/test_single.py tests/samplers/test_batch.py -q
pytest tests/models/test_api.py tests/transforms/test_indices.py -q
pytest tests/tasks/test_segmentation.py::TestSemanticSegmentation::test_trainer -q
```

Adjust the final task test to a current test id if the test file changes. Do not run slow downloads unless the user approves network access.

## Distillation-time environment result

A full editable install was not completed during this fallback recovery. The ambient interpreter had `torch` and `geopandas`, but failed imports for `torchgeo` package metadata, `rasterio`, `lightning`, `kornia`, `segmentation_models_pytorch`, and `timm`. The generated skill therefore carries a `PARTIAL_ENV_VERIFICATION` limitation and should be re-verified in a prepared TorchGeo environment before import into the managed repo-skill library.
