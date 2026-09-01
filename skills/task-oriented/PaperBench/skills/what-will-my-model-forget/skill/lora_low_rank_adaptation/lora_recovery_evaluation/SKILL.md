---
name: lora_recovery_evaluation
description: Assemble and validate a soft-mode reduced LoRA recovery with executable mechanism evidence and source-boundary logs.
---

# LoRA Recovery Evaluation Harness

Use this skill after LoRA module skills and runtime probes are available. It packages a reduced or full recovery into auditable artifacts: experiment plan, command log, generated skill invocation log, source manifest, recovery result, and validator output. Do not use the original implementation repository during recovery.

## Inputs
- Attempt directory with `module_plan.json` and `environment/runtime_handoff.json`.
- Generated skills root containing the LoRA layer, freezing, and training-step skills.
- Recovery mode and the declared full or proxy target.

## Outputs
- Executable recovery command evidence.
- Numeric metric aligned with `module_plan.fast_recovery_target`.
- Mechanism checks for frozen weights, low-rank update, optimizer step, checkpoint filtering, and merge equivalence.

## Workflow
1. Read the module plan target and runtime handoff first.
2. If full torch/transformers recovery is unavailable, declare the soft-mode reduced target before running the harness.
3. Invoke generated skill scripts rather than duplicating their contracts silently.
4. Save training trace, generated data item, command log, source manifest, and recovery result.
5. Run the official recovery validator and treat failures as refinement input.

## Validation
Run `python scripts/evaluate_recovery.py --attempt-dir <attempt> --skills-root <skills>`. The command calls the reduced training skill and reports a numeric loss-reduction ratio.

## Limitations
This harness validates mechanism fidelity for reduced recovery. It cannot certify paper-table metrics without real packages, pretrained models, and benchmark datasets.
