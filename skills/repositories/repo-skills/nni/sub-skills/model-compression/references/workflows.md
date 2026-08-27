# Compression Workflows

This reference distills NNI compression usage into safe planning steps. It assumes the future agent already has a PyTorch model, representative inputs, and any required training or calibration data in the user project.

## Pruning Workflow

Use pruning when the goal is smaller weights, fewer channels, lower parameter count, or a structurally compact model after mask speedup.

1. **Identify the pruning target**: choose module names from `model.named_modules()` and PyTorch type names such as `Conv2d`, `Linear`, `BatchNorm2d`, or `Embedding`.
2. **Write `config_list`**: start with one include config, then add excludes for final heads or fragile layers.
3. **Choose pruner**:
   - `LevelPruner`: element-wise weight magnitude pruning; simple sparsity baseline, not usually structural speedup.
   - `L1NormPruner` or `L2NormPruner`: output-channel pruning by norm; common for convolutional filters and speedup candidates.
   - `FPGMPruner`: output-channel/filter pruning by geometric median; useful when norm pruning is too aggressive on small filters.
   - `SlimPruner`: BatchNorm scaling-factor pruning; fits models with normalization layers and training/fine-tuning budget.
   - `TaylorPruner`: first-order Taylor criterion; needs training/evaluator signals and representative gradients.
   - `LinearPruner` or `AGPPruner`: scheduled sparsity over pruning rounds; use when gradual pruning is safer than one-shot pruning.
   - `MovementPruner`: adaptive sparsity during fine-tuning; most relevant for transformer-style fine-tuning.
4. **Compress and unwrap**: NNI pruners wrap selected modules; after generating masks, unwrap before regular fine-tuning or saving unless the next step expects wrappers.
5. **Fine-tune or retrain**: expect accuracy drop after pruning; plan a bounded fine-tuning phase if the user wants usable model quality.
6. **Speed up if structural**: use `ModelSpeedup` only after you have masks and `dummy_input`; prefer channel/coarse-grained masks over fine-grained masks when real speedup is required.

Minimal pattern:

```python
from nni.compression.pruning import L1NormPruner

config_list = [{
    "op_types": ["Conv2d", "Linear"],
    "exclude_op_names": ["classifier", "fc3"],
    "sparse_ratio": 0.5,
}]
pruner = L1NormPruner(model, config_list)
_, masks = pruner.compress()
pruner.unwrap_model()
```

If skip connections or residual adds exist, consider dependency groups before speedup. NNI exposes `auto_set_denpendency_group_ids(model, config_list, dummy_input)` in compression utilities and speedup helpers to align channels that must be pruned together.

## Quantization Workflow

Use quantization when the goal is lower precision inference or deployment on an integer/accelerated backend.

1. **Decide QAT vs PTQ**:
   - Use `PtqQuantizer` for post-training quantization with calibration data and no full retraining.
   - Use `QATQuantizer` when training/fine-tuning is available and accuracy matters.
   - Use `DoReFaQuantizer`, `BNNQuantizer`, `LsqQuantizer`, or `LsqPlusQuantizer` for algorithm-specific low-bit training experiments.
2. **Write `config_list` targets**: quantization configs usually set `target_names` such as `_input_`, `weight`, and `_output_`, plus `quant_dtype`, `quant_scheme`, `granularity`, and optionally `apply_method`.
3. **Choose evaluator**: PTQ needs calibration/evaluation behavior; QAT and learned-step methods need training behavior.
4. **Compress and collect output artifacts**: PTQ returns a quantized model and calibration config; QAT-style workflows wrap modules for simulated quantization during training.
5. **Plan backend speedup separately**: simulated quantization does not automatically reduce latency; TensorRT/ONNX speedup has extra backend requirements.

Minimal PTQ-style config:

```python
config_list = [{
    "op_names": ["conv1"],
    "target_names": ["_input_", "weight", "_output_"],
    "quant_dtype": "int8",
    "quant_scheme": "affine",
    "granularity": "default",
}]
```

