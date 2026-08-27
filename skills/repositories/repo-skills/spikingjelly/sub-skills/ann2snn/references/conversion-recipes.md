# ANN2SNN conversion recipes

This reference distills the public ann2snn conversion surface for the generated
SpikingJelly repo skill.

## Verified live signatures

These constructor and method signatures were checked in the prepared inspection
environment and are the ones the sub-skill should target:

- `Converter(recipe: Union[str, FXConversionRecipe], device=None)`
- `ModuleConverter(recipe: ModuleConversionRecipe, device=None)`
- `RateCodingRecipe(dataloader, mode="Max", momentum=0.1, fuse_flag=True, channel_wise=False, channel_dim=1, pre_spike_maxpool=False, half_threshold=False, eps=1e-6, neuron_factory=None)`
- `LocalThresholdBalancingRecipe(dataloader, channel_dim=1, fuse_flag=True, eps=1e-6)`
- `TransformerTDEquivalentRecipe(time_steps=None)`
- `STATransformerRecipe(dataloader=None, time_steps=32, mode="equivalent", threshold_mode="mse", threshold_scale=1.0, spike_linear=None, spike_conv2d=None, spike_classifier=False, momentum=0.1, num_calibration_batches=None, show_progress=False, eps=1e-6)`
- `SpikeZIPTFQANNRecipe(time_steps=200, model_family="roberta")`
- `Qwen2SNNConfig(time_steps=32, calibration_levels=16, calibration_quantile=1.0, calibration_reservoir_size=4096, calibration_seed=20260719, neuron_backend="torch")`
- `Qwen2SNNCalibration.state_dict()` / `Qwen2SNNCalibration.from_state_dict(state)`
- `calibrate_qwen2_snn(model, calibration_batches, config)`
- `Qwen2SNNRecipe(calibration, config)`
- `Qwen2SNNModel.forward(input_ids, attention_mask=None, *, position_ids=None, encoding_mode=None, past_key_values=None, use_cache=False, **_)`
- `Qwen2SNNModel.generate(input_ids, attention_mask=None, *, max_new_tokens, do_sample=False, num_beams=1, **_)`
- `SignedQCFSSequenceEncoder(scale, time_steps, *, neuron_backend="torch", channel_dim=-1, collect_statistics=True, name="activation")`
- `estimate_delay_start(model, dataloader, device, time_steps, num_batches=1)`

## Converter boundary

| Path | Executor | Recipe base | Typical use | Output contract |
| --- | --- | --- | --- | --- |
| FX graph conversion | `Converter` / `FXConverter` | `FXConversionRecipe` / `ConversionRecipe` | CNN rate coding, Transformer TD-equivalent, STA | Returns an `fx.GraphModule`-style model with converted submodules |
| Module-tree conversion | `ModuleConverter` | `ModuleConversionRecipe` | SpikeZIP QANN and Qwen2 | Returns a plain `nn.Module` tree; no FX tracing is run |

The aliases matter:

- `Converter` is the compatibility alias for `FXConverter`.
- `ConversionRecipe` is the compatibility alias for `FXConversionRecipe`.
- `ModuleConverter` does **not** auto-dispatch FX recipes.
- `Converter` does **not** auto-dispatch module-tree recipes.

The FX lifecycle is fixed:

`validate` -> `before_trace` -> FX trace -> `after_trace` -> `insert_observers`
-> `calibrate` -> `replace` -> `finalize`.

The module-tree lifecycle is just:

`validate` -> `convert_module`.

## CNN rate-coding family

### `RateCodingRecipe`

Use this for ordinary ANN-to-SNN conversion where the ANN contains exact
`nn.ReLU` activations and you want a ReLU-to-IFNode rate-coded SNN.

Key points:

- Requires a calibration dataloader.
- Calibrates scalar or channel-wise activation scales.
- Fuses Conv-BN pairs by default.
- Replaces each ReLU with `VoltageScaler -> IFNode -> VoltageScaler` in the
  layer-wise path.
- Can switch to channel-wise scaling with `channel_wise=True`.
- `half_threshold=True` activates the channel-wise half-threshold IF path.
- `pre_spike_maxpool=True` can move `MaxPool2d` before the spiking neuron when
  the graph shape allows it.
- `neuron_factory` customizes the spiking neuron only for the layer-wise path
  unless the recipe explicitly forbids it.

