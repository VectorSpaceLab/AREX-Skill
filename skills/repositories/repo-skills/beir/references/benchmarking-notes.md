# Benchmarking Notes

BEIR includes benchmark-style examples for BM25, SBERT, and BM25 plus cross-encoder reranking. Treat those examples as evidence for workflow structure, not as offline smoke tests.

## Practical Benchmark Pattern

1. Validate the dataset layout with the data-loading sub-skill.
2. Choose a first-stage backend with the retrieval-evaluation sub-skill.
3. Save runfiles and metric JSON with BEIR utilities when comparing runs.
4. Add reranking only after first-stage candidates are persisted or reproducible.
5. Record dataset name, split, model identifier, score function, `k_values`, batch size, corpus chunking, optional backend versions, and whether identical query/document ids were ignored.

## Skip Conditions

- Skip full BEIR benchmark runs when the task only needs API inspection or a local smoke test.
- Skip network downloads unless dataset acquisition is explicitly in scope.
- Skip BM25 benchmark execution unless an Elasticsearch-compatible service is configured.
- Skip API-backed provider runs unless credentials, budget, and rate limits are approved.
- Skip GPU/model-heavy benchmarks when hardware, model cache, and dependency versions are not already prepared.

## Lightweight Alternatives

- Use `sub-skills/retrieval-evaluation/scripts/retrieval_smoke.py` for deterministic exact retrieval and metric checks.
- Use `sub-skills/reranking/scripts/rerank_smoke.py` for second-stage candidate ordering checks.
- Use `sub-skills/data-loading/scripts/make_tiny_beir_dataset.py` plus `validate_beir_dataset.py` for schema checks.
