---
name: base_ptq_scale_search
description: Use this skill to calibrate post-training quantization scales for a layer or matrix multiplication using deterministic candidate search.
---

# Base Ptq Scale Search

Use this skill when a recovery or implementation task needs the PTQ4ViT capability described in the module plan. Do not use it to claim full ImageNet accuracy without an actual model, dataset, and evaluation command.

## Inputs
- Numeric calibration tensors or an attempt directory, depending on the script.
- Explicit bit width, candidate scales, and runtime/source-boundary constraints.

## Outputs
- Deterministic numeric traces suitable for validation.
- JSON-compatible metadata that downstream recovery can inspect.

## Workflow
1. Read the module contract and pass only bounded local tensors or attempt artifacts.
2. Run the script in `scripts/` or import its pure functions.
3. Validate outputs with the tests in `tests/`.
4. Record commands and artifacts in the Distiller attempt when used for recovery.

## Validation
Run `python validate_skill_tree.py <skill_dir> --run-tests` from the Distiller module-to-skill validator.

## Limitations
This skill preserves the PTQ4ViT mechanism but does not bundle pretrained models, ImageNet, or the original repository. Recovery must not read the original repository.
