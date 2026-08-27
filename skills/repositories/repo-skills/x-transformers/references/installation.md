# Installation and inspection

x-transformers is a Python package with the public distribution name `x-transformers` and the import package `x_transformers`.

## Baseline install

```bash
pip install x-transformers
```

## Local editable install

For a local checkout, use editable mode instead of copying files into site-packages:

```bash
pip install -e <checkout>
```

If you want the test helpers as well:

```bash
pip install -e <checkout>[test]
```

## Useful extras

| Extra | Purpose |
| --- | --- |
| `test` | Pytest-based repository tests |
| `examples` | Recipe dependencies such as progress bars and optimizer extras |
| `flash-pack-seq` | Optional flash-attention packed-sequence path |

Examples:

```bash
pip install "x-transformers[test]"
pip install "x-transformers[examples]"
pip install "x-transformers[flash-pack-seq]"
```

## Runtime notes

- Python 3.11 is a safe inspection default, but the package metadata supports Python 3.9 and newer.
- The base package depends on PyTorch, einops, einx, loguru, packaging, and torch-einops-utils.
- The optional flash-attention path is only relevant when you intentionally need packed-sequence or flash-attn behavior on compatible CUDA hardware.
- Use `scripts/probe_backend.py` before choosing a CUDA-sensitive workflow.

## Minimal checks

```bash
python -c "import x_transformers; print(x_transformers.__file__)"
python -m pip check
python scripts/probe_backend.py
```

Use `scripts/smoke_models.py` when you want a small runtime check that exercises the package APIs after installation.
