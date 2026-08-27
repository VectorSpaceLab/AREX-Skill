# ANN2SNN troubleshooting

Use this reference when conversion fails, the chosen converter is wrong, or
sequence readout does not match expectations.

## Converter and recipe mismatch

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `FXConverter requires an FXConversionRecipe` or `Converter` does not accept the recipe | A module-tree recipe was passed to the FX converter | Use `Converter` only with `RateCodingRecipe`, `LocalThresholdBalancingRecipe`, `TransformerTDEquivalentRecipe`, or `STATransformerRecipe`. Use `ModuleConverter` for `SpikeZIPTFQANNRecipe` and `Qwen2SNNRecipe`. |
| `ModuleConverter requires a ModuleConversionRecipe` | An FX recipe was passed to the module converter | Switch to `Converter` for FX recipes. |
| `Unknown ann2snn conversion recipe` | A string alias was used instead of the required parameterized recipe object | Instantiate the recipe directly. `"transformer_td_equivalent"` is the only built-in string alias that is currently supported by the FX converter. |
| `rate_coding` or `sta_transformer` string alias rejected | Those paths require parameters | Pass `RateCodingRecipe(...)` or `STATransformerRecipe(...)` directly. |

## Calibration and batch-shape problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `RateCodingRecipe requires a dataloader` | Rate coding was requested without calibration data | Provide a calibration loader or switch to the calibration-free Transformer TD-equivalent path if that is the actual goal. |
| `single-input calibration batches only` | The default rate-coding calibration saw a multi-input batch | Keep calibration to one input tensor per batch, or subclass `RateCodingRecipe.calibrate()` for a custom multi-input model. |
| `Batch data is an empty list or tuple` / `empty dictionary` | The calibration batch is malformed | Return a non-empty tensor batch or a tuple/list/dict that contains the input tensor. |
| `Qwen2 calibration batches require tensor input_ids and attention_mask` | The Qwen2 calibration batch is missing one of the required tensors | Build tokenized calibration batches with both `input_ids` and `attention_mask`. |
| `Calibration ... does not match config` | A stale Qwen2 calibration object was reused with a different config | Regenerate `Qwen2SNNCalibration` with the same `time_steps`, `calibration_levels`, `calibration_quantile`, `calibration_reservoir_size`, and `calibration_seed`. |

## Readout and step-mode mistakes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Output shape looks right but values are wrong | The time axis was not summed, or the model was not reset between sequences | Use `functional.reset_net(model)` before each independent sequence and sum or accumulate over the first dimension explicitly. |
| `step_mode="m"` and `step_mode="s"` disagree | The sequence was built incorrectly or state was not reset | For rate coding, repeat the same analog input over time. For TD/STA, use a first-real-then-zero sequence. Reset before comparing. |
| A mask changed when it should have stayed static | A control tensor was time-expanded by mistake | Keep masks and other static control tensors outside the time axis. |
| `estimate_delay_start` returns `0` | The converted model does not match the scaler-neuron-scaler pattern | This helper only applies to rate-coded graphs that contain `VoltageScaler/ChannelVoltageScaler -> BaseNode -> VoltageScaler/ChannelVoltageScaler`. |
| `estimate_delay_start` warns about too few readout steps | The time window is too short for delayed readout | Increase `time_steps` or disable delayed readout. Keep at least four steps after the delay. |

## Transformer support limits

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `batch_first=True` or `need_weights=False` errors during TD conversion | `nn.MultiheadAttention` is outside the narrow supported subset | Keep `batch_first=True`, `dropout=0.0`, packed `in_proj_weight`, `need_weights=False`, and avoid `key_padding_mask`, `add_bias_kv`, and `add_zero_attn`. |
| `scaled_dot_product_attention` conversion fails | The call uses an unsupported literal | Keep `dropout_p=0.0`, avoid `enable_gqa=True`, and use literal `is_causal` / `scale` arguments when required. |
| `STATransformerRecipe` rejects `spiking_affine` or spiking linear/conv2d options | The current step-mode backend does not support those paths | Stay with `mode="equivalent"` or `mode="spiking_encoder"`. If you need a different design, route to a custom recipe. |
| `MultiheadAttention key_padding_mask` or attention-weight errors | The STA backend only supports the narrow sequence-preserving subset | Remove the key-padding mask, stop requesting weights, or rewrite the model around supported sequence-preserving modules. |
| `function node ... linear` or `unsupported FX tensor op` | The graph contains an op that is not sequence-preserving in the current adapter | Rewrite the model to keep time and batch axes intact, or route the backend-specific question to `performance-and-analysis` if the issue is really about a kernel backend. |

## SpikeZIP compatibility errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `SpikeZIPTFQANNRecipe supports model_family='roberta' or 'vit'` | The wrong model family was chosen | Match the recipe to the model family. |
| `SpikeZIP QANN attention must expose quantizer level` | The QANN attention module does not expose the required quantizer fields | Convert only SpikeZIP-compatible QANNs that expose the quantizer contract used by the recipe. |
| `SpikeZIPTFQANNRecipe v1 supports absolute position attention only` | The attention module is not the supported absolute-position contract | Route to a different model wrapper or conversion strategy. |
| `past_key_value` / decoder / cross-attention errors | The supported SpikeZIP path does not cover decoder cache or cross-attention in this recipe version | Keep to the supported RoBERTa/ViT QANN contracts or use a different conversion route. |

## Qwen2-specific errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Qwen2SNNRecipe requires a Hugging Face Qwen2 causal LM` | The source model is not a Qwen2 causal LM | Use a supported Qwen2 model or stop at the calibration stage. |
| `sliding-window attention is not supported` / `MRoPE is not supported` | The source model configuration uses unsupported Qwen2 features | Disable those features or use a model/configuration that matches the supported path. |
| `Qwen2SNNRecipe requires evaluation-mode source` | The source model is still in training mode | Call `eval()` before calibration and conversion. |
| `past_key_values requires use_cache=True` | Cache continuation was requested without enabling cache | Set `use_cache=True` on both the prefill and continuation call. |
| `Converted Qwen2 supports deterministic greedy generation only` | Sampling or beam search was requested | Use the model for greedy decode only. |
| `encoding_mode` error | A mode outside `signed_if`, `qcfs_sg`, or `exact_td` was passed | Pick one of the supported modes. |
| `neuron_backend must be 'torch' or 'triton'` | An unsupported Qwen2 backend was requested | Use `torch` for a reference path. Route Triton-specific issues to `performance-and-analysis`. |

## Calibration-object hygiene

- `Qwen2SNNCalibration.state_dict()` and `from_state_dict()` are the stable way
  to persist and restore calibration.
- `Qwen2SNNRecipe.validate()` requires the restored calibration metadata to
  match the conversion config exactly.
- `SignedQCFSSequenceEncoder` reports statistics only after an `encode()` or
  `forward()` call that actually runs a sequence.
- If a Qwen2 smoke passes `exact_td` but fails `signed_if`, the calibration
  scales are usually the first place to inspect.

## Where to route next

- If the issue is step-mode or reset behavior, switch to `core-snn`.
- If the issue is calibration data layout, switch to `datasets`.
- If the issue is Triton, CuPy, or FP8 backend behavior, switch to
  `performance-and-analysis`.
