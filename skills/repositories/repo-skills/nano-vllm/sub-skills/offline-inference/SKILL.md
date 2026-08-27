---
name: offline-inference
description: "Use nano-vLLM for CUDA-backed offline Qwen3 generation from local
  Hugging Face weights, including prompt batching, chat templates, sampling
  parameters, and output interpretation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Offline inference

Use this route when the task is to generate text locally with
`nanovllm.LLM`. It assumes a complete local Qwen3-compatible model directory;
this implementation does not accept a remote model id by itself and does not
provide a CPU fallback.

## Fast path

1. Run the root `scripts/check_env.py` and require CUDA.
2. Verify the model directory has Hugging Face config/tokenizer files and one
   or more `safetensors` files.
3. Start with `enforce_eager=True`, `tensor_parallel_size=1`, and a small
   `max_tokens` value.
4. Use the bundled
   [scripts/run_generation.py](scripts/run_generation.py) for a parameterized
   command, or construct the API directly.
5. Check that each result has `text` and `token_ids`, and that result order
   matches input order. Move to
   [../performance-tuning/SKILL.md](../performance-tuning/SKILL.md) only after
   correctness is established.

Read [references/api-reference.md](references/api-reference.md) for signatures
and output shape, [references/workflows.md](references/workflows.md) for model
and chat-template recipes, and
[references/troubleshooting.md](references/troubleshooting.md) for failure
recovery.

## Minimal API

```python
from nanovllm import LLM, SamplingParams

llm = LLM("/path/to/local-qwen3", enforce_eager=True, tensor_parallel_size=1)
params = SamplingParams(temperature=0.6, max_tokens=128)
results = llm.generate(["Explain KV caching in one sentence."], params)
print(results[0]["text"])
llm.exit()
```

`generate` also accepts `list[list[int]]` token-id prompts. Pass a list of
`SamplingParams` with the same length as the prompts when requests need
independent temperatures or budgets. `temperature` must be positive; greedy
sampling is intentionally rejected by `SamplingParams`.

## Guardrails

- Put engine construction and generation behind
  `if __name__ == "__main__":` because tensor parallelism uses spawned worker
  processes.
- If model loading fails, inspect config/tokenizer/weight names before changing
  prompts. The loader is Qwen3-specific and expects safetensors names it can
  map into packed QKV and gate/up projections.
- A low-memory or no-KV-block error is a runtime capacity issue. Lower length
  and batch limits before changing sampling.
- Use `ignore_eos=True` only when deliberately measuring fixed token budgets;
  otherwise EOS can finish a request before `max_tokens`.