## Distillation Workflow

Use distillation when the task asks for teacher/student compression, layerwise losses, or preserving quality while compressing a smaller student.

1. Prepare teacher and student models in the user's project.
2. Decide whether layer outputs need dynamic matching (`DynamicLayerwiseDistiller`) or adaptive 1D layerwise matching (`Adaptive1dLayerwiseDistiller`).
3. Use `target_names` and `target_settings` to describe the tensors to distill. Distillation settings can include `lambda`, `link`, and `apply_method` such as `mse` or `kl`.
4. Provide an evaluator that can train the student for bounded steps or epochs.
5. Keep distillation separate from HPO or NAS unless the user explicitly asks to combine workflows.

Distillation is usually not a standalone config validation task: it depends on teacher/student tensor compatibility and representative data.

## Evaluator Workflow

NNI compression evaluators package training and evaluation logic so compressors can request gradients, activations, calibration, metrics, or bounded fine-tuning.

- **Native PyTorch**: use `TorchEvaluator` when the user has a custom training loop. `training_func` should accept `model`, optimizer(s), `training_step`, scheduler(s), `max_steps`, and `max_epochs`; `training_step` should return a loss, a tuple whose first element is loss, or a dict containing `loss`; `evaluating_func` should return a float or a dict with `default`.
- **PyTorch Lightning**: use `LightningEvaluator` when training already lives in a Lightning `Trainer`, `LightningModule`, and `LightningDataModule`. Wrap optimizer, scheduler, Lightning module, trainer, and datamodule constructors with `nni.trace` where NNI needs constructor metadata.
- **Transformers**: use `TransformersEvaluator` for Hugging Face `Trainer` workflows. Wrap `Trainer` with `nni.trace`; also trace custom optimizers or schedulers.
- **DeepSpeed native PyTorch**: use `DeepspeedTorchEvaluator` when the training loop is native PyTorch but model execution is under DeepSpeed. The training loop receives a DeepSpeed engine and should call engine backward/step methods, not ordinary optimizer steps.

Do not choose an evaluator by package availability alone. Choose it by the user's existing training abstraction and only then explain missing dependencies if imports fail.

## Speedup and Export Workflow

Compression often has two stages: simulated compression and physical deployment speedup.

### Pruning Speedup

`ModelSpeedup` compacts a PyTorch model from pruning masks. It relies on tracing/shape inference and works best for coarse-grained masks that remove channels or compatible tensor dimensions.

Typical pattern:

```python
from nni.compression.speedup import ModelSpeedup

ModelSpeedup(model, dummy_input, masks).speedup_model()
```

Caveats:

- Fine-grained sparsity usually needs sparse kernels and may not become faster through `ModelSpeedup`.
- `dummy_input` must match real inference shapes and device.
- Dynamic control flow, unusual tensor reshapes, unsupported operators, residual dependency mismatches, or masks that prune incompatible channels can break graph inference.
- Validate the compacted model numerically and structurally before saving it.

### Quantization Speedup

NNI's quantization algorithms often simulate lower precision with float operators. Real latency reduction requires a backend such as TensorRT through ONNX/TensorRT conversion and calibration.

Caveats:

- TensorRT speedup is backend-heavy and can require NVIDIA container images, CUDA, TensorRT, ONNX, PyCUDA, calibration data, and fixed input shapes.
- Treat generated calibration caches and engines as project artifacts, not skill artifacts.
- Never promise speedup from QAT/PTQ alone; only promise lower-precision simulation unless a backend conversion succeeds.

## Safe Planning Checklist

- Confirm `torch` and selected optional backend libraries are installed before importing compression modules.
- Validate `config_list` shape with `scripts/validate_config_list.py` for static errors.
- Confirm `op_names` against `model.named_modules()` and `op_types` against module class names.
- Verify evaluator training loops honor `max_steps` or `max_epochs` so compressor-driven training is bounded.
- Avoid running data download, training, TensorRT conversion, or DeepSpeed launch during planning-only tasks.
