# Diffusers Cross-Cutting Troubleshooting

Use this reference for install/import/backend problems that can affect several Diffusers workflows. For workflow-specific failures, use the nearest sub-skill troubleshooting reference.

## Import or Metadata Fails

Symptoms:
- `ModuleNotFoundError: No module named 'diffusers'`
- Package imports from an unexpected checkout or old site-packages location.
- `diffusers-cli` is missing after installation.

Actions:
1. Run `python -m pip show diffusers` and `python -c "import diffusers; print(diffusers.__version__)"` in the same environment used by the task.
2. For source development, install editable package from the checkout with `python -m pip install -e .`.
3. For package use, install from PyPI or the intended wheel/source distribution.
4. Run `scripts/check_diffusers_environment.py --json` from this skill for a compact import/metadata/CLI report.

## Optional Dependency Missing

Symptoms:
- `ImportError` mentions `torch`, `transformers`, `accelerate`, `peft`, `datasets`, `safetensors`, `onnx`, `onnxruntime`, `bitsandbytes`, `gguf`, `torchao`, or another optional backend.
- A lazy Diffusers object exists, but instantiation fails when the optional backend is used.

Actions:
1. Identify the selected workflow before installing extras.
2. Install only the needed optional dependency set: inference often needs `torch`, `transformers`, `accelerate`, and `safetensors`; training additionally needs `datasets`, `protobuf`, `tensorboard`, `Jinja2`, `peft`, and `timm`; conversion/export may need ONNX or format-specific packages.
3. Re-run `python -m pip check` and the root environment checker.
4. Do not install all optional backends or dev extras unless the user explicitly needs broad repository test coverage.

## CUDA, Device, or Dtype Problems

Symptoms:
- `torch.cuda.is_available()` is false despite GPUs on the host.
- CUDA out-of-memory during pipeline loading or training.
- fp16/bf16 errors on CPU or unsupported hardware.
- xFormers, FlashAttention, TensorRT, ONNX, OpenVINO, MPS, or vendor backend import failures.

Actions:
1. Check `torch.__version__`, CUDA availability, GPU count/name, and driver compatibility.
2. Use CPU-only checks for import/signature validation; do not infer real generation/training performance from them.
3. For inference, prefer smaller resolution, fewer steps, attention slicing, VAE slicing/tiling, sequential CPU offload, model CPU offload, or device maps before changing model code.
4. For training, reduce batch size/resolution, increase gradient accumulation, enable gradient checkpointing, use LoRA where possible, and confirm mixed precision is supported.
5. Avoid `--half`/fp16 export or conversion on CPU-only hosts.

## Hub, Network, and Credentials

Symptoms:
- 401/403 for gated models or private repos.
- Offline errors while resolving model configs.
- Unexpected network access in tests or helpers.

Actions:
1. Ask before using tokens, logging in, downloading gated models, or pushing to the Hub.
2. Use local model paths and `local_files_only=True` when the user requires offline operation.
3. Prefer `.safetensors` for untrusted local weights.
4. Treat Hub push, PR creation, or telemetry/reporting as explicit side effects requiring user approval.

## Local Files and Formats

Symptoms:
- `from_pretrained` cannot find `model_index.json` or component subfolders.
- `from_single_file` needs a config but cannot infer it offline.
- Adapter load fails with key/shape mismatches.
- Conversion output is missing expected components.

Actions:
1. For Diffusers directories, check `model_index.json` and expected component subdirectories such as `unet`, `vae`, tokenizers, text encoders, schedulers, transformers, or adapter components.
2. For single-file checkpoints, pass a local config directory or explicit config when offline inference is needed.
3. For adapters, validate file extensions, local paths, expected adapter names, and optional PEFT availability with the adapter sub-skill helper.
4. Route reversible adapter composition to `adapters-and-loaders`; route irreversible merges/exports to `conversion-and-maintenance`.

## Repository Development Pitfalls

Symptoms:
- Copied-code checks fail after editing a copied block.
- Dummy object or dependency table tests fail after changing optional imports.
- Style/copy generated files differ from source.

Actions:
1. Follow the checkout's `AGENTS.md` and copied-code policy.
2. Do not edit `# Copied from ...` blocks directly unless intentionally breaking the link.
3. Run the smallest focused tests first, then `make style` and `make fix-copies` before PR handoff when practical.
4. Keep generated skill artifacts in the repository's configured review/test artifact area; do not mix verification reports into runtime skill directories.
