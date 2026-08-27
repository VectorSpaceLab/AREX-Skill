---
name: bitsandbytes
description: "Use bitsandbytes for k-bit PyTorch quantization, Hugging Face
  quantized model loading, 8-bit and paged optimizers, direct quantized
  layers/functions, and backend installation diagnostics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# bitsandbytes

Use this repo skill when a task involves `bitsandbytes`, k-bit PyTorch quantization, LLM.int8(), QLoRA, 4-bit/NF4/FP4 layers, 8-bit optimizers, paged optimizers, or bitsandbytes install/backend failures.

## Start Here

1. For any new environment, install with `pip install bitsandbytes` and verify with:

   ```bash
   python -c "import bitsandbytes as bnb; print(bnb.__version__)"
   python -m bitsandbytes
   ```

2. If import or backend diagnostics fail, route first to `sub-skills/installation-diagnostics/SKILL.md`.
3. If the user is using Hugging Face `BitsAndBytesConfig`, route to `sub-skills/transformers-integrations/SKILL.md`.
4. If the user is replacing layers or calling `bitsandbytes.functional`, route to `sub-skills/quantized-modules-functions/SKILL.md`.
5. If the user is choosing or debugging `bitsandbytes.optim`, route to `sub-skills/optimizers-training/SKILL.md`.

## Route Map

| User asks about | Use | Why |
| --- | --- | --- |
| `pip install bitsandbytes`, `import bitsandbytes`, `python -m bitsandbytes`, CUDA/ROCm/XPU/HPU/MPS/CPU support, missing `libbitsandbytes_*`, source builds, `BNB_CUDA_VERSION`, `BNB_ROCM_VERSION` | `sub-skills/installation-diagnostics/SKILL.md` | Owns install/backend compatibility and native library troubleshooting. |
| Transformers, Diffusers, PEFT, Accelerate, `BitsAndBytesConfig`, `load_in_8bit`, `load_in_4bit`, NF4, QLoRA, FSDP-QLoRA | `sub-skills/transformers-integrations/SKILL.md` | Owns Hugging Face model-loading and finetuning integration patterns. |
| `Linear8bitLt`, `Linear4bit`, `LinearNF4`, `Embedding8bit`, `Params4bit`, `Int8Params`, `QuantState`, `quantize_4bit`, int8 vectorwise quantization, direct matmul | `sub-skills/quantized-modules-functions/SKILL.md` | Owns direct module/function API usage and state-dict caveats. |
| `Adam8bit`, `AdamW8bit`, `PagedAdamW8bit`, `Lion8bit`, `AdEMAMix8bit`, `GlobalOptimManager`, `StableEmbedding`, optimizer memory savings | `sub-skills/optimizers-training/SKILL.md` | Owns optimizer selection, training-loop integration, and state checks. |

## Shared References and Scripts

- Read `references/repo-provenance.md` before deciding whether this skill matches a current bitsandbytes checkout or should be refreshed.
- Read `references/troubleshooting.md` for cross-cutting routing from symptoms to the right sub-skill.
- Read `references/installation-compatibility.md` for public install requirements and backend support summary.
- Read `references/performance-and-benchmarks.md` before interpreting memory or speed claims.
- Run `scripts/check-bitsandbytes-install.py --json` for a safe import/backend report that delegates to the bundled installation diagnostic helper.

## Common Decision Points

- `BitsAndBytesConfig` belongs to Transformers, not to the `bitsandbytes` package. Use the Transformers integration sub-skill for those configs.
- CPU-only environments can validate imports, signatures, and some construction paths, but they do not prove CUDA/ROCm/XPU kernels or memory savings.
- Direct quantized layers usually quantize when moved to a real device with `.to(device)`. Construction on CPU is not the same as executing quantized kernels.
- 8-bit optimizer memory savings depend on optimizer-state size; small tensors below `min_8bit_size=4096` intentionally remain 32-bit.
- Paged optimizers and many quantized model-loading paths need supported accelerator behavior and should not be promised from CPU-only checks.

## Safe Validation Commands

```bash
python scripts/check-bitsandbytes-install.py --json
python sub-skills/installation-diagnostics/scripts/backend-report.py --json
python sub-skills/quantized-modules-functions/scripts/quantized-module-smoke.py --json
python sub-skills/optimizers-training/scripts/cpu-optimizer-smoke.py --optimizer adam8bit --steps 3
python sub-skills/transformers-integrations/scripts/transformers-bnb-config-check.py --mode qlora --json
```

Only run GPU or model-loading checks after confirming hardware, optional dependencies, model access, and that downloads or cache use are allowed.
