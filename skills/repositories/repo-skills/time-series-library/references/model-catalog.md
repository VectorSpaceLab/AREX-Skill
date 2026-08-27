# Model Catalog and Dependency Surfaces

TSLib discovers models dynamically. `Exp_Basic` scans Python files in `models/`, and `--model <Name>` lazy-imports `models.<Name>` when the experiment builds the model. A valid model file normally exposes either `Model` or a class named after the file.

## Core model families

Core imports verified in the construction environment include:

- `DLinear`
- `TimesNet`
- `TimeXer`
- `PatchTST`
- `Reformer`
- `WPMixer`

Other source files include `Autoformer`, `Crossformer`, `ETSformer`, `FEDformer`, `FiLM`, `FreTS`, `Informer`, `KANAD`, `Koopa`, `LightTS`, `MICN`, `MSGNet`, `Mamba`, `MambaSimple`, `MambaSingleLayer`, `Moirai`, `MultiPatchFormer`, `Nonstationary_Transformer`, `PAttn`, `Pyraformer`, `SCINet`, `SegRNN`, `Sundial`, `TSMixer`, `TemporalFusionTransformer`, `TiDE`, `TiRex`, `TimeFilter`, `TimeMixer`, `TimeMoE`, `TimesFM`, `Transformer`, and `iTransformer`.

## Optional dependencies by source evidence

| Files/models | Dependency surface | Typical error when missing |
| --- | --- | --- |
| `Mamba.py`, `MambaSingleLayer.py`, `layers/MambaBlock.py` | `mamba_ssm` CUDA/Linux wheel matching PyTorch/CUDA/Python | `ModuleNotFoundError: No module named 'mamba_ssm'` |
| `Chronos.py`, `Chronos2.py` | `chronos-forecasting`, model downloads, CUDA/CPU device choices | `ModuleNotFoundError: No module named 'chronos'` |
| `TimesFM.py` | `timesfm`, pretrained model access, CUDA in source | `ModuleNotFoundError: No module named 'timesfm'` |
| `Moirai.py` | `uni2ts`, Moirai pretrained modules, CUDA in source | `ModuleNotFoundError: No module named 'uni2ts'` |
| `TiRex.py` | `tirex-ts`, pretrained model access | `ModuleNotFoundError: No module named 'tirex'` |
| `Sundial.py`, `TimeMoE.py` | `transformers`, remote-code model downloads | `ModuleNotFoundError: No module named 'transformers'` |
| `layers/SelfAttention_Family.py` | `reformer-pytorch`, `einops` | missing Reformer/attention dependency |
| `layers/DWT_Decomposition.py` | `PyWavelets` | missing `pywt` |
| `data_provider/uea.py` | `sktime` | missing `sktime` for UEA `.ts` classification |

## Model interface expectations

Most task models implement:

```python
class Model(nn.Module):
    def __init__(self, configs): ...
    def forward(self, x_enc, x_mark_enc, x_dec, x_mark_dec, mask=None): ...
```

The active experiment decides how to call `forward`:

- Forecasting passes encoder values/marks plus decoder input/marks.
- Imputation passes a random mask into models that implement imputation.
- Anomaly detection commonly calls model with only encoder data and `None` marks.
- Classification passes the padded sequence and padding mask.
- Zero-shot forecast expects the model to handle `task_name == 'zero_shot_forecast'`.

## Verified shape facts

Construction-time smoke checks with tiny tensors observed:

- `DLinear` long-term output shape `(batch, pred_len, channels)`.
- `TimesNet` long-term output shape `(batch, pred_len, channels)`.
- `TimeXer` with `features M` output shape `(batch, pred_len, channels)`.
- `TimeXer` with `features MS` output shape `(batch, pred_len, 1)` because it forecasts the target channel.

Use these facts when diagnosing channel-count mismatches.

## Choosing a model for smoke checks

- Use `DLinear` for very fast CPU forecasting plumbing checks.
- Use `TimesNet` for task coverage across forecasting, imputation, anomaly detection, and classification when dependencies are installed.
- Use `TimeXer` when the task concerns exogenous-variable forecasting or `features MS` behavior.
- Avoid Mamba and LTSM models for default smoke checks unless the user explicitly needs them and the optional packages/model caches are ready.
