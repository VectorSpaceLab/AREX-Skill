---
name: cs230-code-examples
description: "Routes CS230 code-example requests to the correct PyTorch or
  TensorFlow vision and NLP workflows for SIGNS image classification and
  named-entity recognition."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# CS230 Code Examples

This repo is a small workflow collection rather than an installable package. It
contains four user-facing example families:

- PyTorch vision: SIGNS image classification.
- PyTorch NLP: named-entity recognition.
- TensorFlow vision: SIGNS image classification.
- TensorFlow NLP: named-entity recognition.

Use this root skill to choose the right framework sub-skill, confirm the shared
environment, and find the repo-wide troubleshooting notes.

## Read first

- `references/repo-provenance.md` when you need to check whether this skill is
  current for the repository checkout.
- `references/troubleshooting.md` for cross-cutting setup, import, and data
  layout issues.
- `scripts/check_env.py` for a safe shared import/version check.

## Route map

- `sub-skills/pytorch-examples/` for all PyTorch vision and NLP workflows.
- `sub-skills/tensorflow-examples/` for all TensorFlow vision and NLP
  workflows.

Choose the sub-skill by framework first, then read that sub-skill's workflow
reference for the specific domain command.

## What the root skill covers

Use the root skill when you need one of these:

- a high-level overview of the repository topology;
- a pointer to the right framework and workflow family;
- shared installation or import guidance;
- a repo-wide troubleshooting hint before you drill into a sub-skill;
- provenance/staleness checking for this generated skill.

Do not use the root skill for command-level details. The sub-skills own the
actual commands, data layouts, and workflow notes.

## Shared setup guidance

- There is no top-level installable Python distribution.
- Install the runtime dependencies from the selected framework requirements
  files under `pytorch/` or `tensorflow/`.
- For a mixed inspection environment, install both framework stacks plus the
  shared helpers used by the examples: `numpy`, `Pillow`, `tabulate`, and
  `tqdm`.
- A fresh isolated environment is preferred because TensorFlow 1.15 is
  sensitive to `protobuf` and legacy CUDA runtime mismatches.
- PyTorch will use CUDA automatically when the host and wheel support it, but
  the repo's workflows are still valid on CPU-only hosts.

Example install commands:

```bash
python -m pip install -r pytorch/vision/requirements.txt
python -m pip install -r pytorch/nlp/requirements.txt
python -m pip install -r tensorflow/vision/requirements.txt
python -m pip install -r tensorflow/nlp/requirements.txt
```

Pick the requirement files that match the framework workflows you plan to use.

## Minimal shared check

Run the bundled diagnostic before a workflow-specific command:

```bash
python scripts/check_env.py --frameworks pytorch tensorflow
```

Add `--repo-root <repo-path>` when you also want the helper to probe the local
workflow modules from the current checkout.

## Repository layout at a glance

- `pytorch/vision/` and `tensorflow/vision/` both work on the SIGNS dataset.
- `pytorch/nlp/` and `tensorflow/nlp/` both work on the NER text datasets.
- Each family has its own `build_*`, `train.py`, `evaluate.py`,
  `search_hyperparams.py`, and `synthesize_results.py` scripts.
- The starter experiment directories under `experiments/` contain the default
  `params.json` files used by the example commands.

## When to hand off to a sub-skill

- If the user mentions images, hand signs, SIGNS, resizing, or 64x64 image
  preprocessing, switch to the relevant vision sub-skill.
- If the user mentions sentences, tags, NER, vocab building, or Kaggle CSV
  splitting, switch to the relevant NLP sub-skill.
- If the user wants a command that should run in the repo checkout, use the
  framework sub-skill's bundled workflow helper rather than the source script
  path directly.
