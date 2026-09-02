---
name: lora_parameter_freezing
description: Apply LoRA parameter freezing and compact checkpoint filtering for reduced adaptation experiments and audits.
---

# LoRA Parameter Freezing and Checkpointing

Use this skill when a recovery or implementation must prove that only LoRA adaptation parameters are trained or stored. It is useful for reduced experiments, model audits, and checkpoint construction. Do not use it to mutate a shared environment or to import the original repository during recovery.

## Inputs
- Named parameter metadata or a dictionary of parameter payloads.
- Bias policy: `none`, `lora_only`, or `all`.
- Optional expected parameter-count budget from the module plan.

## Outputs
- A map from parameter name to trainable/frozen status.
- A compact state dictionary containing LoRA parameters and permitted biases only.
- Evidence that frozen backbone weights are excluded from optimizer and checkpoint payloads.

## Workflow
1. Mark every name containing `lora_` as trainable.
2. Keep non-LoRA weights frozen under the default `none` bias policy.
3. Include biases only when the explicit policy permits them.
4. Save checkpoints from the filtered LoRA state dictionary rather than full model parameters.
5. Record counts for total parameters, trainable parameters, and checkpoint entries.

## Validation
Run the included tests or `python scripts/parameter_freezing.py --input <fixture.json>`. Tests assert backbone exclusion, LoRA inclusion, and default freezing behavior.

## Limitations
This skill models parameter names and checkpoint filtering deterministically; it does not depend on PyTorch tensors or optimizer objects.
