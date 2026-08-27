---
name: differentiation-and-optimizers
description: "Choose and use TensorFlow Quantum differentiators and tiny
  optimizers for gradients and parameter search loops."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---
# differentiation-and-optimizers

Use this sub-skill when the user needs to pick, attach, or troubleshoot TensorFlow Quantum differentiators, or when they need a small optimizer loop for a quantum-circuit objective.

## Route first

- Need circuit tensor conversion, expectation/sampling ops, backend choice, or noisy execution details? Route to [tensor-ops-and-execution](../tensor-ops-and-execution/SKILL.md).
- Need to build PQC, ControlledPQC, Expectation, or SampledExpectation layer wiring? Route to [keras-quantum-layers](../keras-quantum-layers/SKILL.md).
- Need package import, version, or smoke checks before gradient work? Route to the parent skill at [../../SKILL.md](../../SKILL.md) and its shared smoke helper.
- Need datasets or notebook recipes? Route to [datasets-and-tutorials](../datasets-and-tutorials/SKILL.md).

## Stay here for

- choosing between analytic, sampled, or custom gradients;
- using `tfq.differentiators.Differentiator` and `generate_differentiable_op`;
- the built-ins `ParameterShift`, `ForwardDifference`, `CentralDifference`, `LinearCombination`, and `Adjoint`;
- parsing parameter-shift programs with `parameter_shift_util.parse_programs`;
- tiny `rotosolve_minimize` and `spsa_minimize` loops over real-valued parameter vectors.

## Quick choices

1. **Analytic expectation and `backend=None`**: prefer `Adjoint` for the fastest exact gradient path.
2. **Sampled or noisy expectation**: prefer `ParameterShift` first; use `ForwardDifference` or `CentralDifference` when you want finite-difference behavior.
3. **Custom shift formula or experimental rule**: use `LinearCombination`, or subclass `Differentiator` and implement `get_gradient_circuits`.
4. **Sinusoid-like objective with coordinate updates**: use `rotosolve_minimize`.
5. **Noisy or stochastic objective**: use `spsa_minimize`.
6. **Signature mismatch**: `generate_differentiable_op` wants exactly one op, and the analytic/sampled callable signature must match the op type.
7. **Reuse the same differentiator with another op**: call `refresh()` first.

## Reference map

- API contracts, defaults, and validation rules: [references/api-reference.md](references/api-reference.md)
- Choice guide and tiny gradient/optimizer workflows: [references/workflows.md](references/workflows.md)
- Error messages and recovery steps: [references/troubleshooting.md](references/troubleshooting.md)
- Shared smoke helper in the parent skill: [../../scripts/tfq_smoke_check.py](../../scripts/tfq_smoke_check.py)

## Scope guardrails

- Keep guidance at the differentiator/optimizer layer; do not expand into model architecture or training pipelines.
- Do not describe backend selection beyond what the differentiator contract needs.
- Do not promise `Adjoint` for sampled, noisy, or non-`None` backends.
- Empty programs, empty symbol lists, or empty symbol-value tensors intentionally return zeros-like gradients.
- Optimizer notes should stay about objective shape, convergence, and tiny loops.
