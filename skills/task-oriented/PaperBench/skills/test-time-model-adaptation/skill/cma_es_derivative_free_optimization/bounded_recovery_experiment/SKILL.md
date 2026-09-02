---
name: bounded_recovery_experiment
description: Run a bounded CMA-ES proxy experiment that validates sampling, selection, CSA, and covariance adaptation evidence.
---

# Bounded CMA-ES Recovery Experiment

Use this skill when full-scale paper reproduction is unavailable but soft-mode recovery permits a declared, executable, mechanism-faithful proxy. It should call the parameter, sampling, and adaptation skills rather than duplicate their logic silently.

## Inputs
- Paths to generated CMA-ES module skills.
- Attempt directory with module plan and runtime handoff.
- A deterministic objective specification and generation budget.

## Outputs
- Recovery metrics, generated objective item, optimization trace, skill invocation evidence, and mechanism checks.

## Workflow
1. Load the module plan target and runtime handoff.
2. Construct a small rotated ellipsoid objective as a black-box callable.
3. Initialize CMA-ES defaults, sample/rank offspring, update mean, CSA, and covariance for a bounded number of generations.
4. Save before/after losses, parameter changes, covariance diagnostics, and source-boundary evidence.
5. Run the Distiller recovery experiment gate.

## Validation
Run the recovery harness and validate the attempt with `validate_recovery_experiment.py`.

## Limitations
The output is a reduced/proxy recovery, not a full benchmark claim from the paper.
