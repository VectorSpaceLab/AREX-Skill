# Cross-cutting troubleshooting

Read this for failures that affect more than one colorization workflow. For saved-output workflows, also read `sub-skills/automatic-colorization/references/troubleshooting.md`; for tensor/API workflows, also read `sub-skills/python-api/references/troubleshooting.md`.

## `ModuleNotFoundError: No module named 'colorizers'`

The repo is not packaged as an installable distribution in this checkout. Make the clone root importable:

```bash
PYTHONPATH="path/to/colorization" python -c "import colorizers; print(colorizers.__file__)"
```

Or use a bundled helper with `--repo-root path/to/colorization`. The path should be the directory that contains `colorizers/`, not the `colorizers/` directory itself.

## Bad requirement names

If `pip install -r requirements.txt` fails on names such as `PIL` or `skimage`, install canonical packages directly:

```bash
python -m pip install torch numpy matplotlib pillow scikit-image ipython
```

`argparse` does not need installation on modern Python.

## `ModuleNotFoundError: No module named 'IPython'`

The model source imports `IPython.embed` at module import time. Install `ipython` in the same environment used to import `colorizers`.

## Pretrained-weight download failures

The wrapper functions default to pretrained weights:

```python
colorizers.eccv16(pretrained=True)
colorizers.siggraph17(pretrained=True)
```

On first use, they call `torch.utils.model_zoo.load_url` with hash checking for public weight files. Failures can come from blocked network access, SSL/proxy issues, an unwritable PyTorch cache, or a corrupt partial cache file.

Recovery:

1. For import/API tests, switch to `pretrained=False`.
2. For quality colorization, retry where the public weight URLs are reachable or where the weights already exist in the PyTorch cache.
3. If hash checking fails, remove the incomplete cached file and retry.
4. If the cache is not writable, configure a writable PyTorch cache location according to the user's environment policy.

## CUDA and accelerator confusion

CUDA is optional. The default README workflow runs on CPU unless the user asks for GPU. Use CPU when portability matters:

```bash
python scripts/check_env.py --repo-root path/to/colorization --device cpu --check-forward
```

Use CUDA only when the installed PyTorch build and host device agree:

```bash
python scripts/check_env.py --repo-root path/to/colorization --device cuda --check-forward
```

If CUDA fails, do not treat it as a correctness failure for CPU colorization. Route to CPU unless the task explicitly requires GPU placement or performance.

## Headless or notebook execution

The original release script displayed a Matplotlib figure. The bundled helper scripts are headless and save outputs or JSON diagnostics instead. If a notebook or GUI backend interferes, run the helper as a plain terminal script.

## Unsupported requests

This skill covers the minimal PyTorch test-time release. It does not provide training, Caffe-branch behavior, representation-learning tests, or maintained benchmark pipelines. For those tasks, inspect a suitable source branch or paper implementation separately instead of extending these runtime instructions by assumption.
