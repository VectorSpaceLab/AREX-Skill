# Workflows

Set this helper variable in examples to the directory that contains this sub-skill:

```bash
SIM_SEARCH_SKILL=/path/to/text2vec/sub-skills/similarity-search
```

The scripts below write JSONL and do not load a model unless you pass `--model-name`.

## 1. Score aligned pairs without network using vector columns

Use this when each row already contains two numeric vectors. This avoids model downloads and avoids an accidental cross-product matrix.

```jsonl
{"pair_id":"p1","sentence1":"how to change card","sentence2":"change bound bank card","embedding1":[1,0,0],"embedding2":[0.9,0.1,0]}
{"pair_id":"p2","sentence1":"cat outside","sentence2":"movie is great","embedding1":[0,1,0],"embedding2":[0,0,1]}
```

```bash
python "$SIM_SEARCH_SKILL/scripts/score_pairs.py" \
  --input-file pairs.jsonl \
  --output-file pair_scores.jsonl
```

Expected output shape: one JSON object per input row, each with a single `score` field.

## 2. Score aligned pairs from an embedding lookup file

Use this when pair rows refer to embedding IDs rather than carrying vectors inline.

`pairs.tsv`:

```tsv
pair_id	id1	id2	sentence1	sentence2
p1	q1	d1	如何更换花呗绑定银行卡	花呗更改绑定银行卡
p2	q2	d2	cat outside	movie is great
```

`embeddings.jsonl`:

```jsonl
{"id":"q1","embedding":[1,0]}
{"id":"d1","embedding":[0.95,0.05]}
{"id":"q2","embedding":[0,1]}
{"id":"d2","embedding":[1,0]}
```

```bash
python "$SIM_SEARCH_SKILL/scripts/score_pairs.py" \
  --input-file pairs.tsv --input-format tsv \
  --embedding-file embeddings.jsonl \
  --id1-column id1 --id2-column id2 \
  --output-file pair_scores.jsonl
```

## 3. Score text pairs with `Similarity`

Use this when you need the package model scorer. Prefer a local model directory or already-cached model ID if the environment must stay offline.

```bash
python "$SIM_SEARCH_SKILL/scripts/score_pairs.py" \
  --input-file pairs.csv --input-format csv \
  --text1-column sentence1 --text2-column sentence2 \
  --model-name <local-or-cached-model> \
  --output-file pair_scores.jsonl
```

Notes:

- `score_pairs.py` calls `Similarity.get_score` row by row so output remains aligned.
- If you use the default public model ID and it is not cached, the package may try to download model weights.
- For Word2Vec/WMD experiments, pass `--embedding-type word2vec --similarity-type wmd` and expect optional word-vector dependencies/caches.

## 4. No-network BM25 query-to-corpus retrieval

Use BM25 when you need lexical retrieval immediately and do not want model downloads.

`corpus.txt` is one document per line:

```text
花呗更改绑定银行卡
我什么时候开通了花呗
A man is eating food.
```

`queries.txt` is one query per line:

```text
如何更换花呗绑定银行卡
A man is eating pasta.
```

```bash
python "$SIM_SEARCH_SKILL/scripts/search_corpus.py" \
  --mode bm25 \
  --corpus-file corpus.txt \
  --query-file queries.txt \
  --top-k 2 \
  --output-file bm25_hits.jsonl
```

Output contains one JSON object per query with a `hits` list. Each hit has `rank`, `corpus_id`, `corpus`, and `score`.

## 5. Dense semantic search from cached embeddings

Use this when embeddings were created earlier by another workflow. Embeddings must align by row order with `corpus.txt` and `queries.txt`.

`corpus_embeddings.json`:

```json
[[1, 0], [0, 1], [0.7, 0.7]]
```

`query_embeddings.json`:

```json
[[0.9, 0.1]]
```

```bash
python "$SIM_SEARCH_SKILL/scripts/search_corpus.py" \
  --mode dense \
  --corpus-file corpus.txt \
  --query-file queries.txt \
  --corpus-embeddings-file corpus_embeddings.json \
  --query-embeddings-file query_embeddings.json \
  --top-k 2 \
  --output-file dense_hits.jsonl
```

This path uses cosine semantics. It does not require a model download.

## 6. Optional model-backed dense search

Use this only when a suitable local or cached model is available, or when network downloads are acceptable.

```bash
python "$SIM_SEARCH_SKILL/scripts/search_corpus.py" \
  --mode dense \
  --corpus-file corpus.txt \
  --query-file queries.txt \
  --model-name <local-or-cached-model> \
  --top-k 5 \
  --output-file dense_hits.jsonl
```

For large corpora, generate and cache embeddings separately in the `embeddings` sub-skill, then run dense search from files.

## 7. Library-only pattern for matrix scoring

Use a matrix only when you want all pair combinations:

```python
from text2vec import Similarity

m = Similarity(model_name_or_path="<local-or-cached-model>")
scores = m.get_scores(["a", "b"], ["x", "y"])
assert scores.shape == (2, 2)
print(scores[0][1])  # score for a vs y
```

For aligned pairs, use `get_score` in a loop or the bundled `score_pairs.py` helper.