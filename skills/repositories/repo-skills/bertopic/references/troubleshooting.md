# BERTopic troubleshooting

## Purpose

Use this page for cross-cutting BERTopic problems that do not belong to one narrow workflow yet. If the issue is specific to embeddings, vectorizers, labels, visualization, or serialization, route to that sub-skill after checking this page.

## First recovery step

Run the bundled environment check:

```bash
python scripts/check_env.py
```

Add `--smoke` when you want a tiny no-download model fit that uses synthetic documents and precomputed embeddings.

## Import or base dependency failures

### `ModuleNotFoundError: No module named 'bertopic'`

- Install the package into the environment you are actually using.
- Verify the basic import before debugging a downstream workflow.
- If editable install was used, make sure the environment still points at the intended checkout.

### Missing scientific stack imports

If BERTopic itself imports but the environment later fails on NumPy, pandas, SciPy, scikit-learn, joblib, tqdm, hdbscan, or umap-learn, the environment is incomplete.

- Reinstall the base package dependencies.
- Rerun `python scripts/check_env.py`.
- For tiny smoke checks, prefer synthetic embeddings instead of external datasets or models.

## Optional dependency placeholders

`bertopic.backend` and `bertopic.representation` intentionally expose `NotInstalled` placeholders for optional backends when an extra is missing.

That is expected for optional packages such as:

- `openai`
- `cohere`
- `litellm`
- `langchain`
- `llama-cpp-python`
- `spacy`
- `fastembed`
- `model2vec`
- `gensim`
- `flair`
- `datamapplot`
- `safetensors`
- image-related extras for multimodal workflows

If a placeholder appears, install only the extra or package needed for the workflow you actually want.

## Unexpected downloads

BERTopic defaults often use sentence-transformers or other backend choices that may download models the first time they are used.

Symptoms:

- a warning about Hugging Face or unauthenticated requests
- a long first fit on a tiny corpus
- a backend path that tries to reach the network even though you wanted offline operation

Recovery:

- pass precomputed embeddings when possible
- use a tiny local backend or a deterministic custom backend for smoke checks
- avoid string model ids when you need a hard no-download path

## Plotting failures

Visualization methods can fail for reasons that are not model-train problems.

- `plotly` missing or broken affects the main topic map, document views, hierarchy views, heatmaps, bar charts, and distribution plots.
- `umap-learn` missing affects `visualize_topics()` and `visualize_hierarchy()` and can affect document views when `reduced_embeddings` are not supplied.
- `datamapplot` is required only for the DataMapPlot document view.

Recovery:

- install the missing optional package only if you need that plot family;
- for document views, pass `reduced_embeddings` to avoid the internal UMAP path;
- use the non-UMAP plots first when you only need a quick inspection.

## Serialization failures

If save/load fails:

- verify whether the model was saved as `pickle`, `pytorch`, or `safetensors`
- install `torch` or `safetensors` only if the chosen format needs them
- prefer `pickle` only for trusted same-environment round trips
- prefer lightweight directories for small, shareable artifacts
- remember that lightweight formats do not preserve the original clustering and reduction objects

If a loaded lightweight model cannot transform new documents, pass `embeddings=` or inject an explicit embedding backend at load time.

## Model-shape or alignment issues

A lot of BERTopic errors come from inputs that are no longer aligned.

Common symptoms:

- document count does not match timestamp count or class count
- document views complain about embedding or reduced-embedding shapes
- `visualize_distribution()` was given a full matrix instead of a single row
- `hierarchical_topics()` was called with a corpus that no longer matches the fitted model

Recovery:

- keep `docs`, `embeddings`, `timestamps`, `classes`, and `topics` aligned;
- use one document row at a time for distribution plots;
- use the original fitted corpus when building hierarchy tables.

## When to stop and switch workflow

- If the issue is really about a backend model, switch to `embeddings-backends`.
- If the issue is about topic words or vocabulary, switch to `vectorizers-ctfidf`.
- If the issue is about labels or chained topic text, switch to `representations-labeling`.
- If the issue is about a fitted model plot or table, switch to `analysis-visualization`.
- If the issue is about persistence, switch to `serialization`.
