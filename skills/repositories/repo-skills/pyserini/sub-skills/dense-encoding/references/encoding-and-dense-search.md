# Encoding and Dense Search

This reference distills Pyserini dense corpus encoding, Faiss search, Lucene dense/HNSW search, and hybrid dense-sparse retrieval. Commands are templates: replace placeholder paths and model names only after validating inputs and runtime prerequisites.

## Dense JSONL Inputs

`python -m pyserini.encode` reads either a single JSONL file or a directory of JSONL files. Each line should be one JSON object with a document id and text fields.

Accepted document id keys:

- `id`
- `_id`
- `docid`
- a custom field passed with `input --docid-field FIELD`

Two common content layouts are valid:

- Split fields directly, for example `{"id":"d1","title":"Title","text":"Body"}` with `input --fields title text`.
- A combined `contents` string split by `input --delimiter`, for example `{"id":"d1","contents":"Title\nBody"}` with `input --fields title text --delimiter "\\n"`.

Validate before encoding:

```bash
python scripts/validate_dense_jsonl.py \
  --input collection.jsonl \
  --fields title text
```

Use `--vector-field vector --require-vector --dimension 768` when validating encoded JSONL produced by Pyserini or another encoder.

## Encode a Corpus

Pyserini's dense encoder CLI uses three subcommands in one invocation: `input`, `output`, and `encoder`.

```bash
python -m pyserini.encode \
  input --corpus collection.jsonl --fields text --delimiter "\\n" \
  output --embeddings encoded-jsonl \
  encoder --encoder castorini/tct_colbert-v2-hnp-msmarco \
          --encoder-class tct_colbert \
          --fields text \
          --batch-size 32 \
          --max-length 256 \
          --device cpu
```

Important flags:

- `input --corpus PATH`: JSONL file or directory of JSONL files.
- `input --fields FIELD...`: fields to parse from direct keys or `contents`.
- `input --docid-field FIELD`: custom document id key if not using `id`, `_id`, or `docid`.
- `input --delimiter TEXT`: separator inside `contents`; pass `"\\n"` for newline.
- `input --shard-id N --shard-num M`: split encoding across shards.
- `output --embeddings DIR`: target directory.
- `output --to-faiss`: write a flat Faiss inner-product index directly instead of `embeddings.jsonl`.
- `encoder --encoder NAME_OR_PATH`: model name, model path, or OpenAI embedding model name.
- `encoder --encoder-class CLASS`: explicit class when inference from model name is ambiguous.
- `encoder --fields FIELD...`: fields supplied to the encoder; these must be available from `input --fields`.
- `encoder --device cpu|cuda:0`: Torch inference device.
- `encoder --pooling cls|mean|last|eos`, `--l2-norm`, `--prefix`: auto-model behavior controls.
- `encoder --use-openai --rate-limit N`: use the OpenAI document encoder path; requires credentials at runtime.
- `encoder --multimodal`: route supported multimodal encoders to image/path-aware behavior.

Outputs:

- Without `--to-faiss`: `DIR/embeddings.jsonl`, where each row has `id`, `contents`, and `vector`.
- With `--to-faiss`: `DIR/index` and `DIR/docid`, usable as a flat Faiss index.

For sharded `--to-faiss` encoding, merge shards after all shard commands complete:

```bash
python -m pyserini.index.merge_faiss_indexes --prefix encoded-shard- --shard-num 4
```

## Build a Faiss Index From Encoded Vectors

If you encoded to JSONL first, or want HNSW/PQ options, use the Faiss index builder:

```bash
python -m pyserini.index.faiss \
  --input encoded-jsonl \
  --output dense-index \
  --dim 768 \
  --hnsw \
  --M 64 \
  --efC 256 \
  --threads 8 \
  --device cpu
```

Index modes:

- Flat inner product: omit `--hnsw` and `--pq`.
- Flat L2: add `--metric l2`.
- HNSW: add `--hnsw`; tune `--M` and `--efC`.
- Product quantization: add `--pq`; tune `--pq-m` and `--pq-nbits`.
- HNSW+PQ: add both `--hnsw` and `--pq`.

The input directory may contain either `embeddings.jsonl` files or a previously generated `index` plus `docid`. The output always contains `index` and `docid`.

## Search a Faiss Index

Use `python -m pyserini.search.faiss` for Faiss-backed dense search. It supports local index directories and Pyserini prebuilt index names.

Online query encoding:

```bash
python -m pyserini.search.faiss \
  --index dense-index \
  --topics queries.tsv \
  --topics-format default \
  --output run.dense.txt \
  --hits 1000 \
  --encoder castorini/tct_colbert-v2-hnp-msmarco \
  --encoder-class tct_colbert \
  --device cpu \
  --faiss-device cpu \
  --batch-size 8 \
  --threads 4
```

