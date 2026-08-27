# Maskers and Regions Workflows

## Whole-Brain or Mask-Restricted Voxel Matrix

Use `NiftiMasker` when the analysis wants one feature per voxel.

```python
from nilearn.maskers import NiftiMasker

masker = NiftiMasker(
    mask_img=mask_img,
    standardize="zscore_sample",
    detrend=True,
    t_r=2.0,
    reports=True,
)
X = masker.fit_transform(fmri_img, confounds=confounds)
restored = masker.inverse_transform(X[:1])
report = masker.generate_report()
```

Checklist:

- `X.shape == (n_scans, masker.n_elements_)` for 4D data.
- If `mask_img` is absent, inspect `masker.mask_img_` or the report before
  trusting features.
- Use `runs` when detrending or standardizing should happen independently per
  run; it must have one entry per scan.
- Route raw `apply_mask`, `unmask`, and `signal.clean` calls to
  `../data-io-signal/SKILL.md`.

## Labels Atlas Time Series

Use `NiftiLabelsMasker` for non-overlapping integer atlas labels.

```python
from nilearn.maskers import NiftiLabelsMasker

masker = NiftiLabelsMasker(
    labels_img=labels_img,
    lut=lut,
    background_label=0,
    strategy="mean",
    resampling_target="data",
    standardize_confounds=True,
)
time_series = masker.fit_transform(fmri_img, confounds=confounds)
region_names = masker.region_names_
```

Validation steps:

- Confirm `background_label` matches the atlas, especially when labels include
  an explicit background entry.
- Compare expected labels to `masker.lut_`, `masker.labels_`, and
  `time_series.shape[1]` after fitting.
- If a mask removes regions, decide whether a temporary compatibility path with
  `keep_masked_labels=True` is acceptable; otherwise treat missing columns as
  intentional and update downstream labels.
- Use `strategy="median"` for robustness, `"sum"` for aggregate signal, or
  dispersion strategies only when downstream interpretation needs them.

## Probabilistic Maps Time Series

Use `NiftiMapsMasker` when regions are continuous maps, ICA components, or
probabilistic networks.

```python
from nilearn.maskers import NiftiMapsMasker

masker = NiftiMapsMasker(
    maps_img=maps_img,
    mask_img=mask_img,
    allow_overlap=True,
    resampling_target="data",
    standardize="zscore_sample",
)
time_series = masker.fit_transform(fmri_img, confounds=confounds)
```

Rules:

- Maps image is 4D; `maps_img.shape[-1]` is the nominal number of regions.
- Use `allow_overlap=False` to assert non-overlap, but expect a `ValueError`
  when atlas maps or resampling introduce shared non-zero voxels.
- `resampling_target="maps"` forces data into map space and can be memory-heavy;
  `"data"` is usually safer for extraction.
- If masked maps disappear, validate the warning and output shape before
  passing region names to connectivity or plotting.

## Sphere Seed Extraction

Use `NiftiSpheresMasker` for coordinate seeds in the same world space as the
functional images.

```python
from nilearn.maskers import NiftiSpheresMasker

seeds = [(0.0, 0.0, 0.0), (24.0, -12.0, 40.0)]
masker = NiftiSpheresMasker(
    seeds=seeds,
    radius=6.0,
    mask_img=mask_img,
    allow_overlap=False,
    standardize="zscore_sample",
)
seed_series = masker.fit_transform(fmri_img)
seed_img = masker.inverse_transform(seed_series[:1])
```

Checklist:

- Seed coordinates are world coordinates, not voxel indices.
- Use `mask_img` when inverse transformation or strict in-mask seed validation
  is needed.
- Increase `radius` carefully; overlap errors are expected when
  `allow_overlap=False` and spheres share voxels.

## Multi-Subject or Multi-Run Extraction

Use multi maskers when the input is a list and each item should keep its own
matrix.

```python
from nilearn.maskers import MultiNiftiLabelsMasker

masker = MultiNiftiLabelsMasker(
    labels_img=labels_img,
    background_label=0,
    n_jobs=2,
    standardize="zscore_sample",
)
series_by_subject = masker.fit_transform(
    fmri_imgs,
    confounds=confounds_by_subject,
    sample_mask=sample_masks_by_subject,
)
```

Rules:

- `fmri_imgs`, `confounds_by_subject`, and `sample_masks_by_subject` must have
  identical outer lengths.
- Each confound matrix must align to that image's original scan count, not the
  scrubbed count.
- The return value is a list; concatenate only after verifying matching region
  columns and compatible preprocessing choices.

## Region Extraction From Maps

Use `RegionExtractor` to threshold and split continuous components before
signal extraction.

```python
from nilearn.regions import RegionExtractor

extractor = RegionExtractor(
    maps_img=component_maps,
    threshold=1.0,
    thresholding_strategy="ratio_n_voxels",
    min_region_size=1350,
    extractor="local_regions",
    smoothing_fwhm=6,
    standardize=True,
)
region_series = extractor.fit_transform(fmri_img)
regions_img = extractor.regions_img_
source_map_index = extractor.index_
```

Use `connected_regions` directly when only the 4D split-regions image is
needed. Use `connected_label_regions` when a labels atlas contains disconnected
islands that should become separate integer labels. Remember that region sizes
are in mm³, so voxel size changes the effective number of voxels retained.

## Learned Parcellations and ReNA

Use `Parcellations` when Nilearn should learn an atlas from data.

```python
from nilearn.regions import Parcellations

model = Parcellations(
    method="kmeans",
    n_parcels=50,
    mask=mask_img,
    standardize=True,
    random_state=0,
)
model.fit(fmri_imgs)
labels_img = model.labels_img_
```

Use `method="kmeans"` for a small number of parcels, `"ward"` for higher
quality spatially constrained parcels with more compute, and `"rena"` for fast
large-scale reduction. Use `ReNA` directly for array-level dimensionality
reduction after the feature geometry is already known.

## Inverse Transform Sanity Checks

- For `NiftiMasker`, `inverse_transform(X)` maps voxel columns back into the
  fitted mask image.
- For labels and maps maskers, columns must match the labels/maps retained by
  the fitted masker.
- For spheres, provide `mask_img` at construction; overlapping inverse voxels
  are averaged when `allow_overlap=True`.
- Check the returned image shape and affine against `masker.mask_img_`,
  `masker.labels_img_`, or `masker.maps_img_` before saving or plotting.

## Masker Reports

Reports are diagnostics, not required extraction outputs.

```python
masker = NiftiLabelsMasker(labels_img=labels_img, reports=True).fit(fmri_img)
report = masker.generate_report()
# In notebooks display `report`; in scripts use report.save_as_html(path).
```

Guidelines:

- Generate reports after `fit()` or `fit_transform()` so the masker has data to
  show.
- Use `displayed_maps=[...]`, `displayed_spheres=[...]`, or `"all"` only for
  small atlases; large reports can be slow.
- In CI or no-plotting environments, set `reports=False` and verify extraction
  shapes instead.
