---
name: deep-and-optional-integrations
description: "Optional DeepActiveLearner, PyTorch/skorch MC-dropout, and
  Keras/TensorFlow integration guidance for modAL."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Deep and Optional Integrations

Use this sub-skill only when a modAL task explicitly involves optional deep-learning integrations: `DeepActiveLearner`, skorch-wrapped PyTorch estimators, Monte Carlo dropout query strategies from `modAL.dropout`, or legacy Keras/TensorFlow examples. These workflows are not part of the minimum classical scikit-learn active-learning path.

## Read and run map

- Read [references/deep-integrations.md](references/deep-integrations.md) when building or debugging `DeepActiveLearner`, skorch/PyTorch estimators, `warm_start` teaching, `num_epochs`/`batch_size`, or optional Keras/TensorFlow active-learning wrappers.
- Read [references/mc-dropout-reference.md](references/mc-dropout-reference.md) when using `mc_dropout_bald`, `mc_dropout_mean_st`, `mc_dropout_max_entropy`, `mc_dropout_max_variationRatios`, `get_predictions`, `set_dropout_mode`, dropout layer indexes, tensor/dict pools, or MC-dropout memory knobs.
- Read [references/troubleshooting.md](references/troubleshooting.md) when imports fail, skorch initialization or `partial_fit` behavior is unclear, NumPy arrays are passed to MC dropout, a dropout layer index raises `KeyError`, or a user expects CUDA/Keras behavior that was not selected.
- Run [scripts/dropout_inspection.py](scripts/dropout_inspection.py) to perform a deterministic CPU-only import and dropout-layer-index inspection against the installed package. Use `--help` first; the script does not train, download data, require credentials, or write files.

## Boundaries

- For ordinary `ActiveLearner`, `Committee`, `CommitteeRegressor`, bootstrapping, `only_new=True` with classical or Keras-like estimators, and learner setup not involving deep wrappers, use [../learners-and-committees/SKILL.md](../learners-and-committees/SKILL.md).
- For ordinary uncertainty, disagreement, ranked-batch, density, expected-error, multilabel, or custom query strategies that do not require MC dropout, use [../query-strategies/SKILL.md](../query-strategies/SKILL.md).
- Do not claim that Keras/TensorFlow, torchvision datasets, or CUDA are available unless the user's runtime has separately installed and smoke-tested them.

## Fast routing cues

| User signal | Next file |
|---|---|
| “DeepActiveLearner calls initialize”, “skorch NeuralNetClassifier”, “warm_start”, “partial_fit” | [references/deep-integrations.md](references/deep-integrations.md) |
| “MC dropout BALD/entropy/variation ratios”, “dropout_layer_indexes”, “logits_adaptor” | [references/mc-dropout-reference.md](references/mc-dropout-reference.md) |
| “RuntimeError only dict or tensors supported”, “bad dropout layer index”, “missing torch/skorch/Keras” | [references/troubleshooting.md](references/troubleshooting.md) |
| “Which dropout layer indexes are valid?” | [scripts/dropout_inspection.py](scripts/dropout_inspection.py) |
