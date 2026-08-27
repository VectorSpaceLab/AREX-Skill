---
name: differentiation-core
description: "Routes scalar and array differentiation, higher-order derivatives,
  and gradient checking for Autograd's core AD operators."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Differentiation Core

Use this sub-skill when a task is about Autograd's core differentiation operators: scalar gradients, Jacobians, directional derivatives, Hessians, VJP/JVP pullbacks, generalized Gauss-Newton products, complex holomorphic derivatives, checkpointing, or numerical gradient checks.

## Trigger examples

- "I need `grad` or `value_and_grad` for a scalar loss."
- "I need `jacobian` or `elementwise_grad` for a vector-valued output."
- "I need a Hessian-vector product, `make_vjp`, or `make_jvp`."
- "I want to verify a derivative with `check_grads`."
- "My function has `if`/`while` branches and I want to know whether Autograd can still differentiate it."

## Read first

- `references/api-reference.md` for operator selection, return conventions, and mode relationships.
- `references/workflows.md` for scalar-loss, vector-output, higher-order, complex, and gradient-checking recipes.
- `references/troubleshooting.md` for scalar-output errors, argnum confusion, shape mismatches, holomorphic warnings, and checkpoint tradeoffs.
- `scripts/differentiation_smoke.py` for a runnable smoke that exercises the core operators without plotting.

## Boundary routing

- Wrapper behavior, NumPy/SciPy support, `A.dot(B)` / in-place / container pitfalls, and optional dependency questions belong in `../numpy-scipy-primitives/SKILL.md`.
- `primitive`, `defvjp`, `defjvp`, and custom VJP/JVP mechanics belong in `../extend-primitives/SKILL.md`.
- Optimizer wiring, flattening, and `fixed_point` belong in `../optimization-workflows/SKILL.md`.

## How to choose an operator

- Use reverse mode when the output is a real scalar and the input is large: `grad`, `value_and_grad`, or `make_vjp`.
- Use forward mode when the input is scalar or you want one directional derivative: `deriv` or `make_jvp`.
- Use `jacobian` when you need the full output-to-input sensitivity tensor.
- Use `elementwise_grad` when the function is real-valued and elementwise so the Jacobian is diagonal or column-summed.
- Use `hessian`, `hessian_tensor_product`, `hessian_vector_product`, or `make_ggnvp` when you need curvature without writing the matrix explicitly.
- Use `holomorphic_grad` only for complex-holomorphic functions.
- Use `checkpoint` when the function is deep and memory is the bottleneck.
- Use `grad_and_aux` when the function returns a scalar loss plus extra side information.

## Core rules

- `grad` and `value_and_grad` require a real scalar output.
- `jacobian` works on scalar or array outputs and returns a tensor with output shape first and input shape last.
- `elementwise_grad` is not a general Jacobian helper; it returns the column-sum/diagonal behavior used for elementwise real functions.
- Control flow is transparent to Autograd: the executed Python path matters, not the unexecuted branches.
- `make_vjp` exposes the reverse-mode pullback; `make_jvp` exposes the forward-mode pushforward.
- Higher-order derivatives are usually formed by composing these operators.
- `grad_and_aux` differentiates only the first output and returns the auxiliary payload unchanged.
- `checkpoint` recomputes forward intermediates during the backward pass to trade time for memory.

## Typical route

1. Start with `grad` for a scalar loss.
2. If the output is vector-valued, switch to `jacobian` or `elementwise_grad`.
3. If you need both the value and the gradient, use `value_and_grad`.
4. If you need a directional derivative, use `deriv` or `make_jvp`.
5. If you need a pullback from output cotangents, use `make_vjp`.
6. If you need curvature information, use `hessian` or a Hessian-vector product helper.
7. If the function is complex-valued and holomorphic, use `holomorphic_grad`.
8. If the function is deep and memory-bound, wrap it with `checkpoint`.
9. Validate the chosen operator with `check_grads` before trusting a new workflow.

## Reliability notes

- Use `check_grads` for a single function and `combo_check` when you want the same assertion to cover several positional or keyword combinations.
- When a derivative shape looks wrong, inspect the primal input and output shapes before changing the operator.
- When the function is intentionally branchy, choose a test point away from the branch threshold.
- When the failure message names a missing VJP or JVP rule for a primitive, route to `../extend-primitives/SKILL.md` instead of trying to solve it here.

## What this sub-skill does not cover

- Built-in NumPy/SciPy wrapper behavior and compatibility traps live in `../numpy-scipy-primitives/SKILL.md`.
- Defining new primitives or VJP/JVP rules lives in `../extend-primitives/SKILL.md`.
- Optimizer flattening and structured parameter updates live in `../optimization-workflows/SKILL.md`.

## Fastest sanity check

Run `scripts/differentiation_smoke.py` when you need a quick end-to-end check that the bundled differentiation guidance still matches the installed package.
