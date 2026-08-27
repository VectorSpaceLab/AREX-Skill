# Troubleshooting install and inspection

## When to read this

Use this matrix when a spaCy environment fails to import, a compiled dependency mismatch appears, a model load fails, `validate` reports incompatible pipelines, optional language/tokenizer tables are missing, GPU status is confusing, CUDA/CuPy does not line up, or the shell cannot find the `spacy` command.

## Quick triage order

1. Confirm the active Python is supported: `python -VV` and `python -c "import sys; print(sys.version_info[:3])"` should report Python `>=3.9,<3.15` for this spaCy snapshot.
2. Confirm the base package: `python -c "import spacy; print(spacy.__version__)"`.
3. Run the no-download blank check: `python scripts/spacy_healthcheck.py`.
4. Use `python -m spacy --help` and `python -m spacy info --silent` before relying on a bare `spacy` command.
5. Only then diagnose trained model packages, optional extras, or accelerator backends.

## Failure matrix

| Symptom / error fragment | Likely cause | Recovery | Validate |
| --- | --- | --- | --- |
| `ModuleNotFoundError: No module named 'spacy'` | spaCy is not installed in the active Python environment | Install into the active environment with `python -m pip install -U spacy` or use the project environment that already contains spaCy | `python -c "import spacy; print(spacy.__version__)"` |
| `ModuleNotFoundError` for `thinc`, `cymem`, `preshed`, `murmurhash`, `srsly`, `pydantic`, `typer`, or `click` | Partial install, interrupted install, wrong environment, or missing base dependency | Run `python -m pip check`; reinstall in a clean environment with `python -m pip install --force-reinstall -U spacy`; avoid mixing conda and pip unless intentional | `python -m pip check` then bundled healthcheck |
| `ImportError`, `ValueError: numpy.dtype size changed`, `undefined symbol`, or similar compiled-extension mismatch | Binary wheels were built against incompatible Python, NumPy, Cython, or ABI; source build artifacts are stale | Use supported Python; upgrade installer tools; reinstall spaCy and compiled dependencies; for source checkout run `python -m pip install --no-build-isolation --editable .` after installing build requirements; if needed, recreate the environment | `python -m pip check`; `python -c "import spacy; print(spacy.__version__)"` |
| Installer says `Requires-Python` or cannot find a matching distribution | Unsupported Python version or platform/architecture with no compatible wheel | Switch to Python `>=3.9,<3.15`; prefer a 64-bit CPython environment with binary wheels; for source builds ensure compiler and Python headers are present | `python -VV`; `python -m pip install -U spacy` |
| `python -m spacy --help` works but `spacy --help` says command not found | Console-script directory is not on `PATH`, or the shell command belongs to another environment | Use `python -m spacy ...` for all commands, or reinstall spaCy in the active environment so the console script is generated | `python -m spacy info --silent` |
| `spacy --version` or `spacy` points to the wrong environment | Shell path shadowing or stale console script | Prefer `python -m spacy`; check `python -c "import spacy; print(spacy.__version__)"` in the intended environment | `python -m spacy --help` |
| `OSError: [E050] Can't find model 'en_core_web_sm'` | Base spaCy is installed but the trained pipeline package is not installed, or the model name/path is wrong | If pretrained components are required, install the model with `python -m spacy download en_core_web_sm` or install a pinned model wheel; otherwise use `spacy.blank("en")` | `python -m spacy validate`; `python scripts/spacy_healthcheck.py --model en_core_web_sm --require-model` |
| `OSError: [E941] Can't find model 'en'` | Obsolete shortcut from spaCy v2-era examples | Use `spacy.blank("en")` for a blank English pipeline or `spacy.load("en_core_web_sm")` after installing the full model package | Blank tokenizer smoke |
| `spacy.load(path)` reports missing model directory/config/meta | The path is not a saved spaCy pipeline directory or required files are absent | Check that the directory contains a valid spaCy pipeline with `config.cfg`, `meta.json`, and component data; use the exact user-supplied pipeline output directory | `python -m spacy info /path/to/pipeline --silent` if local path disclosure is acceptable |
| `python -m spacy validate` returns `1` and lists incompatible pipelines | Trained pipeline packages are stale relative to the installed spaCy version | Update/reinstall the listed pipeline packages; for official packages, `python -m spacy download <pipeline-name>` prints compatible install guidance | Rerun `python -m spacy validate` |
| `python -m spacy validate` cannot load compatibility data | Offline environment, blocked network, proxy issue, or service error | Treat this as a validation-environment limitation, not a base import failure; use pinned pipeline package versions or run validate where network access is allowed | Base healthcheck plus package metadata checks |
| Lemmatizer or normalization complains about missing lookup tables | `spacy-lookups-data` is absent and the selected blank pipeline/language needs lookup tables | Install `python -m pip install "spacy[lookups]"` or `python -m pip install spacy-lookups-data`; reinitialize the blank pipeline | Re-run the lemmatizer initialization/check |
| `spacy.blank("ja")`, `spacy.blank("ko")`, or `spacy.blank("th")` fails with missing tokenizer dependency | Optional language tokenizer extra is absent | Install only the needed extra: `python -m pip install "spacy[ja]"`, `"spacy[ko]"`, or `"spacy[th]"` | Run a one-sentence blank tokenizer smoke for that language |
| `spacy.prefer_gpu()` returns `False` | GPU/CuPy/Apple backend is unavailable, not selected, or not compatible | If CPU is acceptable, continue on CPU. If acceleration is required, install the matching CUDA or Apple extra and verify the hardware/runtime | `python scripts/spacy_healthcheck.py --prefer-gpu` |
| `spacy.require_gpu()` raises `ValueError: Cannot use GPU, CuPy is not installed` or similar | GPU is a hard requirement but a compatible backend stack is missing | Install the correct extra, e.g. `python -m pip install "spacy[cuda12x]"`, or remove the hard GPU requirement | `python scripts/spacy_healthcheck.py --require-gpu --gpu-id 0` |
| CuPy import fails or reports driver/runtime mismatch | Wrong CUDA extra for the host runtime, multiple CuPy wheel families installed, or driver/runtime mismatch | Remove conflicting CuPy packages; install the single matching spaCy CUDA extra (`cuda11x`, `cuda12x`, or an older exact variant); verify with a CuPy import before claiming GPU | `python -c "import cupy; print(cupy.__version__)"` and GPU healthcheck |
| Apple acceleration requested on non-Apple host | `spacy[apple]` / `thinc-apple-ops` is not applicable to the host | Do not treat this as a required backend unless the downstream environment is Apple Silicon; use CPU or verify on the actual Apple host | `python scripts/spacy_healthcheck.py --prefer-gpu` on target host |
| Transformer component names or imports fail after base install | `spacy-transformers` extra or model-specific dependencies are absent | Install `python -m pip install "spacy[transformers]"`; route config/component details to the relevant sub-skills; verify model weights/cache separately | `python -c "import spacy_transformers"` |

