# Yellowbrick text visualizers

Yellowbrick text visualizers live in `yellowbrick.text` and expect text data to
be in the right representation before `fit()`: raw strings, token lists,
vectorized document matrices, or nested part-of-speech tags. Use this reference
to choose the visualizer, prepare the input, handle optional dependencies, and
save figures safely in headless environments.

## Import map and signatures

```python
from yellowbrick.text import (
    FreqDistVisualizer,
    TSNEVisualizer,
    UMAPVisualizer,
    DispersionPlot,
    WordCorrelationPlot,
    PosTagVisualizer,
)
```

| Visualizer | Constructor shape | Input to `fit()` | Main use |
|---|---|---|---|
| `FreqDistVisualizer` | `(features, ax=None, n=50, orient="h", color=None, **kwargs)` | Count-vectorized document matrix, optional `y` labels | Top token frequencies, optionally by class. |
| `TSNEVisualizer` | `(ax=None, decompose="svd", decompose_by=50, labels=None, classes=None, colors=None, colormap=None, random_state=None, alpha=0.7, **kwargs)` | Numeric vectorized corpus matrix, optional `y` labels | 2D t-SNE document embedding. |
| `UMAPVisualizer` | `(ax=None, labels=None, classes=None, colors=None, colormap=None, random_state=None, alpha=0.7, **kwargs)` | Numeric vectorized corpus matrix, optional `y` labels | 2D UMAP document embedding. |
| `DispersionPlot` | `(search_terms, ax=None, colors=None, colormap=None, ignore_case=False, annotate_docs=False, labels=None, **kwargs)` | Tokenized docs: list/generator of token lists, optional `y` labels | Location of known terms through a corpus. |
| `WordCorrelationPlot` | `(words, ignore_case=False, ax=None, cmap="RdYlBu", colorbar=True, fontsize=None, **kwargs)` | Raw text docs: list/generator of strings | Co-occurrence/correlation heatmap for words or phrases. |
| `PosTagVisualizer` | `(ax=None, tagset="penn_treebank", colormap=None, colors=None, frequency=False, stack=False, parser=None, **kwargs)` | Pre-tagged nested docs or raw text with a parser | POS tag counts overall or stacked by class. |

Use `FreqDistVisualizer` in public code. `FrequencyVisualizer` exists inside the
implementation as a backward-compatibility alias, but it is not the reliable
top-level import name from `yellowbrick.text`.

## Optional dependency summary

- `UMAPVisualizer` requires `umap-learn`; without it, construction raises a
  Yellowbrick value error telling the user to install UMAP.
- `PosTagVisualizer(parser="nltk" | "nltk_word" | "nltk_wordpunct")` requires
  `nltk` and the Treebank/tokenizer data used by the parser path.
- `PosTagVisualizer(parser="spacy" | "spacy_en_core_web_sm" | ...)` requires
  `spacy` and the named language model.
- Parser-free `PosTagVisualizer` with pre-tagged nested tuples requires no
  `nltk`, `spacy`, parser data, or model download.
- `FreqDistVisualizer`, `TSNEVisualizer`, `DispersionPlot`, and
  `WordCorrelationPlot` do not require Yellowbrick text-specific optional extras,
  but vectorization normally uses scikit-learn.

## `FreqDistVisualizer`

Use for top-token counts after count vectorization.

Required input:

1. raw documents are transformed with `CountVectorizer` or another count-based
   vectorizer;
2. `features` is the vocabulary list ordered by column index;
3. `X` passed to `fit(X, y=None)` is the count matrix;
4. `y` is optional; if supplied for conditional frequencies, use a numpy array or
   pandas Series so boolean indexing works predictably.

Pattern:

```python
from sklearn.feature_extraction.text import CountVectorizer
from yellowbrick.text import FreqDistVisualizer

vectorizer = CountVectorizer()
X = vectorizer.fit_transform(docs)
features = vectorizer.get_feature_names_out()

viz = FreqDistVisualizer(features=features, n=25, orient="h")
viz.fit(X, y)
viz.show(outpath="freqdist.png", clear_figure=True)
```

Common fixes:

- Empty or unhelpful bars usually mean the vectorizer removed expected words via
  `stop_words`, `min_df`, token pattern, or preprocessing.
- For modern scikit-learn versions, prefer `get_feature_names_out()`. Very old
  Yellowbrick examples/tests may still call removed `get_feature_names()`;
  update those snippets instead of downgrading the workflow guidance.
- Use `FreqDistVisualizer`, not `FrequencyVisualizer`, in new guidance.

## `TSNEVisualizer`

Use for a qualitative 2D embedding of already-vectorized documents.

Required input:

- `X` must be numeric document vectors, sparse or dense;
- raw strings must be vectorized first, often with `TfidfVectorizer`;
- `y` is optional and colors points by class or cluster label;
- `labels=` can provide display labels matching sorted classes.

Important parameters:

- `decompose="svd"` is the default and is suitable for sparse text matrices;
- `decompose="pca"` is for dense data;
- `decompose=None` skips pre-decomposition;
- `decompose_by` controls preliminary dimensionality and should be small enough
  for the data shape;
- sklearn TSNE parameters such as `perplexity` can be passed through `**kwargs`.

Pattern:

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from yellowbrick.text import TSNEVisualizer

