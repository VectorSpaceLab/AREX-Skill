# Installation and Environment Setup

## Purpose

Read this before installing or repairing the `fedml` package. Use it for public install commands, editable installs from the repo checkout, and the minimal import check.

## Verified package facts

- Distribution name: `fedml`
- Version: `0.8.30`
- Console entry point: `fedml=fedml.cli.cli:cli`
- Supported Python classifiers in `python/setup.py`: 3.8, 3.9, 3.10
- Public docs also mention Linux, macOS, Windows, and Android support.
- Base install pulls PyTorch, click, aiohttp, boto3, fastapi, paho-mqtt, prettytable, pydantic, urllib/HTTP helpers, and the core FedML runtime.
- Optional extras in `python/setup.py` include `MPI`, `deepspeed`, `fhe`, `jax`, `llm`, `mxnet`, and `tensorflow`.

## Recommended install paths

### From PyPI

```bash
pip install fedml
```

### Editable install from this checkout

From the repository's `python/` directory:

```bash
pip install -e ./
```

Equivalent from the repo root:

```bash
pip install -e python
```

### Optional extras

Only add extras when a selected workflow needs them:

```bash
pip install "fedml[MPI]"
pip install "fedml[deepspeed]"
pip install "fedml[fhe]"
pip install "fedml[jax]"
pip install "fedml[mxnet]"
pip install "fedml[tensorflow]"
```

`llm` pulls the heavy LLM training dependencies used by `python/examples/train/llm_train/`.

## Minimal import check

Use the target environment Python, not the repository checkout Python:

```bash
python -c "import fedml; print(fedml.__version__); print(fedml.__file__)"
```

For a stricter check from a clean working directory:

```bash
python -I -c "import fedml; print(fedml.__version__)"
```

## CLI sanity checks

After install, the following commands should work without credentials or network access:

```bash
fedml --help
fedml version
fedml model --help
fedml launch --help
fedml run --help
```

Use `references/troubleshooting.md` when import fails, `fedml` points at the wrong environment, or the CLI surface differs from the docs.

## Notes

- `pip install fedml` is the public install path.
- `pip install -e python` is the best source checkout path for skill drafting.
- The repo's current CLI exposes `fedml network` for backend diagnostics; some docs still say `diagnosis`.
