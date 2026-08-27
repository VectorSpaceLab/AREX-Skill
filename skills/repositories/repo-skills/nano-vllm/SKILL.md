---
name: nano-vllm
description: "Use nano-vLLM for CUDA-backed offline Qwen3 text generation,
  batched inference, KV-cache and tensor-parallel tuning, throughput
  benchmarking, or maintenance of its lightweight vLLM-like runtime."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# nano-vLLM

nano-vLLM is a small, Qwen3-focused inference engine whose public entry points
are `nanovllm.LLM` and `nanovllm.SamplingParams`. Use this skill for local,
offline generation or for understanding/tuning the engine. It is not a generic
Transformers model runner: the implementation initializes CUDA/NCCL and uses
Triton plus FlashAttention, so a CPU-only environment is not a full substitute.

## Choose a route

- **Generate text from local weights:** read
  [sub-skills/offline-inference/SKILL.md](sub-skills/offline-inference/SKILL.md).
  It covers model-directory checks, chat templates, prompt batching, sampling,
  output records, and the bundled generation wrapper.
- **Tune memory, batching, CUDA graphs, tensor parallelism, or throughput:**
  read [sub-skills/performance-tuning/SKILL.md](sub-skills/performance-tuning/SKILL.md).
- **Modify or diagnose Qwen3 layers, safetensors loading, attention context,
  or tensor-parallel implementation:** read
  [sub-skills/model-internals/SKILL.md](sub-skills/model-internals/SKILL.md).

Read [references/troubleshooting.md](references/troubleshooting.md) before
changing dependencies or interpreting a hang/OOM. Read
[references/repo-provenance.md](references/repo-provenance.md) when deciding
whether this skill matches a checkout or whether a refresh is needed.

## Install and inspect

Use Python 3.10–3.12 and a CUDA-capable PyTorch environment. Install the
published dependency set, including a compatible `flash-attn` build, then
install nano-vLLM from the published Git repository or from a local checkout:

```bash
python -m pip install "torch>=2.4.0" "triton>=3.0.0" "transformers>=4.51.0" flash-attn xxhash
python -m pip install git+https://github.com/GeeeekExplorer/nano-vllm.git
```

For a checkout, an editable install is useful during development:

```bash
python -m pip install -e .
```

Run the bundled read-only probe before loading weights:

```bash
python scripts/check_env.py
```

The probe reports package imports, CUDA visibility, and FlashAttention without
constructing a model. Full inference additionally needs a local Hugging Face
Qwen3-format directory containing configuration, tokenizer files, and
`safetensors` weights; the engine does not download weights itself.

## Shared operating rules

1. Validate the model directory and CUDA stack before constructing `LLM`.
2. Start with `enforce_eager=True` while diagnosing correctness or CUDA-graph
   capture failures; restore graph capture only after a stable smoke run.
3. Use `tensor_parallel_size=1` first. Larger values require NCCL, visible
   GPUs, a localhost rendezvous, and dimensions divisible by the world size.
4. Keep `max_model_len`, batching limits, and `gpu_memory_utilization` within
   available VRAM. A failure while allocating KV cache is a capacity/config
   failure, not a prompt-format failure.
5. Prefer a list of `SamplingParams` when requests need different temperatures
   or token budgets. Results preserve request order and contain `text` and
   `token_ids` fields.
6. Exit cleanly after inference when embedding the engine in a longer process;
   the engine registers an exit handler, but explicit lifecycle management is
   safer around multiprocessing.

The generated runtime tree is self-contained. The source repository snapshot,
coverage decisions, and verification artifacts are intentionally kept outside
this runtime directory.
