# Installation Notes

## When to read this

Read this when you need to install `stitching`, verify the package import,
choose between the GUI and headless OpenCV builds, or decide which bundled
helper to run first in a fresh environment.

## Public install paths

The package name is `stitching`.

```bash
python -m pip install stitching
```

For headless servers, Docker containers, or environments without an OpenCV GUI
stack, use the headless distribution:

```bash
python -m pip install stitching-headless
```

The package metadata and tests show the runtime dependencies used by the public
wheel: `opencv-python` and `largestinteriorrectangle`. The repository's test
suite also uses `requests` to download public sample images when they are not
already present.

## What the install should let you do

After installation, the following should work from a clean environment:

```bash
python -c "import stitching; print(stitching.__version__)"
stitch --help
```

If you want a stronger local smoke check, use:

```bash
python scripts/check_install.py
```

## Choosing a build

- Use `stitching` when you want the normal OpenCV package and may use GUI
  preview features.
- Use `stitching-headless` when the environment cannot provide GUI windows or
  when you are running in Docker or a server session.
- The `--try_use_gpu` flag is optional and is not part of the minimum public
  install contract. It only helps when the underlying OpenCV build supports a
  CUDA-enabled matcher path.

## Helpful package facts

- Public import: `import stitching`
- Public classes: `Stitcher`, `AffineStitcher`
- Console entry point: `stitch`
- Verified package version at the referenced snapshot: `0.6.1`

## Next places to read

- [CLI reference](../sub-skills/cli/references/cli-reference.md) for command
  flags.
- [Python API reference](../sub-skills/python-api/references/api-reference.md)
  for signatures and defaults.
- [Troubleshooting](troubleshooting.md) for import, GUI, crop, and image
  validation failures.
