---
name: evaluation-and-certification
description: "Compute ART robustness/privacy metrics, run evaluation objects,
  route SummaryWriter logging, and perform gradient checks and
  certification/verification workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# evaluation-and-certification

Use this sub-skill when the model is already wrapped and you need to measure robustness, privacy leakage, gradient health, or certification/verification results.

## Use this for

- ART robustness metrics: `adversarial_accuracy`, `empirical_robustness`, `loss_sensitivity`, `clever_u`, `wasserstein_distance`.
- Privacy leakage metrics and threshold helpers: `PDTP`, `SHAPr`, `ComparisonType`, and the ROC helpers in `art.metrics.privacy`.
- Gradient checks: `loss_gradient_check`.
- Evaluation objects: `SecurityCurve`, `GreatScorePyTorch`.
- Tree robustness verification and certified/tree-specific workflows.
- Certification wrappers: randomized smoothing, de-randomized smoothing, DeepZ, and interval/IBP classifiers.
- SummaryWriter/TensorBoard routing for evaluation objects or attack/certification telemetry.

## Start here

1. Read [references/metrics-evaluations-certification.md](references/metrics-evaluations-certification.md) to pick the metric, evaluation object, or certifier and the correct import path.
2. If you need TensorBoard output, follow the SummaryWriter routing table there before enabling logging.
3. Run the bundled smoke script with `--help` first, then choose the tree mode you need:

   ```bash
   python scripts/smoke_metrics_tree.py --help
   python scripts/smoke_metrics_tree.py --tree-mode verify
   python scripts/smoke_pytorch_adv_accuracy.py --attack fgm --json
   ```

   If a tiny tree fixture is too brittle in your environment, rerun with `--tree-mode signature`. Use `smoke_pytorch_adv_accuracy.py` when the user needs an integrated CPU PyTorch wrapper + bounded attack + adversarial-accuracy sanity check.
4. Keep attack generation in `../evasion-and-preprocessing/SKILL.md` and estimator construction in `../estimators-and-models/SKILL.md`.

## Route away from this sub-skill

- Attack crafting, perturbation budgets, preprocessing defences, and adversarial training -> `../evasion-and-preprocessing/SKILL.md`
- Estimator wrappers, `clip_values`, label shape fixes, and gradient-enabled model setup -> `../estimators-and-models/SKILL.md`
- Poisoning, backdoors, extraction, and attack setup for privacy/inference workflows -> `../poisoning-inference-extraction/SKILL.md`
- Package install, optional dependency, and device/backend readiness -> `../setup-and-backends/SKILL.md`

## Guardrails

- Do not run original repo tests, examples, notebooks, or maintainer scripts.
- Keep smoke inputs synthetic, tiny, deterministic, and CPU-only.
- Use `SecurityCurve` as a post-attack evaluation; if a weak attack leaves accuracy high, strengthen the attack rather than assuming the model is robust.
- Tree verification only makes sense for normalized `[0, 1]` data and tree classifiers that expose `get_trees()`.