## Interpreting CPU versus optional-backend results

- Base success means `import spacy`, `spacy.__version__`, blank English tokenization, and CLI help/info all pass.
- A missing model package, failed `validate` due to stale models, `prefer_gpu() == False`, or absent optional language tokenizer extra does not invalidate the base CPU package.
- A user who explicitly requires a model package, CUDA, Apple acceleration, transformers, or language tokenizer extra needs a separate hard gate for that capability.

## Recovery command bundle

Use this sequence when the environment is disposable and the user wants a clean base CPU reinstall:

```bash
python -m pip install -U pip setuptools wheel
python -m pip install --force-reinstall -U spacy
python -m pip check
python -m spacy info --silent
python scripts/spacy_healthcheck.py
```

Use this sequence when base spaCy is healthy but a trained English pipeline is missing:

```bash
python -m spacy download en_core_web_sm
python -m spacy validate
python scripts/spacy_healthcheck.py --model en_core_web_sm --require-model
```

Use this sequence when GPU is optional and should not block CPU work:

```bash
python scripts/spacy_healthcheck.py --prefer-gpu
# If this reports a warning rather than failure, continue with CPU unless the user requires GPU.
```

Use this sequence when GPU is mandatory:

```bash
python -m pip install "spacy[cuda12x]"  # choose the variant that matches the target CUDA runtime
python -c "import cupy; print(cupy.__version__)"
python scripts/spacy_healthcheck.py --require-gpu --gpu-id 0
```
