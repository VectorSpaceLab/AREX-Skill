# Workflows

## 1) Pick the gradient path

| Situation | Pick | Why |
| --- | --- | --- |
| Exact analytic expectation is available and the backend is `None` | `Adjoint` | Fastest exact gradient path in TFQ, but only for analytic expectation calculations. |
| Sampled or noisy expectation is required | `ParameterShift` | Standard built-in differentiator for parameterized circuits that also works with sampled expectation ops. |
| You want a finite-difference baseline | `ForwardDifference` or `CentralDifference` | Both are `LinearCombination` presets; `ForwardDifference` is one-sided, `CentralDifference` is symmetric. |
| You need custom coefficients or perturbation points | `LinearCombination` | Lets you define the gradient rule directly, as long as the perturbation list is valid. |
| You need a specialized backend-aware rule | subclass `Differentiator` | Implement `get_gradient_circuits`, or override `differentiate_analytic` / `differentiate_sampled` only when necessary. |

## 2) Tiny gradient smoke

Use a one-qubit smoke case before you move to larger circuits.

1. Build a circuit like `cirq.Circuit(cirq.Y(qubit) ** sympy.Symbol('alpha'))`.
2. Measure `cirq.X(qubit)`.
3. Attach the differentiator with `generate_differentiable_op(...)`.
4. Watch a `1 x 1` float tensor with `tf.GradientTape` and confirm the result is finite and close to the analytic reference.

The source tests use this exact style of smoke for `ParameterShift`, `ForwardDifference`, `CentralDifference`, and `Adjoint`-backed analytic checks.

### Adjoint-specific smoke

- Use only an analytic expectation op.
- Keep the backend at `None`.
- If you need sampling or noise, switch to another differentiator instead of trying to recover `Adjoint`.

## 3) Tiny optimizer loops

### `rotosolve_minimize`

Use when the objective is sinusoid-like or a linear combination of quantum measurement expectations.

- Start from a real 1-D parameter vector.
- Good smoke objective: `lambda x: tf.reduce_sum(tf.sin(x) * coefficient)`.
- Expect the optimizer to converge on the sinusoid example and fail to converge on a non-sinusoidal objective such as a quadratic.
- If it does not converge, the objective probably violates the rotosolve assumptions.

### `spsa_minimize`

Use when the objective is noisy, stochastic, or only approximately smooth.

- Start from a real 1-D parameter vector.
- Good smoke objectives: quadratics or noisy sinusoid sums.
- Use `blocking=True` only when you want to reject updates that worsen the objective beyond `allowed_increase`.
- Use `seed=` when you need repeatable tiny checks.

### Keras-shaped objectives

When the objective comes from a model helper, flatten trainable variables into a 1-D vector, assign them back inside the objective, and reduce any vector-valued loss to a scalar before calling the optimizer.

## 4) Custom differentiators

1. Subclass `Differentiator`.
2. Implement `get_gradient_circuits` for the standard circuit-batch path.
3. Use `generate_differentiable_op` to attach the differentiator to an expectation op.
4. Call `refresh()` before attaching the same differentiator to another op.
5. If the custom rule only applies to one backend style, make that constraint explicit in the troubleshooting note.

## 5) Shared smoke helper

Before a deeper gradient or optimizer investigation, run `python scripts/tfq_smoke_check.py --quick --differentiators` from the root `tensorflow-quantum` skill directory to confirm the public package imports and a tiny expectation/gradient path still work.
