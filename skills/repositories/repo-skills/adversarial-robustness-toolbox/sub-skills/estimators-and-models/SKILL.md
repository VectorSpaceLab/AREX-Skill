---
name: estimators-and-models
description: "Choose and configure ART estimator wrappers for sklearn, PyTorch,
  TensorFlow/Keras, black-box, boosted tree, GPy, and regression models."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Estimators and Models

Use this sub-skill when the task is to turn an existing model, prediction function, or regressor into an ART estimator that later attacks, defences, metrics, or certification tools can consume.

## Route here when

- The user has a scikit-learn, PyTorch, TensorFlowV2, Keras, XGBoost, LightGBM, CatBoost, GPy, or regression model and needs the right ART wrapper.
- The user needs to validate `predict`, `fit`, `loss_gradient`, `class_gradient`, `input_shape`, `nb_classes`, `channels_first`, `clip_values`, `preprocessing`, or label format before using an ART workflow.
- The user has only a callable `predict_fn` or a lookup table of existing predictions and needs a black-box classifier/regressor wrapper.
- The user hit a wrapper construction, shape, label, gradient, or backend error while preparing an ART estimator.

## Route elsewhere

- Attack selection, perturbation budgets, adversarial example generation, and preprocessing/adversarial-training defences: `../evasion-and-preprocessing/SKILL.md`.
- Poisoning, privacy inference, model extraction, backdoor, and detector workflows: `../poisoning-inference-extraction/SKILL.md`.
- Robustness metrics, evaluation objects, tree verification, and certification: `../evaluation-and-certification/SKILL.md`.
- Installation, optional dependency, and device/package readiness checks: `../setup-and-backends/SKILL.md`.
- Object detection, speech recognition, GAN, generation, tracking, and heavy experimental estimator families are outside this sub-skill's selected scope.

## Operating sequence

1. Identify the model family and whether the next workflow needs gradients, training, probability outputs, logits, tree access, or only predictions.
2. Choose the estimator wrapper and constructor contract from [references/api-reference.md](references/api-reference.md).
3. Build the wrapper with explicit `input_shape`, `nb_classes`, `clip_values`, `preprocessing`, label encoding, and `channels_first` choices.
4. Validate with the workflow checks in [references/workflows.md](references/workflows.md): prediction shape first, then `fit` if needed, then gradients only if the wrapper is gradient-enabled.
5. Use [references/troubleshooting.md](references/troubleshooting.md) for common shape, label, backend, and gradient errors.

## Bundled smoke scripts

Run these only as tiny no-download sanity checks for an installed ART environment:

- `scripts/smoke_sklearn_blackbox.py` validates scikit-learn and black-box classifier wrapping.
- `scripts/smoke_torch_classifier.py` validates a CPU PyTorch classifier wrapper, one short fit pass, and `loss_gradient`.
- `scripts/smoke_tensorflow_classifier.py` validates TensorFlowV2 prediction/fit contracts and a Keras classifier wrapper when TensorFlow/Keras are installed.
