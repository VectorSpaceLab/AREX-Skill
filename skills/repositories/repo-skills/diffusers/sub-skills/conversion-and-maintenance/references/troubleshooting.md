# Troubleshooting

Use this reference when conversion, CLI probing, or repository maintenance fails. Prefer identifying the exact family and failing stage before changing code or dependencies.

## Install Or Import Failures

Symptoms:

- `ModuleNotFoundError` for `torch`, `safetensors`, `transformers`, `onnx`, `onnxruntime`, `optimum`, `peft`, `accelerate`, or quantization backends.
- `diffusers-cli env` reports an optional package as `not installed`.
- Pipeline module import tests report unguarded optional dependency imports.

Actions:

- For CLI/environment inspection, run `python scripts/diffusers_cli_probe.py env` to capture installed versions without running conversion.
- Install only the backend required by the task; do not add broad dependencies just to satisfy an unrelated import.
- If adding a public object with an optional backend, update dependency registration and dummy object generation, then run dependency and dummy checks.
- For ONNX Runtime workflows, prefer the documented Optimum stack for runtime use; repository conversion scripts can additionally require `onnx` and PyTorch export support.

## Backend, Device, And Dtype Mistakes

Symptoms:

- fp16 export fails on CPU.
- CUDA out-of-memory during conversion/export.
- MPS/CPU produces dtype errors after adding `--half` or `torch.float16`.
- ONNX export raises that `float16` export is only supported on CUDA.

Actions:

- Use CPU and float32 for command planning and broad compatibility.
- Use `--half` or `--fp16` only when the output format and hardware support half precision.
- For `convert_stable_diffusion_checkpoint_to_onnx.py --fp16`, require CUDA; otherwise omit `--fp16`.
- For large original checkpoints or SVD-heavy LoRA extraction, prefer CUDA but make memory needs explicit.
- Separate conversion dtype decisions from inference dtype decisions; route generated-image execution to `pipelines-and-inference`.

## Local And Offline File Problems

Symptoms:

- `from_single_file` cannot infer config offline.
- Original Stable Diffusion conversion fails because architecture metadata is missing.
- Local paths work online but fail with `local_files_only=True`.
- Conversion writes into an unexpected directory or overwrites a previous output.

Actions:

- Provide a local config directory via `config` for `from_single_file`, especially with `local_files_only=True`.
- For original checkpoint conversion, add `--original_config_file`, `--config_files`, `--image_size`, `--prediction_type`, or `--pipeline_class_name` when inference is ambiguous.
- Use explicit local output directories and check whether they already exist before running heavy conversions.
- Prefer `.safetensors` inputs and outputs for untrusted weights.
- Do not use `diffusers-cli fp16_safetensors` for local-only/no-push tasks; that command is Hub/PR oriented.

## API Misuse

Symptoms:

- User asks to “convert a LoRA” but expects reversible adapter loading.
- A merged LoRA conversion permanently changes base pipeline weights.
- A custom block command imports and executes untrusted code.
- A CLI command unexpectedly downloads from or opens a PR on the Hub.

Actions:

- Route reversible adapter loading/composition to `adapters-and-loaders`; use conversion only for merged output artifacts or format changes.
- Explain that `convert_lora_safetensor_to_diffusers.py` merges LoRA deltas into a saved pipeline.
- Treat `custom_blocks` modules as executable Python; inspect trusted source before running.
- For no-push requirements, use local scripts or `save_pretrained` workflows, not `diffusers-cli fp16_safetensors`.

## Workflow-Specific Errors

### Original SD To Diffusers

- Missing or wrong config: supply `--original_config_file` or `--config_files`.
- Wrong SD v2 behavior: set `--image_size`, `--prediction_type`, and possibly `--upcast_attention`.
- Safetensors input fails: include `--from_safetensors`.
- Output should be safer: include `--to_safetensors`.
- ControlNet conversion only saves ControlNet when `--controlnet` is set; do not expect a full pipeline output.

### Diffusers To Original SD/SDXL

- Missing component files: verify `unet`, `vae`, and text encoder subfolders exist in the Diffusers directory.
- Wrong family: use the SDXL script for SDXL directories and the SD script for classic SD directories.
- Unsafe output format: add `--use_safetensors` instead of writing `.ckpt` when possible.

### LoRA Merge Or Extraction

- Prefix mismatch: set `--lora_prefix_unet` and `--lora_prefix_text_encoder` to match the safetensors keys.
- Bad merge strength: adjust `--alpha`; the default is `0.75`.
- Extraction output rejected: `--lora_out_path` must end with `.safetensors`.
- Extraction model mismatch: the bundled reference imports `CogVideoXTransformer3DModel`; other model families require intentional code adaptation.

### ONNX Export

- fp16 without CUDA: omit `--fp16` or move to CUDA hardware.
- Very large UNet export: expect external tensor data such as `weights.pb`.
- Runtime class confusion: export is not the same as inference. Use Optimum `ORTStableDiffusionPipeline` or `ORTStableDiffusionXLPipeline` for ONNX Runtime inference.

## Maintainer Check Failures

Symptoms:

- Copy consistency tests fail after editing a copied block.
- Dummy files drift after adding optional-backend public objects.
- Dependency tests fail for missing backend table entries or unguarded imports.

Actions:

- If a `# Copied from ...` target changed, edit the source and run `make fix-copies`.
- Run `python -m pytest tests/others/test_check_copies.py` for copied-code changes.
- Run `python -m pytest tests/others/test_check_dummies.py` after optional dependency or dummy object changes.
- Run `python -m pytest tests/others/test_dependencies.py` after dependency table, lazy import, or public object changes.
- Run `make style` before PR handoff when source files changed.