Typical readout:

- In `step_mode="s"`, call the converted model once per timestep and sum the
  outputs yourself.
- In `step_mode="m"`, pass a sequence with time in dimension 0 and sum the
  returned sequence over time.

### `LocalThresholdBalancingRecipe`

This is the adjacent CNN recipe for channel-wise local-threshold balancing.
Use it when scalar robust normalization is too crude and you want a more local
threshold estimate.

It shares the same explicit time/readout convention as `RateCodingRecipe` but
uses local threshold balancing hooks instead of the voltage-scale observer.

### Optional delayed readout

`estimate_delay_start(model, dataloader, device, time_steps, num_batches=1)`
can estimate a delayed readout start for converted CNN graphs that match the
pattern `VoltageScaler/ChannelVoltageScaler -> BaseNode ->
VoltageScaler/ChannelVoltageScaler`.
It does **not** change neuron dynamics; it only chooses a later window for the
final readout.

Keep at least four readout steps after the estimated delay. If the model does
not match the required scaler-neuron-scaler pattern, the helper returns `0`.

## Transformer FX family

### `TransformerTDEquivalentRecipe`

This is the lightweight TD-equivalent baseline for Transformers.
It is calibration-free and replaces supported modules with temporal-difference
operators.

Supported or directly handled paths include:

- `nn.Linear` -> `TDLinear`
- `nn.Conv2d` -> `TDConv2d`
- `nn.LayerNorm` -> `TDLayerNorm`
- `nn.RMSNorm` -> `TDRMSNorm`
- `nn.SiLU` / `F.silu` -> `TDSiLU`
- `nn.GELU` / `F.gelu` -> `TDGELU`
- `nn.Tanh` / `torch.tanh` -> `_TDTanh`
- `nn.Softmax` / `F.softmax` / `tensor.softmax` -> `TDSoftmax`
- `nn.MultiheadAttention` -> `TDMultiheadAttention` when the module satisfies
  the narrow attention contract
- `torch.matmul` / `operator.matmul` -> `SNNMatrixOperator`
- `F.scaled_dot_product_attention` -> `TDScaledDotProductAttention` when the
  call has literal-supported arguments

Important constraints:

- `MultiheadAttention` must be `batch_first=True`.
- `dropout` must be `0.0`.
- `key_padding_mask` is not supported.
- `need_weights` must be `False`.
- `add_bias_kv` and `add_zero_attn` are not supported.
- SDPA only accepts literal `dropout_p=0.0`, `enable_gqa=False`, and literal
  `is_causal` / `scale` values.

Readout semantics:

- Feed an ordinary ANN input as a first-real-then-zero sequence.
- The converted model returns temporal differences.
- `y_seq.sum(dim=0)` recovers the ANN output for the standard smoke pattern.
- For diagnostics on a raw temporal sequence, compare the cumulative output via
  `y_seq.cumsum(dim=0)`.

### `STATransformerRecipe`

This is the calibrated STA path.
It keeps the cumulative-difference idea and adds calibration-driven spike
encoders at selected Transformer boundaries.

Supported modes:

- `mode="equivalent"`: cumulative-difference baseline, calibration-free.
- `mode="spiking_encoder"`: inserts calibrated spike encoders after
  `LayerNorm`, `GELU`, and supported `MultiheadAttention` outputs.

Currently rejected or unsupported:

- `mode="spiking_affine"`
- `spike_linear=True`
- `spike_conv2d=True`
- `key_padding_mask`
- attention-weight outputs or calls that rely on them
- unsupported FX tensor ops that are not sequence-preserving

Readout semantics:

- Use first-real-then-zero sequence inputs for ANN-equivalence style checks.
- In `step_mode="m"`, pass the whole sequence and sum the output over time.
- In `step_mode="s"`, call the converted model once per timestep and stack the
  outputs.
- Static control tensors, such as attention masks, are not time-expanded.

## Module-tree QANN family

### `SpikeZIPTFQANNRecipe`

This is the module-tree converter for SpikeZIP-compatible QANNs.
It should be used only when the source model already exposes the quantizer and
attention contracts expected by SpikeZIP.

Expected model families:

- `model_family="roberta"`
- `model_family="vit"`

Typical replacements include:

