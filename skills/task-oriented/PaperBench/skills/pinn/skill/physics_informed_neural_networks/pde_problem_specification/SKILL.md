---
name: pde_problem_specification
description: Define auditable PINN PDE recovery items with separate observations, collocation points, coefficients, provenance, and target metadata.
---

# PDE Problem Specification

Use this skill when preparing a Physics-Informed Neural Network recovery item. It is appropriate for continuous-time PINN experiments where observations supervise the solution and collocation points enforce the PDE residual. Do not use it to run optimization or compute residual derivatives.

## Inputs
- PDE name and coefficient dictionary.
- Time and space domain bounds.
- Observation and collocation point counts.
- A deterministic reference function or sampled reference values.
- Provenance label: `synthetic`, `resource_derived`, or `benchmark_style`.

## Outputs
- JSON-compatible item containing `observations`, `collocation_points`, `coefficients`, `domain`, `target`, and provenance fields.
- Validation summary confirming nonempty point sets and bounded coordinates.

## Workflow
1. Normalize the PDE name, domain, counts, and coefficients.
2. Generate observation points separately from collocation points.
3. Evaluate the supplied reference function only for observations.
4. Record target metadata from the module plan without training outputs.
5. Validate count, bound, and role-separation invariants before passing the item to training.

## Validation
Run `python tests/test_problem_spec.py` from this skill directory, or validate the whole tree with the Distiller skill validator using `--run-tests`.

## Limitations
This skill builds small recovery items. Full benchmark loading may wrap this contract, but recovery must still record concrete resource provenance when benchmark files are used.
