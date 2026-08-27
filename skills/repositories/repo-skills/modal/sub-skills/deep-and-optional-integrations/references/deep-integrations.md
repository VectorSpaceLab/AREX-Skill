# DeepActiveLearner and Optional Deep Integrations

This reference distills modAL-python 0.4.2 behavior for optional deep-learning surfaces. It is intentionally self-contained: the full PyTorch and Keras examples are evidence for the contracts below, not runtime dependencies for future agents.

## Capability boundary

| Surface | Status in this skill | Minimum assumption |
|---|---|---|
| `modAL.models.DeepActiveLearner` | Supported optional modAL API | Estimator has the skorch-like methods used below. |
| skorch `NeuralNetClassifier` wrapping a PyTorch `nn.Module` | Supported optional pattern | `torch` and `skorch` installed; CPU is enough for API inspection and small user-owned tests. |
| `modAL.dropout` MC-dropout strategies | Supported optional query strategies | `torch`, `skorch`, tensor/dict pools, initialized skorch estimator. |
| Keras/TensorFlow active-learning examples | Documentation-only optional pattern | User installs a compatible Keras/TensorFlow stack and supplies or explicitly downloads data. |
| CUDA/GPU execution | Not claimed | Only claim CUDA after the user runtime has an explicit CUDA smoke test. |

## `DeepActiveLearner` contract

`DeepActiveLearner(estimator, query_strategy=uncertainty_sampling, on_transformed=False, **fit_kwargs)` wraps a deep estimator in the same modAL learner shell, but it is not a drop-in copy of classical `ActiveLearner`.

Key differences from classical `ActiveLearner`:

- It does not keep `X_training`/`y_training` as learner state and does not provide the same initial-data/add-data flow.
- Its constructor calls `estimator.initialize()` after the base learner is created. A bare scikit-learn estimator usually does not implement this; skorch nets do.
- `fit(X, y, bootstrap=False, **fit_kwargs)` trains on the supplied data via the estimator's fit path and returns the learner.
- `teach(X, y, warm_start=True, bootstrap=False, **fit_kwargs)` uses `warm_start`, not `only_new`.
- `warm_start=True` calls `estimator.partial_fit(...)` on the passed batch, optionally with a bootstrap sample of that batch.
- `warm_start=False` resets through the fit path on the passed data. If you want to train from the full accumulated labeled set, you must pass that full set yourself.
- `num_epochs` proxies `estimator.max_epochs` and must be a positive integer.
- `batch_size` proxies `estimator.batch_size` and must be a positive integer.

### Choosing `warm_start` versus classical `only_new`

| Situation | Use |
|---|---|
| Classical `ActiveLearner` stores the growing training set and the estimator should be refit on all known labels. | Use the classical learner default `teach(X, y)` in the learner/committee sub-skill. |
| Classical or Keras-like estimator's fit method continues training instead of resetting from scratch. | Use classical `ActiveLearner.teach(..., only_new=True)` so only the newly labeled batch is passed to the estimator. |
| `DeepActiveLearner` with a skorch net should continue training from current parameters. | Use `teach(..., warm_start=True)`, which calls `partial_fit` on the provided data. |
| `DeepActiveLearner` should reset model parameters and train from a chosen dataset. | Use `teach(..., warm_start=False)` or `fit(...)`, and pass the dataset you want to train on. |

## skorch/PyTorch estimator expectations

A skorch `NeuralNetClassifier` is the expected estimator shape for PyTorch classifiers because it exposes scikit-learn-style methods plus skorch-specific deep-learning hooks.

Expected attributes/methods used by modAL deep and dropout paths:

| Estimator member | Why modAL needs it |
|---|---|
| `initialize()` | Called by `DeepActiveLearner.__init__`; creates `module_` without training. |
| `fit(X, y, **kwargs)` | Used by `DeepActiveLearner.fit` and by `teach(..., warm_start=False)`. |
| `partial_fit(X, y, **kwargs)` | Used by `teach(..., warm_start=True)`. |
| `predict`, `predict_proba`, `score` | Used by learner prediction/scoring or non-dropout query strategies where applicable. |
| `infer(samples)` | Used by `modAL.dropout.get_predictions` so dropout mode is not reset by `predict`/`predict_proba`. |
| `module_` | Initialized PyTorch module inspected by `set_dropout_mode`. |
| `max_epochs` and `batch_size` | Proxied by `DeepActiveLearner.num_epochs` and `.batch_size`. |

A compact pattern is:

```python
import torch
from torch import nn
from skorch import NeuralNetClassifier
from modAL.models import DeepActiveLearner
from modAL.dropout import mc_dropout_bald

class TorchModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(4, 8),
            nn.ReLU(),
            nn.Dropout(0.25),
            nn.Linear(8, 2),
        )

    def forward(self, x):
        return self.net(x)

net = NeuralNetClassifier(
    TorchModel,
    criterion=torch.nn.CrossEntropyLoss,
    optimizer=torch.optim.Adam,
    max_epochs=1,
    batch_size=16,
    train_split=None,
    verbose=0,
    device="cpu",  # use another device only after separate smoke verification
)

learner = DeepActiveLearner(estimator=net, query_strategy=mc_dropout_bald)
learner.num_epochs = 2
learner.batch_size = 8
```

This snippet constructs an initialized learner. It does not imply that a user's data, loss, labels, or device are correct; validate those in the user's runtime.

## Data and label notes for PyTorch/skorch

- MC dropout pools must be PyTorch tensors or dictionaries of tensors; convert NumPy arrays before calling dropout query strategies.
- For `torch.nn.CrossEntropyLoss`, labels are usually integer class ids with a long/integer dtype, not one-hot arrays.
- Keep all tensors for a single query call on the same device as the estimator. This skill only verifies CPU-oriented API behavior; it does not validate CUDA placement.
- If you use dictionary inputs, every tensor value should have the same first dimension because `get_predictions` splits each value by `sample_per_forward_pass`.

## Keras/TensorFlow examples are optional and legacy-sensitive

The modAL examples show Keras classifiers through scikit-learn wrappers and MNIST data. Treat them as optional patterns, not as an installed or verified minimum capability:

- Keras/TensorFlow are not part of the minimum installed-package facts for this skill.
- Example MNIST helpers often download or load datasets; do not trigger downloads unless the user explicitly asks and the runtime policy allows it.
- Wrapper import paths changed across Keras/TensorFlow versions. If a user asks for Keras, first identify the installed wrapper API in that environment.
- Keras-style estimators commonly continue training from previous weights. With classical `ActiveLearner`, `teach(..., only_new=True)` is the documented way to pass only the new labeled batch instead of rebuilding an accumulated training set. This is distinct from `DeepActiveLearner.teach(..., warm_start=...)`.
- MC dropout in this sub-skill is the PyTorch/skorch `modAL.dropout` path, not the legacy Keras backend-function example.

## Evidence basis, not runtime dependency

The contracts above were distilled from the package implementation, optional deep/dropout unit-test sections, PyTorch/skorch examples, Keras/TensorFlow examples, API-signature inspection, and CPU import smoke evidence. Future agents should use this bundled reference and script rather than opening or running the original evidence files.
