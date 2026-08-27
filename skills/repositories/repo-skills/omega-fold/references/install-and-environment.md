# Install and Environment

Use this reference before running OmegaFold helpers, CLI inference, or Python API snippets.

## Package Identity

- Distribution metadata name: `OmegaFold`.
- Import module: `omegafold`.
- Console script: `omegafold=omegafold.__main__:main`.
- Runtime dependency intent: Biopython and PyTorch.
- Release package version observed from metadata: `0.0.0`.

## Python and Dependency Compatibility

The package metadata declares Python `>=3.8`, but `setup.py` constructs a hard PyTorch wheel URL only for Python 3.8, 3.9, and 3.10. Prefer one of those Python versions for source installs unless you intentionally override the Torch installation path.

The release requirements pin a legacy CUDA wheel:

```text
biopython
torch==1.12.0+cu113
```

When using Torch 1.12, constrain NumPy below 2 because Torch 1.12 was built against NumPy 1.x:

```bash
python -m pip install "numpy<2"
```

If you choose a newer Torch for CPU, CUDA, or MPS compatibility, verify OmegaFold imports and helper scripts before running full inference.

## Safe Installation Checks

Use these checks before full inference:

```bash
python -m pip show OmegaFold
python - <<'PY'
import omegafold
print('OmegaFold import ok')
print('model1 struct_embedder', omegafold.make_config(1).struct_embedder)
print('model2 struct_embedder', omegafold.make_config(2).struct_embedder)
PY
omegafold --help
```

If `omegafold` is missing from `PATH` but the package imports, try the installed module entry point:

```bash
python -m omegafold --help
```

## Bundled Environment Helper

Run the root helper for a no-download report:

```bash
python scripts/check_omega_fold_environment.py
```

It checks:

- Python version.
- `OmegaFold` distribution metadata.
- `omegafold` importability.
- Key API signatures and valid/invalid `make_config` behavior.
- Torch, CUDA, and MPS availability.
- Console script discovery and `--help` flags when available.

The helper does not load model weights, download checkpoints, or instantiate the full model.

## Backend Selection

OmegaFold's device resolver chooses devices in this order when `--device` is omitted:

1. CUDA if `torch.cuda.is_available()`.
2. MPS if `torch.backends.mps.is_available()`.
3. CPU otherwise.

Explicit unavailable devices raise `ValueError`, so validate before full runs:

```bash
python - <<'PY'
import torch
print('torch', torch.__version__)
print('cuda available', torch.cuda.is_available())
print('mps available', getattr(torch.backends, 'mps', None) and torch.backends.mps.is_available())
PY
```

Use CPU only for tiny checks or when the user accepts slow inference. Use MPS only with a PyTorch build that supports Apple Silicon MPS. Use CUDA only when the selected Torch wheel works with the driver and visible GPU.

## Checkpoint and Network Policy

Full CLI inference selects model-specific checkpoints:

- Model 1 defaults to a release-1 checkpoint cached as `model.pt`.
- Model 2 defaults to a release-2 checkpoint cached as `model2.pt`.

If the selected checkpoint file is missing and a weights URL is active, OmegaFold downloads before inference. For offline or reproducible runs, require a local file and pass it explicitly:

```bash
omegafold input.fasta outputs/ --model 2 --weights_file /path/to/model2.pt
```

Do not start full inference when downloads are disallowed and no local checkpoint exists.
