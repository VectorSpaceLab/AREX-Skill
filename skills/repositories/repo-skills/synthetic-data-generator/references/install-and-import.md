# Install and import reference

## Installation choices

For normal users, prefer the public package:

```bash
pip install sdgx
```

For local development from a checkout:

```bash
pip install .
# or, when running repo tests that need test-only packages:
pip install '.[test]'
```

The package metadata declares Python `>=3.9` and includes pandas, NumPy `<2`, SciPy, scikit-learn, Faker, matplotlib, PyTorch `>=2`, table-evaluator, Click, pluggy, loguru, pyarrow, pydantic v2, cloudpickle, OpenAI, python-dotenv, and joblib. The inspected checkout also imports `psutil` through its SDV/RDT component path; install `psutil` if an otherwise successful install fails with `ModuleNotFoundError: No module named 'psutil'`.

## Minimal checks

```bash
python - <<'PY'
import sdgx
print(sdgx.__version__)
PY

sdgx --help
sdgx list-models
sdgx list-data-connectors
sdgx list-data-processors
sdgx list-data-exporters
sdgx list-cachers
```

Run the bundled environment check for a fuller registry/backend snapshot:

```bash
python scripts/check_sdgx_environment.py --json
```

Use `--require-cuda` only when the task explicitly depends on CUDA execution.

## CPU and CUDA

`CTGANSynthesizerModel` defaults to `device="cuda"` when `torch.cuda.is_available()` is true, otherwise CPU. For deterministic low-resource checks, pass `CTGANSynthesizerModel(epochs=1, batch_size=10, device="cpu")` or CLI `--model_kwargs '{"epochs":1,"batch_size":10,"device":"cpu"}'`.

CUDA is useful for CTGAN but not mandatory for core package inspection or small CPU smoke tests. If CUDA is required, verify it with the active environment's PyTorch:

```bash
python - <<'PY'
import torch
print(torch.__version__, torch.version.cuda)
print(torch.cuda.is_available(), torch.cuda.device_count())
if torch.cuda.is_available():
    print(torch.cuda.get_device_name(0), torch.cuda.get_device_capability(0))
    torch.empty((1,), device="cuda")
PY
```

## Environment variables

- `SDGX_LOG_LEVEL`: loguru level, defaults to `INFO`.
- `SDGX_LOG_TO_FILE`: set to `true`/`True` to add a log file handler.
- `SDG_NDARRAY_CACHE_ROOT`: root for `NDArrayLoader` column-wise array caches.
- `OPENAI_KEY`: OpenAI-compatible API key for `SingleTableGPTModel`.
- `OPENAI_URL`: OpenAI-compatible API base URL for `SingleTableGPTModel`; default is `https://api.openai.com/v1/`.
- `SDG_FORCE_LOAD_CPU`: if set, prevents statistic-model load logic from preferring CUDA during unpickling.

## Import surface reminders

- `sdgx` package version comes from `sdgx.__version__`.
- `sdgx.models.manager.ModelManager().registed_models` currently includes `ctgan` via local model registration.
- `GaussianCopulaSynthesizerModel` is available by direct import even though it is not currently listed by `ModelManager` in the inspected version.
- `GeneratorConnector` is a library-only helper and is not registered by default in `DataConnectorManager`.
- CLI command names use Click's hyphenated command conversion: `list-models`, `list-data-connectors`, `list-data-processors`, `list-cachers`, and `list-data-exporters`.
