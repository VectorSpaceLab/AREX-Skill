---
name: mir_recovery_evaluation
description: Run bounded MIR recovery experiments and emit accuracy, forgetting, traces, and mechanism evidence.
---

# MIR Recovery and Evaluation Harness

Use this skill after MIR module skills exist and a runtime handoff has been produced. It orchestrates a small online continual-learning experiment, invokes or cross-checks the generated memory and scoring skills, and writes recovery artifacts suitable for validation.

## Inputs
- Attempt directory containing `module_plan.json` and `environment/runtime_handoff.json`.
- Generated skills root containing online memory, virtual-update interference, and optional latent MIR helpers.
- Output directory under `recovery/`.
- Fixed seed and reduced/proxy declaration when full benchmark recovery is blocked.

## Outputs
- `recovery_result.json` with paper target metadata, numeric metrics, commands, and mechanism checks.
- `logs/training_trace.json` with updates, selected replay examples, losses, and parameters.
- `logs/generated_skill_invocations.json` listing generated skill usage.
- `source_manifest.json` listing allowed sources.

## Workflow
1. Load `module_plan.json.fast_recovery_target` without changing dataset, metric, or target metadata.
2. Build a deterministic non-iid stream with three small binary tasks.
3. Run MIR and a baseline selector using the generated online memory and virtual-update scoring contracts.
4. Evaluate final accuracy and forgetting from task-level histories.
5. Cross-check the latent MIR helper with a tiny probability-vector fixture when no real generator is available.
6. Save all JSON artifacts and report proxy limitations explicitly.

## Validation
Run the script directly in a recovery directory, then run the Distiller recovery validator. Included unit tests exercise metric computation and artifact structure without using external packages.

## Limitations
This skill provides a reduced proxy harness for bounded soft-mode recovery. It does not claim to reproduce the paper's full MNIST, CIFAR-10, or MiniImagenet multi-seed results.