- `nn.Linear` -> `SpikeZIPLinear`
- `nn.Conv2d` -> `SpikeZIPConv2d`
- `nn.Embedding` -> `SpikeZIPEmbedding`
- `nn.LayerNorm` -> `SpikeZIPLayerNorm`
- `nn.Softmax` -> `SpikeZIPSoftmax`
- RoBERTa/ViT attention modules -> SpikeZIP attention wrappers
- quantizer modules -> `STBIFNeuron`

The source QANN must already expose the quantizer fields used by the recipe
(`s`, `sym`, `pos_max`, `neg_min`, and optionally `level`).

Readout semantics:

- Run the converted model in single-step mode and accumulate logits across the
  time window.
- Compare the accumulated logits with the original QANN logits.
- The converted model is inference-only.

## Qwen2 module-tree family

### `Qwen2SNNConfig`

This dataclass defines the tiny conversion and calibration contract.

Important validation rules:

- `time_steps` must be a positive integer.
- `calibration_levels` must be a positive integer no larger than
  `time_steps`.
- `calibration_quantile` must lie in `(0, 1]`.
- `calibration_reservoir_size` must be positive.
- `neuron_backend` must be either `"torch"` or `"triton"`.

### `calibrate_qwen2_snn`

This function collects Qwen2 input, Q/K/V, and MLP scales without storing full
activations.

Input contract:

- `model` must be an evaluation-mode Hugging Face Qwen2 causal LM.
- `calibration_batches` must provide `input_ids` and `attention_mask`
  tensors.
- The caller owns tokenization and batch device placement.

### `Qwen2SNNCalibration`

The calibration object is immutable and serializable.
Its `state_dict()` / `from_state_dict()` pair preserves only tensors and basic
Python values.

The restored object must match the conversion config exactly:

- `time_steps`
- `calibration_levels`
- `calibration_quantile`
- `calibration_reservoir_size`
- `calibration_seed`

### `Qwen2SNNRecipe` and `Qwen2SNNModel`

Use `ModuleConverter(Qwen2SNNRecipe(...))`.
The converted model keeps an explicit `[T,B,S,H]` temporal layout and exposes:

- `signed_encoders()`
- `set_collect_statistics()`
- `encoder_statistics()`
- `structure_summary()`
- `get_input_embeddings()`
- `get_output_embeddings()`
- `tie_weights()`
- `forward(..., encoding_mode=...)`
- `generate(..., max_new_tokens=...)`

Forward modes:

- `exact_td`: dense reference path for equivalence checks.
- `signed_if`: actual signed QCFS replay path.
- `qcfs_sg`: QCFS count reconstruction path for gradient-oriented use.

Readout semantics:

- The model returns logits after summing the hidden time dimension.
- `exact_td` is the closest dense-equivalence check.
- `signed_if` is the real converted path.
- Cached decoding is explicit through `past_key_values` and requires
  `use_cache=True`.
- `generate()` is greedy only and does not support sampling or beam search.

## Tiny synthetic smoke patterns

The bundled smoke script is the canonical quick validation path.
It avoids downloads and checks the smallest useful contracts.

| Case | What it proves | Converter path |
| --- | --- | --- |
| `rate` | Conv-BN-ReLU rate coding, BN fusion, single-step vs multi-step parity, and explicit time readout | FX `Converter` + `RateCodingRecipe` |
| `transformer_td` | TD-equivalent Transformer rewrite and explicit sequence readout | FX `Converter` + `TransformerTDEquivalentRecipe` |
| `sta` | Calibration-driven Transformer spike encoder insertion and step-mode parity | FX `Converter` + `STATransformerRecipe(mode="spiking_encoder")` |
| `qwen2` | Qwen2 calibration round-trip, exact-TD parity, signed-IF flow, and cache continuation | `ModuleConverter` + `Qwen2SNNRecipe` |
| `spikezip` optional | SpikeZIP QANN module-tree parity with accumulated logits | `ModuleConverter` + `SpikeZIPTFQANNRecipe` |

## Route-with-confidence reminders

- If the user says `rate coding`, choose the FX route and supply calibration
  batches.
- If the user says `Transformer` and wants graph rewriting, start with the TD
  or STA FX recipes.
- If the user says `Qwen2`, use the calibration object and module-tree recipe,
  not the FX converter.
- If the user mentions `Triton` or `FP8` backend quirks, route the backend
  discussion to `performance-and-analysis` and keep this skill focused on the
  conversion contract.
