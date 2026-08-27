# TimeMixer Model API Reference

This reference distills the TimeMixer model class and its direct layer dependencies into the operating API facts a future agent needs for safe model instantiation and shape debugging.

## Import and constructor

The model class is imported as:

```python
from models.TimeMixer import Model
model = Model(configs)
```

`configs` is an argparse-like object. It must expose the fields consumed by the model constructor and task-specific forward branches.

### Required configuration fields

| Field | Used for | Practical guidance |
| --- | --- | --- |
| `task_name` | Forward dispatch | One of `long_term_forecast`, `short_term_forecast`, `imputation`, `anomaly_detection`, `classification`. |
| `seq_len` | Input length and projection dimensions | Must match the length of `x_enc`; keep it large enough for all downsampled scales. |
| `label_len` | Constructor compatibility | Stored on the model; forecast `x_dec` is accepted but not used by this implementation. |
| `pred_len` | Forecast horizon | Forecast outputs have this temporal length; classification usually sets it to `0`. |
| `enc_in` | Input channel count | Set to the final feature dimension of `x_enc`. |
| `c_out` | Output channel count | For channel-independent forecast/reconstruction, set equal to the input channel count unless intentionally reshaping. |
| `num_class` | Classification projection | Required only for `classification`; output width equals this value. |
| `d_model` | Embedding width | Keep even for DFT smoke tests; keep `top_k <= d_model // 2 + 1` for `dft_decomp`. |
| `d_ff` | MLP hidden width | Used by cross-channel and output-cross layers. |
| `e_layers` | Number of PDM blocks | At least one block is typical. |
| `dropout` | Embedding and classification dropout | Set the model to eval mode for deterministic smoke output. |
| `embed` | Temporal embedding type | `timeF` expects continuous time features; `fixed`/`learned` expect calendar index tensors. |
| `freq` | Time-feature frequency | For `timeF`, hourly `h` uses four temporal features. |
| `moving_avg` | Moving-average decomposition kernel | Use an odd value so decomposition preserves temporal length. |
| `decomp_method` | PDM decomposition choice | `moving_avg` or `dft_decomp`; other strings raise `ValueError('decompsition is error')`. |
| `top_k` | DFT frequency retention | Used only when `decomp_method='dft_decomp'`. |
| `channel_independence` | Per-channel versus joint-channel path | `1` is the CLI default and treats variables independently in forecast/reconstruction; `0` embeds all channels jointly. |
| `use_norm` | Forecast/reconstruction normalization | `1` enables reversible normalization layers; `0` makes them pass-through. |
| `down_sampling_layers` | Number of extra scales | Use at least `1` for this implementation; benchmark-style configs commonly use `1` to `3`. |
| `down_sampling_window` | Scale ratio | Usually `2`; ensure the smallest scale length remains at least one. |
| `down_sampling_method` | Scale construction | `avg`, `max`, or `conv`; unsupported values bypass pooling but can break PDM scale expectations. |
| `use_future_temporal_feature` | Forecast decoder feature injection | `1` uses `x_mark_dec` in forecast only; `0` ignores future marks. |

## Forward signature

```python
out = model.forward(x_enc, x_mark_enc, x_dec, x_mark_dec, mask=None)
```

The branch is selected only by `configs.task_name`.

| Task name | Inputs consumed | Output shape | Notes |
| --- | --- | --- | --- |
| `long_term_forecast` | `x_enc`, optional `x_mark_enc`, optional `x_mark_dec`; `x_dec` is accepted but not used | `(B, pred_len, c_out)` | Uses multiscale encoder outputs and forecast predict layers; if `use_future_temporal_feature=1`, `x_mark_dec` must be supplied. |
| `short_term_forecast` | Same as long-term forecast | `(B, pred_len, c_out)` | Same model branch as long-term forecast; short-vs-long is an experiment/data distinction. |
| `imputation` | `x_enc`, `mask`, optional `x_mark_enc` placeholder | `(B, seq_len, c_out)` | `mask == 1` marks observed values. `x_mark_enc` is accepted but not used by the current branch after multiscale setup. All-zero observed counts can produce invalid normalization. |
| `anomaly_detection` | `x_enc` only; `x_mark_enc`/`x_dec` are ignored | `(B, seq_len, c_out)` | Reconstructs the input window after normalization and denormalization. |
| `classification` | `x_enc` and `x_mark_enc` as padding mask | `(B, num_class)` | `x_mark_enc` must be shaped `(B, seq_len)`, not temporal calendar features. |

