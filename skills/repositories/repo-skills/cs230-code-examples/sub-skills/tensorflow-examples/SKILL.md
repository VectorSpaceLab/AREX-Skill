---
name: tensorflow-examples
description: "Routes TensorFlow SIGNS and NER example requests to the correct
  preprocessing, training, evaluation, hyperparameter search, and results
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# TensorFlow Examples

Use this sub-skill for every TensorFlow workflow in the repository:

- vision on the SIGNS image dataset;
- NLP on the named-entity recognition dataset;
- preprocessing, training, evaluation, hyperparameter search, and result
  synthesis for either workflow.

The helper scripts in this sub-skill are safe wrappers around the repository's
TensorFlow example commands. Future agents should use them instead of trying to
reconstruct the working directory and flags from memory.

## Read when

- the user mentions TensorFlow, tf.data, tf.contrib, SIGNS, hand signs, or
  image classification;
- the user mentions TensorFlow NER, vocab building, Kaggle CSV splitting, or
  sentence tagging;
- the user wants a train/evaluate/search/synthesize command for a TensorFlow
  example;
- the user needs TensorFlow 1.15-specific troubleshooting or data-layout
  guidance.

## What this sub-skill covers

### Vision route

- resizing the SIGNS dataset to `64x64`;
- training the convolutional classifier;
- evaluating a saved checkpoint;
- launching the built-in learning-rate search;
- aggregating experiment metrics.

### NLP route

- converting the Kaggle CSV into `train/`, `dev/`, and `test/` text splits;
- building word and tag vocabularies;
- training the LSTM-based NER model;
- evaluating a saved checkpoint;
- launching the built-in learning-rate search;
- aggregating experiment metrics.

## What is excluded

- PyTorch workflows.
- Any workflow that needs the PyTorch `torch` / `torchvision` stack.
- Repository-wide provenance or framework selection questions; those belong in
  the root skill.

## Key bundled files

- `references/workflows.md` for copyable command sequences and data layouts.
- `references/api-reference.md` for verified local module signatures and helper
  behavior.
- `references/troubleshooting.md` for common TensorFlow setup and data issues.
- `scripts/run_workflow.py` for a safe command wrapper with `--repo-root` and
  `--execute` support.

## Installation guidance

- Install the packages listed in `../../tensorflow/vision/requirements.txt` when you
  need the vision workflow.
- Install the packages listed in `../../tensorflow/nlp/requirements.txt` when you
  need the NER workflow.
- A single environment that satisfies both files is usually enough for the full
  TensorFlow sub-skill.
- TensorFlow 1.15 is the intended stack for these examples, so use a compatible
  Python version and keep the environment isolated.

Example install commands:

```bash
python -m pip install -r ../../tensorflow/vision/requirements.txt
python -m pip install -r ../../tensorflow/nlp/requirements.txt
```

## Minimal check

Run the shared environment helper first:

```bash
python ../../scripts/check_env.py --frameworks tensorflow
```

If you need to confirm the local checkout as well, add `--repo-root <repo-root>`.

## Workflow selection

- Use the vision route when the task mentions images, signs, resizing, or
  64x64 SIGNS preprocessing.
- Use the NLP route when the task mentions sentences, tokens, tags, words,
  Kaggle CSV splitting, or vocabulary building.

If the user only asks for a command, read `references/workflows.md` first. If
an import or runtime error appears, jump to `references/troubleshooting.md`.
