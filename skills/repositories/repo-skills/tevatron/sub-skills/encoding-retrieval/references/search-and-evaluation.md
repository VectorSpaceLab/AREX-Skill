# Search and Evaluation Reference

Tevatron search loads query and passage embedding pickle files, builds a FAISS flat inner-product index, and writes either text rankings or a Python pickle result. Evaluation then converts the text ranking into benchmark-specific formats such as TREC or MS MARCO.

## FAISS Search Implementation

`tevatron.retriever.searcher.FaissFlatSearcher` wraps `faiss.IndexFlatIP`:

- The constructor uses the initial passage array shape to create an index with `embedding_dim` dimensions.
- `add(passage_reps)` adds vectors to the index.
- `search(query_reps, k)` performs one FAISS call.
- `batch_search(query_reps, k, batch_size, quiet=False)` searches query batches and concatenates score/index arrays.

The CLI `tevatron.retriever.driver.search` loads the first passage pickle, constructs a `FaissFlatSearcher`, adds every passage shard, loads query embeddings, optionally moves the index to GPU, searches, then writes the requested ranking format.

## Basic Search Command

```bash
python -m tevatron.retriever.driver.search \
  --query_reps embeddings/query-dev.pkl \
  --passage_reps 'embeddings/corpus.*.pkl' \
  --depth 1000 \
  --batch_size 64 \
  --save_text \
  --save_ranking_to runs/run.dev.txt
```

Arguments:

- `--query_reps`: query embedding pickle from encoding.
- `--passage_reps`: glob pattern for one or more passage embedding pickles.
- `--depth`: top-k per query; default is `1000`.
- `--batch_size`: query batch size per FAISS call; values `<= 0` search all queries in one call.
- `--save_text`: write `qid<TAB>pid<TAB>score`; omit only for pickle output.
- `--save_ranking_to`: ranking output path.
- `--quiet`: disable progress bars for batched search.

Quote wildcard patterns so the Tevatron process owns glob expansion: `--passage_reps 'embeddings/corpus.*.pkl'`.

## Ranking Output Formats

With `--save_text`, each output line is:

```text
query_id<TAB>passage_id<TAB>score
```

The score is an inner product. If embeddings were normalized, it is equivalent to cosine similarity. Text rankings are the safest format for merging, conversion to TREC/MS MARCO, reranking input preparation, and external evaluation.

Without `--save_text`, Tevatron writes a pickle containing `(all_scores, psg_indices)`, where `psg_indices` is a two-dimensional array of passage IDs mapped through the passage lookup list. Use this only for custom Python consumers.

## Single-Pass Search Across Shards

When memory allows, load all passage shards into one index:

```bash
python -m tevatron.retriever.driver.search \
  --query_reps embeddings/query.pkl \
  --passage_reps 'embeddings/corpus.*.pkl' \
  --depth 100 \
  --batch_size -1 \
  --save_text \
  --save_ranking_to runs/rank.txt
```

`--batch_size -1` searches all queries at once. It is convenient and often fast, but it can allocate large result matrices and FAISS working memory.

## Shard-by-Shard Search and Reduction

When a full passage index is too large, search each passage shard separately and merge the text rankings:

```bash
mkdir -p runs/intermediate
for shard in $(seq -f "%02g" 0 19); do
  python -m tevatron.retriever.driver.search \
    --query_reps embeddings/query.pkl \
    --passage_reps "embeddings/corpus.${shard}.pkl" \
    --depth 100 \
    --batch_size 128 \
    --save_text \
    --save_ranking_to "runs/intermediate/${shard}.txt"
done

python path/to/encoding-retrieval/scripts/reduce_results.py \
  --results_dir runs/intermediate \
  --output runs/rank.txt \
  --depth 100
```

The bundled reducer reads all files in lexical path order, validates whitespace-separated `qid pid score` rows, sorts by descending score for each query, uses document ID as a deterministic tie-breaker for equal scores, and keeps the requested depth. It intentionally preserves duplicate document IDs if they appear in multiple shards so duplicated corpus IDs remain visible.

## CPU and GPU FAISS Behavior

Search always builds a CPU `IndexFlatIP` first, then checks `faiss.get_num_gpus()`:

