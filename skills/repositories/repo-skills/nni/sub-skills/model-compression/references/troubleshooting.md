# Compression Troubleshooting

Use this guide when an NNI compression task fails before or during planning, static config validation, evaluator setup, compression, speedup, or export.

## Import and Optional Dependency Failures

### `ModuleNotFoundError: No module named 'torch'`

Likely cause: `nni.compression` requires PyTorch for compression modules.

Actions:

- Do not treat this as an NNI core install failure if `import nni` works.
- Ask the user whether to install a compatible PyTorch build for their CPU/CUDA platform, or provide an environment that already has it.
- Continue static `config_list` authoring and validation without importing `nni.compression` when the task does not require execution.

### Lightning, Transformers, DeepSpeed, TensorRT, ONNX, or PyCUDA import errors

Likely cause: the chosen evaluator or speedup backend has optional dependencies beyond base NNI and Torch.

Actions:

- Select the evaluator by the user's training abstraction first, then explain the missing package.
- Avoid installing heavyweight GPU/backend stacks without explicit user approval.
- For TensorRT quantization speedup, confirm CUDA/TensorRT/PyCUDA/ONNX availability, fixed input shapes, and calibration data before attempting conversion.

## Config List Failures

### Malformed `config_list`

Symptoms: schema errors, compressor initialization failure, or no modules selected.

Checks:

- `config_list` must be a JSON/Python list of dictionaries.
- Each config should include at least one of `op_names`, `op_names_re`, or `op_types`.
- Selector fields must be lists of strings.
- `exclude_op_names`, `exclude_op_names_re`, and `exclude_op_types` remove selected modules; they should not be confused with the legacy boolean `exclude` field.
- Pruning `sparse_ratio`, `max_sparse_ratio`, and `min_sparse_ratio` must be within valid bounds.
- Quantization `target_names` should usually include one or more of `_input_`, `weight`, or `_output_`.

Run:

```bash
python scripts/validate_config_list.py config_list.json --mode pruning
```

Use `--mode quantization` or `--mode distillation` for those workflows.

### `op_names` do not match the model

Likely cause: names were guessed from code rather than `model.named_modules()`.

Actions:

- Ask the user to print or provide `dict(model.named_modules()).keys()`.
- Use exact fully qualified module names.
- Remember that final classifier heads often have names like `fc`, `fc3`, `classifier`, `head`, or nested names such as `backbone.layer1.0.conv1`.

### `op_types` do not match the model

Likely cause: using lowercase names or wrapper class names incorrectly.

Actions:

- Use PyTorch class names such as `Conv2d`, `Linear`, `BatchNorm2d`, `ReLU`, or project-specific module class names.
- If the model already contains wrappers, inspect the underlying module type before selecting.

### Include and exclude rules cancel everything

Likely cause: `op_names` and `op_types` intersect to an empty set, or exclude rules remove all included modules.

Actions:

- Start with only `op_types`, validate behavior, then add `exclude_op_names` for fragile layers.
- Avoid putting the same name in `op_names` and `exclude_op_names` unless intentionally testing no-op behavior.
- Prefer one focused config entry per selection pattern.

## Pruning Failures

### No real speedup after pruning

Likely cause: the pruner generated masks but did not physically change module shapes.

Actions:

- Explain that masks simulate pruning; they do not necessarily speed up inference.
- Use `ModelSpeedup` only for compatible coarse-grained/channel masks with valid `dummy_input`.
- Fine-grained weight sparsity may need sparse kernels that are outside NNI's ordinary structural speedup path.

### `ModelSpeedup` graph, shape, or mask errors

Likely causes: unsupported dynamic control flow, wrong `dummy_input` shape/device, unsupported operators, residual channel dependency mismatch, or incompatible masks.

Actions:

