---
name: model-training
description: "Train and evaluate DeepChem models; choose metrics, model
  families, hyperparameter search, save/restore, and optional backend-gated
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# DeepChem Model Training

Use this sub-skill when the task is about constructing `deepchem.models` objects, calling `fit()`, `evaluate()`, `predict()`, selecting `deepchem.metrics.Metric`, running `deepchem.hyper` searches, saving/restoring models, or planning model families and optional backends.

Route adjacent work elsewhere:
- Data loading, MoleculeNet loaders, dataset transforms, and splits: `../data-and-molnet/`.
- Molecular featurizers and feature/model compatibility: `../featurization/`.
- Docking or structure scoring workflows: `../docking-and-structure/`.

Start with a base-dependency baseline unless the user explicitly requests neural models:
1. Confirm the dataset is already a DeepChem `Dataset` with compatible `X`, `y`, and `w` shapes.
2. Pick a model family from `references/model-families.md`; prefer `SklearnModel` for fast baselines in minimal installs.
3. Pick metrics from `references/api-reference.md`; match classification metrics to probability/class-label shape requirements.
4. Fit, evaluate, predict, and persist using `references/training-workflows.md`.
5. If a backend warning appears or an import fails, consult `references/troubleshooting.md` before installing extras.

For a deterministic smoke test that avoids TensorFlow/PyTorch/JAX, run:

```bash
python sub-skills/model-training/scripts/train_tiny_sklearn_model.py
```

Expected output includes a JSON object with `score_key`, `prediction_shape`, and `restored_prediction_shape`.
