---
name: stitching
description: "Routes panorama stitching, the `stitch` CLI, `Stitcher` and
  `AffineStitcher` API usage, verbose diagnostics, feature-mask troubleshooting,
  and headless installation decisions for the stitching package."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# stitching

Use this repo skill for image panorama stitching tasks with the Python package
`stitching`. It is the top-level router for the package CLI, the Python API,
and failure analysis around verbose outputs and sample-image workflows.

## Start here

- If you want a shell command, go to [CLI usage](sub-skills/cli/SKILL.md).
- If you want `Stitcher` or `AffineStitcher` from Python, go to [Python API](sub-skills/python-api/SKILL.md).
- If you are diagnosing failed stitches, missing images, or poor matches, go to
  [diagnostics](sub-skills/diagnostics/SKILL.md).
- If you are checking whether this skill matches the current checkout, read
  [repository provenance](references/repo-provenance.md).

## Install

The public package name is `stitching`.

```bash
python -m pip install stitching
```

For headless server or Docker environments, use the headless build when the
OpenCV GUI stack is not available:

```bash
python -m pip install stitching-headless
```

The runtime package depends on OpenCV and `largestinteriorrectangle`. The
repository's native test suite also uses `requests` to download public sample
images when they are not already present.

## Minimal verification

After installing the package in a clean Python environment, run:

```bash
python -c "import stitching; print(stitching.__version__)"
stitch --help
```

If you need a stronger smoke check, use the bundled helper:

```bash
python scripts/check_install.py --help
python scripts/check_install.py
```

## What this skill covers

- Panorama stitching from filenames, glob patterns, or loaded NumPy arrays.
- `stitch` CLI flags for affine mode, masks, verbose output, crop control,
  match tuning, and output selection.
- `Stitcher` and `AffineStitcher` constructors and their verified defaults.
- Verbose output, matches graphs, feature masks, timelapse output, and crop
  troubleshooting.
- Safe sample-image download guidance for users who want to reproduce the
  repository's public examples.

## What this skill does not do

- It does not depend on the original repository checkout at runtime.
- It does not claim CUDA support as a required capability. The `--try_use_gpu`
  option is optional and only works with a CUDA-enabled OpenCV build.
- It does not bundle the original repository's native tests or generated output.

## Bundled references and scripts

Read these when you need deeper detail than the router provides:

- [Installation notes](references/installation.md) for package names, headless
  builds, and verification commands.
- [Troubleshooting](references/troubleshooting.md) for import, OpenCV, image,
  crop, and GUI failures.
- [Package provenance](references/repo-provenance.md) to check whether this
  skill matches the current repository snapshot.
- [Routing metadata](references/repo-routing-metadata.json) for managed router
  placement during import in supported workflows.
- [CLI reference](sub-skills/cli/references/cli-reference.md) for flags and
  options.
- [Python API reference](sub-skills/python-api/references/api-reference.md) for
  signatures and verified defaults.
- [Diagnostics workflow guide](sub-skills/diagnostics/references/diagnostic-workflows.md)
  for verbose outputs, match graphs, and recovery paths.
- [Install check helper](scripts/check_install.py) to verify the installed
  package from a clean environment.
- [Sample image downloader](scripts/download_sample_images.py) when you want
  the public fixture set used by the repository's native tests.

## Quick route map

| User intent | Read next |
| --- | --- |
| "stitch these images from the shell" | [sub-skills/cli/SKILL.md](sub-skills/cli/SKILL.md) |
| "use Stitcher in Python" | [sub-skills/python-api/SKILL.md](sub-skills/python-api/SKILL.md) |
| "why did stitching fail" | [sub-skills/diagnostics/SKILL.md](sub-skills/diagnostics/SKILL.md) |
| "I need the CLI flags" | [sub-skills/cli/references/cli-reference.md](sub-skills/cli/references/cli-reference.md) |
| "what defaults does the API use" | [sub-skills/python-api/references/api-reference.md](sub-skills/python-api/references/api-reference.md) |
| "I need the sample images" | [scripts/download_sample_images.py](scripts/download_sample_images.py) |

## Common runtime reminders

- Use the `stitch` entry point for end users; it is the public CLI.
- Use `AffineStitcher` when the input is scans or specialized-device imagery.
- Use feature masks only when the mask shape matches the image shape.
- Use `stitch --no-crop` or `Cropper(False)` when the cropper cannot find a
  valid interior rectangle.
- Treat verbose output and matches graphs as diagnostics, not as required
  runtime data files.
