# Installation and import notes

Read this when preparing a Python environment for the `colorizers` package or when an import/dependency failure blocks a colorization task.

## Repository shape

The PyTorch release is a small source checkout with a top-level `colorizers/` package and no package metadata (`pyproject.toml`, `setup.py`, or console entry point). That means ordinary `pip install .` may not work in a fresh clone. Use one of these import patterns instead:

1. Run scripts from the clone root so Python can import `colorizers`.
2. Set `PYTHONPATH` to include the clone root.
3. Use the bundled helper scripts' `--repo-root path/to/colorization` option, which prepends a clone root to `sys.path` before importing.

The skill's bundled scripts are designed for pattern 3 so they can run from arbitrary current directories.

## Correct runtime dependencies

Install the runtime packages with canonical package names:

```bash
python -m pip install torch numpy matplotlib pillow scikit-image ipython
```

Notes:

- `PIL` is the import namespace supplied by `pillow`.
- `skimage` is the import namespace supplied by `scikit-image`.
- `argparse` is part of the Python standard library.
- `IPython` is imported by the model modules even though typical calls do not use `embed`; install `ipython` to avoid import-time failure.
- Use a CUDA-capable PyTorch build only when CUDA execution is required. CPU execution is the default portable path.

## No-download import/API check

Use `pretrained=False` for setup checks:

```bash
PYTHONPATH="path/to/colorization" python - <<'PY'
import colorizers
m1 = colorizers.eccv16(pretrained=False).eval()
m2 = colorizers.siggraph17(pretrained=False).eval()
print(type(m1).__name__, type(m2).__name__)
PY
```

This does not fetch model weights. A quality colorization run uses the wrapper default `pretrained=True` and may download public weights through `torch.utils.model_zoo.load_url`.

## Skill diagnostics

From the root of this generated skill, run the shared check:

```bash
python scripts/check_env.py --repo-root path/to/colorization --check-forward
```

Use the workflow-specific helper for saved image outputs:

```bash
python sub-skills/automatic-colorization/scripts/colorize_image.py \
  --repo-root path/to/colorization \
  --input-image path/to/input.jpg \
  --output-dir outputs \
  --save-prefix sample \
  --model both \
  --device cpu
```

Use the API-specific smoke check when debugging tensor shapes or imports:

```bash
python sub-skills/python-api/scripts/api_smoke.py --repo-root path/to/colorization --forward
```

## Version and refresh considerations

This skill was generated from a specific Git snapshot. If a newer checkout adds packaging metadata, changes public signatures, replaces weight URLs, or adds first-class training/batch workflows, refresh this skill before relying on the old guidance.
