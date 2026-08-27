---
name: data-and-config
description: "Work with FlashRAG Config, dataset JSONL, corpus JSONL,
  Item/Dataset concepts, safe input validation, and reproducible path/save
  behavior before retrieval or pipeline execution."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# FlashRAG Data and Config

Use this sub-skill when preparing or reviewing FlashRAG inputs: YAML/dict configuration, dataset rows, corpus rows, split handling, save/output behavior, and safe validation before building indexes or running pipelines.

## Route by task

- **Config merge and defaults**: Start with [configuration.md](references/configuration.md) for priority, required keys, `basic_config` sections, path derivation, and `disable_save`.
- **Dataset and corpus files**: Use [data-formats.md](references/data-formats.md) to distinguish evaluation JSONL from retrieval corpus JSONL and to create tiny fixtures.
- **APIs and utilities**: Use [api-reference.md](references/api-reference.md) for `Config`, `Item`, `Dataset`, and dataset utility behavior.
- **Validation without runtime imports**: Run [validate_flashrag_inputs.py](scripts/validate_flashrag_inputs.py) before expensive pipelines or index builds.
- **Failure diagnosis**: Use [troubleshooting.md](references/troubleshooting.md) for dependency symptoms, invalid JSONL, split normalization, required config keys, and save-directory surprises.

## Boundaries

This sub-skill covers configuration and input data readiness only. For corpus indexing, retriever model paths, cache behavior, and FAISS/BM25 details, switch to `retrieval-and-indexing`. For actually running methods, generators, refiner/pipeline behavior, and method-specific configs, switch to `pipelines-and-methods`.

## Quick safe check

Validate a config plus evaluation and corpus JSONL without importing FlashRAG:

```bash
python skills/flashrag/sub-skills/data-and-config/scripts/validate_flashrag_inputs.py \
  --config my_config.yaml \
  --eval-jsonl dataset/nq/test.jsonl \
  --corpus-jsonl indexes/general_knowledge.jsonl
```

Use `--show-effective-summary` to print the high-impact keys that should be reviewed before routing to retrieval or pipelines.
