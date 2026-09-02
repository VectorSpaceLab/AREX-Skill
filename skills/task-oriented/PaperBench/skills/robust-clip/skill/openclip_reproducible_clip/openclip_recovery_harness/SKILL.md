---
name: openclip_recovery_harness
description: Run an auditable reduced OpenCLIP scaling-law recovery by invoking generated skills and producing validator-compatible recovery artifacts.
---

# OpenCLIP Reduced Recovery Harness

Use this skill when full LAION-scale OpenCLIP training is infeasible but soft-mode recovery permits a declared proxy that must exercise the paper mechanism.

## Inputs
- Attempt directory with `module_plan.json` and `environment/runtime_handoff.json`.
- Generated skill root containing the scale protocol, contrastive objective, zero-shot/retrieval evaluation, and power-law scaling skills.

## Outputs
- Recovery result JSON with target metadata copied from `module_plan.json`.
- Mechanism checks for each generated core module.
- Invocation and command evidence.

## Workflow
1. Create deterministic synthetic paired embeddings and scale points.
2. Invoke generated skill scripts rather than duplicating their logic silently.
3. Check contrastive loss, zero-shot accuracy, retrieval Recall@1, and power-law R2.
4. Mark the run as proxy and reduced; do not claim full model training.
5. Save source and invocation evidence for the Distiller recovery validator.

## Validation
Run `python tests/test_recovery_harness.py`.

## Limitations
This harness validates mechanism faithfulness only. It cannot substitute for full LAION-2B pretraining metrics.

## Cycle 4 API stress check

Run `python scripts/stress_checks.py --check api_imports --attempt-dir <attempt_dir> --skills-root <generated_skills_root> --output <json>` to verify all generated helper APIs import cleanly.
