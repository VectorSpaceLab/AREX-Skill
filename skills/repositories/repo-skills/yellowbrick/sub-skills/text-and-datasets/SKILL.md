---
name: text-and-datasets
description: "Use Yellowbrick dataset loaders, cache controls, and text
  visualizers for tabular data, corpora, and text embeddings."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Yellowbrick Text and Datasets

Use this sub-skill when the task is about Yellowbrick dataset loading, dataset
cache/download behavior, the `load_*` helpers, the hobbies corpus, or
text-specific visualizers. It covers `FreqDistVisualizer`, `TSNEVisualizer`,
`UMAPVisualizer`, `DispersionPlot`, `WordCorrelationPlot`, and
`PosTagVisualizer`.

For package-wide Yellowbrick lifecycle, axes reuse, style, and headless saving,
read [shared visualizer patterns](../../references/visualizer-patterns.md). For
broad install, Matplotlib backend/font, and scikit-learn compatibility failures,
read the root [troubleshooting reference](../../references/troubleshooting.md)
before applying text/dataset-specific fixes.

## Use this sub-skill for

- Choosing among Yellowbrick example datasets and matching them to regression,
  classification, clustering, time-series-style, or text-analysis tasks.
- Loading tabular datasets with `load_bikeshare()`, `load_concrete()`,
  `load_credit()`, `load_energy()`, `load_game()`, `load_mushroom()`,
  `load_occupancy()`, `load_spam()`, `load_walking()`, or `load_nfl()`.
- Loading the hobbies corpus with `load_hobbies()` and using `Corpus.data`,
  `Corpus.target`, `Corpus.labels`, or `Corpus.files`.
- Deciding between default `X, y` returns, `return_dataset=True`, `to_numpy()`,
  `to_pandas()`, and `to_dataframe()`.
- Controlling or inspecting the dataset cache with `data_home`,
  `YELLOWBRICK_DATA`, and the no-download cache inspector.
- Using text visualizers after the corpus is already vectorized, tokenized, or
  part-of-speech tagged.
- Explaining optional extras: `pandas` for DataFrame returns, `umap-learn` for
  `UMAPVisualizer`, and `nltk`/`spacy` plus data/models for parser-based POS
  tagging.

## Route elsewhere when

- The user has already loaded data and now wants classifier score plots such as
  reports, confusion matrices, ROC/PR curves, or threshold tuning: route to
  [classifier visualizers](../classifier-visualizers/SKILL.md).
- The user wants residuals, prediction error, Cook's distance, or alpha
  selection: route to [regressor visualizers](../regressor-visualizers/SKILL.md).
- The user wants feature ranking, PCA/manifold feature projections, class
  balance, binning, or feature-target correlation: route to
  [feature-target visualizers](../feature-target-visualizers/SKILL.md).
- The user wants clustering diagnostics, validation/learning curves, CV scores,
  RFECV, feature importances, or dropping curves: route to
  [cluster-model-selection](../cluster-model-selection/SKILL.md).
- The user asks about contrib wrappers, decision boundaries, missing-value
  contrib plots, or statsmodels adapters: route to
  [contrib-and-extensions](../contrib-and-extensions/SKILL.md).

## Required read and run map

| Need | Read or run | When to use it |
|---|---|---|
| Dataset names, task fit, `load_*`, return types, `Dataset`/`Corpus`, cache rules, downloader flags, and offline behavior | [datasets reference](references/datasets.md) | Read before giving loader code, cache advice, or no-network guidance. |
| Text visualizer selection, exact input formats, optional extras, and safe file output | [text visualizers reference](references/text-visualizers.md) | Read before using any `yellowbrick.text` visualizer or diagnosing text input-shape errors. |
| Dataset cache/download/signature/offline failures, missing optional dependencies, wrong class names, parser/tagset errors, and display/font warnings | [text/dataset troubleshooting](references/troubleshooting.md) | Read after any failure symptom or before advising a risky cleanup/download action. |
| Common Yellowbrick `fit`/`score`/`transform`/`show(outpath=...)`, Matplotlib `Agg`, axes, and style rules | [shared visualizer patterns](../../references/visualizer-patterns.md) | Read before writing report-quality code or headless automation. |
| Broad installation, backend, font, or scikit-learn compatibility issues | [root troubleshooting](../../references/troubleshooting.md) | Read when the problem is not specific to text or datasets. |
| No-download cache inspection | [check_dataset_cache.py](scripts/check_dataset_cache.py) | Run when the user is offline, wants to know what is already cached, or needs signature/cache state without downloads or deletes. |
| Safe text plotting smoke | [text_smoke.py](scripts/text_smoke.py) | Run to confirm `yellowbrick.text` can render inline synthetic text plots with Matplotlib `Agg`; it uses no external data and no optional downloads. |

Example safe runs from an environment where Yellowbrick is importable:

```bash
python skills/disco/yellowbrick/sub-skills/text-and-datasets/scripts/check_dataset_cache.py --dataset hobbies
python skills/disco/yellowbrick/sub-skills/text-and-datasets/scripts/text_smoke.py --outdir /tmp/yellowbrick-text-smoke
```

