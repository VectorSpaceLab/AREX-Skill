# Repo Provenance

## Source Snapshot

- Repository: RAGatouille
- VCS: git
- Commit: `e75b8a964a870dea886548f78da1900804749040`
- Branch: `main`
- Exact tag: none detected
- Remote URL: https://github.com/AnswerDotAI/RAGatouille
- Package distribution: `RAGatouille`
- Package version: `0.0.9post2` in source and `0.0.9.post2` from installed distribution metadata
- Skill generation state: generated from a dirty checkout because the new `skills/` tree was created during generation

## Dirty State Summary

At generation time, the only recorded untracked path was:

- `skills/`

No pre-existing source-code modifications were detected before generating the skill tree.

## Evidence Paths

These repository-relative paths informed this skill:

- `pyproject.toml`
- `README.md`
- `docs/api.md`
- `docs/index.md`
- `docs/roadmap.md`
- `mkdocs.yml`
- `ragatouille/__init__.py`
- `ragatouille/RAGPretrainedModel.py`
- `ragatouille/RAGTrainer.py`
- `ragatouille/data/`
- `ragatouille/integrations/`
- `ragatouille/models/`
- `ragatouille/negative_miners/`
- `ragatouille/utils.py`
- `examples/01-basic_indexing_and_search.ipynb`
- `examples/02-basic_training.ipynb`
- `examples/03-finetuning_without_annotations_with_instructor_and_RAGatouille.ipynb`
- `examples/04-reranking.ipynb`
- `examples/05-llama_hub.ipynb`
- `examples/06-index_free_use.ipynb`
- `tests/test_pretrained_loading.py`
- `tests/test_pretrained_optional_args.py`
- `tests/e2e/test_e2e_indexing_searching.py`
- `tests/test_training_data_loading.py`
- `tests/test_training_data_processor.py`
- `tests/test_training.py`
- `tests/data/`

## Refresh Signals

Refresh this skill when:

- RAGatouille migrates to the PyLate backend in or after version 0.0.10;
- `RAGPretrainedModel`, `RAGTrainer`, data processors, integrations, or export helper signatures change;
- dependency metadata pins LangChain, LlamaIndex, Torch, ColBERT, FAISS, or `fast-pytorch-kmeans` differently;
- new CLI entry points, scripts, docs, or tests are added;
- examples stop matching current public APIs.
