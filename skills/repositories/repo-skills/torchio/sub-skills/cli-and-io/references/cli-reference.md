# TorchIO CLI Reference

TorchIO exposes a `torchio` console command backed by Tyro. The top-level command accepts `--version` and the subcommands `plot`, `animate`, `info`, `convert`, `transform`, and `cache`.

## Safe Discovery Commands

Use these before generating commands for a user environment:

```bash
torchio --version
torchio --help
torchio info --help
torchio convert --help
torchio transform --help
torchio cache --help
torchio cache dir
```

If the executable is not on `PATH`, try the module entry point:

```bash
python -m torchio.cli --version
python -m torchio.cli --help
```

The bundled smoke helper exercises this fallback safely:

```bash
python sub-skills/cli-and-io/scripts/torchio_cli_smoke.py
```

## Command Catalog

| Command | Purpose | Safe example | Notes |
|---|---|---|---|
| `torchio info PATH` | Print `ScalarImage` metadata such as spatial shape, spacing, and orientation. | `torchio info brain.nii.gz` | Reads through `tio.ScalarImage`; non-existent or unsupported inputs fail before output. |
| `torchio convert INPUT OUTPUT` | Convert image files; output format is inferred from extension. | `torchio convert in.nii.gz out.nii` | Uses `ScalarImage.save()` for most formats and `.to_nifti_zarr()` for `OUTPUT` ending in `.nii.zarr`. |
| `torchio transform INPUT OUTPUT NAME [ARGS...]` | Apply one transform class to one image. | `torchio transform in.nii.gz out.nii.gz Noise std=0.1` | `NAME` must be a registered current transform class such as `Noise`, `Flip`, `Affine`, `CropOrPad`, or `RescaleIntensity`. |
| `torchio plot PATH [--output FILE]` | Plot 3 orthogonal slices. | `torchio plot brain.nii.gz --output slices.png` | Requires plotting dependencies. Use `--output` in scripts/headless sessions. |
| `torchio animate PATH OUTPUT` | Export an animated sweep through slices. | `torchio animate brain.nii.gz brain.gif --seconds 3 --direction I` | Output suffix must be `.gif` or `.mp4`; MP4 also needs video dependencies and system `ffmpeg`. |
| `torchio cache dir` | Print TorchIO's user cache directory. | `torchio cache dir` | Safe read-only cache inspection. |
| `torchio cache clean [DATASET]` | Remove cached TorchIO dataset files. | `torchio cache clean colin27` | Without `DATASET`, removes all TorchIO cached data; ask before using. |

## Tyro Syntax Rules

- Positional arguments come first: input paths, output paths, and transform names are not introduced with flags.
- Optional fields use Tyro flags, such as `--device cuda:0`, `--output slices.png`, `--channel 0`, `--seconds 10`, and `--direction S`.
- `transform` extra arguments are positional `key=value` strings after the transform name. Values are parsed with Python literal syntax where possible.
- Quote shell-sensitive tuple/list values: `torchio transform in.nii.gz out.nii.gz CropOrPad 'target_shape=(64, 64, 64)'`.
- Strings that should remain strings can be passed unquoted if the shell allows them, for example `direction=LR`; quote paths or values containing spaces.

## Transform Command Strategy

The CLI performs exactly one transform on exactly one scalar image and then saves the result. For multi-step or probabilistic transform pipelines, generate Python code in the transforms sub-skill instead of overloading the CLI.

Use current TorchIO transform class names. Do not generate legacy `RandomFlip` or `RandomAffine` names. Examples:

```bash
torchio transform input.nii.gz flipped.nii.gz Flip axes=0
torchio transform input.nii.gz crop.nii.gz CropOrPad target_shape=128
torchio transform input.nii.gz rescaled.nii.gz RescaleIntensity out_min=0 out_max=1
torchio transform input.nii.gz noisy.nii.gz Noise std=0.1
```

`RescaleIntensity` uses keyword-only bounds in Python; in the CLI, pass them as `key=value` transform arguments, for example `out_min=0 out_max=1 in_min=0 in_max=255`.

## Conversion Notes

- `.nii` and `.nii.gz` are handled through the normal image save path.
- Other SimpleITK-supported formats may work when SimpleITK can infer them from the output extension.
- `.nii.zarr` output is a directory-like NIfTI-Zarr store and requires the Zarr/NIfTI-Zarr optional dependencies.
- Conversion loads the input image through `tio.ScalarImage`, so remote non-Zarr inputs may be downloaded before conversion.

## Visualization Commands

Use file outputs for automation:

```bash
torchio plot image.nii.gz --output slices.png
torchio plot image.nii.gz --indices 40 50 60 --output slices.png
torchio animate image.nii.gz sweep.gif --seconds 5 --direction I
torchio animate image.nii.gz sweep.mp4 --seconds 5 --direction S
```

`plot` creates three orthogonal anatomical views. `animate` sweeps along one anatomical direction: `I`, `S`, `A`, `P`, `R`, or `L`.

## Cache Commands

`torchio cache dir` prints the platform-specific TorchIO cache root used by built-in dataset download helpers. `torchio cache clean DATASET` removes one dataset cache directory under that root. `torchio cache clean` removes the whole TorchIO cache root, so it should be treated as a destructive operation and confirmed with the user.
