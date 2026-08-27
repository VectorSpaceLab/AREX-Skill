# TorchIO Troubleshooting

## Import or Install Fails

- Verify Python is supported by the installed TorchIO version and that base dependencies such as `torch`, `nibabel`, `SimpleITK`, `numpy`, and `tyro` are installed.
- Run `python -m pip check` when imports fail after installation.
- Do not install all extras by default. Add only the extra needed for the failing workflow: `plot`, `video`, `monai`, `cornucopia`, `zarr`, `s3`, `azure`, or `gcs`.

## Old Examples Do Not Match TorchIO 2.0

- Replace old `RandomFlip`, `RandomAffine`, `RandomNoise`, or similar names with current classes such as `Flip`, `Affine`, and `Noise`.
- Use `tio.RescaleIntensity(out_min=0, out_max=1)` instead of passing a positional tuple.
- Use `tio.ScalarImage(tensor)` or `tio.LabelMap(tensor)` for in-memory tensors; the tensor should be 4D `(C, I, J, K)`.
- Inspect `subject.applied_transforms`, `subject.get_inverse_transform()`, and `subject.apply_inverse_transform()` for current history/inverse behavior.

## Tensor, Shape, or Affine Errors

- A TorchIO image tensor must be channel-first 4D: `(channels, i, j, k)`.
- Use `channels_last=True` only when the input tensor/array is `(i, j, k, channels)`.
- Affines must be 4x4 matrices; spacing and orientation derive from affine metadata.
- Route detailed shape/source/annotation errors to [data-model troubleshooting](../sub-skills/data-model/references/troubleshooting.md).

## Transform Output Looks Wrong

- Check whether the data should be a `ScalarImage` or `LabelMap`; label maps use label-safe interpolation.
- Check transform `include` and `exclude` image keys.
- Zero-range images can warn during intensity rescaling because all voxels have the same value.
- Route pipeline, history, inverse, no-op warning, adapter, and include/exclude issues to [transforms troubleshooting](../sub-skills/transforms/references/troubleshooting.md).

## Patch Workflow Fails

- Confirm patch sizes and overlaps are 3D values and compatible with the subject spatial shape.
- For weighted sampling, the probability map key must exist and contain valid positive weights.
- For dense inference, pass patch predictions and matching `PatchLocation` metadata to `PatchAggregator`.
- Route sampler, queue, batch, and aggregator issues to [patch workflow troubleshooting](../sub-skills/patch-workflows/references/troubleshooting.md).

## CLI or I/O Fails

- Use `torchio --help` and subcommand `--help` before generating commands.
- CLI transform arguments are command-line key/value strings; complex Python pipelines are usually safer through the Python API.
- Plotting/animation may need optional extras and explicit output paths outside notebooks.
- Remote and cloud paths may need credentials and provider-specific extras; NIfTI-Zarr needs the `zarr` extra.
- Route CLI syntax, cache, remote, plotting, and conversion issues to [CLI and I/O troubleshooting](../sub-skills/cli-and-io/references/troubleshooting.md).
