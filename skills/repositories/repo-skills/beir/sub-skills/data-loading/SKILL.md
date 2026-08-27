---
name: data-loading
description: "Prepare, validate, load, download, and persist BEIR-format
  datasets and result files."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Data Loading

Use this sub-skill when the task is about preparing BEIR corpus/query/qrels files, loading local or Hugging Face datasets, validating custom datasets, downloading packaged BEIR data, or saving/loading BEIR runfiles and metric JSON.

## Route

- For file schemas and return shapes, read [references/data-formats.md](references/data-formats.md).
- For local dataset creation, validation, prefixed datasets, downloads, Hugging Face loading, and persistence workflows, read [references/workflows.md](references/workflows.md).
- For exact loader and utility APIs, read [references/api-reference.md](references/api-reference.md).
- For common failures and repair advice, read [references/troubleshooting.md](references/troubleshooting.md).

## Bundled Helpers

- Create a tiny offline fixture: `python scripts/make_tiny_beir_dataset.py ./tiny-beir`
- Validate a BEIR-format dataset: `python scripts/validate_beir_dataset.py ./tiny-beir --split test`
- Validate prefixed query/qrels files: `python scripts/validate_beir_dataset.py ./tiny-beir --split test --prefix my-prefix`

The helpers are self-contained and do not import BEIR. Use them before routing a dataset into retrieval or evaluation.

## Boundaries

- This sub-skill owns `GenericDataLoader`, `HFDataLoader`, `util.download_and_unzip`, `util.save_runfile`, `util.load_runfile`, `util.save_results`, BEIR JSONL/TSV schema checks, prefixed local datasets, and local validation helpers.
- Route retrieval and metric execution to [../retrieval-evaluation/SKILL.md](../retrieval-evaluation/SKILL.md).
- Route reranking to [../reranking/SKILL.md](../reranking/SKILL.md).
- Route query generation or passage expansion to [../generation/SKILL.md](../generation/SKILL.md).
- Route model training data loops to [../training/SKILL.md](../training/SKILL.md).
