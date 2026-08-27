# API Quick Map

Use this map to choose the right TorchIO route before opening detailed sub-skill references.

## Data Model

- `tio.ScalarImage(source)` for continuous images from tensors, arrays, paths, NiBabel objects, SimpleITK objects, bytes, or file-like sources.
- `tio.LabelMap(source)` for segmentation masks and labels; use this so spatial transforms choose nearest-neighbor label interpolation.
- `tio.Subject(**items)` or `tio.Study(**items)` to group images, points, bounding boxes, and metadata.
- `tio.Points(data, axes="IJK", affine=...)` and `tio.BoundingBoxes(data, format=..., labels=...)` for annotations.
- Open [data-model](../sub-skills/data-model/SKILL.md) when validation, shape, affine, metadata, or lazy-loading behavior is the main issue.

## Transforms

- Base args shared by transforms: `p`, `copy`, `per_instance`, `include`, and `exclude`.
- Composition: `tio.Compose([...])`, `tio.OneOf([...])`, `tio.SomeOf([...])`.
- Intensity examples: `Normalize`/`RescaleIntensity`, `Standardize`/`ZNormalization`, `Clamp`, `Blur`, `Noise`, `Gamma`, `Motion`, `BiasField`, `Spike`, `Ghosting`, `LabelsToImage`.
- Spatial examples: `CropOrPad`, `Crop`, `Pad`, `Resize`, `Resample`, `Reorient`, `Flip`, `Affine`, `Spatial`, `ElasticDeformation`.
- Label examples: `OneHot`, `RemapLabels`, `RemoveLabels`, `SequentialLabels`, `KeepLargestComponent`, `Contour`.
- Open [transforms](../sub-skills/transforms/SKILL.md) when the task is pipeline design, migration from older examples, transform debugging, history, inverse behavior, or adapters.

## Patch Workflows

- Dense inference: `GridSampler(subject, patch_size, patch_overlap)` plus `PatchAggregator(spatial_shape, overlap_mode, patch_overlap)`.
- Random training patches: `UniformSampler`, `WeightedSampler`, or `LabelSampler`.
- Buffered training: `Queue(subjects, patch_sampler, max_length, patches_per_volume, num_workers, transform=...)` plus `SubjectsLoader`.
- Open [patch-workflows](../sub-skills/patch-workflows/SKILL.md) when image sizes, patch locations, batch metadata, or aggregation are central.

## CLI and I/O

- Console entry point: `torchio`.
- Subcommands: `plot`, `animate`, `info`, `convert`, `transform`, `cache`.
- Optional extras: `plot`, `video`, `zarr`, `monai`, `cornucopia`, `s3`, `azure`, `gcs`.
- Open [cli-and-io](../sub-skills/cli-and-io/SKILL.md) when the task is shell command generation, format conversion, plotting/animation, cache handling, remote files, or NIfTI-Zarr.