## Dataset quick map

| Loader | Object | Shape or size | Best fit | Notes |
|---|---|---:|---|---|
| `load_bikeshare()` | `Dataset` | `X=(17379, 12)` | regression | Bike sharing demand examples. |
| `load_concrete()` | `Dataset` | `X=(1030, 8)` | regression | Small, numeric, good for regressor demos. |
| `load_credit()` | `Dataset` | `X=(30000, 23)` | binary classification / clustering | Credit default data; can be large for quick CV examples. |
| `load_energy()` | `Dataset` | `X=(768, 8)` | regression / multi-output source data | Default `y` is the documented primary target. |
| `load_game()` | `Dataset` | `X=(67557, 42)` | multiclass classification | Categorical features usually need encoding before sklearn estimators. |
| `load_hobbies()` | `Corpus` | `448` docs, `5` labels | text analysis / classification / clustering | Returns a `Corpus`, not `X, y`; use `corpus.data` and `corpus.target`. |
| `load_mushroom()` | `Dataset` | `X=(8123, 3)` | binary classification / clustering | Categorical mushroom attributes need preprocessing for many estimators. |
| `load_occupancy()` | `Dataset` | `X=(20560, 5)` | binary classification | Multivariate time-series-style occupancy data. |
| `load_spam()` | `Dataset` | `X=(4600, 57)` | binary classification / threshold analysis | Useful for threshold and imbalance demonstrations. |
| `load_walking()` | `Dataset` | `X=(149332, 4)` | clustering / time-series-style diagnostics | Large row count; sample for quick visual checks. |
| `load_nfl()` | `Dataset` | `X=(494, 23)` | clustering | Football receiver clustering examples. |

## Text visualizer quick map

| Visualizer | Input required | Best fit | Constraints |
|---|---|---|---|
| `FreqDistVisualizer` | Count-vectorized document matrix plus feature names | Top-token counts in a corpus or by class | Use `FreqDistVisualizer`, not `FrequencyVisualizer`, in public guidance. |
| `TSNEVisualizer` | Numeric vectorized corpus matrix | 2D document embedding and class/cluster separation | t-SNE is expensive; vectorize first and lower `perplexity` for tiny samples. |
| `UMAPVisualizer` | Numeric vectorized corpus matrix | 2D document embedding with UMAP | Requires optional `umap-learn`; use `metric="cosine"` for many text vectors. |
| `DispersionPlot` | Tokenized documents: list/generator of token lists | Lexical dispersion of known terms across documents | Search terms must survive tokenization and casing. |
| `WordCorrelationPlot` | Raw text documents: list/generator of strings | Word or phrase co-occurrence heatmap | Every requested word/phrase must appear in the corpus. |
| `PosTagVisualizer` | Pre-tagged nested docs or raw text with parser | POS tag distributions | Prefer pre-tagged tuples for no-optional-dependency smoke checks. |

## Canonical dataset pattern

```python
from yellowbrick.datasets import load_concrete, load_hobbies

# Tabular data: pandas DataFrame/Series if pandas is installed, otherwise numpy arrays.
X, y = load_concrete()

# Request the object when you need metadata or explicit return control.
dataset = load_concrete(return_dataset=True)
X_np, y_np = dataset.to_numpy()

# Text corpus loaders return Corpus objects, not X/y directly.
corpus = load_hobbies()
docs = corpus.data
target = corpus.target
labels = corpus.labels
```

## Canonical text pattern

```python
import matplotlib
matplotlib.use("Agg")  # set before pyplot in headless sessions

from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from yellowbrick.text import FreqDistVisualizer, TSNEVisualizer

count_vectorizer = CountVectorizer()
X_counts = count_vectorizer.fit_transform(docs)
features = count_vectorizer.get_feature_names_out()

freq = FreqDistVisualizer(features=features)
freq.fit(X_counts, target)
freq.show(outpath="freqdist.png", clear_figure=True)

X_tfidf = TfidfVectorizer().fit_transform(docs)
tsne = TSNEVisualizer(random_state=13, perplexity=10)
tsne.fit(X_tfidf, target)
tsne.show(outpath="tsne.png", clear_figure=True)
```

## Safety checklist

- Do not call a loader in offline mode unless its dataset directory already
  exists in the selected cache; missing data triggers Yellowbrick's downloader.
- Use the cache inspector before telling an offline user that a loader will work.
- Use `return_dataset=True` only on tabular loaders; `load_hobbies()` already
  returns a `Corpus` object.
- Confirm whether `pandas` is installed before promising DataFrame/Series
  returns; numpy arrays are the normal fallback.
- Confirm text input state: raw strings for vectorizers and `WordCorrelationPlot`,
  token lists for `DispersionPlot`, numeric vectors for TSNE/UMAP, and nested
  `(token, tag)` tuples for parser-free POS visualization.
- Confirm optional dependencies before recommending `UMAPVisualizer` or raw-text
  parser mode for `PosTagVisualizer`.
- Save figures with a non-interactive backend and class visualizer API when the
  output must be a file.
