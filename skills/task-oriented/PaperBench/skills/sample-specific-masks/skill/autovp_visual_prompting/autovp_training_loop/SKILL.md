---
name: autovp_training_loop
description: Run a reduced AutoVP prompt optimization step while proving the source classifier remains frozen.
---
# AutoVP Training Loop
Use this skill to recover or test AutoVP's parameter-efficient adaptation mechanism. It is appropriate when a frozen classifier callable, prompt module, label mapper, and small dataset are available.

## Inputs
Training examples, labels, prompt parameters, frozen classifier weights/callable, label mapping, learning rate, and step count.

## Outputs
Loss before/after, prompt parameters before/after, classifier frozen check, predictions, and accuracy.

## Workflow
Apply visual prompt, run frozen classifier, map logits to targets, compute loss, update only prompt or mapping parameters, and record trace evidence. Never mutate source classifier weights.

## Validation
Run included tiny deterministic optimizer test.
