---
name: zeroshot_prompt_classifier
description: Build natural-language prompt classifiers and evaluate zero-shot predictions from embeddings.
---

# Zeroshot Prompt Classifier

## When To Use
Use this skill when reproducing or testing the CLIP paper mechanism in a bounded setting. It is designed for generated recovery workflows and does not require the original CLIP repository.

## Inputs
- Small image-text feature records or class prompt features.
- A module plan target describing whether the run is full or reduced/proxy.
- Standard Python 3; no required external packages.

## Outputs
- Deterministic validation results or helper values suitable for recovery artifacts.
- Clear errors when the input violates the CLIP contract.

## Workflow
1. Keep image and text rows aligned so the diagonal represents positive matches.
2. Normalize embeddings before similarity scoring.
3. Use symmetric image-to-text and text-to-image evidence for training objectives when applicable.
4. For zero-shot evaluation, synthesize classifier weights from prompt text rather than supervised downstream labels.
5. Record whether the run is a reduced proxy and never claim full ImageNet-scale recovery without real model and data evidence.

## Validation
Run `python /share/project/yuyang/workspace/Paper2Skills/Paper2Skills-Agent/src/packages/paper2skills-agent/src/paper2skills/skills/module-to-skill/scripts/validate_skill_tree.py <skill_dir> --run-tests`.

## Limitations
This skill preserves the paper mechanism but does not include OpenAI CLIP weights, ImageNet data, or the original repository. Full reproduction requires those external resources and a much larger runtime.
