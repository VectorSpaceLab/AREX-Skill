---
name: flag-embedding
description: "Use FlagEmbedding for embedding, reranking, retrieval evaluation,
  and fine-tuning workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# FlagEmbedding

Use this repo skill when a task involves FlagEmbedding, BGE embedding models,
BGE-M3 dense/sparse/ColBERT retrieval, BGE rerankers, retrieval evaluation, or
FlagEmbedding fine-tuning data and launch commands.

Read `references/repo-provenance.md` when checking whether this skill matches a
current checkout or package version. Read `references/model-overview.md` when
choosing model families or deciding whether automatic model routing is likely to
work. Read `references/troubleshooting.md` for install/import, optional
dependency, backend, model-cache, and remote-code problems.

## Install And Import

Base package install:

```bash
python -m pip install -U FlagEmbedding
```

Fine-tuning extras:

```bash
python -m pip install -U "FlagEmbedding[finetune]"
```

Evaluation workflows also need retrieval metric/index dependencies that are not
always installed by the base package metadata:

```bash
python -m pip install faiss-cpu pytrec_eval
```

Use GPU-specific FAISS, CUDA PyTorch, DeepSpeed, or flash-attn only after the
runtime backend is deliberately prepared. Do not treat a CPU import as proof of
GPU training or flash-attn compatibility.

Minimal import check:

```bash
python - <<'PY'
from FlagEmbedding import FlagAutoModel, FlagAutoReranker
print(FlagAutoModel, FlagAutoReranker)
PY
```

Bundled environment/API probe from this skill directory:

```bash
python scripts/check_flag_embedding_env.py
```

## Route Map

Use `sub-skills/inference/SKILL.md` when the task is to load embedders or
rerankers, encode queries/corpus, compute BGE-M3 dense/sparse/ColBERT scores,
rerank query-passage pairs, choose `model_class`, handle instructions, or
smoke-check inference APIs without running training or benchmark jobs.

Use `sub-skills/fine-tuning/SKILL.md` when the task is to prepare or validate
training JSONL, mine or reason about hard negatives, add teacher-score fields,
split long data, choose an embedder/reranker fine-tuning module, build a
`torchrun` command, or diagnose DeepSpeed/flash-attn/training-data issues.

Use `sub-skills/evaluation/SKILL.md` when the task is to run or prepare
retrieval evaluation with FlagEmbedding, create custom `corpus.jsonl` /
`test_queries.jsonl` / `test_qrels.jsonl`, choose MTEB/BEIR/MSMARCO/MIRACL/MLDR
/MKQA/AIR-Bench/BRIGHT commands, add a reranker to evaluation, or interpret
metrics and output directories.

## Common Decisions

Prefer auto loaders for mapped checkpoints:

```python
from FlagEmbedding import FlagAutoModel, FlagAutoReranker

embedder = FlagAutoModel.from_finetuned(
    "BAAI/bge-base-en-v1.5",
    query_instruction_for_retrieval="Represent this sentence for searching relevant passages:",
    devices="cpu",
    use_fp16=False,
)

reranker = FlagAutoReranker.from_finetuned(
    "BAAI/bge-reranker-base",
    devices="cpu",
    use_fp16=False,
)
```

For custom or unmapped checkpoints, set `model_class` explicitly instead of
retrying the same auto call. Embedder ids include `encoder-only-base`,
`encoder-only-m3`, `decoder-only-base`, `decoder-only-icl`, and
`decoder-only-pseudo_moe`. Reranker ids include `encoder-only-base`,
`decoder-only-base`, `decoder-only-layerwise`, and `decoder-only-lightweight`.

Use CPU and full precision for cheap smoke checks. Move to CUDA, fp16, bf16,
large batch sizes, remote model ids, or benchmark downloads only after the user
approves the runtime, cache, and budget.

## Verification Anchors

The generated skill is grounded in these public surfaces:

- Public imports and mappings under `FlagEmbedding.inference`.
- Fine-tuning module entry points under `FlagEmbedding.finetune`.
- Evaluation module entry points under `FlagEmbedding.evaluation`.
- Maintained package examples distilled into bundled references and scripts.
- Small native candidates and synthetic fixtures recorded in the integration
  reports under the review/test artifact directory.

Runtime files do not require the original checkout. Source examples and scripts
were distilled into the generated skill references or adapted as bundled helper
scripts.