- `0`: use CPU FAISS and log the fallback.
- `1`: copy the index to GPU 0 with float16 GPU cloner options.
- `>1`: copy to all GPUs with sharding and float16 GPU cloner options.

`faiss-cpu` is sufficient for correctness checks and small retrieval. GPU acceleration requires a GPU-enabled FAISS build compatible with the active CUDA runtime; do not assume it is available from a minimal Tevatron installation.

## Minimal Programmatic Search Pattern

```python
import pickle
import numpy as np
from tevatron.retriever.searcher import FaissFlatSearcher

with open('embeddings/corpus.00.pkl', 'rb') as handle:
    passage_reps, passage_ids = pickle.load(handle)
with open('embeddings/query.pkl', 'rb') as handle:
    query_reps, query_ids = pickle.load(handle)

passage_reps = np.asarray(passage_reps, dtype='float32')
query_reps = np.asarray(query_reps, dtype='float32')
assert passage_reps.ndim == query_reps.ndim == 2
assert passage_reps.shape[1] == query_reps.shape[1]

searcher = FaissFlatSearcher(passage_reps)
searcher.add(passage_reps)
scores, indices = searcher.search(query_reps, k=10)
for qid, score_row, index_row in zip(query_ids, scores, indices):
    for score, index in zip(score_row, index_row):
        print(qid, passage_ids[index], float(score), sep='\t')
```

The constructor does not add vectors; call `add()` exactly once for each passage array you want indexed.

## BEIR Evaluation Plan

The repository BEIR shell recipe is reference-only for this skill because it uses benchmark datasets, Pyserini, model downloads, and runtime dependencies outside a minimal smoke environment. Recreate the flow explicitly when those dependencies are allowed:

1. Encode BEIR corpus shards from `Tevatron/beir-corpus` with `--dataset_config DATASET`, optional query/passage prefixes, optional LoRA, optional `--normalize`, and `--dataset_number_of_shards 8`.
2. Encode test queries from `Tevatron/beir` with the same `--dataset_config DATASET`, `--dataset_split test`, model, tokenizer, pooling, normalization, and query prefix choices.
3. Search with `--passage_reps 'EMBEDDING_DIR/corpus_DATASET.*.pkl'`, `--depth 1000`, `--batch_size 64`, and `--save_text`.
4. Convert text ranking to TREC with `python -m tevatron.utils.format.convert_result_to_trec --input rank.DATASET.txt --output rank.DATASET.trec --remove_query`.
5. Evaluate with Pyserini, for example `python -m pyserini.eval.trec_eval -c -mrecall.100 -mndcg_cut.10 beir-v1.0.0-DATASET-test rank.DATASET.trec`.

Common BEIR configs include `arguana`, `climate-fever`, `dbpedia-entity`, `fever`, `fiqa`, `hotpotqa`, `nfcorpus`, `quora`, `scidocs`, `trec-covid`, `webis-touche2020`, and `nq`.

## MS MARCO Evaluation Plan

For MS MARCO passage ranking, convert the text ranking to MARCO format and use Pyserini's MS MARCO evaluator:

```bash
python -m tevatron.utils.format.convert_result_to_marco \
  --input runs/run.dev.txt \
  --output runs/run.dev.marco
python -m pyserini.eval.msmarco_passage_eval msmarco-passage-dev-subset runs/run.dev.marco
```

Ensure the ranking was created with MS MARCO passage query and corpus IDs, not arbitrary local fixture IDs.

## TREC and DPR-Style Evaluation Plan

For TREC-style qrels or DPR-style retrieval accuracy:

```bash
python -m tevatron.utils.format.convert_result_to_trec \
  --input runs/run.nq.test.txt \
  --output runs/run.nq.test.trec
python -m pyserini.eval.convert_trec_run_to_dpr_retrieval_run \
  --topics dpr-nq-test \
  --index wikipedia-dpr \
  --input runs/run.nq.test.trec \
  --output runs/run.nq.test.json
python -m pyserini.eval.evaluate_dpr_retrieval \
  --retrieval runs/run.nq.test.json \
  --topk 20 100
```

These commands require benchmark resources. Treat them as evaluation plans unless the environment is intentionally prepared with Pyserini indexes, qrels, and datasets.
