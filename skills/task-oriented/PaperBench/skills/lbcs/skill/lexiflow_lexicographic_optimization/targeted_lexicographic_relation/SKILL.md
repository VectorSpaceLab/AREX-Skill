---
name: targeted_lexicographic_relation
description: Compare two objective vectors under target-aware equality and strict preference while preserving vanilla lexicographic tie breaking.
---

# Targeted Lexicographic Relation

Use this skill when implementing or auditing the LexiFlow paper mechanism for bounded recovery or reusable optimization tooling. Do not use it as a generic scalarized multi-objective optimizer; it assumes priority-ordered minimization objectives, optional goals, and non-negative tolerances.

## Inputs
- Candidate objective vector
- Incumbent objective vector
- Current target vector z_H

## Outputs
- Target-aware equality boolean
- Target-aware strict preference boolean
- Vanilla lexicographic comparison result

## Workflow
1. Confirm objective values are ordered by priority and are minimization values.
2. Preserve the paper mechanism described in the module document rather than replacing it with weighted scalarization.
3. Run the companion script or import its pure functions for deterministic behavior.
4. Save command outputs, trace files, and metrics when the skill is used in a recovery experiment.

## Validation
Run `python scripts/targeted_lexicographic_relation.py --self-test` when available, then run the bundled test command through the Distiller skill-tree validator.

## Limitations
This generated skill is source-repository independent and derived from the paper text. Full HPO benchmark reproduction still requires real model training stacks and datasets; the included scripts are intended for deterministic mechanism validation and bounded proxy recovery.
