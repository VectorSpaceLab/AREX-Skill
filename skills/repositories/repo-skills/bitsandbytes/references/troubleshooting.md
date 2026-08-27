# Cross-Cutting Troubleshooting

## Purpose

Use this reference to route a bitsandbytes failure to the nearest focused sub-skill. Do not treat it as a substitute for the detailed troubleshooting files under each sub-skill.

## Symptom Routing

| Symptom or request | First route | Why |
| --- | --- | --- |
| `ModuleNotFoundError: torch`, `ModuleNotFoundError: bitsandbytes`, failed `pip install`, `python -m bitsandbytes` output, missing `libbitsandbytes_cpu.so`, `libbitsandbytes_cuda*`, `libbitsandbytes_rocm*`, `libcudart`, `amdhip64`, or source build questions | `sub-skills/installation-diagnostics/references/troubleshooting.md` | Package/backend setup is failing before workflow code can be trusted. |
| Transformers `BitsAndBytesConfig` errors, missing `transformers`, `accelerate`, or `peft`, `device_map` issues, gated model downloads, QLoRA/FSDP-QLoRA dtype confusion | `sub-skills/transformers-integrations/references/troubleshooting.md` | The failure is in the Hugging Face integration layer or optional dependencies. |
| `Linear8bitLt`/`Linear4bit` state dict issues, missing `SCB`, `quant_state` lost, `.to(device)` timing, unsupported quantization dtype, direct primitive errors | `sub-skills/quantized-modules-functions/references/troubleshooting.md` | The failure is direct bitsandbytes module/function behavior. |
| `Adam8bit` memory savings missing, `GlobalOptimManager` override ignored, paged optimizer unavailable, small tensors remain float32 | `sub-skills/optimizers-training/references/troubleshooting.md` | The failure is optimizer-state or training-loop behavior. |

## General Rules

- Fix import/backend setup before changing model, module, or optimizer code.
- Separate no-download config validation from model execution. A config can be valid while runtime loading fails because of hardware, memory, credentials, or network.
- Treat CPU-only smoke checks as import/API validation only. Do not infer accelerator kernel support or memory savings from them.
- Prefer bundled scripts in this skill over original repository scripts; runtime instructions must stay self-contained.

## Minimal Read-Only Checks

```bash
python scripts/check-bitsandbytes-install.py --json
python -c "import bitsandbytes as bnb, torch; print(bnb.__version__, torch.__version__)"
python -m bitsandbytes
```

If these fail, collect the exact traceback and route to installation diagnostics before running deeper workflow checks.
