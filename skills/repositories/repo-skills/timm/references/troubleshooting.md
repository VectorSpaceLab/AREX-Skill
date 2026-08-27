# Cross-Cutting Troubleshooting

## Import Or Install Fails

- Verify Python version compatibility and install with `python -m pip install timm` in the intended environment.
- If `torch` or `torchvision` fails to import, fix the PyTorch install first; timm depends on those packages but does not provide their backend wheels.
- If CUDA is required, match the PyTorch wheel to the driver-supported CUDA runtime and verify `torch.cuda.is_available()` before blaming timm APIs.
- If a source checkout install fails, use `python -m pip install -e .` from the checkout and avoid installing broad dev/docs dependencies unless tests or docs are in scope.

## Pretrained Weights Fail

- Use `timm.list_pretrained(filter='*pattern*')` to find exact `architecture.tag` names.
- Treat Hugging Face Hub errors as network, cache, revision, auth, or model-id problems; retry with exact names, a known revision, or local-dir packaging when possible.
- Run no-download checks with `pretrained=False` to separate model-construction bugs from weight-download problems.
- Inspect `model.pretrained_cfg` before changing transforms, class counts, or local cache behavior.

## Predictions Look Wrong

- Confirm the model is in eval mode for inference.
- Resolve preprocessing from the model: `timm.data.resolve_data_config(model=model)` or `resolve_data_config(model.pretrained_cfg)`.
- Check image mode, channel order, resize/crop mode, interpolation, mean/std, and batch dimension.
- If `num_classes`, `in_chans`, or `global_pool` were changed, verify whether pretrained classifier weights were intentionally discarded or adapted.

## Device Or Backend Errors

- Many scripts and loader helpers default toward CUDA. On CPU hosts, pass `--device cpu` for scripts and set CPU device or disable prefetching for loaders.
- AMP dtype choices are hardware-dependent; `float16` and `bfloat16` support differs across GPUs and CPUs.
- Benchmark, training, and validation failures caused by out-of-memory usually need smaller `--batch-size`, fewer workers, lower input size, or a bounded model list.

## Repository Scripts Missing

- Root scripts such as `train.py`, `validate.py`, `inference.py`, `benchmark.py`, and `onnx_export.py` are repository files, not guaranteed pip console scripts.
- If the user only installed from PyPI, either clone/copy the relevant script or translate the command into package API code using the model/data/training sub-skills.
- Use the bundled command-builder scripts in sub-skills to construct commands without assuming the original checkout is present.

## Checkpoint Or Export Problems

- Checkpoint errors often come from EMA vs non-EMA keys, `module.` prefixes, classifier shape changes, SplitBN/auxiliary keys, or unsafe pickle loading.
- ONNX export issues often require `exportable=True`, static shape first, optional `onnx`/`onnxruntime`, and model-specific operator support checks.
- Prefer dry command generation and small models before attempting expensive exports, validation, or conversion workflows.
