# Model Catalog and Dependencies

TSLib's model catalog is the set of Python files under `models/`. The README groups them into benchmarked models, newly added baselines, and large time-series models. The runtime mechanism is simpler: `Exp_Basic` scans `models/*.py`, maps the file basename to an import path, then lazy-imports the selected module when `--model <Name>` is used.

## Core models for ordinary smoke checks

Use these when the goal is to validate data, CLI, and experiment plumbing with minimal optional dependency risk:

| Model | Good for | Notes |
| --- | --- | --- |
| `DLinear` | Fast CPU long-term forecasting smoke | Small dependency surface. |
| `TimesNet` | README examples across forecasting, imputation, anomaly detection, classification | Uses FFT/Inception blocks and task-specific forward branches. |
| `TimeXer` | Exogenous or target-channel forecasting | `features MS` returns target-only forecasts. |
| `PatchTST` | Forecasting/classification-style transformer baseline | Useful when PatchTST scripts are the template. |
| `Transformer`, `Autoformer`, `Informer`, `Reformer` | Transformer-family baselines | Reformer requires `reformer-pytorch`. |

## Optional-heavy model families

| Model files | What they need | Why to check first |
| --- | --- | --- |
| `Mamba.py`, `MambaSingleLayer.py`, `layers/MambaBlock.py` | `mamba_ssm` and a CUDA/Linux wheel matching Python, PyTorch, CUDA, and ABI | Missing or mismatched wheels fail at import or kernel runtime. |
| `Chronos.py`, `Chronos2.py` | `chronos-forecasting`, model cache/network, device compatibility | Source uses `BaseChronosPipeline.from_pretrained`. |
| `TimesFM.py` | `timesfm`, pretrained model access, CUDA in source | Source creates `TimesFM_2p5_200M_torch` on CUDA. |
| `Moirai.py` | `uni2ts`, Moirai pretrained modules, CUDA in source | README suggests `uni2ts --no-deps`; full runtime may require more packages. |
| `TiRex.py` | `tirex-ts`, pretrained model access | Source calls `load_model("NX-AI/TiRex")`. |
| `Sundial.py`, `TimeMoE.py` | `transformers`, remote-code model access | Source uses `trust_remote_code=True`; require explicit model trust/network decisions. |
| `WPMixer.py` | `PyWavelets` through wavelet layers | Install `PyWavelets` for wavelet decomposition paths. |
| `Reformer.py`, attention layers | `reformer-pytorch`, `einops` | Needed by Reformer attention implementation. |

## Inspecting availability

From a TSLib checkout:

```bash
python sub-skills/foundation-models-and-customization/scripts/inspect_tslib_models.py --repo-root . --optional-models
```

Interpretation:

- A core model import failure usually means the base environment is incomplete.
- An optional model import failure is expected unless that model family was intentionally installed.
- Import success is not the same as end-to-end execution for models that download pretrained weights or require CUDA.

## Model task support

Not every model implements every task branch. When adding or choosing a model, inspect its `forward` method for branches such as:

- `long_term_forecast` / `short_term_forecast`
- `imputation`
- `anomaly_detection`
- `classification`
- `zero_shot_forecast`

If a task branch returns `None` or raises for unsupported tasks, choose another model or implement that branch before running `run.py`.
