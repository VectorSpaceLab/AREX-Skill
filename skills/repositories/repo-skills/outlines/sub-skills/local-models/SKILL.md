---
name: local-models
description: "Set up and troubleshoot Outlines local steerable model
  integrations for Transformers, llama.cpp, MLX-LM, and vLLM offline."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Local Models

Use this sub-skill when an Outlines task needs an offline or local inference engine whose tokens/logits can be steered: Hugging Face Transformers, Transformers multimodal processors, llama.cpp, MLX-LM, or vLLM offline.

This sub-skill is for setup planning, compatibility checks, and local-runtime troubleshooting. It does **not** download models, install GPU stacks, start services, or claim that CUDA/MPS runtime was verified. After a local model object exists, route output-type design to `../structured-generation/SKILL.md` and prompt/chat construction to `../prompt-workflows/SKILL.md`.

## Quick Route

1. **Choose the local wrapper.**
   - Transformers text or multimodal: `outlines.from_transformers(model, tokenizer_or_processor, device_dtype=None)`.
   - llama.cpp: `outlines.from_llamacpp(llama, chat_mode=True)`.
   - MLX-LM: `outlines.from_mlxlm(model, tokenizer)`.
   - vLLM offline: `outlines.from_vllm_offline(llm)`.
2. **Install the smallest optional stack.** Install only the extra and runtime required by the selected wrapper. Do not install every Outlines extra.
3. **Validate prerequisite imports and devices.** Run [`scripts/check_local_model_prereqs.py`](scripts/check_local_model_prereqs.py) before downloading models or allocating GPU memory.
4. **Create the vendor model/tokenizer/client object using that library.** Outlines wraps an existing object; it does not hide the underlying library's model acquisition.
5. **Wrap with Outlines.** The local wrapper exposes `model(prompt, output_type=None, backend=None, **kwargs)`, `batch` where supported, and `stream` where supported.
6. **Pick the output type and backend.** Use `../structured-generation/SKILL.md` for JSON/regex/CFG and backend choices.
7. **Treat hardware failures as runtime constraints.** CUDA, VRAM, MPS, GGUF compilation, tokenizer chat templates, and vLLM guided decoding are not prompt errors.

## Load These References

- [`references/api-reference.md`](references/api-reference.md): loader signatures, local model call patterns, input/output behavior, batch/stream notes, and tokenizer facts.
- [`references/compatibility.md`](references/compatibility.md): optional dependencies, hardware, backend/output support, and what was not verified in the base inspection environment.
- [`references/workflows.md`](references/workflows.md): setup recipes for Transformers, multimodal Transformers, llama.cpp, MLX-LM, and vLLM offline.
- [`references/custom-logits-processors.md`](references/custom-logits-processors.md): extending local generation with an `OutlinesLogitsProcessor`.
- [`references/troubleshooting.md`](references/troubleshooting.md): local runtime errors and recovery steps.

## Bundled Script

Run the read-only prerequisite probe before a local-model setup:

```bash
python scripts/check_local_model_prereqs.py --targets transformers vllm-offline --format text
```

The script checks optional module availability and basic device visibility without installing packages, downloading model weights, or calling network services.

## Non-Negotiable Checks

- Do not claim local CUDA/vLLM/Transformers generation works just because `outlines` imports.
- Do not claim MLX-LM is available on Linux or non-Apple-Silicon hardware.
- Do not use CPU importability as proof of vLLM offline GPU readiness.
- Do not tell future agents to run original repository examples. Distill or reproduce safe checks inside this generated skill.
- Do not confuse `from_vllm` server mode with `from_vllm_offline`; server mode belongs in `../remote-providers/SKILL.md`.
