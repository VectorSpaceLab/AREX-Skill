# Install and Backend Notes

## Purpose

Read this when you need to install PhiFlow, verify the minimal environment, or
understand which optional packages are needed for a workflow.

## Install choices

| Need | Recommended command | Notes |
| --- | --- | --- |
| Local checkout | `python -m pip install -e .` | Best for repo inspection and editing. |
| Published package | `python -m pip install phiflow` | Use when you do not need the checkout. |
| Web UI | `python -m pip install dash plotly` | Needed for Dash/Plotly display support. |
| Torch backend | install the torch wheel that matches the environment | Only when a workflow needs PyTorch backend registration or CUDA. |
| JAX backend | install `jax` / `jaxlib` compatible with the host | CPU-only JAX is enough for many verification tasks. |
| TensorFlow backend | install `tensorflow-cpu` or the GPU build | Use the variant that matches the workflow. |

PhiFlow itself declares `phiml>=1.14.0`, `matplotlib>=3.5.0`, and `packaging`.
The `phiml` dependency brings in the tensor and backend layer used by the public
API.

## Minimal verification path

```bash
python scripts/check_install.py --show-backends
```

Run that helper from the generated skill directory so the bundled script resolves correctly.

The script confirms:

- `phi` imports successfully
- the `phiflow` distribution metadata is present
- the minimal config check passes
- the package reports the Dash / Plotly status used by the web UI
- the backend registry can be printed when requested

## Backend notes

- `phi.detect_backends()` only lists backends that are actually installed and
  importable.
- A successful CPU import does not prove GPU readiness.
- Do not install every optional backend just because one workflow needs one of
  them.
- If you need a specific backend for gradients or accelerator work, install
  that backend first and then rerun the smoke check.

## When to read this before other sub-skills

Read this first whenever a task starts with one of these signals:

- `pip install`
- `phi.verify()`
- `phi.detect_backends()`
- `dash`
- `plotly`
- `torch`, `jax`, or `tensorflow` installation questions
- missing import / missing dependency / backend registration errors
