---
name: anomalib
description: "Use anomalib for anomaly-detection install, data/model selection,
  training and evaluation, deployment and inference, and benchmark pipelines."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Anomalib Repo Skill

Use this repo skill when the user asks about the `anomalib` Python package, anomaly-detection data modules, model selection, training and evaluation, export and inference, or benchmark pipelines.

This skill tree is self-contained. Future agents should use the bundled references and scripts inside this directory, not the original source checkout.

## Repo at a glance

- `src/anomalib/`: public package source for data, models, engine, deploy, and pipelines.
- `docs/source/...`: user-facing guides, API references, and troubleshooting notes distilled into bundled references.
- `examples/api/` and `examples/cli/`: runnable workflow examples that informed the bundled recipes and scripts.
- `tests/`: behavior evidence for defaults, errors, and edge cases.
- `tools/`: repo-owned helpers and advanced entry points that were copied, adapted, or referenced where safe.

## Quick start

- If you only need to confirm the package imports, run `scripts/check_import.py`.
- If installation, optional extras, or CLI flags are the problem, start with `sub-skills/install-and-cli/SKILL.md`.
- If the request is about data layout or choosing a model, route to `sub-skills/data-and-models/SKILL.md`.
- If the request is about fit/train/test/validate, metrics, callbacks, logging, preprocessing, or visualization, route to `sub-skills/training-and-evaluation/SKILL.md`.
- If the request is about export, `Engine.predict`, or runtime inferencers, route to `sub-skills/deployment-and-inference/SKILL.md`.
- If the request is about benchmark configs or tiled ensemble workflows, route to `sub-skills/pipelines-and-benchmarks/SKILL.md`.

## Route by task

| User request | Go to |
| --- | --- |
| "How do I install anomalib or fix a CLI/help problem?" | `sub-skills/install-and-cli/` |
| "Which datamodule or model should I use?" | `sub-skills/data-and-models/` |
| "How do training, validation, metrics, or callbacks work?" | `sub-skills/training-and-evaluation/` |
| "How do I export or run inference from a checkpoint?" | `sub-skills/deployment-and-inference/` |
| "How do I run a benchmark or tiled ensemble config?" | `sub-skills/pipelines-and-benchmarks/` |

## How to choose quickly

1. Start with the smallest workflow that matches the user's current step.
2. If the user is blocked by installation or CLI syntax, resolve that first through install-and-cli.
3. If the user already has data and a model choice, use data-and-models before any training step.
4. If the user has a checkpoint and wants predictions or deployment artifacts, use deployment-and-inference.
5. If the user needs benchmark-scale orchestration, use pipelines-and-benchmarks and keep execution planning separate from model or data selection.

## Shared references

- `references/repo-provenance.md` records the source snapshot, package version, and evidence footprint.
- `references/repo-routing-metadata.json` feeds the managed repo-skill router during import.
- `references/troubleshooting.md` covers package-wide install, import, and routing failures.
- `scripts/check_import.py` is a minimal package-import smoke check.

## Operating notes

- Prefer the most specific sub-skill instead of staying at the root.
- Keep install and CLI issues separate from model or pipeline questions.
- Keep deployment and inference separate from training and evaluation.
- Keep benchmark orchestration separate from engine internals unless the user explicitly asks for both.
- If a user asks for a broad end-to-end task, use the sub-skill that owns the current bottleneck, then cross-link to the next step.

## Self-check

A healthy runtime installation should at least be able to import `anomalib` and report its version. Use the bundled import check first, then move into the relevant sub-skill for deeper guidance.
