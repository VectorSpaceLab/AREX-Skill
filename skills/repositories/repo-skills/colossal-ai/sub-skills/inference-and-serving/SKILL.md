---
name: inference-and-serving
description: "Use Colossal-Inference APIs and commands for LLM generation,
  speculative decoding, diffusion inference, serving, and benchmark planning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Inference and Serving

Use this sub-skill when the task involves `colossalai.inference`, `InferenceConfig`, `InferenceEngine`, LLaMA generation, tensor-parallel inference, speculative decoding, Stable Diffusion 3 patched parallelism, or inference service/client benchmarks.

## Route Here

- Construct or interpret `InferenceConfig` and `InferenceEngine` usage.
- Generate safe `colossalai run` commands for LLM generation, tensor parallelism, drafter/speculative decoding, or diffusion prompts.
- Diagnose model path, tokenizer, policy, CUDA graph, KV cache, TP size, or patched parallelism errors.
- Plan serving/client/benchmark checks without starting a service by default.

## Reroute

- General install, `colossalai run`, and hostfile issues: use `../installation-and-launch/SKILL.md`.
- ShardFormer training/model-sharding and topology theory: use `../parallelism-and-sharding/SKILL.md`.
- Training/fine-tuning with Booster: use `../booster-training/SKILL.md`.
- ColossalChat or application-specific inference after training: use `../application-recipes/SKILL.md`.

## Fast Start

```python
from colossalai.inference import InferenceConfig, InferenceEngine
config = InferenceConfig(max_batch_size=8, max_output_len=256, tp_size=1)
```

Generate commands without running models:

```bash
python scripts/inference_command_builder.py llama --model /models/llama --max-length 128 --nproc-per-node 1
python scripts/inference_command_builder.py llama --model /models/main --drafter-model /models/draft --tp-size 2 --nproc-per-node 2
python scripts/inference_command_builder.py diffusion --model /models/sd3 --prompt "hello world" --nproc-per-node 2
```

## References and Helpers

- `references/inference-api.md` lists inspected `InferenceConfig`/`InferenceEngine` fields and API patterns.
- `references/llm-and-speculative-decoding.md` covers LLaMA generation, tensor parallelism, drafter models, and GLIDE caveats.
- `references/diffusion-serving-benchmarks.md` covers Stable Diffusion 3, patched parallelism, serving, clients, and benchmark safety.
- `references/troubleshooting.md` maps inference-specific failures to checks.
- `scripts/inference_command_builder.py` prints safe ColossalAI inference command templates.

## Operating Rules

- Do not download or load real model weights unless the user provided/approved the model path and compute budget.
- Align `--nproc_per_node` with tensor or patched parallelism sizes.
- Treat optimized CUDA kernels and CUDA graphs as optional acceleration paths; fall back to safer settings for debugging.
