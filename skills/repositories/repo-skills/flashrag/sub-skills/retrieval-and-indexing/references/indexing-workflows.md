# Indexing Workflows

FlashRAG builds indexes with `python -m flashrag.retriever.index_builder`. Treat this command as an offline preprocessing step: the generated index must match the corpus, retrieval method, model path, pooling/instruction behavior, and modality used at retrieval time.

## Builder Arguments

| Argument | Use | Notes |
| --- | --- | --- |
| `--retrieval_method` | Selects index family and output names | `bm25` builds sparse lexical index; `splade` builds Seismic sparse neural index; other names usually build dense/CLIP Faiss indexes. |
| `--model_path` | Embedding/rerieval model path or model id | Not needed for BM25; required for dense, CLIP, and SPLADE. |
| `--corpus_path` | Input corpus | JSONL with `contents`; multimodal examples may use parquet with text/image fields. |
| `--corpus_embedded_path` | Cached SPLADE/Seismic corpus | Optional; skips re-embedding when already in Seismic expected format. |
| `--save_dir` | Output directory | BM25 creates a `bm25` subdirectory; dense creates `{retrieval_method}_{faiss_type}.index`; CLIP may create modality-suffixed files. |
| `--max_length` | Document token limit for encoding | Impacts dense/CLIP/SPLADE indexing; does not control corpus chunking. |
| `--batch_size` | Encoding batch size | Reduce for GPU memory errors; SPLADE often needs smaller batches than dense bi-encoders. |
| `--use_fp16` | Half precision encoder inference | Useful on GPU; verify model/backend support. |
| `--pooling_method` | Dense pooling | Use `mean`, `cls`, or `pooler`; SentenceTransformers mode does not require manual pooling. |
| `--instruction` | Retrieval instruction prefix | Useful for embedding models not auto-covered by FlashRAG defaults. |
| `--faiss_type` | Faiss factory string | Defaults to `Flat` in `Index_Builder`; choose trained indexes only with enough vectors and validation. |
| `--embedding_path` | Existing memmap embeddings | Must match corpus size and model hidden dimension. |
| `--save_embedding` | Write embedding memmap | Useful for reuse/diagnosis; increases disk usage. |
| `--faiss_gpu` | Build Faiss on GPU then save CPU index | Requires GPU-capable Faiss and compatible CUDA runtime. |
| `--sentence_transformer` | Use SentenceTransformers encoder | Requires `sentence-transformers`; bypasses manual pooling concerns. |
| `--bm25_backend` | BM25 implementation | `bm25s` is lightweight; `pyserini` needs Java/Pyserini. |
| `--index_modal` | CLIP modality | `text`, `image`, or `all`; `all` creates separate text and image indexes. |
| `--n_postings`, `--centroid_fraction`, `--min_cluster_size`, `--summary_energy`, `--nknn`, `--batched_indexing` | SPLADE/Seismic parameters | Require Seismic support and are unrelated to BM25 or dense Faiss. |

Use the bundled command inspector before running expensive indexing:

```bash
python skills/flashrag/sub-skills/retrieval-and-indexing/scripts/inspect_index_builder_args.py \
  --retrieval_method e5 \
  --model_path intfloat/e5-base-v2 \
  --corpus_path corpus.jsonl \
  --save_dir indexes \
  --max_length 512 \
  --batch_size 256 \
  --pooling_method mean \
  --faiss_type Flat
```

## BM25 Workflow

Use BM25 when the task needs CPU-friendly lexical retrieval, quick local indexing, no embedding model, or a fallback baseline.

```bash
python -m flashrag.retriever.index_builder \
  --retrieval_method bm25 \
  --corpus_path corpus.jsonl \
  --save_dir indexes \
  --bm25_backend bm25s
```

Decision points:

- Prefer `bm25s` for easier CPU-only setup and fewer Java/Pyserini issues.
- Use `pyserini` only when Lucene/Pyserini compatibility or existing Pyserini index expectations matter.
- Retrieval config should set `retrieval_method: bm25`, `bm25_backend` to the same backend used at build time, `corpus_path` to the same corpus, and `index_path` to the created BM25 directory.

## Dense Faiss Workflow

Use dense retrieval for embedding-model semantic search. The index is tied to the embedding model, pooling method, instruction behavior, corpus ordering, and Faiss factory type.

```bash
python -m flashrag.retriever.index_builder \
  --retrieval_method e5 \
  --model_path intfloat/e5-base-v2 \
  --corpus_path corpus.jsonl \
  --save_dir indexes \
  --use_fp16 \
  --max_length 512 \
  --batch_size 256 \
  --pooling_method mean \
  --faiss_type Flat
```

If the model is intended for SentenceTransformers:

```bash
python -m flashrag.retriever.index_builder \
  --retrieval_method e5 \
  --model_path intfloat/e5-base-v2 \
  --corpus_path corpus.jsonl \
  --save_dir indexes \
  --sentence_transformer \
  --faiss_type Flat
```

Retrieval config should point `index_path` at the resulting `.index` file and set `retrieval_model_path`, `retrieval_pooling_method`, `instruction`, and `use_sentence_transformer` consistently with the build command.

## Multimodal CLIP Workflow

FlashRAG detects CLIP-style models from the retrieval method or model config. Multimodal indexing can build text, image, or both indexes.

```bash
python -m flashrag.retriever.index_builder \
  --retrieval_method openai-clip-vit-large-patch14-336 \
  --model_path openai/clip-vit-large-patch14-336 \
  --corpus_path mm_corpus.parquet \
  --save_dir indexes/mmqa \
  --max_length 512 \
  --batch_size 512 \
  --faiss_type Flat \
  --index_modal all
```

For retrieval, set `multimodal_index_path_dict` with `text` and/or `image` paths. Image queries may be local image paths, URLs, PIL images, or non-string image-like values depending on the caller. URL image queries require `requests`; local image paths require readable image files and PIL support.

## SPLADE/Seismic Workflow

`retrieval_method splade` builds sparse neural indexes with Seismic. It requires SPLADE model files, Seismic dependencies, and usually smaller batches.

```bash
python -m flashrag.retriever.index_builder \
  --retrieval_method splade \
  --model_path retriever/splade-v3 \
  --corpus_path corpus.jsonl \
  --save_dir indexes \
  --use_fp16 \
  --max_length 512 \
  --batch_size 4 \
  --n_postings 1000 \
  --centroid_fraction 0.2 \
  --min_cluster_size 2 \
  --summary_energy 0.4 \
  --batched_indexing 10000 \
  --nknn 32
```

If `corpus_embedded_path` is supplied, the builder can reuse cached sparse embeddings in Seismic format.

## Index Consistency Checklist

- Validate corpus JSONL before building: every line should parse, `id` values should be unique, and `contents` should be non-empty text.
- Keep corpus and index together as a matched pair; changing corpus order/content requires rebuilding the index.
- Keep dense model, pooling method, instruction, SentenceTransformers flag, and Faiss type recorded with the index.
- For `faiss_gpu`, remember FlashRAG writes a CPU Faiss index after GPU construction; retrieval-time GPU loading still requires GPU-capable Faiss if `faiss_gpu: True`.
- For multimodal CLIP, confirm corpus fields match the chosen `index_modal` and retrieval target modality.
