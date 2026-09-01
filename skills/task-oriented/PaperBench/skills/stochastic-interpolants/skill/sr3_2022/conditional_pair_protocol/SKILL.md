---
name: conditional_pair_protocol
description: Build and validate SR3-style low-resolution conditioning paired with high-resolution targets for reduced or full recovery experiments.
---

# Conditional Pair Protocol

Use this skill when a recovery experiment needs SR3-style paired data. Do not use it to evaluate image quality or to replace the diffusion objective.

## Inputs
- A clean high-resolution scalar or image-like value.
- A deterministic degradation or scale factor.
- Optional provenance describing whether the item is real, resource-derived, or synthetic proxy data.

## Outputs
- A JSON-compatible pair containing `condition`, `target`, `scale_factor`, `is_proxy`, and provenance fields.
- Validation errors for missing values or nonpositive scale factors.

## Workflow
1. Keep the low-resolution condition and high-resolution target as separate fields.
2. Record whether the pair comes from a real dataset or from a declared reduced proxy.
3. Preserve source metadata so recovery can distinguish benchmark-derived items from synthetic examples.
4. Pass only the pair object to diffusion objective or sampler skills; do not inject evaluation decisions here.

## Validation
Run `python tests/test_pair_protocol.py` or validate the skill tree with `--run-tests`.

## Limitations
A synthetic scalar pair can test conditioning contracts, but it is not evidence of full SR3 visual fidelity.