## Input tensor contracts

| Tensor | Forecast | Imputation | Anomaly detection | Classification |
| --- | --- | --- | --- | --- |
| `x_enc` | Float `(B, seq_len, enc_in)` | Float `(B, seq_len, enc_in)` | Float `(B, seq_len, enc_in)` | Float `(B, seq_len, enc_in)` |
| `x_mark_enc` | Optional temporal features `(B, seq_len, time_dim)` | Optional placeholder; accepted but ignored after multiscale setup | Ignored; pass `None` | Padding mask `(B, seq_len)`, values 1 keep and 0 pad |
| `x_dec` | Accepted but unused; pass a compatible placeholder | Ignored | Ignored | Ignored |
| `x_mark_dec` | Required only when `use_future_temporal_feature=1`; shape `(B, pred_len, time_dim)` | Ignored | Ignored | Ignored |
| `mask` | Ignored | Observed-value mask broadcastable to `(B, seq_len, enc_in)` | Ignored | Ignored |

For `embed='timeF'` and `freq='h'`, use `time_dim=4`. For minute data (`freq='t'`), use `time_dim=5`. For fixed or learned temporal embeddings, marks must contain integer calendar fields in the expected order.

## Task-specific behavior

### Forecast branches

1. Optionally embed future temporal features from `x_mark_dec`.
2. Build multiscale versions of `x_enc` using the selected downsampling method.
3. Normalize each scale unless `use_norm=0`.
4. If `channel_independence=1`, reshape `(B, T, N)` into `(B*N, T, 1)` before embedding, then reshape predictions back to `(B, pred_len, c_out)`.
5. Run the PDM block stack on every scale.
6. Apply per-scale `predict_layers`, optionally add future temporal embeddings, project to output channels, sum all scale predictions, and denormalize.

### Imputation and anomaly-detection branches

Both branches reconstruct a window of length `seq_len`. Imputation first computes observed-value mean and standard deviation using `mask`, fills missing positions with zero after centering, runs the encoder/projection path, then restores the original scale. Anomaly detection uses the model's reversible normalization layer instead of the explicit imputation-mask statistics.

### Classification branch

Classification builds multiscale inputs, embeds them without temporal marks, applies the PDM stack, keeps the first/original scale, multiplies by `x_mark_enc.unsqueeze(-1)` to zero padded positions, flattens `(B, seq_len, d_model)`, and projects to `(B, num_class)`.

Important classification caveat: the CLI default is `channel_independence=1`, which constructs an input embedding with one value channel. Forecast and reconstruction branches explicitly reshape multi-feature tensors for that case; classification does not. Multi-feature classification tensors normally need `channel_independence=0` or a one-feature input tensor.

## Minimal shape examples

| Goal | Safe shape/config sketch |
| --- | --- |
| Multivariate forecast smoke | `x_enc=(2,16,3)`, `pred_len=4`, `enc_in=c_out=3`, `channel_independence=1`, `down_sampling_layers=1`, `down_sampling_window=2` -> `(2,4,3)`. |
| DFT forecast smoke | Same as forecast, plus `decomp_method='dft_decomp'`, even `d_model`, and `top_k <= d_model // 2 + 1`. |
| Imputation smoke | `x_enc=(2,16,3)`, `mask=ones_like(x_enc)`, `enc_in=c_out=3` -> `(2,16,3)`. |
| Anomaly reconstruction smoke | `x_enc=(2,16,3)`, `enc_in=c_out=3` -> `(2,16,3)`. |
| Multi-feature classification smoke | `x_enc=(2,16,3)`, `x_mark_enc=(2,16)`, `enc_in=3`, `num_class=3`, `channel_independence=0` -> `(2,3)`. |
