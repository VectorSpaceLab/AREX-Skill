---
name: inference
description: "Load and smoke-check FlagEmbedding embedders, M3 models, and
  rerankers for retrieval inference."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Inference

Use this sub-skill when the task is to load a FlagEmbedding model for inference,
encode queries or corpus passages, compute embedding similarity, compute BGE-M3
dense/sparse/ColBERT scores, rerank query-passage pairs, or smoke-check the
inference API before a retrieval run.

Do not use this sub-skill for fine-tuning data formats, fine-tuning launchers,
training hyperparameters, or checkpoint production. Route those tasks to the
sibling fine-tuning sub-skill. Do not use it for benchmark suites, leaderboard
evaluation, or metric scripts. Route those tasks to the sibling evaluation
sub-skill. For package installation, import failures, and global optional
dependency repair, route to the root troubleshooting reference at
`../../references/troubleshooting.md`.

## Start Here

1. Decide whether the model is an embedder, an M3 embedder, or a reranker.
2. Prefer `FlagAutoModel.from_finetuned(...)` for embedders and
   `FlagAutoReranker.from_finetuned(...)` for rerankers when the checkpoint name
   is in the built-in mapping.
3. For a custom local checkpoint or an unmapped remote checkpoint, pass
   `model_class` explicitly and choose the concrete class behavior from
   [references/api-reference.md](references/api-reference.md).
4. For retrieval, use `encode_queries(...)` for queries and
   `encode_corpus(...)` for passages. Query instructions are applied by
   `encode_queries`; passages normally should not receive the query instruction.
5. For reranking, pass a pair as `("query", "passage")` or a batch as a list
   of pairs to `compute_score(...)`; validate the returned list or nested list
   shape before sorting results.
6. For a safe local check, run `scripts/smoke_inference_api.py --help` first.
   Running the script with no `--model-name` performs import and signature
   probing only. Loading or encoding happens only when `--model-name` is passed.

## Public Entry Points

Embedder auto loader and concrete classes:

- `FlagAutoModel`
- `FlagModel`
- `BGEM3FlagModel`
- `FlagLLMModel`
- `FlagICLModel`
- `FlagPseudoMoEModel`

Reranker auto loader and concrete classes:

- `FlagAutoReranker`
- `FlagReranker`
- `FlagLLMReranker`
- `LayerWiseFlagLLMReranker`
- `LightWeightFlagLLMReranker`

Embedder `model_class` ids:

- `encoder-only-base`: encoder-only dense embedder, normally `FlagModel`.
- `encoder-only-m3`: BGE-M3 dense/sparse/ColBERT embedder,
  `BGEM3FlagModel`.
- `decoder-only-base`: decoder-only LLM embedder, `FlagLLMModel`.
- `decoder-only-icl`: few-shot ICL LLM embedder, `FlagICLModel`.
- `decoder-only-pseudo_moe`: pseudo-MoE LLM embedder,
  `FlagPseudoMoEModel`.

Reranker `model_class` ids:

- `encoder-only-base`: encoder cross-encoder reranker, `FlagReranker`.
- `decoder-only-base`: decoder-only LLM reranker, `FlagLLMReranker`.
- `decoder-only-layerwise`: layer-selectable LLM reranker,
  `LayerWiseFlagLLMReranker`.
- `decoder-only-lightweight`: token-compression LLM reranker,
  `LightWeightFlagLLMReranker`.

## Loader Choice

Use auto loaders when the checkpoint's effective model name is in the built-in
mapping. The effective name is the basename of `model_name_or_path`; if the
basename starts with `checkpoint-`, the parent directory basename is used. This
means a fine-tuned checkpoint directory such as `.../my-bge/checkpoint-1000`
is mapped as `my-bge`, not `checkpoint-1000`.

If auto mapping raises a model-not-found error, do not keep retrying with the
same call. Pick the correct `model_class`, and for embedders also set
`pooling_method`, `query_instruction_format`, and `trust_remote_code` rather
than relying on mapping defaults. Custom decoder-only and remote-code
checkpoints are especially likely to need explicit `trust_remote_code=True`
after code review.

