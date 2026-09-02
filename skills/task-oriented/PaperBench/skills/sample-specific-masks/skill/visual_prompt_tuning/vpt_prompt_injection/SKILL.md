---
name: vpt_prompt_injection
description: Build shallow or deep visual prompt token insertions for VPT-style Transformer inputs.
---

# vpt_prompt_injection

Use this skill when implementing or checking Visual Prompt Tuning mechanisms from Jia et al. Do not use it for unrelated pixel-prompt or full-backbone fine-tuning experiments.

## Inputs
Provide small token vectors, prompt settings, named parameter records, training examples, or prediction/label lists depending on the script. Inputs must make the frozen-backbone boundary explicit.

## Outputs
The scripts return prompted token sequences, freeze-audit dictionaries, training traces, or metric reports. Recovery users should save these outputs as experiment evidence.

## Workflow
1. Preserve the class token and image-patch token order.
2. Add continuous prompt parameters in input/token space.
3. Freeze all backbone parameters and update only prompt/head records.
4. Log loss, parameter changes, accuracy, and storage-efficient parameter ratios.

## Validation
Run `python -m pytest tests` or validate this tree with the Distiller `validate_skill_tree.py --run-tests` command.

## Limitations
These helpers are minimal and deterministic. They are intended for mechanism-faithful bounded recovery, not full VTAB/FGVC reproduction.
