# Retrieval and Indexing Troubleshooting

Start by identifying the retrieval family: BM25, dense Faiss, multimodal CLIP, SPLADE/Seismic, Serper web, reranking, or multi-retriever fusion. Most failures come from optional dependencies, index/corpus mismatch, model/index mismatch, or malformed corpus data.

## Fast Diagnosis Commands

```bash
python skills/flashrag/sub-skills/retrieval-and-indexing/scripts/validate_corpus_jsonl.py corpus.jsonl --sample 20
python skills/flashrag/sub-skills/retrieval-and-indexing/scripts/inspect_index_builder_args.py --retrieval_method bm25 --corpus_path corpus.jsonl --save_dir indexes --bm25_backend bm25s
python skills/flashrag/sub-skills/retrieval-and-indexing/scripts/inspect_index_builder_args.py --retrieval_method e5 --model_path intfloat/e5-base-v2 --corpus_path corpus.jsonl --save_dir indexes --faiss_type Flat
```

## Dependency Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: faiss` | Dense/CLIP retrieval or indexing imports Faiss | Install CPU or GPU Faiss compatible with the platform; use CPU Faiss unless GPU loading is required. |
| `AttributeError` around `GpuMultipleClonerOptions` or `index_cpu_to_all_gpus` | CPU-only Faiss with `faiss_gpu: True` or `--faiss_gpu` | Disable Faiss GPU or install GPU-capable Faiss. |
| `ModuleNotFoundError: pyserini` | BM25 configured with `bm25_backend: pyserini` | Switch to `bm25s` for lightweight CPU usage or install Pyserini. |
| Java errors from Pyserini/Lucene | Java missing or incompatible | Install a Pyserini-compatible Java runtime and ensure `JAVA_HOME`/PATH are visible. |
| `ModuleNotFoundError: bm25s` or `Stemmer` | BM25s backend missing packages | Install `bm25s` and stemming dependency, or choose Pyserini if already supported. |
| `ModuleNotFoundError: sentence_transformers` | `--sentence_transformer` or `use_sentence_transformer: True` | Install `sentence-transformers` or switch to the Transformers encoder path and set pooling explicitly. |
| `ModuleNotFoundError: requests` | Serper retrieval or URL image loading | Install `requests`; for Serper also provide credentials and network access. |
| Seismic import/build errors | SPLADE/Seismic dependencies unavailable | Install Seismic support and confirm Rust/build prerequisites when needed. |

## Malformed Corpus JSONL

Common problems:

- A line is not valid JSON.
- `contents` is missing, empty, not a string, or lacks `title\nbody` formatting expected by chunking.
- `id` is missing or duplicated.
- Corpus is changed after the index is built.
- Dense corpus order no longer matches Faiss vector positions.

Use `validate_corpus_jsonl.py` and fix the corpus before indexing. For dense retrieval, rebuilding is safer than trying to patch a corpus/index mismatch.

## Dense Model and Index Mismatch

Symptoms include poor retrieval quality, Faiss dimension errors, or warnings about pooling.

Check:

- `retrieval_model_path` at retrieval time matches `--model_path` used for indexing.
- `retrieval_pooling_method` matches `--pooling_method`, unless both indexing and retrieval use SentenceTransformers.
- `instruction` is the same for query/document behavior expected by the embedding model.
- `index_path` points to the `.index` created for this method, not a different model or corpus.
- `faiss_type` was appropriate for corpus size; trained Faiss factories need enough vectors.

## BM25s vs Pyserini Decision

For a CPU-only BM25 task, prefer `bm25s` unless there is a specific Pyserini/Lucene requirement. `bm25s` avoids Java setup and is the FlashRAG default in the base config. Use Pyserini only when the environment has Java/Pyserini working or existing Lucene index compatibility is required.

If a user says “BM25 fails on Java” or “Pyserini install is painful,” recommend rebuilding with:

```bash
python -m flashrag.retriever.index_builder --retrieval_method bm25 --corpus_path corpus.jsonl --save_dir indexes --bm25_backend bm25s
```

and setting:

```yaml
retrieval_method: bm25
bm25_backend: bm25s
index_path: indexes/bm25
corpus_path: corpus.jsonl
```

## Dense Index Command Diagnosis

If a dense-index command is missing required parts:

- No `--model_path`: add the embedding model path or model id.
- No `--corpus_path`: provide the validated corpus JSONL.
- No `--save_dir`: set an output directory with enough disk space.
- No `--faiss_type`: FlashRAG defaults to `Flat`, but specify it explicitly for reproducibility.
- Model path unavailable locally/offline: use a model id only if downloads are allowed; otherwise provide a local model directory.

The bundled command inspector reports these issues without importing `faiss`, `torch`, or model libraries.

## Reranker Problems

- If `use_reranker: True`, set `rerank_model_name`, `rerank_model_path`, `rerank_topk`, `rerank_max_length`, and `rerank_batch_size`.
- Keep `retrieval_topk` at least as large as `rerank_topk`; otherwise FlashRAG may warn that too few documents were retrieved.
- Cross rerankers need sequence classification model compatibility; bi rerankers need pooling settings similar to dense retrieval.
- Reranking uses document `contents`; missing or non-text `contents` reduces quality or fails.

## Multi-Retriever Problems

- Child retrievers need complete `corpus_path`, `index_path`, and model/backend settings.
- `merge_method: rerank` requires reranker fields inside `multi_retriever_setting`, not only global reranker fields.
- Child result lists are reordered by query and retriever count; exceptions from one retriever can cause missing results and confusing counts.
- If combining multimodal and text retrievers, confirm target modality and that each multimodal index path exists.

## Serper Web Retrieval

Serper requires a non-empty `serper_api_key`, `requests`, network access, and a reachable `https://google.serper.dev/search` endpoint. Do not commit keys. If web retrieval returns empty lists, check API quota, HTTP errors, location/language filters, and network restrictions.

## Multimodal Image Fields

- `--index_modal all` creates separate text and image indexes; retrieval config must point to the correct files.
- String queries ending in `.jpg` or `.png`, or beginning with `http`, are treated as images; other strings are text.
- URL image retrieval requires `requests`; local image retrieval needs readable image paths.
- Corpus fields must align with CLIP indexing expectations; missing image values produce failed or low-quality image indexes.
