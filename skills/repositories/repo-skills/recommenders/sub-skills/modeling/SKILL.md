---
name: modeling
description: "Choose, instantiate, fit, score, and recommend with Microsoft
  Recommenders model families across verified CPU and optional Spark, GPU, and
  experimental backends."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Modeling

Use this sub-skill when a user asks which Recommenders model family to use, how to instantiate and fit a model, how to produce predictions or top-k recommendations, or how optional Spark/deep-learning/content-based/experimental model paths differ.

## Backend truth for this skill

- Verified in the base CPU scope: package import, SAR, TF-IDF utilities, Cornac prediction helpers, and LightGBM helper imports/signatures.
- Optional and not verified in this CPU scope: Spark ALS/SARplus/Spark LightGBM, TensorFlow/PyTorch deep-learning models, NewsRec/DeepRec notebooks, cloud workflows, and experimental packages such as Surprise, LightFM, Vowpal Wabbit, xLearn, GeoIMC, and RLRMC dependencies.
- Do not present a visible GPU, Spark, or cloud host as sufficient. The matching optional Python packages, system runtime, data files, and credentials must also be present.

## Start here

- For algorithm choice across SAR, TF-IDF, Cornac, LightGBM, Spark ALS, NewsRec, NCF, Wide&Deep, VAE, RBM, SASRec/SSEPT, and experimental families, read [model-overview.md](references/model-overview.md).
- For constructors, methods, dataframe contracts, and return columns, read [api-reference.md](references/api-reference.md).
- For runnable recipes, use [workflows.md](references/workflows.md):
  - CPU SAR collaborative filtering with `SAR.fit`, `SAR.predict`, and `SAR.recommend_k_items`.
  - CPU TF-IDF content-based recommendation with `TfidfRecommender`.
  - Cornac scoring/ranking helpers.
  - LightGBM feature encoding helper usage.
  - Optional Spark, deep-learning, and news/sequential model preparation checklists.
- For symptoms and fixes, read [troubleshooting.md](references/troubleshooting.md).
- To prove a local install can run the two lightweight CPU model paths, run:

```bash
python sub-skills/modeling/scripts/sar_tiny_smoke.py --top-k 2
python sub-skills/modeling/scripts/tfidf_tiny_smoke.py --top-k 1
```

Run the commands from the root of this generated skill tree, or adapt the script paths to the location where the skill was installed.

## Route elsewhere

- Data loading, schema validation, de-duplication before training, filtering, negative sampling, sparse matrix conversion, and train/test splitting belong in [data-preparation](../data-preparation/SKILL.md).
- Metric calculation after predictions or top-k output belongs in [evaluation](../evaluation/SKILL.md).
- Hyperparameter sweeps, benchmark harnesses, NNI/AzureML/Databricks/AKS, service sizing, and long-running operationalization belong in [operations-and-tuning](../operations-and-tuning/SKILL.md).

## Working rules

1. Identify the available data signal first: interaction ratings/clicks, item text/content, tabular ad features, sequence/session logs, news/MIND files, or Spark-scale data.
2. Identify the permitted backend: base CPU only, Spark, GPU/deep-learning, experimental native packages, or cloud services.
3. Pick the smallest verified path that matches the data. Prefer SAR for a lightweight pandas interaction baseline and TF-IDF for text-only item similarity before escalating to optional models.
4. Keep `userID`, `itemID`, `rating`, `timestamp`, and `prediction` column names unless the user explicitly uses custom names and passes matching `col_*` parameters.
5. When producing recommendations for evaluation, ensure top-k output has one row per `(userID, itemID)` candidate and a `prediction` score, then route metrics to the evaluation sub-skill.
