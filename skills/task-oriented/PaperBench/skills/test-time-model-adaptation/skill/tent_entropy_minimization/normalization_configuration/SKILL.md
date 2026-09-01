---
name: normalization_configuration
description: Configure normalization layers for Tent by exposing only affine modulation parameters and target batch statistics.
---

# Normalization Configuration for Tent

Use this skill before running entropy-minimizing test-time adaptation on a model with normalization layers. It is appropriate for creating a Tent configuration report, checking a proxy model, or comparing against normalization-only adaptation. Do not use it to authorize updating all model weights unless the run is an explicit ablation outside standard Tent.

## Inputs

- A model inventory JSON with modules, parameter names, layer types, and affine/statistics fields.
- Optional flags for target batch statistics and whether running statistics should be disabled.

## Outputs

- Trainable parameter names limited to normalization affine scale and shift.
- A configured module inventory with target-batch statistics enabled for normalization layers.
- Validation errors for missing normalization layers or accidental full-model training.

## Workflow

1. Set the model-level mode to training for adaptation.
2. Disable gradients for all parameters by default.
3. For each batch normalization descriptor, enable gradients on `weight` and `bias` only.
4. Set `track_running_stats` false when using target-batch-only statistics.
5. Return a report with trainable parameters and configuration checks.
6. Reject configurations where no normalization affine parameters are available.

## Validation

Run `python scripts/configure_norm.py --self-test`. The test constructs a tiny inventory and confirms that only batch-normalization affine parameters are trainable while classifier parameters remain frozen.

## Limitations

The script works on portable inventory dictionaries. For live frameworks such as PyTorch, use this report as a contract and apply the same logic to actual modules.