X = TfidfVectorizer().fit_transform(docs)
viz = TSNEVisualizer(random_state=13, decompose="svd", decompose_by=50, perplexity=20)
viz.fit(X, y)
viz.show(outpath="tsne.png", clear_figure=True)
```

For tiny synthetic smokes, lower `perplexity` below the number of samples. For
large corpora, sample documents or skip t-SNE unless the user accepts the cost.

## `UMAPVisualizer`

Use for UMAP embeddings of already-vectorized documents when `umap-learn` is
available.

Required input:

- `X` must be numeric document vectors;
- `y` is optional and colors points;
- raw text must be vectorized first.

Text-specific guidance:

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from yellowbrick.text import UMAPVisualizer

X = TfidfVectorizer().fit_transform(docs)
viz = UMAPVisualizer(random_state=13, metric="cosine", n_neighbors=10)
viz.fit(X, y)
viz.show(outpath="umap.png", clear_figure=True)
```

If `umap-learn` is missing, do not pretend UMAP is available. Either install the
optional dependency in a user-approved environment or fall back to
`TSNEVisualizer` for a dependency-light qualitative embedding.

## `DispersionPlot`

Use for the relative positions of selected terms throughout a corpus.

Required input:

- `search_terms` is a list of terms to track;
- `X` passed to `fit()` is a list or generator of token lists, not raw strings;
- `y` is optional and colors points by document category;
- `ignore_case=True` is useful when token casing is inconsistent;
- `annotate_docs=True` draws document boundaries.

Pattern:

```python
from yellowbrick.text import DispersionPlot

token_docs = [doc.split() for doc in docs]
viz = DispersionPlot(["game", "player", "score"], ignore_case=True, annotate_docs=True)
viz.fit(token_docs, y)
viz.show(outpath="dispersion.png", clear_figure=True)
```

Every search term must appear after tokenization and case normalization. If a
term is missing, update tokenization/casing or choose terms that actually appear.

## `WordCorrelationPlot`

Use for a heatmap of binary document-level co-occurrence among requested words
or phrases.

Required input:

- `words` is a non-empty list of words or multi-word phrases;
- `X` passed to `fit()` is a list or generator of raw text strings;
- every requested term must occur in at least one document;
- `ignore_case=True` lowercases terms and vectorization.

Pattern:

```python
from yellowbrick.text import WordCorrelationPlot

viz = WordCorrelationPlot(["game", "player", "score", "team"], ignore_case=True)
viz.fit(docs)
viz.show(outpath="word_correlation.png", clear_figure=True)
```

Prefer the class API when case handling matters. It exposes `ignore_case`
directly, supports file output cleanly, and avoids quick-method surprises in
older code paths.

## `PosTagVisualizer`

Use for counts of part-of-speech categories. The safest input is pre-tagged
nested tuples:

```python
tagged_docs = [
    [[("Apple", "NN"), ("grows", "VBZ"), ("fast", "RB"), (".", ".")]],
    [[("Clouds", "NNS"), ("drift", "VBP"), ("quietly", "RB"), (".", ".")]],
]
```

Input styles:

1. Parser-free: `fit(tagged_docs)` where each document contains sentences and
   each sentence contains `(token, tag)` tuples.
2. Raw text with NLTK: construct with `parser="nltk"`, `parser="nltk_word"`, or
   `parser="nltk_wordpunct"`; the tagset should be `"penn_treebank"`.
3. Raw text with SpaCy: construct with `parser="spacy"` or a named model such as
   `parser="spacy_en_core_web_sm"`; the tagset should usually be `"universal"`.

Parameters:

- `tagset="penn_treebank"` maps Penn Treebank tags such as `NN`, `VBZ`, and `RB`;
- `tagset="universal"` maps Universal Dependencies tags such as `NOUN`, `VERB`,
  and `ADV`;
- `frequency=True` sorts POS categories by frequency;
- `stack=True` requires `y` and plots per-class stacked counts.

Parser-free pattern:

```python
from yellowbrick.text import PosTagVisualizer

viz = PosTagVisualizer(frequency=True)
viz.fit(tagged_docs)
viz.show(outpath="postag.png", clear_figure=True)
```

Use parser-free input for safe tests and offline agents. Parser modes can fail
because the Python package is missing, NLTK data is missing, or the SpaCy model
has not been downloaded.

## Quick methods

Quick methods are available for notebook-style one-offs:

- `freqdist(features, X, y=None, ...)`
- `tsne(X, y=None, ...)`
- `umap(X, y=None, ...)`
- `dispersion(search_terms, corpus, y=None, ...)`
- `word_correlation(words, corpus, ...)`
- `postag(X, y=None, ...)`

For reusable agent guidance, saved files, axes reuse, or robust error handling,
prefer the class API. If a quick method is used and a file is required, pass
`show=False` when supported, then call `viz.show(outpath=..., clear_figure=True)`
on the returned visualizer.

## Safe headless output

For CI, servers, and agent environments without a display:

```python
import matplotlib
matplotlib.use("Agg")  # call before importing matplotlib.pyplot

from yellowbrick.text import FreqDistVisualizer
```

Then use the explicit lifecycle:

1. instantiate the visualizer;
2. call `fit(...)` or `fit_transform(...)` as appropriate;
3. call `show(outpath="name.png", clear_figure=True)`;
4. close figures if the script creates many plots.

The bundled `scripts/text_smoke.py` follows this rule and uses inline synthetic
text only. It does not load Yellowbrick datasets, run the downloader, require
UMAP/NLTK/SpaCy, or fetch parser data.