Pre-encoded queries:

```bash
python -m pyserini.search.faiss \
  --index dense-index \
  --topics queries.tsv \
  --output run.dense.txt \
  --encoded-queries encoded-query-dir \
  --device cpu \
  --faiss-device cpu
```

Useful Faiss search flags:

- `--encoded-queries PATH_OR_NAME`: avoid model inference by loading encoded queries.
- `--encoder`, `--encoder-class`, `--tokenizer`: online query encoder selection.
- `--query-prefix TEXT`: prefix prompts for models that need query instructions.
- `--instruction-config PATH`: instruction configuration for UniIR-style retrievers.
- `--pca-model PATH`: wrap query embeddings with a Faiss PCA model.
- `--searcher bpr`: use binary dense searcher behavior for BPR indexes.
- `--prf-depth`, `--prf-method avg|rocchio|ance-prf`: pseudo-relevance feedback.
- `--sparse-index PATH_OR_NAME`: companion Lucene index required by ANCE-PRF and useful for content lookup.
- `--ef-search N`: HNSW search-time parameter.
- `--normalize-distances`: match Lucene dense score normalization behavior for inner-product indexes.
- `--remove-query`: remove the query document from results for collections where queries are corpus documents.

Faiss indexes do not store raw document text. If the user needs snippets or raw JSON, fetch from a companion sparse Lucene index with `index-search-fetch`.

## Search Lucene Dense/HNSW Indexes

Lucene dense search uses the Lucene search CLI, not the Faiss CLI. Use this route when the index is a Lucene dense vector index, commonly HNSW or flat.

```bash
python -m pyserini.search.lucene \
  --index msmarco-v1-passage.bge-base-en-v1.5.hnsw \
  --topics queries.tsv \
  --output run.lucene-dense.txt \
  --dense \
  --hnsw \
  --ef-search 1000 \
  --onnx-encoder BgeBaseEn15 \
  --hits 1000
```

Dense Lucene flags:

- `--dense`: switch from sparse BM25/impact to vector search.
- `--hnsw` or `--flat`: choose dense vector index type; one is required with `--dense`.
- `--ef-search N`: HNSW search-time breadth.
- `--onnx-encoder NAME`: ONNX encoder used by Pyserini's Lucene dense path.

Route construction of local Lucene indexes, field storage, and raw document fetching to `../../index-search-fetch/SKILL.md`.

## Hybrid Dense-Sparse Retrieval

Hybrid retrieval combines a dense Faiss searcher with a sparse Lucene searcher and interpolates scores. Use it when the user asks for dense+sparse, hybrid, interpolation at search time, or combining BM25 with dense retrieval.

CLI template:

```bash
python -m pyserini.search.hybrid \
  dense --index dense-index \
        --encoder castorini/tct_colbert-v2-hnp-msmarco \
        --encoder-class tct_colbert \
        --device cpu \
  sparse --index sparse-lucene-index \
         --bm25 \
  fusion --alpha 0.1 \
         --hits 1000 \
         --normalization \
  run --topics queries.tsv \
      --output run.hybrid.txt \
      --hits 1000
```

Python API shape:

```python
from pyserini.encode import TctColBertQueryEncoder
from pyserini.search.faiss import FaissSearcher
from pyserini.search.lucene import LuceneSearcher
from pyserini.search.hybrid import HybridSearcher

sparse_searcher = LuceneSearcher.from_prebuilt_index('msmarco-v1-passage')
encoder = TctColBertQueryEncoder('castorini/tct_colbert-msmarco')
dense_searcher = FaissSearcher.from_prebuilt_index('msmarco-v1-passage.tct_colbert-v2-hnp', encoder)
hybrid_searcher = HybridSearcher(dense_searcher, sparse_searcher)
hits = hybrid_searcher.search('what is a lobster roll')
```

Hybrid tuning notes:

- `fusion --alpha` controls interpolation weight; confirm whether a workflow expects the weight on sparse or dense scores.
- `fusion --weight-on-dense` changes the interpretation to weight the dense component.
- `fusion --normalization` normalizes scores before interpolation, which is usually safer when dense and sparse score scales differ.
- Evaluate output runs with `evaluation-and-fusion` after retrieval is complete.

## Command Builder

Use the bundled helper to assemble safe commands without importing Pyserini:

```bash
python scripts/dense_cli_builder.py encode \
  --corpus collection.jsonl \
  --embeddings encoded-jsonl \
  --encoder castorini/tct_colbert-v2-hnp-msmarco \
  --encoder-class tct_colbert \
  --fields text \
  --device cpu
```

The helper also supports `faiss-index`, `faiss-search`, `lucene-dense-search`, and `hybrid-search` subcommands.
