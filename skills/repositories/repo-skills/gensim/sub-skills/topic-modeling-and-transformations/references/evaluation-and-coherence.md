# Evaluation and Coherence

`CoherenceModel` supports several families of topic coherence. Select inputs and
parameters deliberately:

| Measure | Typical inputs | Caution |
| --- | --- | --- |
| `u_mass` | BoW corpus + dictionary | Based on corpus co-occurrence; sensitive to corpus and dictionary. |
| `c_v` | Tokenized texts + dictionary | Uses sliding-window/text analysis; can be slower. |
| `c_uci` | Tokenized texts + dictionary | Window and probability estimates affect scores. |
| `c_npmi` | Tokenized texts + dictionary | Requires sufficient co-occurrence observations. |
| `c_w2v` | Tokenized texts + keyed vectors | Requires compatible word vectors and OOV handling. |

Example shape:

```python
from gensim.models import CoherenceModel

coherence = CoherenceModel(
    model=lda,
    texts=texts,
    dictionary=dictionary,
    coherence="c_v",
    topn=10,
)
score = coherence.get_coherence()
```

For `u_mass`, pass `corpus=corpus` instead of relying on text windows. For
explicit topic lists, use `topics=...` and provide the matching dictionary or
keyed vectors as required.

Do not treat coherence as an absolute truth. Keep preprocessing, vocabulary
filtering, topic count, `topn`, window size, and measure constant while comparing
models. Check topic interpretability and downstream retrieval/classification
behavior as well.

Callbacks such as `CoherenceMetric`, `PerplexityMetric`, `DiffMetric`, and
`ConvergenceMetric` can monitor training, but visualization callbacks may require
optional Visdom. Keep callback failures separate from model-training failures.
