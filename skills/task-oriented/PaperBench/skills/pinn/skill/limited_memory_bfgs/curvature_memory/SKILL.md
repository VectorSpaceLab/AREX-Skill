---
name: curvature_memory
description: Maintain bounded positive-curvature L-BFGS correction memory for large-scale quasi-Newton optimization.
---

# Curvature Memory

Use this skill when implementing or auditing an L-BFGS optimizer that must store only a small number of recent BFGS correction pairs. Do not use it for dense BFGS updates or constrained optimization logic.

## Inputs
- Previous and next iterates `x_old`, `x_new`.
- Previous and next gradients `g_old`, `g_new`.
- Existing ordered memory of `(s, y)` pairs.
- Positive integer memory limit `m`.

## Outputs
- A FIFO memory list containing at most `m` valid pairs.
- Each valid pair satisfies `s^T y > tolerance`.

## Workflow
1. Compute `s = x_new - x_old` and `y = g_new - g_old`.
2. Validate matching vector dimensions and memory limit.
3. Reject non-positive or tiny curvature pairs.
4. Append valid pairs and drop oldest entries until the memory length is bounded.
5. Preserve oldest-to-newest order for downstream two-loop recursion.

## Validation
Run `python tests/test_curvature_memory.py` or validate this skill tree with the Paper2Skills module-to-skill validator.

## Limitations
This skill manages only correction-pair state. It does not choose step lengths or compute search directions.
