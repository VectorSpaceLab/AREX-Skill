---
name: boltz
description: "Route Boltz package tasks for biomolecular structure and affinity
  prediction, data preparation, training, and evaluation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Boltz Repo Skill

Use this repo skill when a user asks about Boltz, the `boltz` Python package, or workflows for biomolecular structure prediction, binding-affinity prediction, training data preparation, retraining, or evaluation.

## Quick Triage

- **Run or debug `boltz predict`:** use `sub-skills/prediction/SKILL.md` for CLI options, YAML/FASTA inputs, MSA server/authentication, affinity prediction, output files, cache behavior, and prediction-time troubleshooting.
- **Prepare raw training/evaluation data:** use `sub-skills/data-preparation/SKILL.md` for CCD, sequence clustering, MSA processing, RCSB/mmCIF processing, Redis, `mmseqs`, processed file layouts, and safe preflight checks.
- **Train or retrain models:** use `sub-skills/training/SKILL.md` for Hydra config edits, debug launches, checkpoint intent, resource knobs, wandb/DDP issues, and training-data readiness checks.
- **Evaluate or summarize outputs:** use `sub-skills/evaluation/SKILL.md` for confidence/affinity metrics, benchmark folder layouts, legacy OpenStructure evaluation scripts, CSV/JSON summaries, and top-1 versus oracle distinctions.

## Install And Smoke Checks

Boltz is a Python package named `boltz`, with a public CLI entry point named `boltz` and a `predict` command. Public installation guidance recommends a fresh Python environment:

```bash
pip install boltz -U
```

For CUDA-enabled inference, public docs use the CUDA extra:

```bash
pip install 'boltz[cuda]' -U
```

Use CPU-only installs for inspection, input validation, and documentation tasks. Full prediction, training, and benchmark workflows may require GPU hardware, large model/data downloads, external tools, or long runtimes.

Run safe checks before expensive work:

```bash
python scripts/boltz_environment_check.py
boltz --help
boltz predict --help
```

## Shared References

- `references/package-overview.md` — package purpose, installed facts, dependency/back-end expectations, and workflow map.
- `references/troubleshooting.md` — cross-cutting install/import, cache, GPU, data/config, CLI, and external dependency failures.
- `references/repo-provenance.md` — source repository snapshot used to generate this skill.
- `references/repo-routing-metadata.json` — structured routing metadata used by DisCo's managed repo-skills router.
- `scripts/boltz_environment_check.py` — safe local environment and CLI preflight helper.

## Cross-Workflow Guardrails

- Prefer prediction YAML for new inference inputs; FASTA remains supported but is deprecated and lacks several YAML-only features.
- Do not run model downloads, MSA-server calls, full training, raw-data preprocessing, or benchmark evaluation until the user has confirmed hardware, storage, credentials, network, and runtime expectations.
- Treat original Boltz examples, docs, tests, and scripts as evidence. This skill bundles portable references and helpers so future agents do not need the original source checkout for routine guidance.
- Keep credentials out of prompts and logs. For MSA server secrets, prefer environment variables over inline CLI values.
- Be explicit about Boltz-2 documentation gaps: inspected docs mark updated Boltz-2 training and evaluation assets as coming soon.
