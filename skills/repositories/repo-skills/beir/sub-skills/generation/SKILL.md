---
name: generation
description: "Generate synthetic BEIR queries, qrels, and passage expansions
  with BEIR generation wrappers and compatible model protocols."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# BEIR Generation

Use this sub-skill when the task is to create synthetic queries, generated training qrels, or expanded passage corpora with BEIR's generation helpers.

## Route

- Start with [references/workflows.md](references/workflows.md) for offline smoke checks, synthetic query generation, generated dataset loading, passage expansion, and multi-process generation patterns.
- Use [references/api-reference.md](references/api-reference.md) for `QueryGenerator`, `PassageExpansion`, `QGenModel`, `TILDE`, output filenames, model protocols, and return shapes.
- Use [references/troubleshooting.md](references/troubleshooting.md) for query-count assertions, duplicate generated questions, prefix/layout confusion, `save_after`, NLTK/model dependency issues, multi-process pool shape, and large model constraints.

## Bundled Helper

- Run a no-download smoke test with fake model objects: `python scripts/generation_smoke.py`
- Keep the generated fixture for inspection: `python scripts/generation_smoke.py --keep-output beir-generation-smoke-output`

The helper imports BEIR generation classes, uses tiny in-memory corpora, and validates that `gen-queries.jsonl`, `gen-qrels/train.tsv`, and `gen-corpus.jsonl` are produced.

## Boundaries

- This sub-skill owns `beir.generation.QueryGenerator`, `beir.generation.PassageExpansion`, `beir.generation.models.QGenModel`, `beir.generation.models.TILDE`, compatible custom generation model protocols, generated qrels layout, output prefixes, `save_after`, and multi-process generation shape.
- Route loading or validating generated BEIR files to [../data-loading/SKILL.md](../data-loading/SKILL.md), especially when using `GenericDataLoader(..., prefix="gen")`.
- Route training on generated queries and qrels to the `training` sub-skill when present.
- Route retrieval runs or metric evaluation on generated datasets to [../retrieval-evaluation/SKILL.md](../retrieval-evaluation/SKILL.md).