Use concrete classes directly when the architecture is already known or when
you need class-specific options such as M3 return modes, ICL examples,
pseudo-MoE domains, layerwise cutoff layers, or lightweight compression.

## Core Parameters

Use [references/api-reference.md](references/api-reference.md) for verified
signatures and parameter defaults. The parameters most likely to affect
inference behavior are:

- `normalize_embeddings`: normalize dense embeddings before similarity.
- `use_fp16` and `use_bf16`: inference dtype. Use CPU with full precision for
  conservative smoke checks.
- `query_instruction_for_retrieval` and `query_instruction_format`: query-side
  retrieval instructions for embedders.
- `devices`: `None` auto-selects available accelerators then CPU; a string such
  as `"cpu"` or `"cuda:0"` pins one device; a list enables multi-process
  inference across target devices.
- `pooling_method`: use `cls` or `mean` for compatible encoder-only models;
  decoder-only embedders require `last_token`.
- `trust_remote_code`: keep `False` unless the checkpoint requires custom model
  code and that code has been reviewed.
- `truncate_dim`: truncate output vectors for Matryoshka-style embeddings.
- `batch_size`, `query_max_length`, and `passage_max_length`: embedder
  throughput and truncation controls.
- Reranker `query_max_length`, `max_length`, and `normalize`: pair scoring
  truncation and optional sigmoid normalization.
- Layerwise/lightweight reranker `cutoff_layers`, `compress_ratio`, and
  `compress_layers`: score layer selection and token compression controls.

## Expected Outputs

Base embedders return a NumPy array by default. A single input returns a 1-D
vector; a list returns a 2-D array shaped like `(num_texts, embedding_dim)`.
With `convert_to_numpy=False`, expect a torch tensor instead.

`BGEM3FlagModel` returns a dictionary with `dense_vecs`, `lexical_weights`, and
`colbert_vecs`. Keys whose return flag is false are present with `None` values.
Use `dense_vecs @ dense_vecs.T` for dense similarity, use
`compute_lexical_matching_score(...)` for sparse lexical weights, and use
`compute_score(...)` for per-pair M3 mode scores.

Standard rerankers return a list of float scores for a batch. Layerwise and
lightweight rerankers return one score list when a single cutoff layer is used,
or a list of score lists when multiple cutoff layers are requested. Do not sort
documents until this shape is validated.

## Workflows

Use [references/workflows.md](references/workflows.md) for these recipes:

- Auto and concrete embedder loading.
- Query/corpus encoding and similarity computation.
- M3 dense, sparse, ColBERT, and `compute_score` workflows.
- Decoder-only, ICL, and pseudo-MoE embedder options.
- Encoder, decoder, layerwise, and lightweight reranker workflows.
- Batch sizing, CPU fallback, and multi-device inference.

Use [references/troubleshooting.md](references/troubleshooting.md) when:

- Auto mapping cannot find a model.
- Remote-code or local custom-code loading fails.
- Network/cache behavior is surprising.
- CPU/GPU fallback, dtype, or OOM behavior changes results or fails.
- Output shapes or score modes are misused.

## Smoke Checks

Run the bundled helper before writing a larger pipeline:

```bash
python sub-skills/inference/scripts/smoke_inference_api.py
```

The default command imports public inference symbols and prints signatures only.
It does not instantiate a model and should not trigger downloads. From the
`flag-embedding` skill directory, load and encode only when an explicit local
path or model id is supplied:

```bash
python sub-skills/inference/scripts/smoke_inference_api.py \
  --model-kind embedder \
  --model-name MODEL_NAME_OR_PATH \
  --devices cpu \
  --batch-size 2
```

For a custom local checkpoint, add `--model-class`, `--pooling-method`, and
`--query-instruction-format` as needed. For a reranker, use
`--model-kind reranker`; for BGE-M3-specific probes, use `--model-kind m3`.
