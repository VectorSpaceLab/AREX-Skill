# Model Overview

This sub-skill owns the six core long-term forecasting model families in the
root workflow.

## Quick choice guide

| Model | Best when | Important notes |
| --- | --- | --- |
| Linear | You want the cheapest baseline or a fast sanity check | Single linear layer. Can be shared across channels or split with `--individual`. |
| DLinear | Trend and seasonality are both visible | Decomposes the series into seasonal and trend branches before forecasting. Supports weight visualization. |
| NLinear | The series has a strong last-value shift | Subtracts the last observed value, runs a linear layer, then adds the value back. |
| Informer | You want a former-style baseline with sparse attention | Uses ProbSparse attention and the encoder-decoder path. |
| Transformer | You want the vanilla attention baseline | Full attention, most useful as a comparison point. |
| Autoformer | You want the paper's decomposition-based former baseline | Uses decomposition plus autocorrelation; prefer CUDA for test/predict runs. |

## Linear family

### Linear

- One linear layer maps `seq_len` to `pred_len`.
- The forward path is simple and fast.
- Use it when you want a baseline that is easy to reason about.

### DLinear

- Decomposes the input into seasonal and trend components with a moving average.
- Applies one linear layer to each component and sums the outputs.
- Best when the series has a clear trend and periodicity.
- The checkpoint contains `Linear_Seasonal.weight` and `Linear_Trend.weight`,
  which are the weights that the plotting helper visualizes.

### NLinear

- Subtracts the last value of the input sequence before the linear layer.
- Adds the last value back after forecasting.
- Good when the main difficulty is distribution shift across the train and test
  windows.

## Former family

### Informer

- Uses ProbSparse attention in the encoder and decoder.
- Shares the same encoder-decoder argument shape contract as the other former
  models.
- The `embed_type` sweep is relevant here.

### Transformer

- Uses the full attention baseline.
- Useful as a reference point for comparing the more specialized former
  architectures.

### Autoformer

- Uses series decomposition and autocorrelation.
- In this repo, the test and predict paths are the risky ones on CPU because the
  autocorrelation code path calls `.cuda()` during inference.
- If you need a quick forward smoke, keep the model in train mode or use the
  bundled smoke helper on a CUDA-capable machine.

## Flags that matter by family

| Family | Flags that matter most | Notes |
| --- | --- | --- |
| Linear | `--seq_len`, `--pred_len`, `--enc_in`, `--individual` | `--dec_in` and `--c_out` are mostly consistency flags. |
| DLinear | `--seq_len`, `--pred_len`, `--enc_in`, `--individual` | Use the same `--individual` convention as the benchmark scripts. |
| NLinear | `--seq_len`, `--pred_len`, `--enc_in`, `--individual` | Same channel handling as Linear. |
| Informer | `--seq_len`, `--label_len`, `--pred_len`, `--embed_type`, `--factor`, `--e_layers`, `--d_layers`, `--d_model`, `--n_heads` | Needs the decoder path and embedding branch. |
| Transformer | Same as Informer | Full attention instead of ProbSparse attention. |
| Autoformer | Same as Informer plus `--moving_avg` | Uses decomposition in both the encoder and decoder. |

## Benchmark-script defaults

The reference scripts usually follow these patterns:

- Linear-family long forecasting: longer look-back windows such as `336` and
  `--individual` for multivariate runs.
- Former long forecasting: `seq_len=96`, `label_len=48`, `factor=3`,
  `e_layers=2`, `d_layers=1`.
- Embedding sweeps: `embed_type` values `1` through `4` for the former models.
- Look-back sweeps: keep the model fixed and vary `seq_len` across the paper's
  grid.

If a request is only about one of those sweep families, use the workflow
reference rather than rewriting the model logic.
