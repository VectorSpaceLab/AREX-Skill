---
name: evaluation
description: "Compute and interpret SketchCode BLEU scores for single or batch
  GUI DSL files."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# SketchCode evaluation

Use this sub-skill when the task is to evaluate SketchCode-style `.gui` output, compute BLEU for one generated GUI, compare original and predicted GUI folders, explain button-color normalization, or debug NLTK BLEU warnings.

## Start here

1. For commands and workflow choices, read [references/evaluation-workflow.md](references/evaluation-workflow.md).
2. For the distilled `Evaluator` behavior, normalization rules, prediction trimming, and batch pairing contract, read [references/api-reference.md](references/api-reference.md).
3. For skipped files, low BLEU, NLTK warnings, short-sequence behavior, or surprising button-color results, read [references/troubleshooting.md](references/troubleshooting.md).
4. For a self-contained smoke check or file-based local score without depending on original source scripts, run [scripts/evaluate_tiny_gui_bleu.py](scripts/evaluate_tiny_gui_bleu.py).

## Route elsewhere

- If the user still needs to generate predicted `.gui` files from sketches or HTML conversion outputs, route to [../conversion-inference/SKILL.md](../conversion-inference/SKILL.md).
- If the user is preparing data, training, fine-tuning, or validating paired training examples, route to [../training-data/SKILL.md](../training-data/SKILL.md).

This sub-skill distills the SketchCode evaluation behavior into bundled references and a safe helper. Do not require runtime access to the original repository scripts just to understand normalization, pairing, or BLEU interpretation.
