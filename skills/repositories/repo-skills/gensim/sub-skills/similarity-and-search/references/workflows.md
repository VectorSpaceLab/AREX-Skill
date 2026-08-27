# Similarity and Search Workflows

## In-memory semantic search

```python
from gensim import corpora, models, similarities

texts = [["human", "computer"], ["graph", "trees"], ["user", "system"]]
dictionary = corpora.Dictionary(texts)
corpus = [dictionary.doc2bow(text) for text in texts]
tfidf = models.TfidfModel(corpus)
lsi = models.LsiModel(tfidf[corpus], id2word=dictionary, num_topics=2, random_seed=0)
index = similarities.MatrixSimilarity(lsi[tfidf[corpus]], num_features=2)
query = dictionary.doc2bow(["human", "system"])
ranked = sorted(enumerate(index[lsi[tfidf[query]]]), key=lambda pair: -pair[1])
```

Use this only when the transformed vector matrix fits in memory.

## Sharded index

```python
index = similarities.Similarity(
    output_prefix="my-index",
    corpus=lsi[tfidf[corpus]],
    num_features=2,
    shardsize=32768,
)
index.save("my-index.gensim")
```

Use a stable output prefix and keep the generated shard files. Sharded indexes
are appropriate when the corpus may be too large for a dense matrix.

## Choosing the vector space

- Raw BoW cosine is usually too lexical for semantic search.
- TF-IDF is a lightweight baseline.
- LSI can improve semantic matching for sparse text corpora.
- Embedding-based similarities can help when word-level semantic relatedness
  matters.

Always transform the query through the same dictionary and model chain used for
the indexed corpus.

## Mapping scores back to documents

Indexes return numeric positions/scores. Maintain a separate list, table, or
metadata map from index position to document id/title/source. Persist it next to
the index.
