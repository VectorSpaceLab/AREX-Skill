---
name: rnd_observation_normalization
description: Normalize observations for Random Network Distillation with running statistics and clipping before target and predictor feature computation.
---

# RND Observation Normalization

Use this skill when implementing or validating Random Network Distillation (RND) pipelines that feed observations into a frozen random target and a trainable predictor. Do not use it as a generic image augmentation skill; its purpose is to preserve the paper's scale-control mechanism.

## Inputs
- A batch of numeric observations represented as lists of equal-length vectors.
- Optional running statistics with `mean`, `var`, and `count` fields.
- Optional clipping bounds, defaulting to the paper's `[-5, 5]` range.

## Outputs
- Normalized and clipped observation vectors.
- Updated running statistics that must be shared by target and predictor paths.

## Workflow
1. Merge incoming batch moments with existing running moments using a numerically stable parallel variance update.
2. Normalize each dimension with `(x - mean) / sqrt(var + eps)`.
3. Clip normalized values after whitening.
4. Feed exactly the same normalized batch to both RND target and predictor modules.

## Validation
Run `python scripts/normalization.py --self-test` or validate the skill tree with tests enabled. The self-test checks running-stat updates, finite normalization, and clipping bounds.

## Limitations
The script handles vector observations for deterministic recovery and tests. Image tensors should be flattened or batched into vectors before use, while preserving the same running-stat semantics.
