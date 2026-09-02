---
name: circuit_recovery_harness
description: Build and validate bounded mechanism-faithful recovery artifacts for Transformer Circuits proxy experiments.
---

# Circuit Recovery Harness

Use this skill to assemble a recovery experiment for a conceptual mechanistic interpretability paper when no original trained model is available. It should orchestrate generated circuit-analysis skills, write auditable command and invocation logs, and declare proxy status honestly. Do not use it to bypass module skills with duplicated one-off logic; the harness must call or cross-check the generated scripts.

## Inputs

- Attempt directory and module plan.
- Generated skill root containing the circuit skills.
- Runtime handoff that records full-runtime blockers and permitted proxy recovery.
- A deterministic synthetic or real attention-only circuit item.

## Outputs

- Experiment plan and source manifest.
- Generated data item and optional training/mechanism trace.
- Recovery result with numeric metric and mechanism checks.
- Experiment command log and generated skill invocation log.

## Workflow

1. Read the module-plan recovery target and runtime handoff.
2. If trained paper models are unavailable, declare a soft-mode proxy.
3. Construct a repeated-token circuit item.
4. Invoke logit-lens, QK/OV expansion, path-expansion, and induction-detector scripts.
5. Aggregate metrics and mechanism booleans.
6. Run the recovery experiment validator.

## Validation

The smoke test checks that required result fields exist and that proxy mechanism checks are not empty.

## Limitations

This skill creates recovery evidence, not a full-scale paper reproduction. Full trained-model recovery must replace the synthetic item when the relevant model assets become available.
