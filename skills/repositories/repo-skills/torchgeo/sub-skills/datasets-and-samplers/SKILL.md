---
name: datasets-and-samplers
description: "Use for TorchGeo GeoDataset/NonGeoDataset usage, dataset
  composition, raster/vector dataset implementation, sample dictionaries,
  collate functions, and patch samplers."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# TorchGeo datasets and samplers

Use this sub-skill for dataset selection, custom dataset implementation, geospatial composition, patch sampling, data loader collation, and dataset tests.

## Choose the dataset family

- Use `GeoDataset` when samples are queried by geospatial extent/time and the dataset has CRS/resolution/geometry metadata. These datasets support spatial/temporal indexing and composition.
- Use `NonGeoDataset` for torchvision-style benchmark datasets indexed by integer sample id and usually stored under a `root` directory.
- Raster-like geospatial datasets should normally subclass TorchGeo raster/vector helpers rather than manually reimplementing file indexing. Confirm the expected base class in the adjacent dataset source and tests before editing.

## Compose geospatial datasets

- `dataset_a & dataset_b` creates an `IntersectionDataset`: every query must be available in both datasets. Use this for image + mask/label/elevation/data-fusion workflows.
- `dataset_a | dataset_b` creates a `UnionDataset`: a query may be satisfied by either dataset. Use this for alternate sensors or adjacent regions.
- Composition is meaningful only when the participating indexes share compatible CRS/resolution/time assumptions. If outputs look empty, inspect bounds, CRS, resolution, and time interval overlap.

## Sample dictionary expectations

Common keys:

- `image`: tensor shaped like `(C, H, W)` for a single sample or batched by a collate function.
- `mask`: semantic/change/instance segmentation target.
- `label`: classification/regression target.
- `bbox_xyxy`: object detection boxes in xyxy format.
- metadata keys such as `crs`, `bounds`, dates, filenames, or dataset-specific attributes.

Always read the dataset test fixture before assuming keys. Use `stack_samples` for ordinary tensor dictionaries; use detection-specific collate helpers when boxes/masks are variable length.

## Sampler selection

- Use `RandomPatchSampler(dataset, size=..., length=...)` for stochastic training chips from a `GeoDataset`.
- Use gridded samplers for deterministic tiling, validation, or prediction over a region.
- Use batch samplers when the sampler should yield lists of geospatial windows directly.
- Pass `roi` for a spatial region of interest and `toi` for a time interval of interest. Verify that ROI and TOI intersect `dataset.index`.
- Check the `units` argument where available: pixel units are converted using dataset resolution, while CRS units are already in projected units.

## Dataset implementation checklist

1. Add or update the dataset class in `torchgeo/datasets/<name>.py` with the TorchGeo license header.
2. Choose `GeoDataset`, `NonGeoDataset`, raster, or vector base class based on indexing semantics.
3. Keep `root='data'` default when adding a new dataset unless an existing nearby class uses a different convention.
4. Implement `_verify()`/download/checksum behavior consistently with adjacent datasets.
5. Return a sample dictionary with documented keys and stable tensor shapes.
6. Add import/export wiring in `torchgeo/datasets/__init__.py`.
7. Add fake fixture generation under `tests/data/<dataset>/` and a focused `tests/datasets/test_<dataset>.py` with plot/download/checksum/error coverage as applicable.
8. Update docs tables and RST pages when the public dataset catalog changes.

## Read next

- [reference](references/datasets-and-samplers.md) for deeper API facts and failure modes.
- Root [troubleshooting](../../references/troubleshooting.md) for install and dependency issues.
