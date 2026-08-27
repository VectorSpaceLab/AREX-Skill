# Embeddings and Phrases Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `RuntimeError` or empty vocabulary during training | `min_count` filtered out every token or sentence iterator is empty. | Lower `min_count`, inspect the first sentences, and verify the iterator can be iterated more than once if needed. |
| `KeyError` for a word in `Word2Vec`/`KeyedVectors` | The word is out-of-vocabulary. | Check `word in model.wv.key_to_index`; use FastText for OOV-capable workflows or handle missing words explicitly. |
| FastText OOV vectors still fail or look bad | The word has no useful known character n-grams or training data is too small. | Tune `min_n`/`max_n`, improve corpus coverage, or treat the token as unknown. |
| Doc2Vec cannot infer or tag documents correctly | Training docs were not `TaggedDocument` objects or tags collide unexpectedly. | Use `TaggedDocument(tokens, [tag])` for training and plain token lists for `infer_vector`. |
| Results change between runs | Random initialization, workers, and floating-point order vary. | Set `seed`, use `workers=1` for deterministic smoke tests, and assert shapes/rankings rather than exact vector values. |
| A saved artifact cannot continue training | Only `KeyedVectors` were saved. | Save the full `Word2Vec`/`FastText`/`Doc2Vec` model when future training is required. |
| `load_word2vec_format` fails | Text/binary flag, header, encoding, or dimension mismatch. | Confirm `binary`, `no_header`, `encoding`, and first-line vector count/dimension. |
| No phrases are emitted | `threshold` or `min_count` too high, or tokenization split phrases differently. | Inspect tokenized sentences; lower thresholds for diagnostics; freeze only after tuning. |
| Word Mover's Distance fails | Optional POT/import name `ot` is missing. | Install POT only when WMD is selected, or route to exact cosine/soft-cosine similarity alternatives. |

## Diagnostic checklist

1. Print a few input sentences or tagged documents.
2. Check `len(model.wv)` or `len(model.dv)` after training.
3. Verify `model.vector_size` or inferred vector shape.
4. Save/load a tiny artifact before running a full training job.
5. Run `scripts/embedding_smoke.py` to separate package/environment issues from
   corpus-specific issues.
