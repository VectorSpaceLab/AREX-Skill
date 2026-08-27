# BEIR Troubleshooting

Read this when a BEIR workflow fails before the issue clearly belongs to one sub-skill.

## Install and Import Problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: beir` | BEIR is not installed in the active Python | Install with `pip install beir`; for checkout work use `pip install -e .` from the repository root. |
| `ModuleNotFoundError` for `faiss`, `elasticsearch`, `cohere`, `voyageai`, `vllm`, `peft`, or `llm2vec` | Optional backend package is missing | Install only the optional dependency needed for the chosen backend. Do not install every optional group just to run a local data or metric check. |
| Transformer or SentenceTransformers import errors | Version drift between PyTorch, Transformers, SentenceTransformers, and NumPy | Pin a mutually compatible stack before debugging BEIR logic. For older BEIR training APIs, verify that the Transformers version still exposes APIs used by `beir.retrieval.train`. |
| `nltk` or stopwords errors in generation models | TILDE-style generation needs NLTK and the stopwords corpus | Install `nltk` and make the stopwords corpus available, or use fake-model smoke tests for offline workflow validation. |

## Data and File Layout Problems

- BEIR local datasets expect `corpus.jsonl`, `queries.jsonl`, and `qrels/<split>.tsv` unless a prefix or custom filenames are passed.
- `GenericDataLoader(prefix="gen")` looks for `gen-queries.jsonl` and `gen-qrels/<split>.tsv`; it does not automatically use `gen-corpus.jsonl` unless `corpus_file="gen-corpus.jsonl"` is passed.
- Qrels rows referencing missing query or document ids usually cause empty evaluation coverage or loader filtering surprises; run `sub-skills/data-loading/scripts/validate_beir_dataset.py` first.
- `EvaluateRetrieval.evaluate(..., ignore_identical_ids=True)` mutates the supplied results by removing query ids that match document ids. Copy the results first if you need the original object.

## Service, Credential, and Network Problems

- Dataset downloads, Hugging Face datasets, model downloads, API embedding providers, and benchmark examples can require network access. Use bundled smoke scripts for offline checks.
- BM25 requires a running Elasticsearch-compatible service in addition to the Python package. Check host, index name, analyzer language, field mapping, and service health before debugging BEIR scoring.
- API-backed embeddings require provider credentials and can incur costs or rate limits. Verify environment variables and provider package imports before running large corpora.

## Hardware and Scale Problems

- Dense exact search encodes and scores corpus chunks in memory; reduce `batch_size`, `corpus_chunk_size`, and `top_k` for small machines.
- FAISS GPU, vLLM, LoRA, NVEmbed, LLM2Vec, MonoT5, TILDE, and full training workflows may require GPU memory and model cache access.
- Training examples are long-running and download-heavy. Use the training sub-skill preflight script to validate qrels, triplets, and evaluator guards before starting expensive training.

## Where to Go Next

- Data schema or loader errors: [data-loading troubleshooting](../sub-skills/data-loading/references/troubleshooting.md).
- Retrieval backend or metric errors: [retrieval-evaluation troubleshooting](../sub-skills/retrieval-evaluation/references/troubleshooting.md).
- Reranker candidate or model-output errors: [reranking troubleshooting](../sub-skills/reranking/references/troubleshooting.md).
- Query generation or expansion output errors: [generation troubleshooting](../sub-skills/generation/references/troubleshooting.md).
- Training data or dependency compatibility errors: [training troubleshooting](../sub-skills/training/references/troubleshooting.md).
