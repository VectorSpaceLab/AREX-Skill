---
name: baleen-multihop
description: "Optional ColBERT Baleen multi-hop retrieval extension: HopSearcher
  context search, Baleen engine loops, Condenser fact selection, collectionX
  format, and artifact caveats. Use when tasks mention Baleen, multi-hop
  retrieval, condensed retrieval, HopSearcher, Condenser, collectionX, or L1/L2
  condenser checkpoints."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Baleen Multi-hop

Use this sub-skill for ColBERT's optional Baleen multi-hop retrieval components, not for ordinary one-hop ColBERT indexing or search. Baleen composes a ColBERT `Searcher` variant with an Electra-based `Condenser` to retrieve passages, select sentence-level facts, and feed those facts as context into later hops.

## Route here when

- The user asks about Baleen, multi-hop retrieval, condensed retrieval, hop-aware search, `HopSearcher`, `Condenser`, `collectionX`, or L1/L2 condenser checkpoints.
- The code path involves `baleen.engine.Baleen`, `baleen.hop_searcher.HopSearcher`, `baleen.condenser.condense.Condenser`, `baleen.condenser.model.ElectraReader`, or `baleen.condenser.tokenization.AnswerAwareTokenizer`.
- The user has, or needs to reason about, a built ColBERT index plus Baleen-specific sentence JSONL and condenser checkpoint artifacts.
- The safe answer is to inspect imports/signatures, explain prerequisites, plan an adaptation, or diagnose why a full Baleen run cannot be validated locally.

## Route elsewhere when

- Use `indexing-and-search` for normal `Indexer`, `Searcher`, collection TSVs, one-hop search, or ranking files.
- Use `training-and-distillation` for training or fine-tuning ColBERT retriever checkpoints.
- Use data/evaluation guidance for non-Baleen data conversion and metrics; keep only `collectionX` sentence-format notes here.
- Use modeling/tokenization guidance for ColBERT checkpoint internals unless the tokenizer issue is specifically Baleen's answer-aware condenser tokenizer.

## Safe operating stance

Baleen is bundled as a research-style extension. Imports and source signatures can be inspected on CPU, but end-to-end multi-hop retrieval usually needs local ColBERT index artifacts, a retrieval checkpoint, two Baleen Electra reader checkpoints, a compatible sentence-level `collectionX` file, and often CUDA-capable devices. Do not promise full execution from package import success alone.

Start by confirming artifacts and device constraints. If the user is CPU-only or lacks checkpoints/data, run the import inspector, explain what is available, and provide a static adaptation plan rather than attempting retrieval.

## Common actions

- Use `references/api-reference.md` when you need source-backed class/function behavior, signatures, and composition notes.
- Use `references/baleen-workflows.md` when planning a safe multi-hop flow, validating artifact shape, or explaining how facts become context.
- Use `references/troubleshooting.md` for install/import, optional dependency, CUDA/device, checkpoint, `collectionX`, API misuse, and depth/hop failures.
- Use `scripts/inspect_baleen_imports.py` when you need deterministic import/signature diagnostics without loading checkpoints, building indexes, downloading datasets, or running retrieval.

## Minimal diagnostic

From an environment where `colbert-ai` is installed and `colbert` is importable:

```bash
python scripts/inspect_baleen_imports.py --tiny-fixture
```

Add `--json` for machine-readable output. Treat a passing report as evidence that Baleen import surfaces and loader behavior are available, not as evidence that the user's checkpoints, GPU, index, or full multi-hop workflow will run.
