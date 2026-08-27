---
name: tabular-modeling
description: "Use Libra for tabular regression, classification, clustering,
  recommendation, tuning, and model-inspection workflows on structured
  datasets."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Tabular Modeling with Libra

Load this sub-skill when the task centers on CSV/XLSX/JSON data, target-column guessing, classical machine learning, feed-forward ANNs, clustering, content recommendations, tuning, model inspection, or dashboard launch for structured datasets.

## What this sub-skill owns
- `client(...).regression_query_ann`, `classification_query_ann`, and `neural_network_query`
- `svm_query`, `nearest_neighbor_query`, `decision_tree_query`, and `xgboost_query`
- `kmeans_clustering_query`, `content_recommender_query`, and `recommend`
- `tune`, `predict`, `info`, `model`, `operators`, `accuracy`, `losses`, `target`, `plots`, `plot_names`, and `analyze`
- structured-data dashboard launch and EDA caveats

## Trigger phrases
Use this route when a user asks to:
- predict a numeric or categorical column from a table
- compare ANN, SVM, decision tree, KNN, XGBoost, or k-means on a spreadsheet-like dataset
- inspect `client.models`, `model()`, `info()`, `accuracy()`, `losses()`, `target()`, or `operators()` after a run
- tune a trained ANN or CNN model
- build recommendations from a movie/catalog-style table
- open the Streamlit dashboard for tabular data

## Bundled references
- `references/api-reference.md` for the tabular method map and return shapes
- `references/workflows.md` for end-to-end tabular recipes
- `references/data-formats.md` for accepted file types and column assumptions
- `references/troubleshooting.md` for target matching, model-key, and dashboard failures
- `references/compatibility.md` for the verified modern/legacy stack notes

## Bundled scripts
- `scripts/inspect_tabular_surface.py` prints the tabular client surface with signatures.
- `scripts/smoke_tabular_decision_tree.py` creates a synthetic CSV and runs a tiny CPU decision-tree smoke test.

## Operating notes
1. Keep the instruction phrase close to the target column name. Libra uses text parsing plus column similarity, so vague prompts are more likely to misroute.
2. `neural_network_query` auto-selects classification or regression from the target cardinality; use the specific ANN method when you already know the task family.
3. `tune()` defaults to `latest_model` when `model_to_tune` is omitted. Train the model you want to tune last or pass the key explicitly.
4. `content_recommender_query` and `recommend()` depend on a stable `indexer` column and matching feature names.
5. `analyze()` and `plots()` operate on stored model dictionaries; inspect `c.models[key].keys()` before assuming the same fields exist for every algorithm.
6. For dashboard and EDA work, keep the path and generated files isolated; the source dashboard helper uses a hardcoded source-layout path that is not portable.

## Cross-links
- Use the root skill for installation, compatibility shims, and global troubleshooting.
- Route text-heavy tasks, summarization, NER, and GPT-2 generation to `sub-skills/nlp-and-generation`.
- Route image-layout and export tasks to `sub-skills/vision-and-generative`.
