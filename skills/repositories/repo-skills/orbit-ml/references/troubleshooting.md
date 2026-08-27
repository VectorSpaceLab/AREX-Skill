# Orbit troubleshooting

## Purpose

Use this page for install, import, backend, and cross-cutting runtime failures
before or after you route to a subskill.

## Common failures

| Symptom or error fragment | Likely cause | Recovery | Owner |
| --- | --- | --- | --- |
| `ModuleNotFoundError: No module named 'orbit'` | `orbit-ml` is not installed in the active environment | Install `orbit-ml`, then run `scripts/check_install.py` | root / install |
| `ModuleNotFoundError: No module named 'cmdstanpy'` or `cmdstan_path()` fails | Stan backend is missing or CmdStan is not discoverable | Install `cmdstanpy` and a compatible CmdStan, then rerun `scripts/check_install.py` | root / install |
| `ModuleNotFoundError: No module named 'pyro'` | Pyro / Torch dependencies are missing | Install the package dependencies required for `pyro-svi`, or switch to a Stan-backed path | `forecasting`, `ktr`, `custom-models` |
| `ImportError` from `orbit.template.ktr` | Circular import between `orbit.template.ktr` and `orbit.models` | Import KTR through `orbit.models.KTR` instead of importing the template module directly | `custom-models`, `ktr` |
| `ModuleNotFoundError: No module named 'statsmodels'` when plotting | The evaluation plot surface imports statsmodels at module import time | Install the diagnostics plotting dependency set, then retry the plotting helper | `evaluation` |
| Remote sample loader timeout / 404 / SSL error | The sample dataset helpers fetch public CSVs over the network | Use a synthetic frame or local cached data for smoke checks | `utilities` |
| Headless Matplotlib `TclError` | Interactive backend in a non-GUI session | Use a non-interactive backend such as `Agg` or call the plotting helpers with `is_visible=False` | `evaluation`, `utilities` |

## Recovery order

1. Run `python scripts/check_install.py`.
2. If the failure is model-specific, open the matching subskill.
3. If the failure is about plotting, backtests, or WBIC/BIC, open
   `evaluation`.
4. If the failure is about knots, multi-seasonality, or KTR/KTRLite, open `ktr`.
5. If the failure is about sample data, simulation, or feature helpers, open
   `utilities`.
6. If the failure is about custom templates or backend wiring, open
   `custom-models`.
