---
name: forward-forward-training
description: "Guides Forward-Forward training workflows, model-type selection,
  data loading, and Python compatibility troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# Forward-Forward training

Use this sub-skill when the user wants to train a Forward-Forward model, choose between the progressive/recurrent/NLP variants, or understand the package's source-era compatibility constraints.

## Triggers

- Train a Forward-Forward model on MNIST or Aesop fables.
- Choose `progressive`, `recurrent`, or `nlp` model types.
- Handle `predicted_tokens` for the NLP variant.
- Debug Python-version issues or dataset-download behavior.

## Read next

- `references/api-reference.md` for the public training API and model-type routing.
- `references/data-and-compatibility.md` for dataset loaders, vocabulary shape, and Python compatibility notes.
- `references/workflows.md` for the end-to-end training recipes.
- `references/troubleshooting.md` for import, download, and shape-failure recovery.
- `scripts/forward_forward_probe.py` for a safe import/signature check.

## What to include

- The `train_with_forward_forward_algorithm(...)` entry point.
- The `ForwardForwardModelType` selector.
- MNIST and Aesop Fables data-loading behavior.
- The progressive, recurrent, and NLP training branches.
- The Python 3.9 compatibility constraint.

## What to exclude

- Long training runs and dataset downloads as default actions.
- Repository-local notebook paths.
- Any unsupported model type beyond the three source-defined options.

## Quick decision rule

If the user says “train the Forward-Forward model,” route here. If they say “how do I install the backend packages?” read the root install notes first, then return here for the workflow.
