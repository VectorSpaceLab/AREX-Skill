# TimeMixer Architecture Notes

TimeMixer is a multiscale, MLP-based model organized around two ideas:

- **Past-Decomposable-Mixing (PDM):** decompose historical representations into seasonal and trend parts at several temporal scales, then mix those parts in opposite scale directions.
- **Future-Multipredictor-Mixing (FMM):** forecast from every mixed scale with separate prediction layers and sum the resulting predictions.

These notes describe the implementation-level behavior that matters when configuring or debugging the model API.

## Multiscale input construction

Before embedding, forecast, imputation, anomaly-detection, and classification branches call the same multiscale helper. It starts with the original input scale and appends `down_sampling_layers` additional scales.

| `down_sampling_method` | Operation | Shape implications |
| --- | --- | --- |
| `avg` | `AvgPool1d(window)` over the time axis | New length is roughly `floor(T / window)` at each scale. |
| `max` | `MaxPool1d(window)` over the time axis | Same length rule as average pooling. |
| `conv` | Circular `Conv1d` with stride `window` and kernel size 3 | Safest when `seq_len` is divisible by `window ** down_sampling_layers`; otherwise convolution output lengths can diverge from linear layer dimensions. |

Use at least one downsampling layer for TimeMixer PDM. The implementation's season/trend mixing modules index both the original and first downsampled scale; a zero-scale configuration can fail even though the CLI parser has a zero default.

## Past-Decomposable-Mixing (PDM)

Each PDM block receives a list of embedded tensors, one per scale. For every scale it:

1. Decomposes the representation into seasonal and trend parts.
2. Optionally applies a cross-channel MLP when `channel_independence=0`.
3. Mixes seasonal parts from fine to coarse using `MultiScaleSeasonMixing`.
4. Mixes trend parts from coarse to fine using `MultiScaleTrendMixing`.
5. Adds seasonal and trend outputs; when `channel_independence=1`, it also adds a residual path through an output MLP.

The model stacks `e_layers` PDM blocks.

## Decomposition choices

| `decomp_method` | What it does | Use when | Watch for |
| --- | --- | --- | --- |
| `moving_avg` | Uses a centered moving average as trend and residual as seasonal. | Default, stable, simple, good first choice. | Use an odd `moving_avg` kernel so the output length stays equal to `seq_len`. |
| `dft_decomp` | Applies a DFT-based filter that keeps top-k coefficients and treats the inverse transform as seasonal. | You want the DFT variant introduced by the TimeMixer implementation. | Keep `top_k` no larger than the available transformed width. With embedded PDM tensors, an even `d_model` and modest `top_k` make smoke tests safer. |

Any other `decomp_method` raises a `ValueError` with the implementation's misspelled message `decompsition is error`.

## Future-Multipredictor-Mixing (FMM)

Forecasting uses one temporal predictor per scale. Each scale's encoded tensor is projected from its scale length to `pred_len`; all scale predictions are then summed.

- With `channel_independence=1`, the forecast path reshapes input channels into the batch dimension, predicts each channel independently, projects to one value channel, then reshapes back to `(B, pred_len, c_out)`.
- With `channel_independence=0`, the forecast path embeds all channels together and adds a residual projection from the decomposed pre-encoding branch.
- `x_dec` is accepted by the forward signature but is not used in this implementation's forecast branch.

## Future temporal features

`use_future_temporal_feature=1` affects only forecasting. The branch embeds `x_mark_dec` and adds the embedded future temporal representation before the forecast projection.

Shape rules:

- `x_mark_dec` length should be `pred_len`, not `label_len + pred_len`.
- For `channel_independence=1`, the model repeats future marks once per channel to align with the internal `(B * channels, pred_len, d_model)` forecast tensor.
- For `embed='timeF'` and hourly frequency, use four continuous time features. Fixed/learned temporal embeddings require integer calendar fields.

If you do not need future temporal features, keep `use_future_temporal_feature=0` and pass `None` or a harmless placeholder for `x_mark_dec`.

## Channel independence

`channel_independence=1` is the default model/CLI setting. It is useful for multivariate forecasting, imputation, and anomaly reconstruction because those branches reshape `(B, T, N)` to `(B*N, T, 1)` before value embedding and reshape outputs back afterward.

`channel_independence=0` embeds all input channels jointly with `enc_in` value channels. Use it when:

- cross-channel interactions are important;
- Solar/PEMS-style recipes require joint channels;
- classification input has more than one feature channel;
- channel-independent reshaping would make `c_out` inconsistent with the number of input variables.

Classification caveat: the classification branch does not perform the `(B*N, T, 1)` channel-independent reshape. If `channel_independence=1` and `enc_in > 1`, the value embedding expects one channel but receives multiple channels. Set `channel_independence=0` or reduce the input to one feature.

## Normalization

Forecast and anomaly-detection branches use `Normalize` layers, one per scale. With `use_norm=1`, normalization records per-sample mean and standard deviation over time and denormalizes final outputs. With `use_norm=0`, the layers become pass-through.

Imputation uses its own mask-aware mean and standard deviation before the model path. The imputation mask must contain at least one observed value per batch/channel; otherwise division by zero can make the forward pass invalid.

## Known gaps and safe assumptions

- This sub-skill verifies model-level shape behavior only; it does not validate dataset loaders, metrics, checkpoint files, or training convergence.
- Original benchmark scripts commonly use one to three downsampling layers and external datasets; those scripts are intentionally outside this model API sub-skill.
- The DFT branch is documented as implemented, including its practical `top_k`/`d_model` constraints; it is not a claim about paper-level frequency-domain semantics.
- CUDA is not required for the smoke helper. Use CPU for deterministic shape checks before attempting training.
