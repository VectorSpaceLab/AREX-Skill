---
name: progressive_lora_pruning_loop
description: Run LoRAPrune's iterative LoRA optimization, moving-average importance update, and progressive structured mask schedule.
---

# Progressive LoRA Pruning Loop

Use this skill when recovering or implementing the central LoRAPrune algorithm after you have a LoRA-guided element importance function and a structured group masker. Do not use it as evidence for LoRAPrune unless it performs an actual optimizer step on LoRA parameters and records a trace.

## Inputs

- Calibration examples `(x, y)` or equivalent model batches.
- Frozen base weights or module `W0`.
- Trainable LoRA matrices `B` and `A`.
- Learning rate, iteration count, moving-average coefficient, and target structured sparsity.

## Outputs

- Updated LoRA parameters.
- Final group mask and per-iteration mask history.
- Training trace with loss before/after, raw group scores, moving-average scores, and prune count.
- Validator-compatible `params_before`, `params_after`, and `optimizer_step_executed` fields.

## Workflow

1. Start with all groups retained and moving-average scores initialized to zero.
2. For each calibration step, compute masked LoRA predictions and loss.
3. Backpropagate or analytically compute gradients only for LoRA parameters.
4. Compute LoRA-guided importance and aggregate it by structured group.
5. Update `Gbar_t = lambda * Gbar_{t-1} + (1-lambda) * Ghat_t`.
6. Apply an optimizer update to `A` and `B`.
7. Increase the prune count according to the progressive schedule and update the group mask.
8. Save enough trace data to prove the recurrence, optimizer change, and nondecreasing sparsity.

## Validation

The included deterministic tests run a tiny regression loop and check optimizer execution, monotonic pruning, and the moving-average recurrence.

```bash
python /share/project/yuyang/workspace/Paper2Skills/Distiller/skills/module-to-skill/scripts/validate_skill_tree.py <this_skill_dir> --run-tests
```

## Limitations

The script uses a small list-based linear model for bounded recovery. For real LLMs, replace the analytic gradient code with framework autograd while retaining the same trace fields and LoRA-only-gradient boundary.
