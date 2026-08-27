---
name: local-inference-decoding
description: "Use OptiLLM local HuggingFace and MLX inference, LoRA adapters,
  backend checks, reasoning tokens, logprobs, and advanced decoding methods
  safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Local Inference and Decoding

Use this sub-skill when OptiLLM itself loads and serves local models, or when a task involves local decoding methods and backend troubleshooting.

## Read first for these tasks

- Use `OPTILLM_API_KEY=optillm` to enable the built-in local inference client.
- Serve HuggingFace models, private models, or model strings with LoRA adapters separated by `+`.
- Configure `active_adapter`, logprobs, token limits, or reasoning-token accounting.
- Use local decoding modes: `cot_decoding`, `entropy_decoding`, `thinkdeeper`, `deepconf`, or `autothink`.
- Diagnose CUDA, MPS, MLX, bitsandbytes, PEFT, transformers, HuggingFace cache, or model download issues.

Route external provider/server setup to [../proxy-server/SKILL.md](../proxy-server/SKILL.md). Route core approach selection to [../optimization-approaches/SKILL.md](../optimization-approaches/SKILL.md). Route JSON/router/deepthink plugins to [../plugins-and-tools/SKILL.md](../plugins-and-tools/SKILL.md) when the plugin is the user-facing surface.

## Core workflow

1. **Confirm local inference is intended.** `OPTILLM_API_KEY` activates the local engine; unset it for external provider proxying.
2. **Probe backend before loading models.** Run `python scripts/check_local_backend.py --json` to inspect torch/CUDA/MPS/transformers/MLX imports without downloads.
3. **Choose model string.** Use a HuggingFace model id, optionally with LoRA adapters appended by `+`.
4. **Bound generation.** Set request `max_tokens` or `OPTILLM_MAX_TOKENS` for small models that may not emit EOS.
5. **Add decoding only when supported.** `cot_decoding`, `entropy_decoding`, `thinkdeeper`, `deepconf`, and `autothink` require local model internals/logits, not just an external provider.
6. **Validate response fields.** Check `usage.completion_tokens_details.reasoning_tokens` when using `<think>` tags or reasoning methods.

## Minimal local server example

```bash
export OPTILLM_API_KEY=optillm
optillm --model meta-llama/Llama-3.2-1B-Instruct
```

Client:

```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8000/v1", api_key="optillm")
response = client.chat.completions.create(
    model="meta-llama/Llama-3.2-1B-Instruct",
    messages=[{"role": "user", "content": "Say hello."}],
    max_tokens=64,
)
```

LoRA model string:

```text
base-model+adapter-one+adapter-two
```

Select adapter through request body:

```python
extra_body={"active_adapter": "adapter-one"}
```

## References and helper

- [references/local-inference.md](references/local-inference.md) covers local engine APIs, model/LoRA strings, logprobs, response classes, and request knobs.
- [references/decoding-methods.md](references/decoding-methods.md) covers `cot_decoding`, `entropy_decoding`, `thinkdeeper`, `deepconf`, and `autothink`.
- [references/hardware-and-backends.md](references/hardware-and-backends.md) covers CUDA/MPS/MLX checks and backend claims.
- [references/troubleshooting.md](references/troubleshooting.md) maps model/cache/backend errors to recovery steps.
- Run `python scripts/check_local_backend.py --help` before loading a real model.

## Validation checklist

- Local inference was requested explicitly; external provider env vars are not being shadowed by `OPTILLM_API_KEY`.
- `torch` imports and reports the expected backend.
- Private HuggingFace models have a non-empty token set.
- Model and adapter identifiers are accessible or cached.
- Token limits are bounded for smoke tests.
- MLX-specific paths are used only on macOS Apple Silicon.
