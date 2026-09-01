---
name: output_label_mapping
description: Convert frozen source-model logits or predictions to target classes with AutoVP label mapping strategies.
---
# Output Label Mapping
Use this skill for AutoVP FreqMap, IterMap-style refreshes, SemanticMap planning, or FullyMap linear logit mapping.

## Inputs
Source predictions/logits, target labels, mapping multiplicity, optional class embeddings, and optional linear weights.

## Outputs
Target-to-source mappings, target predictions, or mapped target logits.

## Workflow
For FreqMap, count source predictions per target and choose deterministic top source labels. For IterMap, recompute FreqMap after prompt updates. For FullyMap, compute `W L_s + b`. Keep tie-breaking reproducible.

## Validation
Run included deterministic tests.
