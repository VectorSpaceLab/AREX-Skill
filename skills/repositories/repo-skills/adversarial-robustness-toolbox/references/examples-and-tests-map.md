# Bundled helper and native-candidate map

## Purpose

Use this reference to find the self-contained helpers bundled with this skill and to understand which upstream example/test categories informed them. Do not run original repository examples or tests as runtime instructions from this skill; they were used as construction evidence and later verification candidates only.

## Bundled helper map

| Bundled helper | Owner | What it proves | Safe default |
|---|---|---|---|
| `scripts/inspect_art_install.py` | root/setup | ART import plus selected optional backend versions | Import-only diagnostic, optional `--json` output. |
| `sub-skills/setup-and-backends/scripts/inspect_art_install.py` | setup-and-backends | Same diagnostic with richer setup context | Import-only diagnostic, no downloads. |
| `sub-skills/estimators-and-models/scripts/smoke_sklearn_blackbox.py` | estimators-and-models | sklearn wrapper and black-box classifier predictions | Tiny iris fixture; no downloads. |
| `sub-skills/estimators-and-models/scripts/smoke_torch_classifier.py` | estimators-and-models | CPU `PyTorchClassifier`, short fit, `loss_gradient` shape | Synthetic data; explicit CPU device. |
| `sub-skills/estimators-and-models/scripts/smoke_tensorflow_classifier.py` | estimators-and-models | TensorFlowV2/Keras wrapper prediction and optional fit | Synthetic data; use `--skip-fit` for fastest check. |
| `sub-skills/evasion-and-preprocessing/scripts/smoke_evasion_pytorch.py` | evasion-and-preprocessing | FGM/PGD generation against a tiny CPU PyTorch estimator | Synthetic image tensor; bounded perturbation check. |
| `sub-skills/evasion-and-preprocessing/scripts/smoke_preprocessor_numpy.py` | evasion-and-preprocessing | NumPy standardisation and spatial smoothing preprocessors | Synthetic image tensor; channel-order option. |
| `sub-skills/poisoning-inference-extraction/scripts/inspect_privacy_poisoning_apis.py` | poisoning-inference-extraction | Import/signature availability for poisoning, privacy, extraction, and mitigation APIs | Import-only; no training or queries. |
| `sub-skills/evaluation-and-certification/scripts/smoke_metrics_tree.py` | evaluation-and-certification | Robustness metrics, privacy metrics, evaluation object imports, and tree/certification signature checks | Synthetic fixtures; use `--tree-mode signature` if tree verification is brittle. |
| `sub-skills/evaluation-and-certification/scripts/smoke_pytorch_adv_accuracy.py` | evaluation-and-certification | Integrated CPU PyTorch wrapper, bounded FGM/PGD adversarial example, and adversarial accuracy smoke | Synthetic fixture; no downloads or training. |

## Native evidence categories distilled into the skill

| Evidence category | Runtime replacement |
|---|---|
| Get-started estimator examples for sklearn, PyTorch, TensorFlow/Keras, XGBoost, and LightGBM | Estimator workflows reference plus no-download sklearn/PyTorch/TensorFlow smoke scripts. |
| MNIST FGSM and adversarial-training examples | Evasion/preprocessing references plus no-download PyTorch evasion smoke. |
| Poisoning and poison-detection examples | Poisoning/privacy/extraction references and import/signature helper. |
| Attack unit tests for PGD, HopSkipJump, patch, SimBA, Pixel/Threshold, DecisionTree, feature adversaries, and universal perturbation | Attack chooser, troubleshooting guidance, and later native verification candidates. |
| Estimator unit tests for black-box, sklearn, PyTorch, TensorFlow, boosted trees, GPy, and regression wrappers | Estimator API reference and smoke scripts. |
| Metric/evaluation/certification tests | Evaluation/certification reference and smoke script. |
| CI, docs build, generated resources, notebooks, and long training examples | Excluded from runtime helpers because they are maintainer-heavy, download-prone, or outside selected runtime scope. |

## Using this map

- Prefer the bundled helper nearest to the user's workflow before scaling to real data.
- If a bundled helper passes but the user's real workflow fails, use the owning sub-skill's troubleshooting reference to compare labels, shapes, estimator capabilities, optional dependencies, and backend choices.
- If a user specifically asks to reproduce an upstream example or test, treat it as a source-repository maintenance or verification task, not as a runtime helper supplied by this skill.
