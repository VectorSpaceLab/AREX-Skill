# Metrics, evaluations, and certification

Use this reference after you already have an ART estimator. Build the model, attack, and training wrapper elsewhere.

> Note: the top-level `art.evaluations` namespace does **not** export `SecurityCurve` or `GreatScorePyTorch`. Import them from their submodules. For privacy leakage, the callable APIs are `PDTP` and `SHAPr`; `membership_leakage` is the module name, not a function.

## Workflow table

| Need | Correct import path | Core contract | Returns / behavior | Route away / notes |
|---|---|---|---|---|
| Attack-conditioned robustness scores | `from art.metrics import adversarial_accuracy, empirical_robustness, loss_sensitivity, loss_gradient_check, clever_u` | `adversarial_accuracy` and `empirical_robustness` need a classifier and a crafted attack; built-in `attack_name` only covers `auto`, `fgsm`, and `hsj`. `loss_sensitivity` and `loss_gradient_check` need `loss_gradient`. `clever_u` needs `class_gradient`. | `adversarial_accuracy` returns a success rate; `empirical_robustness` returns mean minimal perturbation norm; `loss_sensitivity` returns mean loss-gradient norm; `loss_gradient_check` flags zero/nan/inf gradients; `clever_u` returns an untargeted CLEVER estimate. | Build or tune the attack in `../evasion-and-preprocessing/`; fix the wrapper in `../estimators-and-models/` if gradients are missing. |
| Distribution distance | `from art.metrics import wasserstein_distance` | Two arrays with the same shape, optional weights. | Per-sample first Wasserstein distance. | No classifier required. |
| Privacy leakage and MIA thresholding | `from art.metrics import PDTP, SHAPr, ComparisonType` and `from art.metrics.privacy import get_roc_for_fpr, get_roc_for_multi_fprs` | `PDTP` needs a resettable classifier pair plus training data; `SHAPr` needs train/test arrays with matching feature dimensions and labels. ROC helpers take binary attack probabilities and labels. | Per-sample leakage scores or ROC/threshold tuples. | If the task is attack setup, route to `../poisoning-inference-extraction/`. |
| Tree robustness verification | `from art.metrics.verification_decisions_trees import RobustnessVerificationTreeModelsCliqueMethod` | Tree classifier with `get_trees()`, normalized `[0, 1]` inputs, and `eps_init` > 0. | `(average_bound, verified_error)` for the chosen eps search. | Use only for tree models; keep `max_clique` and `max_level` small for smoke checks. |
| Security curve / obfuscation probe | `from art.evaluations.security_curve import SecurityCurve` | Loss-gradient classifier plus PGD kwargs such as `eps_step`, `max_iter`, `num_random_init`, and optional `summary_writer`. `eps` may be an int grid size or an explicit list. | `evaluate` returns `(eps_list, adversarial_accuracy_list, benign_accuracy)` and sets `detected_obfuscating_gradients`. | If the curve stays high under weak settings, strengthen the attack instead of trusting the curve. |
| GREAT score | `from art.evaluations.great_score import GreatScorePyTorch` | PyTorch classifier plus `x, y`. | `(great_score, accuracy)`. | Post-hoc evaluation only. |
| Randomized smoothing | `from art.estimators.certification import NumpyRandomizedSmoothing, PyTorchRandomizedSmoothing, TensorFlowV2RandomizedSmoothing` | `NumpyRandomizedSmoothing(classifier, sample_size, scale, alpha)`. PyTorch and TF need model, loss/loss_object, input shape, class count, and optimizer or train step. | `predict`, `fit`, `certify`, and `loss_gradient`. | Monte Carlo is expensive; keep `sample_size`, `n`, and batch size tiny for smoke checks. |
| De-randomized smoothing | `from art.estimators.certification import PyTorchDeRandomizedSmoothing` | Needs `model`, `loss`, `input_shape`, `nb_classes`, `ablation_size`, and ablation/algorithm settings. | Smoothed / certified patch-robust classifier. | PyTorch path is the common CPU smoke target; `channels_first=True` is required. |
| DeepZ certification | `from art.estimators.certification.deep_z import PytorchDeepZ, ZonoBounds, ZonoConv, ZonoDenseLayer, ZonoReLU` | PyTorch model, loss, input shape, class count. | Zonotope-based certification wrapper and helper layers. | Dense-before-conv is unsupported; only Conv2D / Linear / ReLU-style networks are in scope here. |
| Interval / IBP certification | `from art.estimators.certification.interval import PyTorchIBPClassifier, PyTorchIntervalBounds, PyTorchIntervalConv2D, PyTorchIntervalDense, PyTorchIntervalFlatten, PyTorchIntervalReLU` | PyTorch model, loss, input shape, class count, and optionally `concrete_to_interval`. | Interval-bound certification wrapper and helper layers. | Input must be channels-first; abstract interval inputs use lower/upper pairs on axis 1. |

## Bundled metric checks

- `scripts/smoke_metrics_tree.py --tree-mode signature` runs synthetic robustness/privacy/evaluation checks plus tree/certification import/signature validation; use `--tree-mode verify` when a tiny tree fixture is compatible.
- `scripts/smoke_pytorch_adv_accuracy.py --attack fgm --json` builds a deterministic CPU `PyTorchClassifier`, crafts bounded adversarial examples, and reports benign plus adversarial accuracy without downloads or training. Use it for integrated setup -> estimator -> attack -> metric sanity checks.

## SummaryWriter routing

| Need | Route |
|---|---|
| Disable TensorBoard output | Pass `summary_writer=False` on the ART object that owns the logging. |
| Enable default TensorBoard logs | Pass `summary_writer=True` or a string path to the owning ART object. |
| Custom logging behavior | Pass a custom `SummaryWriter` instance where the API accepts it. |
| Attack-failure indicators | Use `SummaryWriterDefault(..., ind_1=True, ind_2=True, ind_3=True, ind_4=True)` when you want silent-success, break-point angle, diverging-loss, or zero-gradient telemetry. |

## Certified family quick notes

- `PyTorchRandomizedSmoothing` and `TensorFlowV2RandomizedSmoothing` are the framework-specific certified wrappers; `PyTorchRandomizedSmoothing` defaults to `device_type='gpu'`, so pass `device_type='cpu'` on CPU-only hosts.
- `PyTorchDeRandomizedSmoothing` supports both CNN and ViT-style patch certification workflows; keep `channels_first=True`.
- If TensorFlow is available, `TensorFlowV2DeRandomizedSmoothing` is also exported from `art.estimators.certification`.
- `PytorchDeepZ` and `PyTorchIBPClassifier` only support Conv2D / Linear / ReLU-style networks and infer the reshape from convolution to dense.
- `SecurityCurve` forwards attack kwargs to PGD, so `summary_writer` and other PGD settings are configured at the evaluation call.
