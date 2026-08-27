# Troubleshooting Quantization Integrations

Start with the smallest failing layer: config construction, package import, model metadata, weight loading, device placement, first forward pass, generation, save/reload, or distributed/serving behavior.

## Quick Triage

1. Run the no-download smoke script for config construction.
2. Print package versions for `transformers`, `torch`, `accelerate`, and the quantization backend.
3. Print hardware availability: CUDA/ROCm/MPS/XPU/HPU, device count, GPU names, and driver/runtime versions.
4. Inspect checkpoint metadata for `quantization_config`, `quant_method`, `bits`, `group_size`, backend version, and architecture.
5. Load with the fewest optimizations: no compile, no fused kernels, no tensor parallel, no service batching, and simple `device_map`.
6. Add offload, PEFT, distributed, kernels, compile, or serving features one at a time.

## Smoke Script Signals

Run:

```bash
python scripts/quantization_config_smoke.py --method bitsandbytes-4bit --print-json
```

Interpretation:

- `OK quantization config validated`: the config class imported and accepted the provided options. It does not prove model loading or kernel execution.
- `MISSING optional dependency`: install the named backend or choose a fallback method.
- `UNAVAILABLE config class`: the installed Transformers version does not expose that config class.
- `ERROR`: an option combination is invalid or the class raised during construction.

## Optional Package Missing

Symptoms:

- `ImportError`, `PackageNotFoundError`, or a Transformers optional dependency message.
- Config class unavailable despite base `import transformers` working.
- Model load fails only after adding `quantization_config`.

Fixes:

- Install the method-specific package, not every optional extra.
- Match backend wheel to hardware: CUDA/CPU/XPU/HPU/ROCm/MPS as applicable.
- Re-run the config smoke script before downloading a model.
- If a package would downgrade Transformers, pin deliberately and explain the trade-off.

## Unsupported Hardware Or Backend

Symptoms:

- Kernel dispatch errors such as missing CUDA kernels, unsupported compute capability, no GPU found, ROCm/MPS unsupported, or slow CPU fallback.
- `bitsandbytes` imports but cannot initialize the requested backend.
- FP8, Marlin, FlashAttention, or fused AWQ fails at first forward pass.

Fixes:

- Choose a method compatible with the host from [compatibility](compatibility.md).
- On CPU-only hosts, consider GGUF/GGML, torchao CPU, or smaller non-quantized models.
- On CUDA, verify GPU generation, CUDA runtime, PyTorch CUDA build, and backend wheel.
- Disable specialized kernels first; validate baseline quantized loading.

## CPU, CUDA, ROCm, MPS, XPU, And HPU Mismatch

Symptoms:

- `torch.cuda.is_available()` false while code uses `device_map="cuda"` or CUDA-specific kernels.
- MPS host receives CUDA-only examples.
- ROCm host fails on CUDA extension builds.
- Intel/Gaudi hosts install generic wheels without backend support.

Fixes:

- Use `device_map="auto"` only after confirming Accelerate and visible devices.
- Prefer explicit CPU/GGUF fallback when no accelerator exists.
- Replace CUDA-only kernels with PyTorch-native or backend-specific options.
- Avoid promising speedups without a benchmark on the actual hardware.

## `torch.compile` Incompatibility

Symptoms:

- First inference hangs or compiles for a long time.
- Shape changes trigger repeated recompilation.
- Custom quantized modules produce graph breaks or unsupported ops.
- Serving latency worsens after compile.

Fixes:

- Add `disable_compile=True` to generation when supported, or remove compile/cache settings.
- Validate fixed batch size and sequence length before enabling static cache.
- Avoid combining compile with fused AWQ, Marlin, FlashAttention, and continuous batching until the baseline path works.
- Report compile as an optional optimization, not a required correctness step.

## Serialization Limits

Symptoms:

- `save_pretrained` fails after loading with `device_map`.
- Reloaded model loses quantization metadata.
- Hub push omits quantization config or uploads incompatible weights.
- Method docs say serialization is unsupported or partial.

Fixes:

- Check whether the method supports `save_pretrained` and Hub push.
- Move a GPTQ model to CPU or a single supported device before saving when required.
- Save tokenizer/processor files with the quantized model.
- Verify a fresh reload in a new process.
- For GGUF, use the artifact's conversion/reload workflow rather than normal PyTorch serialization assumptions.

## PEFT Fine-tuning Compatibility

Symptoms:

- Base quantized weights are unexpectedly trainable.
- Adapter checkpoint saves only `adapter_model.safetensors` and the user expects full base weights.
- FSDP/DeepSpeed saves frozen quantized parameters or fails while saving.
- `prepare_model_for_kbit_training` or adapter attachment fails due to method mismatch.

Fixes:

- Explain that QLoRA trains extra adapter parameters on top of a frozen quantized base.
- Verify adapter config, target modules, and base model identity.
- Use PEFT-compatible quantization methods such as bitsandbytes for standard QLoRA unless a specialized backend is proven.
- Route optimizer, dataset, evaluation, and `TrainingArguments` debugging to [training](../../training/SKILL.md).

## Device Map And Offload Issues

Symptoms:

- Some modules remain on CPU unexpectedly.
- `lm_head` or tied embeddings are on a different device than expected.
- CPU RAM spikes despite quantization.
- Tensor parallel and `device_map` produce loading errors.
- GPTQ calibration runs out of memory and disk offload does not help.

Fixes:

- Print `model.hf_device_map` after load.
- Use `max_memory` to constrain placement.
- Remember bitsandbytes CPU offload stores offloaded weights in fp32.
- Do not combine `tp_plan="auto"` and `device_map` by default.
- For GPTQ calibration memory, use smaller calibration samples or `max_memory`; do not rely on unsupported disk offload.

## Quantized Checkpoint Mismatch

Symptoms:

- `quant_method` in the checkpoint does not match the config class passed by code.
- Loading a legacy AutoGPTQ checkpoint with GPT-QModel fails.
- AWQ/GPTQ group size, bits, zero point, or kernel metadata differs from the code.
- Tokenizer files are missing or special tokens changed after conversion.

Fixes:

- First load a pre-quantized checkpoint without overriding `quantization_config`.
- Inspect saved metadata and choose the matching backend package.
- Keep tokenizer/processor artifacts tied to the quantized checkpoint.
- Do not convert between AWQ, GPTQ, GGUF, and bitsandbytes by changing only the class name.

## Continuous Batching Or Serving Failure

Symptoms:

- Service works for single request but fails under concurrent requests.
- Paged KV cache, scheduler, offload, or compile settings conflict with quantized modules.
- Batch-size changes trigger compile or kernel errors.

Fixes:

- Disable continuous batching, static compile, or paged KV cache first.
- Validate single-request generation with the quantized model.
- Add one serving optimization at a time.
- Route endpoint flags and CLI behavior to [serving-cli](../../serving-cli/SKILL.md); keep quantized backend compatibility here.

## Escalation Checklist

When returning a troubleshooting answer, include:

- Exact failing phase and exception summary.
- Quantization method and config options.
- Backend package versions and hardware summary.
- Whether the checkpoint is regular, pre-quantized, adapter-only, or GGUF.
- Minimal reproduction command or script.
- Safe fallback path and what capability is lost.
