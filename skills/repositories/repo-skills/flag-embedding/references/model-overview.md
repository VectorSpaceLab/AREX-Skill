# Model Overview

Use this reference when choosing a FlagEmbedding model family, `model_class`, or
backend strategy before entering the inference, fine-tuning, or evaluation
sub-skills.

## Loader Families

FlagEmbedding exposes two auto loaders:

- `FlagAutoModel.from_finetuned(...)` for embedders.
- `FlagAutoReranker.from_finetuned(...)` for rerankers.

Auto loaders infer the concrete class from the effective checkpoint name. The
effective name is the basename of `model_name_or_path`; if that basename starts
with `checkpoint-`, the parent directory basename is used. If a checkpoint is
not in the mapping, pass `model_class` explicitly.

## Embedder Classes

| `model_class` | Public class | Primary use |
| --- | --- | --- |
| `encoder-only-base` | `FlagModel` | Dense encoder embeddings such as BGE, E5, GTE, BCE, or compatible local checkpoints. |
| `encoder-only-m3` | `BGEM3FlagModel` | BGE-M3 dense, sparse lexical, and ColBERT multivector retrieval. |
| `decoder-only-base` | `FlagLLMModel` | LLM embedding checkpoints with last-token pooling. |
| `decoder-only-icl` | `FlagICLModel` | LLM embedding checkpoints using few-shot task examples. |
| `decoder-only-pseudo_moe` | `FlagPseudoMoEModel` | Pseudo-MoE LLM embedding checkpoints with optional domain routing. |

Common mapped embedder families include BGE, Qwen3-Embedding, E5, GTE, SFR,
Linq, and BCE. For BGE checkpoints, common names include `bge-m3`,
`bge-en-icl`, `bge-multilingual-gemma2`, and BGE English/Chinese small/base
/large variants.

## Reranker Classes

| `model_class` | Public class | Primary use |
| --- | --- | --- |
| `encoder-only-base` | `FlagReranker` | Encoder cross-encoder rerankers such as BGE reranker base/large/v2-m3. |
| `decoder-only-base` | `FlagLLMReranker` | Decoder-only LLM rerankers. |
| `decoder-only-layerwise` | `LayerWiseFlagLLMReranker` | Layer-selectable MiniCPM-style rerankers. |
| `decoder-only-lightweight` | `LightWeightFlagLLMReranker` | Lightweight layerwise rerankers with token compression. |

Common mapped reranker names include `bge-reranker-base`, `bge-reranker-large`,
`bge-reranker-v2-m3`, `bge-reranker-v2-gemma`,
`bge-reranker-v2-minicpm-layerwise`, and
`bge-reranker-v2.5-gemma2-lightweight`.

## Task-Based Choice

- For ordinary semantic retrieval, start with `FlagAutoModel` and a dense BGE
  or compatible encoder checkpoint.
- For multilingual, long-context, or hybrid dense/sparse retrieval, choose
  `BGEM3FlagModel` or `model_class="encoder-only-m3"` and decide which return
  modes are needed.
- For few-shot query adaptation, use `FlagICLModel` with examples and matching
  instruction formats.
- For reranking top retrieved documents, use `FlagAutoReranker` or a concrete
  reranker class; keep `--rerank_top_k` small enough for the target hardware.
- For training a model, use `sub-skills/fine-tuning/SKILL.md`; for measuring a
  model, use `sub-skills/evaluation/SKILL.md`.

## Backend And Dependency Implications

CPU is sufficient for import, signature, schema, and tiny command validation.
GPU is usually needed for practical throughput, large LLM embedders/rerankers,
full fine-tuning, DeepSpeed, and flash-attn workflows.

Evaluation imports require FAISS and `pytrec_eval`; CPU evaluation can use
`faiss-cpu`. GPU FAISS should be installed only in a CUDA-compatible environment
chosen for that purpose.

Fine-tuning extras install DeepSpeed and flash-attn, but flash-attn depends on
the PyTorch, CUDA, compiler, and GPU architecture combination. Removing
`--use_flash_attn True` is a valid fallback when the model can run without it.

## Model Loading Risk

Remote model ids may download model weights, tokenizers, and custom code.
Before using remote ids, confirm network/cache policy and whether the checkpoint
requires `trust_remote_code=True`. Prefer local checkpoint paths for offline or
reproducible workflows.
