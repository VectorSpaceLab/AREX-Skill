# Evidence Summary

This generated repo skill was distilled from repository-owned source, docs, examples, tests, and installed-package inspection for RAGatouille 0.0.9post2.

## Primary Evidence

| Evidence | Use in skill |
| --- | --- |
| `pyproject.toml` | Distribution name/version, package list, runtime dependencies, optional extras. |
| `ragatouille/__init__.py` | Public exports, version, future PyLate migration warning. |
| `ragatouille/RAGPretrainedModel.py` | Public model-loading, indexing, search, rerank, encode, LangChain adapter methods and signatures. |
| `ragatouille/RAGTrainer.py` | Training/fine-tuning API, data-prep parameters, training config defaults. |
| `ragatouille/data/` | `CorpusProcessor`, `TrainingDataProcessor`, LlamaIndex sentence splitter, raw-data conversion behavior. |
| `ragatouille/models/colbert.py` | ColBERT index/search/rerank/encode internals, result shapes, warnings, CRUD behavior, training call. |
| `ragatouille/models/index.py` | PLAID index construction/search/update/delete behavior, FAISS/PyTorch k-means branch, metadata loading. |
| `ragatouille/models/utils.py` | Hugging Face Hub and Vespa ONNX export helpers. |
| `ragatouille/integrations/_langchain.py` | LangChain retriever and compressor wrappers. |
| `ragatouille/negative_miners/simpleminer.py` | Hard negative mining, language/model-size routing, Voyager/sentence-transformer behavior. |
| `README.md` | Public install notes, Windows/WSL warning, training/indexing/search examples, integrations context. |
| `docs/` | API docs and project roadmap context. |
| `examples/*.ipynb` | User-facing indexing, training, reranking, index-free, LlamaHub, and synthetic-data recipes; treated as evidence only because many require network/credentials/model downloads. |
| `tests/` | Ground-truth candidates for input validation, metadata/index behavior, training-data processing, and expensive model tests. |

## Installed-Package Facts Verified

The private inspection environment verified these public facts without exposing private paths in runtime skill files:

- Distribution metadata: `RAGatouille` version `0.0.9.post2`.
- Import module: `ragatouille`, exposing `RAGPretrainedModel` and `RAGTrainer`.
- Public signatures for `RAGPretrainedModel.from_pretrained`, `from_index`, `index`, `add_to_index`, `delete_from_index`, `search`, `rerank`, `encode`, `search_encoded_docs`, `clear_encoded_docs`, and LangChain adapter methods.
- Public signatures for `RAGTrainer.__init__`, `prepare_training_data`, `train`, `TrainingDataProcessor.process_raw_data`, `CorpusProcessor.process_corpus`, `ModelIndexFactory.construct`, `export_to_huggingface_hub`, and `export_to_vespa_onnx`.
- `TrainingDataProcessor` tiny triplet smoke can produce `[[0, 0, 1]]` without model downloads when using explicit triplets and `mine_hard_negatives=False`.
- CPU Torch import was sufficient for inspection; real training/indexing may need more compute.

## Compatibility Findings

- RAGatouille 0.0.9post2 imports a legacy LangChain path; latest LangChain 1.x can break top-level import.
- A legacy-compatible LangChain line is needed for this release unless upstream code is updated.
- `fast-pytorch-kmeans` can require `psutil` at import time.
- The package warns on import that a future RAGatouille 0.0.10 release migrates to PyLate.

## Native Candidate Classification

| Native artifact | Planned verification role | Safety class |
| --- | --- | --- |
| `tests/test_training_data_processor.py` | Safe evidence for training-data processor dispatch. | safe-runnable |
| `tests/test_training_data_loading.py` | Data-shape evidence, but direct fixture initializes models. | skip-network unless monkeypatched |
| `tests/test_pretrained_optional_args.py` | Ground truth for indexing metadata/doc IDs and CRUD. | skip-network/skip-expensive |
| `tests/e2e/test_e2e_indexing_searching.py` | End-to-end index/search expected results. | skip-network/skip-expensive |
| `tests/test_training.py` | One-step training smoke. | skip-gpu-or-hardware/skip-expensive |
| `examples/*.ipynb` | User workflow evidence for recipes. | evidence-only unless network/model/credential use is approved |

## Source Script Inventory

The repository contains no source-owned `scripts/`, `tools/`, or `bin/` directories. Generated skill helpers are adapted from public API/test behavior and intentionally avoid model downloads, uploads, GPU use, or original-repo file dependencies.
