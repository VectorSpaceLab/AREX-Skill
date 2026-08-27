# Datasets and samplers reference

## Evidence-backed API facts

- `GeoDataset.__getitem__` consumes a spatiotemporal slice and returns a sample dictionary. Its `__and__` and `__or__` operators construct intersection/union datasets.
- `GeoSampler` and `BatchGeoSampler` store a clipped geospatial index, dataset resolution, `roi`, and `toi`. They yield `GeoSlice` objects or lists of `GeoSlice` objects.
- `RandomPatchSampler`/legacy random samplers compute chip windows from dataset bounds and resolution; empty or too-small geometries lead to no usable chips.
- `BaseDataModule` defaults to Kornia normalization and stores split-specific augmentation attributes. `GeoDataModule` defaults to `stack_samples` and sampler/batch-sampler fields for each split.

## Practical patterns

### Minimal geospatial loader

```python
from torch.utils.data import DataLoader
from torchgeo.datasets import CDL, Landsat8, stack_samples
from torchgeo.samplers import RandomPatchSampler

imagery = Landsat8(paths='landsat', bands=['B2', 'B3', 'B4', 'B5'])
labels = CDL(paths='cdl', download=False)
dataset = imagery & labels
sampler = RandomPatchSampler(dataset, size=256, length=1000)
loader = DataLoader(dataset, batch_size=8, sampler=sampler, collate_fn=stack_samples)
```

### Non-geospatial benchmark loader

```python
from torch.utils.data import DataLoader
from torchgeo.datasets import EuroSAT

dataset = EuroSAT(root='data', split='train', download=True, checksum=True)
loader = DataLoader(dataset, batch_size=32, shuffle=True, num_workers=4)
```

## Native test candidates

- `tests/datasets/test_geo.py`: base `GeoDataset`, intersection/union, raster/vector behavior.
- `tests/samplers/test_single.py`: random/gridded patch samplers.
- `tests/samplers/test_batch.py`: batch sampler behavior.
- `tests/samplers/test_spatial.py` and `tests/samplers/test_temporal.py`: ROI/TOI and temporal sampler composition.
- Individual `tests/datasets/test_<name>.py` files: dataset-specific fake data, downloads, checksum, plotting, and error handling.

## Common pitfalls

- Querying a `GeoDataset` with an integer as if it were a `NonGeoDataset`.
- Forgetting `collate_fn=stack_samples` for geospatial dictionaries.
- Sampling from a dataset before verifying that its `index` contains geometries large enough for the requested chip size.
- Using intersection when the datasets do not overlap in CRS/time, producing an empty effective dataset.
- Copying real dataset files into tests instead of generated/minimal fixtures.
