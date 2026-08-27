---
name: text-classification
description: "Routes legacy TensorFlow 1.x text-classification workflows for
  brightmart/text_classification, including raw data preparation, classic
  baselines, seq2seq and memory models, relation workflows, and ensemble
  post-processing."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# text-classification

Use this repo skill for the legacy `brightmart/text_classification` checkout: a TensorFlow 1.x / TFLearn-era collection of classic text-classification models, Zhihu-style data utilities, seq2seq label generation, memory-network variants, relation workflows, and logit post-processing helpers.

This repository is not an installable Python package. When you need runtime inspection, use a Python 3.7-era TensorFlow 1.x/TFLearn environment and the bundled smoke scripts; do not assume TensorFlow 2.x, eager execution, or Python 3.13 compatibility.

## Start here

1. Read [`references/repo-provenance.md`](references/repo-provenance.md) if you need to compare this skill against another checkout or decide whether it is stale.
2. Read [`references/model-overview.md`](references/model-overview.md) for the high-level model-family map.
3. Read [`references/troubleshooting.md`](references/troubleshooting.md) for cross-cutting TensorFlow 1.x, cache, checkpoint, and import pitfalls.
4. Use [`scripts/check_legacy_text_classification_env.py`](scripts/check_legacy_text_classification_env.py) when you want a safe environment/import smoke check.

## Route map

| Task signal | Read this sub-skill | Why |
| --- | --- | --- |
| Raw text lines, `__label__` parsing, vocabulary/label dictionaries, n-grams, cache keys, TSV validation, label formatting | [`sub-skills/data-preparation/SKILL.md`](sub-skills/data-preparation/SKILL.md) | Validates and normalizes the repo's Zhihu-style data formats before a model run. |
| fastTextB, TextCNN, TextRNN, TextRCNN, Hierarchical Attention Network, BERT, toy TFLearn examples, graph-shape inspection | [`sub-skills/classification-models/SKILL.md`](sub-skills/classification-models/SKILL.md) | Covers the classic flat classifier families and their checkpoints, shapes, and losses. |
| Seq2seq with attention, Transformer seq2seq/classifier, EntityNetwork, Dynamic Memory Network, `_GO`/`_END`/`_PAD` label generation | [`sub-skills/sequence-and-memory-models/SKILL.md`](sub-skills/sequence-and-memory-models/SKILL.md) | Covers sequence-generation and memory-network style workflows. |
| Two-sentence relation classification, TextCNN+RCNN hybrids, boosting label weights, ensemble logit fusion | [`sub-skills/relation-and-ensemble-workflows/SKILL.md`](sub-skills/relation-and-ensemble-workflows/SKILL.md) | Covers paired-input workflows and post-processing of exported logits. |

## Shared references

- `references/model-overview.md` — concise model-family selection guide for the repo.
- `references/troubleshooting.md` — cross-cutting failure patterns that affect more than one sub-skill.
- `references/repo-provenance.md` — commit, dirty-state, and evidence-path snapshot for staleness checks.
- `references/repo-routing-metadata.json` — structured metadata consumed by the repo-skills router during import.

## Shared scripts

- `scripts/check_legacy_text_classification_env.py` — safe import/environment smoke check for the legacy TensorFlow 1.x stack and common helper modules.

## Operating rules

- Prefer the closest sub-skill instead of trying to solve every workflow from the root.
- Treat README performance numbers as historical context, not a reproduction guarantee.
- Expect external HDF5 caches, pickle vocabularies, pretrained word2vec binaries, checkpoint directories, and long runs for full training/prediction.
- Use `data-preparation` first whenever raw line formats, cache keys, or label encodings are unclear; many downstream failures start there.
- Use `classification-models` for the main flat classifiers; use `sequence-and-memory-models` only when label generation or memory context is part of the contract.
- Use `relation-and-ensemble-workflows` for two-input relation tasks, hybrid CNN+RCNN variants, boosting, and logit fusion instead of trying to adapt a flat classifier ad hoc.

## When to cross-check

- If a task mentions a specific model family, read that sub-skill's references before making graph or data claims.
- If a task mentions checkpoint restore, label-map mismatch, or fixed batch sizes, read the appropriate troubleshooting page before rerunning anything.
- If you are considering a refresh for another checkout, compare the current repository state to `references/repo-provenance.md` first.
