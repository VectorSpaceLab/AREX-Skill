# KeyedVectors and Vector Formats

## KeyedVectors

`KeyedVectors` stores vectors and similarity operations without the full training
state of a model. It is the right target when you need lookup, similarity,
export, or import.

Important uses:

- `KeyedVectors.load_word2vec_format(...)` for loading the original C word2vec
  text or binary format.
- `KeyedVectors.save_word2vec_format(...)` for exporting vectors in that format.
- `wv.most_similar(...)`, `wv.similarity(...)`, and `wv.distance(...)` for
  retrieval and ranking.

When a task only needs vectors, prefer `KeyedVectors` over a trainable model.
When a task needs continued training or subword/document inference, keep the full
model.

## word2vec format contracts

- Text format typically starts with a header line of `num_vectors vector_size`.
- Binary format uses the same logical layout but stores vector values in binary.
- The `no_header` flag is only for headerless text files that already match the
  expected row count/dimension assumptions.
- `limit` is useful for tiny smoke tests and debugging, not for silent truncation
  of real models.

## Export/import recipe

```python
from gensim.models import KeyedVectors

kv = KeyedVectors.load_word2vec_format("vectors.txt", binary=False)
kv.save_word2vec_format("vectors-out.txt")
```

If a downstream system expects TensorBoard Projector TSV, use the bundled
`word2vec_to_tensor_tsv.py` helper or the Gensim `word2vec2tensor` wrapper.

## Common mistakes

- Loading a text file as binary, or vice versa.
- Expecting a `KeyedVectors` object to continue training like a full model.
- Forgetting that exported vectors need the same token normalization as the
  system that will consume them.
- Exporting large pretrained vectors without confirming the target system can
  load the file size.
