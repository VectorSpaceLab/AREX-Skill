---
name: model-data-api
description: "Inspect SPLADE model, data, index, and inference APIs plus
  validate small SPLADE-style data layouts without running full training."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# SPLADE Model/Data API

Use this sub-skill when a future agent needs to reason about SPLADE Python APIs, data schemas, index objects, or small data validation without launching full training, indexing, retrieval, export, pruning, or evaluation jobs.

## Start Here

- For model classes, `get_model`, bag-of-words helpers, HF Trainer model wrappers, DPR, and inverted index objects, read [API reference](references/api-reference.md).
- For `raw.tsv`, qrel JSON, score JSON, hard-negative pkl-gz, TREC run, and row-id/content-id expectations, read [data formats](references/data-formats.md).
- For safe API inspection and notebook-style bag-of-expanded-words inference concepts, read [inference and API](references/inference-and-api.md).
- For schema mismatches, row/content id bugs, special-token cleaning, offline model issues, and empty vectors, read [troubleshooting](references/troubleshooting.md).

## Bundled Scripts

- Validate a SPLADE-style fixture root without importing SPLADE:

  ```bash
  python sub-skills/model-data-api/scripts/validate_splade_toy_data.py /path/to/dataset-root
  ```

- Inspect installed SPLADE imports and signatures without downloading model weights:

  ```bash
  python sub-skills/model-data-api/scripts/inspect_splade_api.py --json
  ```

## Routing Boundaries

- Use this sub-skill for API signatures, object behavior, data schemas, toy validation, small smoke checks, and inference snippets that do not download weights by default.
- Route classic Hydra train/index/retrieve/evaluate module execution to `../hydra-pipelines/SKILL.md`.
- Route HuggingFace Trainer training and reranking command construction to `../hf-training-reranking/SKILL.md`.
- Route Anserini export, pruning, PISA, BEIR, and evaluation caveats to `../pruning-export-evaluation/SKILL.md`.
