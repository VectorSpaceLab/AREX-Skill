# Troubleshooting

## Missing or bad gradients

| Symptom | Likely cause | Fix |
|---|---|---|
| `loss_sensitivity`, `SecurityCurve`, `GreatScorePyTorch`, or PGD-based evaluation fails with gradient errors | The estimator wrapper does not expose `loss_gradient` or the wrapper configuration is wrong | Fix the estimator in `../estimators-and-models/` before returning here. Run `loss_gradient_check` on a tiny synthetic batch first. |
| `clever_u` fails or returns nonsense | The estimator does not expose `class_gradient`, or the model is saturating | Use a gradient-enabled wrapper and verify `clip_values`, preprocessing, and label format. |
| `loss_gradient_check` reports zero / nan / inf gradients | Saturated activations, bad preprocessing, or gradient masking | Inspect `clip_values`, input scaling, and the attack/estimator pair. If `SecurityCurve` also looks suspicious, strengthen the attack instead of trusting the metric. |

## Classifier and metric requirements

| Metric / workflow | Required behavior |
|---|---|
| `RobustnessVerificationTreeModelsCliqueMethod` | Use a tree classifier that exposes `get_trees()`, and keep inputs normalized to `[0, 1]`. |
| `PDTP` | Use a resettable classifier pair of the supported family (PyTorch, TensorFlowV2, or ScikitLearn). The extra estimator must be refit repeatedly. |
| `SHAPr` | Use matching train/test feature dimensions and matching label row counts. |
| `SecurityCurve` | Use a classifier with loss gradients. The evaluation will craft PGD examples internally. |
| Randomized smoothing | Provide a model/loss/optimizer stack that can actually run prediction and certification. |

## Slow Monte Carlo or long certification runs

- Randomized smoothing is Monte Carlo-heavy. Lower `sample_size`, `n`, and `batch_size` for smoke checks.
- `SecurityCurve` is also attack-heavy because it runs PGD once per eps value and then performs an obfuscation probe.
- For smoke scripts, prefer a small explicit eps list such as `[0.05]` rather than a long integer grid.
- If the call is only for import/path validation, switch the tree smoke to `--tree-mode signature`.

## Empty eps or malformed budgets

- `SecurityCurve(eps=0)` can divide by zero.
- `SecurityCurve(eps=[])` gives an empty curve and can make `plot()` fail.
- Always use a positive integer or a non-empty explicit list of eps values.
- Keep eps in the same scale as the wrapped estimator’s `clip_values`.

## Weak attacks and gradient obfuscation

- If `SecurityCurve` still reports high adversarial accuracy at large eps, or `detected_obfuscating_gradients` is `True`, assume the attack is too weak or gradients are being masked.
- Increase `max_iter`, lower `eps_step`, or add `num_random_init` before trusting the result.
- If the goal is only to generate stronger adversarial examples, route back to `../evasion-and-preprocessing/SKILL.md`.

## TensorBoard / SummaryWriter output

- `summary_writer=False` disables logging at the ART object that owns the call.
- `True` or a string path enables default TensorBoard routing; pass a writable path when you want logs.
- `SummaryWriterDefault` can emit gradient norms, patch images, losses, and selected attack-failure indicators.
- If logs do not appear, confirm that `tensorboardX` is installed and that the owner object actually accepted the `summary_writer` parameter.
- `SecurityCurve` forwards `summary_writer` through to PGD, so the logging control lives at the evaluation call.

## Certification-specific failures

| Symptom | Likely cause | Fix |
|---|---|---|
| PyTorch certification wrapper complains about channels | `channels_first` is wrong for the wrapper or the input layout is not what the model expects | Use channels-first tensors for the PyTorch certification wrappers and keep tabular inputs flat. |
| DeepZ / IBP refuses a network | The model contains unsupported layers or a dense layer appears before the convolution stack | Keep the network to Conv2D / Linear / ReLU-style modules and follow the supported reshape pattern. |
| Randomized smoothing fit/certify is too slow or unstable | `sample_size` or `n` is too large for the smoke check | Reduce the count first; only scale it up after the tiny fixture passes. |
| TensorFlow randomized smoothing fit fails | The TF wrapper is missing the expected `loss_object`, `optimizer`, or `train_step` | Fix the estimator in `../estimators-and-models/` before retrying. |

## When to stop and reroute

- If the problem is wrapper construction, shape handling, or missing gradients, stop here and use `../estimators-and-models/SKILL.md`.
- If the problem is attack generation, parameter search, or preprocessing defences, stop here and use `../evasion-and-preprocessing/SKILL.md`.
- If the problem is install/import/backend readiness, stop here and use `../setup-and-backends/SKILL.md`.
