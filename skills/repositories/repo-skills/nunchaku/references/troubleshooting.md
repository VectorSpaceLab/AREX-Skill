# Cross-cutting troubleshooting

Use the nearest sub-skill troubleshooting reference first when a problem belongs to one workflow. Use this root reference for installation, import, asset, backend, and routing failures that cut across the package.

## Import or installation fails

### Symptom: `ModuleNotFoundError: nunchaku`

- Confirm the user is running the Python environment where Nunchaku was installed.
- For ComfyUI portable setups, install into ComfyUI's bundled Python, not the shell's default Python.
- Run `python -m pip show nunchaku` and `python scripts/inspect_nunchaku_install.py --pretty` in the same interpreter.

### Symptom: `ImportError` or undefined CUDA/Torch symbols

Likely causes:

- Nunchaku wheel built for a different Python, PyTorch, CUDA, or ABI combination.
- PyTorch was upgraded/downgraded after installing Nunchaku.
- Source install was built against a different visible GPU architecture or missing submodules.

Actions:

1. Check `torch.__version__`, `torch.version.cuda`, Python version, and GPU SM.
2. Reinstall a matching prebuilt Nunchaku wheel or rebuild from source in a clean environment.
3. If source-building with PyTorch CUDA pip wheels, ensure NVIDIA wheel include/library directories are visible to the compiler as described in `installation-build-runtime.md`.

## CUDA/backend fails

### Symptom: CUDA unavailable

Nunchaku quantized inference is CUDA-oriented. Do not substitute CPU unless the task only needs static code inspection or a non-inference utility. Ask for a CUDA runtime or narrow the task.

### Symptom: unsupported architecture assertion or precision mismatch

- Supported source-build SM targets are `75`, `80`, `86`, `89`, `120a`, and `121a` when NVCC supports them.
- Turing/Ampere/Ada generally use INT4 assets; Blackwell uses FP4 assets.
- Use `nunchaku.utils.get_precision(device=...)` and avoid manually pairing FP4 assets with non-Blackwell GPUs or INT4 assets with Blackwell-specific examples.

### Symptom: source install only works on the build GPU family

The default `NUNCHAKU_INSTALL_MODE=FAST` builds only visible SMs. Rebuild with `NUNCHAKU_INSTALL_MODE=ALL` when the package/wheel must move across GPU families.

## Model asset loading fails

### Symptom: safetensors assertion or directory passed where file is expected

Some Nunchaku loaders require a specific quantized `.safetensors` or `.sft` file rather than a model directory. Qwen's loader explicitly asserts file-style input. Use a full Hub file path or local file path.

### Symptom: Hugging Face download/authentication errors

- Confirm the model is public or the user has accepted license/gated terms.
- Ask for a token policy rather than embedding tokens in scripts.
- Prefer local paths for reproducible/offline tasks.
- Do not assume examples' default model IDs are accessible in the user's environment.

### Symptom: base model and quantized asset mismatch

The Diffusers base model and Nunchaku quantized component must be from the same family and compatible variant. Do not put a Qwen transformer into a FLUX pipeline, a Sana transformer into an SDXL UNet slot, or a non-Turbo quantized asset into a Turbo-only recipe without checking docs/tests.

## Diffusers compatibility fails

- Qwen 2509 and some newer Qwen classes require Diffusers APIs at least as new as the documented examples (`diffusers>=0.36` for 2509).
- Z-Image pipeline imports can move across Diffusers versions; try both top-level and package-internal imports only in diagnostic code.
- Sana PAG uses attention-processor behavior that can be affected by Diffusers upgrades; re-check native examples after upgrading.
- Pipeline offload internals such as `_exclude_from_cpu_offload` are version-sensitive and should be guarded.

## Memory/offload problems

- FLUX legacy transformer: `NunchakuFluxTransformer2dModel.from_pretrained(..., offload=True)` can be paired with Diffusers sequential CPU offload; avoid `pipe.to('cuda')` afterward.
- FLUX v2: source inspection shows transformer-level `offload=True` is not implemented; rely on Diffusers pipeline-level offload or choose the non-V2 class if transformer-level offload is required.
- Qwen: for aggressive low-VRAM mode, call `transformer.set_offload(True, num_blocks_on_gpu=...)`, exclude `transformer` from Diffusers CPU offload, then enable sequential CPU offload.
- Cache and offload together can change memory/timing; validate with a bounded smoke before claiming speedups.

## LoRA/adapters fail

- Single FLUX LoRA: use `update_lora_params` then `set_lora_strength`.
- Multiple FLUX LoRAs: compose with per-LoRA strengths first; `set_lora_strength` after composition applies a global scale only.
- Nunchaku-format LoRAs should not be composed with other LoRAs; strengths are baked into the composed weights.
- Qwen custom LoRA is excluded because docs state support is under development.
- IP-Adapter support is documented as deprecated in March 2026; warn before recommending it for new long-lived workflows.
- PuLID requires the specialized pipeline and forward-method binding order; do not mix it blindly with unrelated transformer mutations.

## Native tests/examples and benchmarks

Before running native checks:

1. Confirm the exact model assets and credentials.
2. Confirm GPU memory and expected runtime.
3. Set any required cache/output environment variables explicitly.
4. Select one or two bounded candidates rather than all tests.
5. Capture command, exit status, output files, and skipped assets.

Benchmark tests such as speed/memory cases are optional evidence; never block ordinary usage on unrequested benchmark numbers.
