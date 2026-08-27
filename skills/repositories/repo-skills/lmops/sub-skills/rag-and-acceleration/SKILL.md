---
name: rag-and-acceleration
description: "Operate CoRAG chain-of-retrieval augmented generation and LLMA
  reference-based lossless decoding workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# rag-and-acceleration

Use this sub-skill when the user asks about either of these LMOps workflow families:

- **CoRAG**: chain-of-retrieval augmented generation for multihop QA using an E5 search server, a vLLM OpenAI-compatible server, a CoRAG-tuned Llama model, and evaluation metrics.
- **LLMA**: reference-based lossless decoding acceleration when generated text overlaps retrieved documents, multi-turn context, or other reference passages.

Do **not** use this sub-skill for generic LLM serving, unrelated vLLM deployments, or in-context-example retriever training. Route retriever training, prompt pools, UPRISE, SE2, CED-ICL, and LLM Retriever work to `../example-retrieval/SKILL.md`.

## Operating route

1. Classify the request:
   - CoRAG service/evaluation orchestration: use `references/corag-workflows.md`, then run the bundled planner `scripts/corag_service_plan.py` to produce a safe checklist before any external command is attempted.
   - LLMA acceleration fit, algorithm explanation, or small sanity check: use `references/llma-reference-decoding.md`, then run `scripts/llma_overlap_demo.py` on a tiny reference/target sample if the user needs an overlap demonstration.
   - Failures or ambiguous runtime symptoms: use `references/troubleshooting.md` first, then return to the relevant workflow reference.
2. Keep heavy operations explicit. CoRAG end-to-end inference expects model/data downloads, long-running servers, CUDA GPUs, and two occupied local ports. LLMA experiments expect converted LLaMA-family weights and a GPU for real model timing.
3. Treat the bundled scripts as planning and demonstration utilities only. They do not download data, start servers, import repository code, load models, or run evaluation.
4. For CoRAG, verify service order before evaluation: embeddings staged -> E5 server ready -> vLLM server ready with the intended model -> multihop QA inference.
5. For LLMA, verify the lossless assumption: copied spans are only accepted after model verification. If references do not overlap likely generations, LLMA may add overhead rather than speed.

## Bundled reference map

- `references/corag-workflows.md`: CoRAG datasets/models, server order, ports/logs, inference flags, outputs, and metrics.
- `references/llma-reference-decoding.md`: LLMA algorithm, CLI parameters, data expectations, and fit criteria for RAG or multi-turn settings.
- `references/troubleshooting.md`: missing data/model/embeddings, E5/vLLM ordering, port/log issues, hardware notes, decode path length, metrics JSON, and reference-overlap assumptions.

## Bundled scripts

- `scripts/corag_service_plan.py`: prints a safe service/evaluation checklist and command concepts for CoRAG without executing anything.
- `scripts/llma_overlap_demo.py`: CPU-only toy demonstration of reference-overlap proposal and verification behavior without importing repository code.

## Verification status

Creation-time verification for this sub-skill is static and CPU-only. End-to-end CoRAG server startup, model downloads, vLLM serving, E5 retrieval over full embeddings, and LLMA GPU timing are documented but not claimed as executed by this skill.
