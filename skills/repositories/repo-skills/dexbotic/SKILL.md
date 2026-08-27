---
name: dexbotic
description: "Use Dexbotic to prepare DexData, train and serve
  vision-language-action policies, evaluate checkpoints, and integrate
  explicitly external RL or robot backends."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Dexbotic operating guide

Use this root route for the public `dexbotic` 0.2.0 package at the recorded provenance snapshot. It is a CUDA-oriented VLA toolkit spanning data, model-family experiments, HTTP serving, evaluation, deployment adapters, and optional RL backends. This skill is self-contained: use its bundled references/scripts rather than requiring the source checkout.

## Route by intent

- **Data conversion, DexData JSONL, registration, masks, normalization:** [data-preparation](sub-skills/data-preparation/SKILL.md)
- **SFT, LoRA, model/config selection, DDP/DeepSpeed/FSDP/FSDP2:** [training](sub-skills/training/SKILL.md)
- **HTTP `/v1` or legacy serving, `DexClient`, `BasePolicy`, DM0 realtime:** [inference-serving](sub-skills/inference-serving/SKILL.md)
- **Benchmarks, navigation, checkpoint evaluation, robot deployment topology:** [evaluation-deployment](sub-skills/evaluation-deployment/SKILL.md)
- **SimpleVLA-RL or RLinf adapters/launch contracts:** [rl-backends](sub-skills/rl-backends/SKILL.md)

## Install and verify

Install the pinned public package in an isolated environment, then run the generated diagnostic:

```bash
python -m pip install dexbotic==0.2.0
python scripts/check_environment.py
```

For a source checkout used only for maintenance, an editable install is also valid, but the operating skill itself does not require that checkout to remain available. The diagnostic is read-only; it does not download checkpoints or install optional backends.

## Root gates

1. Read [environment](references/environment.md) before installing or selecting a backend. Core VLA training/inference claims require a working CUDA stack; CPU imports are not a substitute.
2. Keep checkpoints, norm stats, action semantics, camera order, and data registration together. A package import alone does not make a model deployable.
3. Use [troubleshooting](references/troubleshooting.md) for cross-cutting failures, then the nearest sub-skill troubleshooting page.
4. Use bundled scripts only for safe, bounded, local diagnostics. They do not download weights, launch training, start servers, access hardware, or run simulators by default.
5. Optional simulator, LeRobot, RLinf, Triton checkpoint, vendor, and physical-robot surfaces are documented with prerequisites and verification limits; do not claim them as core verification.

## Common lifecycle

`data-preparation` → `training` → `inference-serving` → `evaluation-deployment`; branch to `rl-backends` only for RL post-training. Before a deployment request, query the serving capabilities contract and validate a no-actuation captured-observation path. See [provenance](references/repo-provenance.md) and [routing metadata](references/repo-routing-metadata.json) for version and selection boundaries.
