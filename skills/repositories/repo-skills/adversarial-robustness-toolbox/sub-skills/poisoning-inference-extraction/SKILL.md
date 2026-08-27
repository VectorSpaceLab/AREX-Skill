---
name: poisoning-inference-extraction
description: "Plan ART poisoning, privacy inference, model
  inversion/reconstruction, extraction, and detector/mitigation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Poisoning, inference, and extraction

Use this sub-skill when the task is to plan or reason about poisoning/backdoor attacks, privacy inference attacks, model inversion/reconstruction, model extraction/stealing, or poison/backdoor detectors and mitigations.

## Route here

- Poisoning and backdoor attack planning for SVMs, feature collision, backdoors, clean-label backdoors, hidden triggers, adversarial embedding, gradient matching, and sleeper-agent-style workflows.
- Privacy inference workflows for membership inference, attribute inference, model inversion, and reconstruction.
- Model extraction / stealing workflows such as Copycat CNN, Knockoff Nets, and Functionally Equivalent Extraction.
- Poisoning detectors and mitigations such as Activation Defence, Spectral Signature Defense, Provenance Defense, RONI Defense, Neural Cleanse, and STRIP.
- Questions about train/validation splits, label format, trigger construction, classifier capabilities, or query budgets for these attack families.

## Route elsewhere

- Ordinary evasion attacks, preprocessing defences, and adversarial training belong to [`../evasion-and-preprocessing/SKILL.md`](../evasion-and-preprocessing/SKILL.md).
- Robustness metrics, certification, tree verification, security curves, and gradient checks belong to [`../evaluation-and-certification/SKILL.md`](../evaluation-and-certification/SKILL.md).
- Estimator wrapping, `clip_values`, `input_shape`, label encoding, and gradient availability belong to [`../estimators-and-models/SKILL.md`](../estimators-and-models/SKILL.md).
- Installation, import readiness, and backend selection belong to [`../setup-and-backends/SKILL.md`](../setup-and-backends/SKILL.md).
- Object detection, audio, malware, and other special-purpose attack families are outside this bundled runtime scope unless a reference note explicitly says otherwise.

## Operating sequence

1. Identify the attack family and the minimum estimator/data capability from [references/attack-families.md](references/attack-families.md).
2. Check detector and mitigation routing, plus backend constraints, in [references/defences-and-mitigations.md](references/defences-and-mitigations.md).
3. Use [references/troubleshooting.md](references/troubleshooting.md) for split, label, trigger, query-budget, and import issues.
4. Run [scripts/inspect_privacy_poisoning_apis.py](scripts/inspect_privacy_poisoning_apis.py) to confirm available imports and signatures before drafting a recipe.

## Bundled checks

- `python scripts/inspect_privacy_poisoning_apis.py --help`
- `python scripts/inspect_privacy_poisoning_apis.py --json`

The helper only imports and inspects signatures; it does not train models or download data.
