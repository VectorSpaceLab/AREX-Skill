---
name: lora_recovery_protocol
description: Run a bounded soft-mode LoRA recovery protocol with executable mechanism checks and source-boundary logging.
---

# LoRA Recovery Protocol

Use this skill when full pretrained Transformer fine-tuning is unavailable but a mechanism-faithful LoRA recovery is allowed.

## Inputs
Attempt directory, generated LoRA skills, runtime handoff, and a deterministic synthetic low-rank task.

## Outputs
Recovery result JSON, training trace, generated data item, skill invocation log, and source manifest.

## Workflow
1. Declare proxy status and full-runtime blockers.
2. Generate examples from a frozen base matrix plus a rank-limited target update.
3. Invoke the LoRA update, merge, and budget skills.
4. Require loss decrease, unchanged base weights, changed LoRA factors, and merge equivalence.
5. Write validator-compatible artifacts.

## Validation
Run the recovery harness and then `validate_recovery_experiment.py` on the attempt directory.

## Limitations
This protocol validates mechanism transfer, not the paper's full GLUE/E2E benchmark scores.
