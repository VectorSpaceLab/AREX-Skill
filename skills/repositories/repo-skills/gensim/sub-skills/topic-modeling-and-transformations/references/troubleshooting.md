# Topic Modeling and Transformation Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| LSI/LDA outputs look meaningless or empty | Training and query vectors came from different preprocessing or dictionary ids. | Reuse the saved dictionary and identical tokenization for both training and queries. |
| `LdaModel` appears unstable between runs | Random initialization and multithreading introduce variability. | Set `random_state`, use a small fixture with `workers=1` for smoke checks, and compare topic sets rather than exact floating-point order. |
| LDA training is very slow | Corpus is large, `passes`/`iterations` are high, or BLAS is slow. | Reduce the diagnostic corpus, tune `chunksize`, inspect SciPy BLAS configuration, and consider `LdaMulticore` on one machine. |
| `id2word` missing or topics show numeric ids only | The model was trained without a matching dictionary mapping. | Save the dictionary alongside the model or pass the right `id2word` mapping on load. |
| Coherence scores vary unexpectedly | Tokenization, `topn`, window size, or measure changed. | Keep the exact preprocessing and measure configuration fixed when comparing runs. |
| `CoherenceModel` fails on keyed-vector coherence | Word vectors are unavailable or incompatible with the topic vocabulary. | Use a coherence measure that matches your available inputs, or load matching vectors. |
| `ImportError: Pyro4` | Distributed LDA/LSI path requires the optional `Pyro4` extra. | Install `Pyro4` only if distributed workers/dispatchers are needed; otherwise use local models. |
| Topics collapse to common words | Vocabulary filtering is too weak or stopwords were not removed. | Tighten preprocessing, raise `no_below`, lower `no_above`, and inspect the token list before training. |

## Sanity checks

- Print the first few tokenized documents and the first few BoW vectors.
- Compare `len(dictionary)` with the model's expected feature count.
- Use the bundled `scripts/topic_transform_smoke.py` on a tiny corpus to isolate
  environment issues from corpus-specific issues.
- If an evaluation corpus is too small to be meaningful, treat the run as a
  wiring check rather than a quality verdict.
