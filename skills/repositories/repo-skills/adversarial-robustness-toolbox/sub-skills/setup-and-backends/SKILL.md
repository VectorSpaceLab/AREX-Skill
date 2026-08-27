---
name: setup-and-backends
description: "Install, import, optional dependency, backend-selection, and
  environment diagnostics guidance for ART users."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# setup-and-backends

Use this sub-skill before any ART workflow when the user needs to install ART, verify imports, choose CPU/GPU packages, or resolve optional-backend failures.

## Use this for

- Installing the public distribution `adversarial-robustness-toolbox` and importing the Python module `art`.
- Choosing a minimal CPU-capable stack or adding optional backend families for PyTorch, TensorFlow/Keras, boosted trees, GPy, image helpers, or TensorBoard logging.
- Running a safe install/import diagnostic with [`scripts/inspect_art_install.py`](scripts/inspect_art_install.py).
- Diagnosing ImportError, missing optional dependencies, TensorFlow/NumPy/ml-dtypes conflicts, CPU-only wheels, no-CUDA hosts, and version mismatches.

## Start here

1. Read [`references/install-and-backends.md`](references/install-and-backends.md) to select the package group and minimal import check.
2. Run the bundled diagnostic when the environment is already installed:

   ```bash
   python scripts/inspect_art_install.py --json
   ```

3. If the user is on CPU and uses a PyTorch ART estimator or PyTorch preprocessor, explicitly pass `device_type="cpu"`. ART's `PyTorchClassifier` constructor defaults `device_type="gpu"`; being explicit prevents confusing CPU-only or no-CUDA diagnoses.
4. If imports fail, use [`references/troubleshooting.md`](references/troubleshooting.md) before changing framework versions.

## Route away from this sub-skill

- Estimator/model wrapper construction, `clip_values`, label shapes, gradient availability, and black-box vs white-box wrapper choice -> sibling `estimators-and-models`.
- Evasion attacks, preprocessing defences, adversarial training, and attack budgets -> sibling `evasion-and-preprocessing`.
- Poisoning, backdoor, inference/privacy, extraction, and detectors -> sibling `poisoning-inference-extraction`.
- Metrics, evaluation objects, SummaryWriter workflow details, certification, and verification -> sibling `evaluation-and-certification`.

## Guardrails

- Do not run the original repository's tests, examples, notebooks, or maintainer scripts for setup diagnosis. Use the bundled diagnostic and tiny user-owned checks only.
- Do not install broad `all` extras by default. Start with the core package plus only the backend family required by the user's selected workflow.
- Treat GPU as optional acceleration unless the user's workflow explicitly requires GPU-only dependencies. A CPU-capable ART workflow should not require CUDA packages.
- Keep install commands and troubleshooting self-contained; do not depend on a source checkout being available.
