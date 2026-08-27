# AIMET API overview

This reference records the public entry points verified during skill production against AIMET `2.37.0`. Use it to avoid guessing signatures when writing examples or debugging user code.

## PyTorch entry points

### `aimet_torch.QuantizationSimModel`

```python
QuantizationSimModel(
    model: torch.nn.Module,
    dummy_input: torch.Tensor | Sequence[torch.Tensor],
    quant_scheme: str | QuantScheme | None = None,
    default_output_bw: int = 8,
    default_param_bw: int = 8,
    in_place: bool = False,
    config_file: str | None = None,
    default_data_type: QuantizationDataType = QuantizationDataType.int,
)
```

Important methods:

```python
sim.compute_encodings(forward_pass_callback, forward_pass_callback_args=...)
sim.export(path: str, filename_prefix: str, dummy_input, *args, **kwargs)
sim.quantizers()
sim.named_quantizers()
sim.qmodules()
sim.named_qmodules()
```

Typical use: prepare/fold the model if needed, create `QuantizationSimModel`, calibrate encodings with representative data, evaluate `sim.model`, and export the model plus AIMET encodings.

### Model preparation and folding

```python
from aimet_torch import model_preparer, batch_norm_fold

prepared = model_preparer.prepare_model(
    model,
    modules_to_exclude=None,
    module_classes_to_exclude=None,
    concrete_args=None,
)

folded_pairs = batch_norm_fold.fold_all_batch_norms(
    model,
    input_shapes,
    dummy_input=None,
)
```

Use `model_preparer.prepare_model` when forward code uses functional activations or reuses modules in ways QuantSim cannot instrument accurately. Use BatchNorm folding before quantization when the deployment runtime will fold BN into adjacent layers.

### Compression

```python
from aimet_torch.compress import ModelCompressor

compressed_model, stats = ModelCompressor.compress_model(
    model,
    eval_callback,
    eval_iterations,
    input_shape,
    compress_scheme,
    cost_metric,
    parameters,
    trainer=None,
    visualization_url=None,
)
```

Parameter classes include `SpatialSvdParameters`, `WeightSvdParameters`, and `ChannelPruningParameters`. Compression is normally two-phase: select ratios, then apply compression and evaluate or fine-tune.

## ONNX entry points

### `aimet_onnx.QuantizationSimModel`

```python
QuantizationSimModel(
    model: onnx.ModelProto,
    *,
    param_type=aimet_onnx.int8,
    activation_type=aimet_onnx.int8,
    quant_scheme=QuantScheme.min_max,
    config_file: str | None = None,
    dummy_input: dict[str, numpy.ndarray] | None = None,
    user_onnx_libs: list[str] | None = None,
    providers: Sequence[str | tuple[str, dict]] | None = None,
    path: str | None = None,
)
```

Important methods and utilities:

```python
sim.compute_encodings(inputs_or_callback, *args, **kwargs)
sim.export(path, filename_prefix, export_model=True, export_int32_bias=None, encoding_version=None)
sim.to_onnx_qdq(export_int32_bias=False, prequantize_constants=False, force_activation_as="unsigned")
aimet_onnx.QuantizationSimModel.from_onnx_qdq(model, strict=False, **kwargs)
sim.set_tensor_precision(names, precision, strict=True)
aimet_onnx.compute_encodings(sim)
```

Use an iterable of input dictionaries for calibration when possible: `[{input_name: np_array}, ...]`. For CUDA execution, explicitly pass `providers=["CUDAExecutionProvider", "CPUExecutionProvider"]` and prove that ONNX Runtime exposes the CUDA provider.

### ONNX PTQ and analysis utilities

```python
aimet_onnx.apply_seq_mse(sim, inputs, num_candidates=20, nodes_to_exclude=None)
aimet_onnx.apply_adaround(sim, inputs, num_iterations=10000, nodes_to_include=None, node_names_to_optimize=None)
aimet_onnx.analyze_per_layer_sensitivity(sim, eval_fn, filename=None)
```

For mixed precision and low-power blockwise workflows, use `set_tensor_precision`, `set_param_type`, `set_blockwise_quantization_for_weights`, or `set_grouped_blockwise_quantization_for_weights` from `aimet_onnx.quantsim` as appropriate.

## GenAILab repository entry points

GenAILab is launched through the repository module:

```bash
python -m GenAILab --framework torch --config config.yaml
python -m GenAILab --framework onnx --config config.yaml
python -m GenAILab --framework both --config config.yaml
python -m GenAILab --framework torch --config config.yaml --online --wait
python -m GenAILab --framework torch --config config.yaml --download <run_id>
```

Local runs execute the pytest entry points:

```bash
pytest -s GenAILab/bench/torch/test_genai.py --config config.yaml --force-export
pytest -s GenAILab/bench/onnx/test_genai.py --config config.yaml --force-export
```

The config parser requires top-level `model` and `metrics`, accepts optional `precision`, `recipe`, `export`, `eval_in_onnx`, `run_group`, and `profiler`, and rejects unrecognized top-level keys. Use `scripts/genai_config_preflight.py` for a static check before model downloads.

## Qualcomm AI Hub / QNN utility entry points

The AIMETRegression QNN utility provides these semantics for AI Hub-backed target checks:

```python
compile_and_profile_qdq_model(
    qdq_model_path: str,
    device_name: str,
    model_name: str,
    export_dir: str,
    options: str | None = None,
)

eval_qnn_accuracy(
    target_model=compiled_model,
    device_name=device_name,
    input_spec=input_spec,
    dataset_loader=loader,
    channel_last=False,
    debug_print_feeds=False,
)
```

Key behavior: compile/profile uploads a QDQ ONNX model to AI Hub, downloads a compiled QNN zip, and returns job URLs plus latency when available. Accuracy evaluation submits per-sample `N=1` input arrays using the actual input name from `input_spec`, returns the first inference URL even when accuracy is `None`, and treats empty outputs/device errors as non-computable accuracy rather than target proof.

## Encoding and export reminders

- AIMET exports an ONNX model and a JSON encodings file; keep them paired.
- Torch workflows often export through `sim.export(...)` or Torch-to-ONNX helpers after calibration.
- ONNX workflows can export plain AIMET artifacts or a QDQ graph with `to_onnx_qdq`.
- For local Qualcomm QAIRT/QNN, the `.encodings` file is passed to `qairt-converter --quantization_overrides`.
- For Qualcomm AI Hub QNN compile/profile, use QDQ ONNX when that is the accepted target input form.
- Loading encodings into a changed graph may require non-strict behavior, but non-strict loading can hide a model/encoding mismatch; inspect missing and extra quantizers before deployment.
