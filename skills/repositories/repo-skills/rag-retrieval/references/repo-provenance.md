# Repo Provenance

schema: `disco.repo-provenance.v1`

Generated skill id: `rag-retrieval`

## Source Snapshot

- Source repository: `RAG-Retrieval`
- Remote URL: `https://github.com/NovaSearch-Team/RAG-Retrieval.git`
- Commit: `a91c2922e669c1300720f51cf4e7e9e3896c3027`
- Branch: `master`
- Exact tag: none detected
- Working tree state at generation: dirty due generated `skills/` output only
- Package distribution: `rag_retrieval`
- Package version: `0.2.2`
- Python requirement from metadata: `>=3.8`

## Evidence Paths

- `pyproject.toml`
- `requirements.txt`
- `README.md`
- `README_zh.md`
- `examples/Reranker_Tutorial.md`
- `rag_retrieval/reranker.py`
- `rag_retrieval/infer/reranker_models/`
- `tests/test_cross_encoder_reranker_bge.py`
- `tests/test_cross_encoder_reranker_bge_m3.py`
- `tests/test_cross_encoder_reranker_bce.py`
- `tests/test_llm_reranker_bge_gemma.py`
- `tests/test_llm_reranker_bge_cpm.py`
- `rag_retrieval/train/embedding/`
- `rag_retrieval/train/reranker/`
- `rag_retrieval/train/colbert/`
- `config/`
- `example_data/`
- `examples/stella_embedding_distill/`
- `examples/distill_llm_to_bert_reranker/`
- `examples/synthetic_data_embedding/`
- `examples/MyopicTrap/`

## Refresh Signals

Refresh this skill if any of these change:

- Package metadata begins declaring training packages or console scripts.
- `rag_retrieval.infer.reranker_models` registers a working `ColBERTRanker`.
- `Reranker`, `CorssEncoderRanker`, `LLMRanker`, `RankedResults`, or training script signatures change.
- Training YAML schemas, data loaders, loss names, or distributed config assumptions change.
- MyopicTrap, synthetic data, or distillation examples become supported package workflows instead of example-only scripts.
