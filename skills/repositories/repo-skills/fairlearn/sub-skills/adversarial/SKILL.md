---
name: adversarial
description: "Use Fairlearn adversarial fairness estimators with PyTorch or
  TensorFlow backends, callbacks, CUDA, and backend-specific troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Fairlearn adversarial

Use this sub-skill when the task asks for neural adversarial unfairness mitigation: `AdversarialFairnessClassifier`, `AdversarialFairnessRegressor`, PyTorch, TensorFlow, neural predictor/adversary models, callbacks, dynamic `alpha`, `warm_start`, CUDA, or backend import failures.

## Quick workflow

1. Confirm the selected backend is installed. PyTorch CPU and optional CUDA were verified for this skill; TensorFlow is documented but unverified here.
2. Prepare numeric 2D float features `X`, labels `y`, and row-aligned `sensitive_features`.
3. Define predictor and adversary models with compatible backend classes, or use Fairlearn's list model builder for simple experiments.
4. Construct the estimator with `backend`, model, optimizer, constraint, learning-rate, epoch, batch, callback, and CUDA settings.
5. Fit with `sensitive_features=...`.
6. Evaluate with `../assessment/`, watching for mode collapse, accuracy loss, or unchanged disparity.

## Read these references

- [`references/backends-and-training.md`](references/backends-and-training.md) for constructor fields, backend selection, model shapes, data preprocessing, callbacks, CUDA, and evaluation.
- [`references/troubleshooting.md`](references/troubleshooting.md) for missing backends, 2D input errors, invalid activations, BCE range failures, callbacks, and CUDA errors.
- [`scripts/smoke_torch_adversarial.py`](scripts/smoke_torch_adversarial.py) for a tiny explicit-PyTorch-model smoke check with optional CUDA.

## Core APIs to recognize

- `AdversarialFairnessClassifier(*, backend="auto", predictor_model=None, adversary_model=None, predictor_optimizer="Adam", adversary_optimizer="Adam", constraints="demographic_parity", learning_rate=0.001, alpha=1.0, epochs=1, batch_size=32, shuffle=False, progress_updates=None, skip_validation=False, callbacks=None, cuda=None, warm_start=False, random_state=None)`
- `AdversarialFairnessRegressor(...)` with the same constructor surface.
- Supported constraint strings in this family: `demographic_parity` and `equalized_odds`.

## Boundary rules

- This sub-skill owns neural adversarial mitigation only. Use `../reductions/` for sklearn-estimator constrained retraining and `../postprocessing/` for threshold adjustment.
- Use `../installation/` if backend installation is the main task.
- Use `../datasets/` for Adult/ACS data loading and `../assessment/` for final metric tables.
- Do not install TensorFlow or large GPU stacks unless the user explicitly chooses that backend.

## Operating rules

- `X` must be two-dimensional and numeric. One-hot encode categoricals and scale numeric columns before neural training.
- Labels and sensitive features are auto-preprocessed as binary, categorical, or continuous, but row alignment is still the caller's responsibility.
- Do not mix backends: PyTorch models/optimizers go with the PyTorch backend; Keras/TensorFlow models go with TensorFlow.
- In the inspected PyTorch engine, binary losses use `BCELoss`; custom binary predictor/adversary modules should output values in `[0, 1]`, usually with a final `torch.nn.Sigmoid()`.
- Adversarial training is sensitive to hyperparameters. Start tiny, validate often, and use callbacks for early stopping or learning-rate/alpha schedules.
- Use `cuda="cuda:0"` only after `torch.cuda.is_available()` is true; otherwise run CPU.

## Fast validation

CPU PyTorch smoke:

```bash
python sub-skills/adversarial/scripts/smoke_torch_adversarial.py
```

Optional CUDA smoke:

```bash
python sub-skills/adversarial/scripts/smoke_torch_adversarial.py --cuda cuda:0
```
