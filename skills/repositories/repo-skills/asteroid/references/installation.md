# Installation notes

Asteroid's generated runtime is designed to install without the original repository checkout.

Use the bundled runtime bootstrap helper and its skill-local requirements file instead of a source-tree editable install:

```bash
python scripts/install_runtime.py
python scripts/install_runtime.py --with-tests
python -m pip install -r scripts/runtime_requirements.txt
```

Optional flags:

- `--index-url` for a primary pip mirror, or `--extra-index-url` for a PyTorch/backend wheel index
- `--requirements` to point at a different self-contained requirements file when you intentionally customize the runtime
- `--package` to add one or more extra package specifiers without editing the bundled runtime list
- `--with-tests` to add `pytest`
- `--skip-verify` if you only want installation and will verify later

## Runtime extras already handled by the generated skill

The runtime bootstrap installs `scripts/runtime_requirements.txt`, which includes the extra packages that inspection found were needed for public workflows:

- `asteroid` from the public package index
- `requests` for pretrained-model and hub helpers
- `librosa` so the full `asteroid.data` import surface works

## Optional additions

- `pytest` is only needed when you want to run the repo's own test suite; the bundled smoke scripts do not require it.
- GPU support comes from the installed PyTorch wheel. A CUDA-enabled wheel is optional for Asteroid but supported when available.

## Quick verification

- `python -m pip check`
- `python -I -c "import asteroid; print(asteroid.__version__)"`
- `python -I -c "import asteroid.data; print('asteroid.data ok')"`
- `python scripts/inspect_versions.py`
- `python scripts/smoke_training.py --device cpu`

## Notes from inspection

- A plain editable source install was not needed for the generated skill runtime; the bundled runtime bootstrap installs the public package and the discovered runtime extras directly.
- `librosa` is required before `asteroid.data` can import cleanly.
