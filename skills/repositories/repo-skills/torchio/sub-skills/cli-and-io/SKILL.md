---
name: cli-and-io
description: "Use TorchIO's command-line interface and I/O integration surfaces
  for image metadata, conversion, transform commands, cache inspection,
  visualization exports, and local or remote NIfTI/NIfTI-Zarr backends."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# TorchIO CLI and I/O

Use this sub-skill when the task is to run or generate `torchio` CLI commands, inspect or convert medical image files, apply a one-off transform from the shell, manage TorchIO's dataset cache, troubleshoot plotting or animation exports, or reason about local, remote, and NIfTI-Zarr image loading.

## Route Map

- For CLI syntax, safe command patterns, command-specific caveats, and the bundled smoke check, read [CLI reference](references/cli-reference.md).
- For accepted image sources, lazy backends, remote URI behavior, NIfTI-Zarr conversion, and optional cloud extras, read [I/O backends](references/io-backends.md).
- For failures involving missing extras, Tyro argument parsing, cache side effects, remote credentials, `.nii.zarr` dependencies, or non-notebook plotting, read [troubleshooting](references/troubleshooting.md).
- To verify a TorchIO CLI installation on synthetic data, run `python sub-skills/cli-and-io/scripts/torchio_cli_smoke.py --help` first, then run the script without arguments.

## Quick Start

1. Confirm the CLI is installed: `torchio --version` or `python -m torchio.cli --version`.
2. Inspect an image: `torchio info image.nii.gz`.
3. Convert between supported image formats: `torchio convert input.nii.gz output.nii` or `torchio convert input.nii.gz output.nii.zarr` when the `zarr` extra is installed.
4. Apply a one-off transform: `torchio transform input.nii.gz output.nii.gz Noise std=0.1` or `torchio transform input.nii.gz crop.nii.gz CropOrPad target_shape=128`.
5. Save visual output explicitly outside notebooks: `torchio plot image.nii.gz --output slices.png` or `torchio animate image.nii.gz sweep.gif --seconds 3 --direction I`.

## Boundaries

- This sub-skill owns CLI command generation, image file I/O behavior, optional visualization/export dependencies, remote/Zarr/cloud caveats, and cache command safety.
- For in-Python image construction such as `tio.ScalarImage(tensor)` or subject metadata modeling, route to the data-model sub-skill.
- For composing transform pipelines in Python, current transform class names, and transform API details, route to the transforms sub-skill.
- For patch sampling, training queues, aggregation, and inference tiling, route to the patch-workflows sub-skill.

## Safety Defaults

- Prefer `torchio cache dir` over `torchio cache clean`; cleaning without a dataset name removes all TorchIO cached data.
- Treat cloud URIs as network and credential-dependent; avoid running them in smoke checks unless the user explicitly provides a safe test endpoint and credentials.
- Use `--output` for `plot` and explicit `.gif` or `.mp4` paths for `animate` in non-interactive sessions.
