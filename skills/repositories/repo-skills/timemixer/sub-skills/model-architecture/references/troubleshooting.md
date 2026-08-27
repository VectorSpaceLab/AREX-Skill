# TimeMixer Model Troubleshooting

Use this guide when a TimeMixer model instantiates but forward propagation fails, or when an output shape does not match the selected task.

## Quick checks

1. Confirm `configs.task_name` selects the branch you expect.
2. Confirm `x_enc.shape == (B, seq_len, enc_in)` and `configs.enc_in == x_enc.shape[-1]`.
3. For forecast/reconstruction with `channel_independence=1`, keep `configs.c_out == configs.enc_in` unless you intentionally understand the reshape.
4. Use `down_sampling_layers >= 1` and keep `seq_len // (down_sampling_window ** down_sampling_layers) >= 1`.
5. Use an odd `moving_avg` kernel for `moving_avg` decomposition.
6. For classification, pass a padding mask shaped `(B, seq_len)` as `x_mark_enc`.
7. Run the smoke helper with the same task and decomposition to isolate model API issues from data-loader or training issues.

## Error-to-fix map

| Symptom or message | Likely cause | Fix |
| --- | --- | --- |
| `ValueError: decompsition is error` | `decomp_method` is not exactly `moving_avg` or `dft_decomp`. | Correct the config string; preserve the source spelling only when matching the error message. |
| `IndexError: list index out of range` inside seasonal/trend mixing | `down_sampling_layers=0` created only one scale, but PDM expects original plus at least one downsampled scale. | Set `down_sampling_layers=1` or higher; choose a window that leaves a nonempty smallest scale. |
| `mat1 and mat2 shapes cannot be multiplied` in a mixing or prediction linear layer | Actual downsampled length differs from `seq_len // window**i`, often from incompatible `conv` downsampling or an unexpected `seq_len`. | Use `avg` or `max`, or make `seq_len` divisible by `down_sampling_window ** down_sampling_layers`; ensure runtime `x_enc` length equals `configs.seq_len`. |
| Forecast output is not `(B, pred_len, c_out)` | `pred_len`, `c_out`, or channel-independent reshape is inconsistent with the input channels. | Set `pred_len` to desired horizon and set `enc_in=c_out=x_enc.shape[-1]` for standard channel-independent use. |
| Reconstruction output is not `(B, seq_len, c_out)` | `c_out` does not match the number of input channels after the internal reshape. | For imputation/anomaly with `channel_independence=1`, use `c_out=enc_in`. |
| Classification convolution error: expected input to have 1 channel but got multiple channels | `channel_independence=1` with multi-feature classification input. Forecast branches reshape this case; classification does not. | Set `channel_independence=0` for multi-feature classification, or provide one feature channel. |
| Classification projection shape mismatch | `configs.seq_len` does not equal the padded sequence length used to build `x_enc` and `x_mark_enc`. | Set `seq_len` to the classification dataset's max padded length before constructing the model. |
| Classification mask broadcast error | `x_mark_enc` is temporal features or has a trailing feature dimension. | Pass a padding mask shaped `(B, seq_len)`; values should be 1 for valid steps and 0 for padding. |
| Future temporal feature error involving `x_mark_dec` | `use_future_temporal_feature=1` but future marks are missing or wrong length/feature count. | Provide `x_mark_dec` shaped `(B, pred_len, time_dim)`; for hourly `timeF`, `time_dim=4`. |
| DFT `selected index k out of range` or similar top-k failure | `top_k` exceeds the transformed width. | Lower `top_k`; with `d_model=8`, use `top_k<=5`. |
| Moving-average decomposition length mismatch | `moving_avg` kernel is even. | Use an odd kernel such as 3, 5, 25, or 51. |
| Imputation returns NaNs or infinities | A batch/channel has no observed values where `mask == 1`. | Ensure every series/channel has at least one observed value before calling the imputation branch. |

## Shape debugging recipes

### Forecast smoke

```bash
cd /path/to/TimeMixer-checkout
python /path/to/timemixer-skill/sub-skills/model-architecture/scripts/smoke_timemixer_forward.py \
  --repo-root /path/to/TimeMixer-checkout \
  --task long_term_forecast \
  --decomp-method moving_avg \
  --channels 3 \
  --seq-len 16 \
  --pred-len 4
```

Expected output shape: `[2, 4, 3]`.

### DFT forecast smoke

```bash
python scripts/smoke_timemixer_forward.py \
  --repo-root . \
  --task long_term_forecast \
  --decomp-method dft_decomp \
  --channels 2 \
  --seq-len 16 \
  --pred-len 4
```

Expected output shape: `[2, 4, 2]`.

### Multi-feature classification smoke

```bash
python scripts/smoke_timemixer_forward.py \
  --repo-root . \
  --task classification \
  --channels 3 \
  --seq-len 16 \
  --pred-len 4 \
  --channel-independence 0
```

Expected output shape: `[2, 3]` when the default `--num-class 3` is used.

### Reproduce the classification default mismatch intentionally

```bash
python scripts/smoke_timemixer_forward.py \
  --repo-root . \
  --task classification \
  --channels 3 \
  --channel-independence 1
```

This should fail with a channel mismatch. Use it only to confirm that a user's error is the known default-channel-independence classification pitfall.

## Backend notes

The model smoke helper is CPU-only and deterministic. CUDA is useful for full training but is not required to validate constructor fields, forward dispatch, decomposition selection, or output shapes.
