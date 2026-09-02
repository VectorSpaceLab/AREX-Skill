---
name: cross_task_split_protocol
description: Create task-level seen and unseen splits with leakage diagnostics for Natural Instructions style generalization experiments.
---

# Cross Task Split Protocol

Use this skill when reconstructing the BART0/Natural Instructions cross-task generalization workflow without relying on the original paper repository. Do not use it for unrelated instruction-following papers unless the task uses a Natural-Instructions-style schema, task-level held-out evaluation, and generation metrics.

## Inputs
- Paper-derived module document and `module_plan.json`.
- Small task records or instruction items supplied by the current recovery attempt.
- Optional output paths for deterministic JSON artifacts.

## Outputs
- Deterministic JSON or Python return values that can be consumed by downstream recovery scripts.
- Validation evidence from the included tests.

## Workflow
1. Read the current attempt inputs and keep source use inside the allowed recovery boundary.
2. Apply the module contract exactly as described by the paper-derived module document.
3. Write machine-readable artifacts when a CLI output path is provided.
4. Cross-check downstream consumers with tests before accepting recovery evidence.

## Validation
Run `python <distiller>/module-to-skill/scripts/validate_skill_tree.py <skill_dir> --run-tests` from any working directory. The included tests are standard-library compatible and do not require the original source repository.

## Limitations
This skill preserves a reusable mechanism from the paper but does not by itself reproduce full BART-base training on all 61 Natural Instructions tasks. Full recovery requires a resolved dataset and model runtime; reduced recovery must remain explicitly marked as proxy evidence.
