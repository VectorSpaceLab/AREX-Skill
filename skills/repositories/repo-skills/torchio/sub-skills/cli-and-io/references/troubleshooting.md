# CLI and I/O Troubleshooting

Use this page when a TorchIO command or image-loading workflow fails before model or transform logic becomes the main issue.

## Command Not Found

Symptom: `torchio: command not found` or the shell cannot locate the executable.

Likely causes:

- TorchIO is installed in a different Python environment.
- The environment's script directory is not on `PATH`.
- Only source files are present, not an installed package with console scripts.

Recovery:

1. Try `python -m torchio.cli --version` in the intended Python environment.
2. Verify the package import: `python -c "import torchio as tio; print(tio.__version__)"`.
3. Reinstall TorchIO into the active environment if import or module execution fails.
4. Use the bundled smoke helper; it falls back from `torchio` to `python -m torchio.cli` automatically.

## Tyro Syntax Confusion

Symptom: Tyro reports an unrecognized option, missing positional argument, or invalid command shape.

Recovery:

- Run command-specific help: `torchio transform --help` or `torchio plot --help`.
- Put positional arguments in order before optional transform `key=value` arguments.
- For `transform`, pass the current transform class name without legacy `Random` prefixes, for example `Noise`, `Flip`, `Affine`, `CropOrPad`, or `RescaleIntensity`.
- Quote tuple/list values so the shell does not split or interpret them: `torchio transform in.nii.gz out.nii.gz CropOrPad 'target_shape=(64, 64, 64)'`.
- Pass `RescaleIntensity` bounds as CLI `key=value` strings: `out_min=0 out_max=1 in_min=0 in_max=255`.

## Missing Plot or Video Extras

Symptoms:

- ImportError says matplotlib is required for plotting.
- GIF export complains about missing Pillow/image writer support.
- MP4 export complains about missing `ffmpeg` Python package or system executable.

Recovery:

```bash
pip install 'torchio[plot]'
pip install 'torchio[video]'
```

For MP4, also install a working system `ffmpeg` binary. In non-interactive agents and CI, prefer explicit output files:

```bash
torchio plot image.nii.gz --output slices.png
torchio animate image.nii.gz sweep.gif --seconds 3 --direction I
```

Do not rely on notebook inline display outside Jupyter.

## NIfTI-Zarr Dependency Failures

Symptoms:

- ImportError mentions `nifti-zarr`, `niizarr`, or `zarr`.
- `.nii.zarr` conversion or loading fails even though `.nii.gz` works.

Recovery:

```bash
pip install 'torchio[zarr]'
```

Then retry a small local conversion before using remote data:

```bash
torchio convert input.nii.gz output.nii.zarr
torchio info output.nii.zarr
```

Remember `.nii.zarr` is a directory-like store, not a single `.nii.gz` file.

## Remote and Cloud Failures

Symptoms:

- Auth errors from `s3fs`, `adlfs`, `gcsfs`, or fsspec.
- A remote `.nii.gz` command is slow or downloads unexpectedly.
- A remote `.nii.zarr` URI works locally but fails in CI or another machine.

Recovery:

1. Confirm whether the path ends in `.nii.zarr`; only remote NIfTI-Zarr streams lazily.
2. Install provider extras: `torchio[zarr,s3]`, `torchio[zarr,azure]`, or `torchio[zarr,gcs]`.
3. Verify credentials with the provider's normal tooling or environment variables before running TorchIO.
4. Avoid hard-coding credentials in commands or generated scripts. Use environment variables, cloud profiles, managed identity, or runtime `reader_kwargs` in Python.
5. Start with metadata-only checks such as `torchio info URI` or `image.shape` before transform or conversion commands that may materialize data.
6. If no safe endpoint or credentials are available, mark remote/cloud verification as skipped or untested. Local import, help, and `.nii.zarr` checks only prove local installation and Zarr support, not remote access.

## Cache Side Effects

Symptoms:

- User asks where TorchIO downloaded a dataset.
- Cache cleaning unexpectedly removes more data than intended.

Recovery and safety rules:

- Use `torchio cache dir` for read-only inspection.
- Use `torchio cache clean DATASET` only when the user names a dataset cache to remove.
- Treat `torchio cache clean` without a dataset as destructive because it removes the full TorchIO cache root.
- Built-in datasets may re-download data later if their cache was removed.

## Unsupported or Invalid Image Files

Symptoms:

- `FileNotFoundError` for a bad path.
- Reader errors from NiBabel or SimpleITK.
- `ValueError` says expected 3D or 4D data.

Recovery:

1. Confirm the path or URI is reachable from the active process.
2. Use `torchio info PATH` on a small known-good NIfTI to separate install problems from data problems.
3. For file-like Python sources, provide a suffix hint such as `suffix='.nii.gz'`.
4. For unusual medical image formats, test whether SimpleITK can read the format; TorchIO delegates non-NIfTI paths to SimpleITK.
5. Convert unsupported dimensional layouts to 3D or 4D before constructing a TorchIO image.

## CLI Smoke Check Fails

The bundled smoke script creates temporary synthetic NIfTI files and runs safe help/info/convert commands. If it fails:

- Check the printed command and stderr; the script does not mutate user data.
- Missing `nibabel`, `numpy`, or `torchio` indicates an incomplete installation.
- `info` or `convert` failure on the tiny fixture usually points to a broken TorchIO, NiBabel, SimpleITK, or console-script installation.
- If only the executable lookup fails, retry the module fallback manually: `python -m torchio.cli --help`.