- Make `dummy_input` match real inference input shapes and device.
- Prefer channel pruning (`out_channel`/compatible targets) for structural speedup.
- Use dependency-group helpers for residual/add/mul paths when compatible.
- Run a forward pass before and after speedup and compare output shape and coarse metric.
- If speedup fails but masked inference works, report that the model is compression-simulated but not structurally compacted.

### Accuracy collapses after pruning

Likely causes: too high `sparse_ratio`, pruning final heads, no fine-tuning, missing dependency constraints, or unsuitable algorithm.

Actions:

- Reduce sparsity and schedule it with `LinearPruner` or `AGPPruner`.
- Exclude final classifier/regression heads.
- Fine-tune after mask generation or after speedup.
- Use evaluator-aware pruners when gradients or training dynamics matter.

## Quantization Failures

### PTQ accuracy is poor

Likely causes: insufficient calibration data, quantizing sensitive layers, wrong `target_names`, or no representative input distribution.

Actions:

- Use representative calibration data and enough batches for the user's model scale.
- Exclude first/last layers or sensitive blocks.
- Confirm `_input_`, `weight`, and `_output_` targets match the quantizer and backend goal.
- Consider QAT if the user can fine-tune.

### QAT does not improve latency

Likely cause: QAT simulates quantization during training; it does not automatically produce a backend engine.

Actions:

- Distinguish accuracy-aware quantization from deployment speedup.
- Plan ONNX/TensorRT or target-runtime conversion separately.
- Avoid promising latency improvement until backend conversion and measurement succeed.

### TensorRT speedup fails

Likely causes: missing CUDA/TensorRT/PyCUDA/ONNX, unsupported operator, dynamic shapes, invalid calibration cache, or model export issues.

Actions:

- Verify backend dependencies and GPU environment before conversion.
- Fix input shapes and provide representative calibration samples.
- Export or simplify unsupported model operations where possible.
- Treat TensorRT engines and calibration caches as project artifacts outside this skill.

## Distillation Failures

### Teacher/student tensors do not align

Likely causes: wrong layer links, incompatible hidden sizes, missing projection/adaptation, or mismatched batch outputs.

Actions:

- Inspect layer output shapes before configuring distillation.
- Use compatible `link` settings and `apply_method` (`mse` or `kl`) for the tensor semantics.
- Add a small adapter in the user's model code when dimensions differ.

### Distillation loss dominates task loss

Likely cause: `lambda` is too high or the selected teacher layer is not appropriate for the student.

Actions:

- Lower `lambda` and monitor both task loss and distillation loss.
- Distill fewer layers first, then expand.
- Validate final metric with the user's normal evaluator.

## Evaluator Failures

### Compressor hangs or trains too long

Likely cause: `training_func` ignores `max_steps` and `max_epochs`.

Actions:

- Ensure the loop exits when either bound is reached.
- Use a small bounded run while testing compression setup.
- Avoid full training during configuration-only tasks.

### `training_step` output is rejected

Likely cause: it returns logits or metrics instead of loss.

Actions:

- Return a loss tensor directly, a tuple whose first item is the loss, or a dict containing `loss`.
- Keep metric reporting in `evaluating_func`.

### Lightning or Transformers evaluator cannot reconstruct objects

Likely cause: constructors were not wrapped with `nni.trace` where NNI needs initialization metadata.

Actions:

- Wrap `pl.Trainer`, Lightning modules/datamodules, Hugging Face `Trainer`, optimizers, and schedulers with `nni.trace` as appropriate.
- Keep project-specific callbacks and dataloaders in user code, not in the skill.

## Safe Fallbacks

- If execution dependencies are unavailable, still provide a validated `config_list` and a non-executed code skeleton.
- If module names are unknown, ask for `model.named_modules()` output rather than guessing.
- If backend speedup is impossible in the current environment, produce a clear two-stage plan: simulated compression now, deployment conversion later.
- If the task actually asks for HPO/NAS orchestration around compression, route experiment launch to the HPO or NAS sub-skill and keep this sub-skill focused on compression-specific config and API contracts.
