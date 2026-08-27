# Installation and optional dependencies

## Package variants

Darts 0.46.1 is installed from the `darts` distribution and imports as `darts`. Use Python 3.10+.

| Need | pip install | Conda-forge install | Notes |
| --- | --- | --- | --- |
| Core package | `pip install darts` | `conda install -c conda-forge u8darts` | `TimeSeries`, preprocessing, metrics, anomaly APIs, statistical/regression models whose dependencies are in the base package. |
| PyTorch models | `pip install "darts[torch]"` | `conda install -c conda-forge -c pytorch u8darts-torch` | Adds PyTorch, PyTorch Lightning, TensorBoardX, Hugging Face Hub, and safetensors. Choose a CUDA/ROCm/MPS-capable torch wheel separately when GPU execution is required. |
| Non-torch optional models | `pip install "darts[notorch]"` | `conda install -c conda-forge u8darts-notorch` | Adds Prophet, LightGBM, XGBoost, CatBoost, and StatsForecast families. |
| Broad local environment | `pip install "darts[all]"` | `conda install -c conda-forge -c pytorch u8darts-all` | Use only when both torch and notorch extras are needed. It still does not include every optional wrapper listed below. |

As of Darts >=0.41.0, use `darts` rather than legacy `u8darts` for pip installs. Old `u8darts[option]` installs map to `darts[option]`.

## Optional dependencies not fully covered by `all`

Some wrappers require separate packages or external artifacts:

- `NeuralForecastModel`: `neuralforecast>=3.0.0`.
- `TiRexModel`: `tirex-ts>=1.4.0`.
- Foundation wrappers such as Chronos/TimesFM families may require local model weights/cache, approved network downloads, and enough memory. Do not silently trigger downloads in restricted environments.
- ONNX, Optuna, Ray, Polars, Plotly, and notebook/runtime tooling are developer or optional workflow dependencies, not part of the smallest runtime install.

## Backend evidence boundary

The generated skill baseline verified:

- Core `darts` import, package metadata, and `TimeSeries` availability.
- Required CPU workflows for data, preprocessing, core forecasting, anomaly, and metrics.
- Optional CPU PyTorch availability and a tiny CPU torch model smoke.

The baseline did **not** verify:

- CUDA, ROCm, MPS, TPU, or other accelerator execution.
- Foundation model weight download/cache availability.
- Heavy optional model families from `notorch` or separately installed extras.

When a user asks for GPU or foundation model execution, first verify the target environment instead of assuming that a CPU import proves backend readiness.

## Quick checks

```bash
python - <<'PY'
import importlib.util
import darts
from darts import TimeSeries
print("darts", darts.__version__)
print("TimeSeries", TimeSeries)
for name in ["torch", "pytorch_lightning", "prophet", "lightgbm", "xgboost", "catboost", "statsforecast", "neuralforecast", "tirex"]:
    print(name, bool(importlib.util.find_spec(name)))
PY
```

Then run the bundled root doctor:

```bash
python scripts/darts_doctor.py --json
```

Run it from inside this skill directory after import/copy, or pass the script path explicitly from another working directory.
