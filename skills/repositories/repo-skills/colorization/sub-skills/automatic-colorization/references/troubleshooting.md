# Troubleshooting

## Dependency name mistakes

The runtime package names are:

```bash
python -m pip install torch numpy matplotlib pillow scikit-image ipython
```

Common mistakes:

- `skimage` is the import name, but the install name is `scikit-image`.
- `PIL` is the import name, but the install name is `pillow`.
- `argparse` is already included with Python; do not install it.

If `torch` is installed without CUDA support, CPU runs should still work, but `--device cuda` will not.

## Import failures

If the helper cannot import `colorizers`, check one of these:

1. The package is not installed in the active environment.
2. `--repo-root` was omitted.
3. `--repo-root` points at the wrong directory.

The helper expects `--repo-root` to be a directory that contains `colorizers/__init__.py`.

Typical recovery:

```bash
python scripts/colorize_image.py \
  --repo-root path/to/colorization \
  --input-image path/to/input.jpg \
  --output-dir outputs \
  --save-prefix sample
```

If you are already working from an installed package, `--repo-root` is optional.

## Missing `--repo-root` or wrong import path

When running from an arbitrary current directory, the helper does not guess the import root. Provide `--repo-root` explicitly or install the package into the environment.

If the path is wrong, fix it so it points at the import root that contains the `colorizers` package, not at the `colorizers/` subdirectory itself.

## Model download, cache, hash, and network failures

By default, pretrained model constructors call PyTorch `torch.utils.model_zoo.load_url` with hash checking and public `colorizers.s3...` URLs.

Possible failures:

- No network access.
- A proxy or SSL issue.
- A corrupt cached weight file.
- A non-writable or misconfigured PyTorch cache location.

Recovery steps:

1. Retry on a network that can reach the public weight URLs, if downloads are allowed.
2. Remove the corrupt cached weight file and retry.
3. If the cache location is not writable, point PyTorch at a writable cache location using the standard PyTorch cache configuration for your environment.
4. Use `--skip-pretrained` only to check smoke behavior, not output quality.

Hash mismatch usually means the cached file is incomplete or corrupted.

## CUDA unavailable or device mismatch

Symptoms:

- `--device cuda` fails immediately.
- PyTorch reports no CUDA device.
- A runtime error mentions device mismatch or a missing CUDA kernel.

Fixes:

- Use `--device cpu` for the most reliable path.
- Use `--device auto` if you want CUDA when available and CPU otherwise.
- Confirm that the installed PyTorch build matches your intended accelerator support.
- Confirm the host really exposes a CUDA device to the process.

The helper moves the model and the resized input tensor to the selected device, but external modifications or a mismatched PyTorch build can still produce errors.

## Invalid or unreadable image

The input must be readable by Pillow and compatible with the color conversion path.

Common issues:

- The file does not exist.
- The file is corrupted.
- The file is not an image.
- The image format is unusual or unreadable by Pillow.

The helper accepts grayscale or standard RGB images. If you have a different mode, convert it to a standard RGB image first.

## Output path problems

The helper creates `--output-dir` automatically, but it still needs a writable location.

Common issues:

- The directory cannot be created.
- The directory is not writable.
- `--save-prefix` accidentally contains path separators.

Recovery:

- Point `--output-dir` at a writable directory.
- Keep `--save-prefix` to a filename stem such as `sample`.
- Use `--output-dir` for directory structure, not `--save-prefix`.

## Headless Matplotlib differences

The bundled helper is designed for headless use. It sets a non-interactive backend and saves PNGs directly with Matplotlib image saving.

If you are comparing behavior with the original release-style figure display, note these differences:

- No GUI window is opened.
- No interactive `show()` call is made.
- Only saved files are part of the supported runtime contract.

If a notebook or GUI environment tries to override the backend, prefer running the helper as a normal script in a plain terminal session.
