# Install and Environment Notes

## Purpose

Read this before launching Informer2020 workflows or debugging import/backend failures. The repository is source-style: it exposes Python modules and a forecasting launcher from a checkout rather than a packaged distribution.

## Dependency baseline

The project documentation pins a legacy research stack:

| Dependency | Documented version |
| --- | --- |
| Python | 3.6 |
| PyTorch | 1.8.0 |
| NumPy | 1.19.4 |
| pandas | 0.25.1 |
| scikit-learn | 0.21.3 |
| matplotlib | 3.1.1 |

Use those pins when exact historical reproduction matters. If a modern environment is already required by the surrounding project, validate it with the bundled smoke helpers before trusting long-run results. For this snapshot, avoid NumPy 2.x unless you patch the early-stopping helper, because the code uses the removed `np.Inf` alias.

## Source-style usage

There is no package metadata to install as an editable distribution. Use one of these patterns:

1. Run from the repository checkout so local modules such as `models`, `data`, `exp`, and `utils` are importable.
2. Or add the checkout root to `PYTHONPATH` before running source-compatible helpers.
3. Keep generated outputs in an explicit work directory when possible so `checkpoints/` and `results/` do not pollute the source tree.

Minimal import check:

```bash
python - <<'PY'
from models.model import Informer, InformerStack
from data.data_loader import Dataset_Custom, Dataset_Pred
from exp.exp_informer import Exp_Informer
print('Informer2020 source imports OK')
PY
```

## Backend behavior

- CPU is sufficient for tiny validation and custom-data smoke runs.
- CUDA is used automatically when visible and enabled by the source launcher.
- Passing a string value such as `False` to the GPU flag is unreliable because the flag is parsed as a Python `bool` from a string. Prefer the bundled smoke helper's `--backend cpu` path or hide CUDA when a CPU-only run is required.
- Multi-GPU mode wraps the model with `DataParallel` and uses the first listed device as the primary GPU.

## Data acquisition boundaries

Built-in benchmark names expect CSV files under the chosen data root. Those datasets are external and are not bundled with this skill. Use custom CSV smoke data first, then acquire benchmark data deliberately if the task requires reproduction-scale results.

The original project includes Docker and dataset-download automation, but those targets perform container builds or network downloads. Treat them as historical context, not as the default validation path for this skill.

## Recommended preflight

1. Run [`../scripts/make_tiny_forecast_csv.py`](../scripts/make_tiny_forecast_csv.py) to create a small custom CSV.
2. Run [`../scripts/check_forecast_csv.py`](../scripts/check_forecast_csv.py) with the intended `features`, `target`, `seq_len`, `pred_len`, and `freq`.
3. Run [`../scripts/run_forecasting_smoke.py`](../scripts/run_forecasting_smoke.py) without `--execute` first to inspect the generated command.
4. Execute a small smoke run only after the dry-run command and CSV validation look correct.
