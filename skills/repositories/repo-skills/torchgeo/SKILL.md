---
name: torchgeo
description: "Use for TorchGeo geospatial deep learning work: datasets,
  samplers, data modules, transforms, pre-trained models, Lightning tasks, and
  contribution/testing workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# TorchGeo

Use this repo skill when working with the `torchgeo` Python package, a PyTorch domain library for geospatial and remote-sensing machine learning. The skill is grounded in the TorchGeo repository at commit `51a30d67f28794090f88a59b91deeadf91de1878` and is intended for later Researcher sessions; do not assume the original checkout is available.

## Route by task

- Dataset composition, `GeoDataset`/`NonGeoDataset`, raster/vector IO, sample dictionaries, collate functions, patch samplers, ROI/TOI selection, or fake dataset fixtures: read [datasets-and-samplers](sub-skills/datasets-and-samplers/SKILL.md).
- Lightning `DataModule` usage, `torchgeo` CLI/JSONArgParse configs, task classes for classification, segmentation, detection, regression, self-supervised learning, or batch augmentation handoff: read [datamodules-and-tasks](sub-skills/datamodules-and-tasks/SKILL.md).
- Pre-trained models, weight enums, `get_model`, `get_weight`, `list_models`, timm/SMP integration, spectral indices, SAR/color/spatial/temporal transforms, or optional model dependencies: read [models-and-transforms](sub-skills/models-and-transforms/SKILL.md).
- Adding or modifying TorchGeo code, dataset tests, docs tables, style/type checks, fake data generation, or project conventions: read [contribution-and-testing](sub-skills/contribution-and-testing/SKILL.md).

## High-signal operating facts

- TorchGeo has two dataset families:
  - `GeoDataset` instances are indexed by spatiotemporal slices and can be composed with `&` for intersection and `|` for union.
  - `NonGeoDataset` instances behave like torchvision-style benchmark datasets and are indexed by integer sample id.
- Dataset samples are dictionaries. Common keys are `image`, `mask`, `label`, `bbox_xyxy`, metadata keys such as `crs`/`bounds`, and task-specific keys. Do not assume a fixed schema without reading the dataset class or test fixture.
- Use `stack_samples` for geospatial sample dictionaries and task-specific collate helpers such as detection collation where the datamodule/test uses them.
- Patch samplers yield `GeoSlice` windows; `RandomPatchSampler` is for stochastic training chips and `Grid`/`GriddedPatchSampler` style samplers are for deterministic tiling/evaluation.
- The `torchgeo` command line entry point is backed by `torchgeo.main:main` and Lightning/JSONArgParse. Prefer a config file for reproducible task/datamodule/trainer runs.
- Most practical workflows require geospatial dependencies (`rasterio`, `pyproj`, `shapely`, `geopandas`) and ML dependencies (`torch`, `torchvision`, `lightning`, `kornia`, `timm`, `segmentation-models-pytorch`). Optional dataset/model extras are not always installed.
- Avoid downloads/network in routine tests unless the test is explicitly marked slow. The repository uses small generated fake fixtures under `tests/data/<dataset>/`.

## Bundled references and scripts

- [Repo provenance](references/repo-provenance.md)
- [Troubleshooting](references/troubleshooting.md)
- [Backend and environment plan](references/backend-verification-plan.md)
- [Router metadata](references/repo-routing-metadata.json)
- [`scripts/probe_torchgeo_install.py`](scripts/probe_torchgeo_install.py): inspect an installed TorchGeo environment without downloading data.
- [`scripts/minimal_geodataset_smoke.py`](scripts/minimal_geodataset_smoke.py): create a tiny in-memory `GeoDataset`/sampler smoke check when dependencies are installed.
