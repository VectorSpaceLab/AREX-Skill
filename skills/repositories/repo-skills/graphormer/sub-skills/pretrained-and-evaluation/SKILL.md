---
name: pretrained-and-evaluation
description: "Guide Graphormer pretrained checkpoint loading, fine-tuning, and
  evaluation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Pretrained And Evaluation

Use this sub-skill when the task is to choose a Graphormer pretrained model, render a safe fine-tuning command, evaluate an official pretrained checkpoint, or evaluate checkpoints saved by a Graphormer run.

Do not use this sub-skill for base training templates, custom dataset implementation, or model architecture internals. Route those questions to the Graphormer training, dataset/customization, or model-extension sub-skills instead.

## Bundled Runtime Materials

- Read [references/pretrained-and-evaluation.md](references/pretrained-and-evaluation.md) for pretrained model names, output-layer loading semantics, MolHIV FLAG fine-tuning knobs, and evaluation/checkpoint behavior.
- Read [references/troubleshooting.md](references/troubleshooting.md) for checkpoint download/cache issues, output-head mismatches, CUDA-only evaluation behavior, metric mistakes, OGB split/evaluator mismatches, and strict checkpoint loading failures.
- Use [scripts/build_graphormer_eval_or_finetune_command.py](scripts/build_graphormer_eval_or_finetune_command.py) to render, but never execute, safe Graphormer evaluation or MolHIV fine-tuning commands.

## Operating Boundary

The bundled helper prints shell commands only. Treat any rendered command as a reviewable plan: check dataset availability, checkpoint source, GPU availability, output-layer decision, and metric before running it in a separate Researcher execution session.
