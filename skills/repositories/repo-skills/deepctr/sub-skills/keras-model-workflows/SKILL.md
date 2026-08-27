---
name: keras-model-workflows
description: "Use this DeepCTR sub-skill for Keras-style CTR and recommender
  models, model selection, compile-fit-predict workflows, save/load, and tiny
  DeepFM smoke tests."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Keras Model Workflows

Use this sub-skill for DeepCTR's primary `tf.keras.Model`-style API: choose a CTR/recommender model, build Keras feature columns, compile, fit, evaluate, predict, save/load, and smoke-test an installation.

## When to use this sub-skill

- The user asks for DeepFM, WDL, DCN, xDeepFM, AutoInt, FiBiNET, AFM, NFM, PNN, FGCNN, EDCN, or another single-output DeepCTR model.
- The task is binary CTR classification or scalar regression with tabular sparse/dense features.
- The user needs Keras `compile`, `fit`, `predict`, `evaluate`, `save_model`, `load_model`, custom objects, callbacks, optimizers, or embedding extraction.
- The user wants a safe DeepCTR smoke test that does not depend on example files.

## Route map

- Read [references/model-catalog.md](references/model-catalog.md) to choose a model family and understand the supported Keras model constructors.
- Read [references/workflows.md](references/workflows.md) for end-to-end preprocessing, model creation, fitting, prediction, evaluation, save/load, embedding extraction, and AFM attention recipes.
- Read [references/api-reference.md](references/api-reference.md) for verified constructor signatures and Keras method contracts.
- Read [references/troubleshooting.md](references/troubleshooting.md) for TensorFlow compatibility, missing dependencies, input shape, string hashing, save/load, and optional GPU issues.
- Run [scripts/keras_tiny_ctr_smoke.py](scripts/keras_tiny_ctr_smoke.py) to verify a public DeepCTR installation using synthetic data.

## Minimal Keras CTR workflow

```python
from deepctr.feature_column import DenseFeat, SparseFeat, get_feature_names
from deepctr.models import DeepFM

feature_columns = [
    SparseFeat("user_id", vocabulary_size=10000, embedding_dim=8),
    SparseFeat("item_id", vocabulary_size=50000, embedding_dim=8),
    DenseFeat("score", 1),
]
feature_names = get_feature_names(feature_columns)
model_input = {name: frame[name].values for name in feature_names}
model = DeepFM(feature_columns, feature_columns, task="binary")
model.compile("adam", "binary_crossentropy", metrics=["binary_crossentropy"])
model.fit(model_input, labels, batch_size=256, epochs=3, validation_split=0.2)
pred = model.predict(model_input, batch_size=256)
```

For feature-column construction details, route to [../data-and-feature-columns/SKILL.md](../data-and-feature-columns/SKILL.md).

## Smoke test

From the generated skill root, run:

```bash
python sub-skills/keras-model-workflows/scripts/keras_tiny_ctr_smoke.py --task binary --save-load --json
```

A successful run builds a tiny `DeepFM`, trains one epoch on synthetic data, predicts a `(n, 1)` output, and optionally verifies H5 save/load with DeepCTR `custom_objects`.

## Boundaries

- Use [../sequence-models/SKILL.md](../sequence-models/SKILL.md) for DIN, DIEN, DSIN, and BST history/session-specific conventions.
- Use [../multitask-models/SKILL.md](../multitask-models/SKILL.md) for SharedBottom, ESMM, MMOE, and PLE multi-output models.
- Use [../estimator-workflows/SKILL.md](../estimator-workflows/SKILL.md) for legacy `tf.estimator` workflows.
- Do not depend on original example scripts or sample files at runtime; use the bundled smoke script and references here.
