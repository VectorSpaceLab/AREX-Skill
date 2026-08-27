---
name: bertopic
description: "Route BERTopic topic modeling, embedding, vectorizer, labeling,
  visualization, and serialization workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# BERTopic

BERTopic turns documents, precomputed embeddings, or multimodal inputs into topic models you can fit, inspect, label, visualize, and save.

## Install

```bash
python -m pip install bertopic
```

Use only the optional packages that the chosen workflow needs. For example, multimodal image workflows use `bertopic[vision]`, while label and backend workflows may require `openai`, `litellm`, `langchain`, `llama-cpp-python`, `spacy`, `fastembed`, `model2vec`, `gensim`, `flair`, `safetensors`, or `datamapplot`.

If you are working from a local checkout to inspect the package, editable install is also fine:

```bash
python -m pip install -e .
```

## Quick check

Run the bundled environment check first:

```bash
python scripts/check_env.py
```

Add `--smoke` for a tiny no-download fit/load-style smoke that uses synthetic documents and precomputed embeddings.

## Route map

- `sub-skills/topic-modeling/` — build BERTopic models, fit and transform data, run `partial_fit`, mutate topics, and combine or reduce fitted models.
- `sub-skills/embeddings-backends/` — choose embedding backends, build custom embedders, inventory optional backend imports, and handle precomputed or multimodal embeddings.
- `sub-skills/vectorizers-ctfidf/` — tune `ClassTfidfTransformer`, `CountVectorizer`, and `OnlineCountVectorizer` for better topic words.
- `sub-skills/representations-labeling/` — rerank keywords, generate labels, chain representation models, and manage multi-aspect topic outputs.
- `sub-skills/analysis-visualization/` — inspect fitted models with topic tables, hierarchies, distributions, and plots.
- `sub-skills/serialization/` — save, reload, and share fitted models locally or through the Hugging Face Hub.

When a task spans more than one route, start with the earliest route in the pipeline and move forward: embeddings → model building → topic-word tuning → labels → analysis → serialization.

## Read next

- `references/workflows.md` for the fastest route through common BERTopic tasks.
- `references/troubleshooting.md` when imports, optional dependencies, plotting, or save/load fail.
- `references/repo-provenance.md` before deciding whether this skill matches the current checkout.
