---
name: adversarial-robustness-toolbox
description: "Use Adversarial Robustness Toolbox (ART) for estimator wrappers,
  adversarial attacks, defences, poisoning/privacy/extraction, metrics, and
  certification workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Adversarial Robustness Toolbox (ART)

Use this repo skill when a task names `adversarial-robustness-toolbox`, `art`, ART estimators, adversarial examples, robustness defences, poisoning/backdoor attacks, privacy inference attacks, model extraction, robustness metrics, or certification workflows.

ART is a Python library for wrapping ML models as estimators, attacking and defending them, and evaluating robustness. This skill covers the core CPU-capable Python workflows verified for ART 1.20.1; heavy speech, object-detection, tracking, malware, GAN/generation, experimental, notebook, and container-only workflows are treated as out of selected runtime scope unless a future refresh expands them.

## Start here

1. If ART is not installed or imports fail, go to [`sub-skills/setup-and-backends/`](sub-skills/setup-and-backends/SKILL.md).
2. For a quick installed-environment check, run the bundled diagnostic from this skill directory:

   ```bash
   python scripts/inspect_art_install.py --json
   ```

3. If a model is not yet wrapped as an ART estimator, use [`sub-skills/estimators-and-models/`](sub-skills/estimators-and-models/SKILL.md) before choosing attacks or metrics.
4. Choose the workflow owner from the route table below, then read that sub-skill's references and bundled scripts.
5. Before deciding whether this skill matches a newer checkout, read [`references/repo-provenance.md`](references/repo-provenance.md).

## Route map

| User request | Load this sub-skill | Why |
|---|---|---|
| Install ART, verify `import art`, choose CPU/GPU packages, resolve optional dependency or backend errors | [`setup-and-backends`](sub-skills/setup-and-backends/SKILL.md) | Owns package groups, backend matrix, and import diagnostics. |
| Wrap sklearn, PyTorch, TensorFlow/Keras, boosted-tree, GPy, black-box, or regression models for ART | [`estimators-and-models`](sub-skills/estimators-and-models/SKILL.md) | Owns estimator constructor contracts, labels, shapes, `clip_values`, gradients, and black-box limitations. |
| Generate evasion adversarial examples, choose FGSM/PGD/AutoAttack/HopSkipJump/patch attacks, add preprocessors, or plan adversarial training | [`evasion-and-preprocessing`](sub-skills/evasion-and-preprocessing/SKILL.md) | Owns attack-family compatibility, perturbation budgets, preprocessing defences, and trainer recipes. |
| Plan poisoning/backdoor, membership/attribute inference, model inversion/reconstruction, model extraction/stealing, or detector/mitigation workflows | [`poisoning-inference-extraction`](sub-skills/poisoning-inference-extraction/SKILL.md) | Owns poisoning, privacy inference, extraction, Neural Cleanse, Activation Defence, STRIP, and query/data split guidance. |
| Compute robustness/privacy metrics, run SecurityCurve or GREAT score, use SummaryWriter routing, run tree verification, or choose certification wrappers | [`evaluation-and-certification`](sub-skills/evaluation-and-certification/SKILL.md) | Owns ART metrics, evaluation objects, gradient checks, tree verification, randomized smoothing, DeepZ, and interval/IBP routes. |

## Shared references

- [`references/backend-matrix.md`](references/backend-matrix.md) — install groups, optional backend families, and CPU/GPU notes used across sub-skills.
- [`references/workflow-overview.md`](references/workflow-overview.md) — end-to-end workflow order, input/label conventions, and cross-sub-skill handoffs.
- [`references/examples-and-tests-map.md`](references/examples-and-tests-map.md) — bundled helper map and native-candidate categories, without requiring source examples at runtime.
- [`references/troubleshooting.md`](references/troubleshooting.md) — cross-cutting install/import, data shape, optional dependency, and workflow-routing failures.
- [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json) — structured router placement consumed during managed repo-skill import.

## Public install check

For a normal user environment, start with the base package and only add backend libraries needed by the selected workflow:

```bash
python -m pip install adversarial-robustness-toolbox
python -c "import art; print(art.__version__)"
```

For PyTorch CPU workflows, be explicit in ART wrappers that accept a device parameter:

```python
classifier = PyTorchClassifier(..., device_type="cpu")
```

ART's PyTorch wrappers often default to GPU-oriented device selection, so this explicit CPU choice avoids no-CUDA confusion.

## Guardrails

- Do not run original repository examples, notebooks, tests, or CI scripts as runtime instructions for users. Use the bundled scripts and distilled references in this skill tree.
- Do not claim a black-box estimator supports white-box attacks requiring `loss_gradient`; route to compatible attacks or rebuild a gradient-enabled estimator.
- Do not treat successful attack generation as proof of robustness. Use the metrics/certification sub-skill for evaluation, stronger attacks, and gradient-obfuscation checks.
- Do not import or update the managed repo-skill library from this runtime skill. Import is a separate verified creation workflow step.
