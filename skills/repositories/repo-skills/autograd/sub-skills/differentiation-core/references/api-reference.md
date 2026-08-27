# API Reference

## Purpose

This reference condenses the verified differentiation operators, return conventions, and mode relationships behind this sub-skill. It is distilled from the package source, installed-package behavior, and the repository's differentiation tests and examples.

## When to read

Read this when you already know you need an Autograd derivative helper but want the exact operator, return shape, and failure surface before writing code.

## Wrapper semantics

`grad`, `jacobian`, `elementwise_grad`, `deriv`, `value_and_grad`, `make_vjp`, `make_jvp`, and `holomorphic_grad` are n-ary wrappers around unary differentiation kernels. They accept the same positional and keyword arguments as the target function, plus `argnum`, which may be a single positional index or an ordered tuple/list of positional indices.

### Return conventions

- `make_vjp(fun)(x)` returns `(pullback, primal_output)`.
- `make_jvp(fun)(x)(v)` returns `(primal_output, jvp)`.
- `value_and_grad(fun)(x)` returns `(primal_output, grad)`.
- `grad_and_aux(fun)(x)` returns `(grad, aux)`.

## Primary operators

| Operator | Mode / return | Use when | Key notes |
| --- | --- | --- | --- |
| `grad(fun, argnum=0)` | reverse mode; gradient only | You need the gradient of a real scalar-output function | Raises `TypeError` if the output is not a real scalar |
| `value_and_grad(fun, argnum=0)` | reverse mode; `(value, grad)` | You want the scalar objective and its gradient in one pass | Same scalar-output requirement as `grad` |
| `jacobian(fun, argnum=0)` | full Jacobian tensor | The function output is vector- or array-valued | Output shape comes first, input shape last |
| `elementwise_grad(fun, argnum=0)` | Jacobian column-sum / diagonal behavior | The function is real-valued and elementwise | Not a full Jacobian helper |
| `deriv(fun, argnum=0)` | forward-mode derivative | You want a directional derivative for a scalar input or a single forward sweep | Forward-mode counterpart to `grad` for scalar inputs |
| `make_vjp(fun, argnum=0)` | reverse-mode pullback | You need to reuse a VJP or inspect output cotangents | Returns a callable pullback plus the primal output |
| `make_jvp(fun, argnum=0)` | forward-mode pushforward | You need a JVP or a directional derivative through a vector-valued function | Returns a callable that accepts the tangent vector |
| `hessian(fun, argnum=0)` | nested Jacobian | You need the exact Hessian of a scalar-output function | Equivalent to `jacobian(jacobian(fun))` |
| `hessian_tensor_product(fun, argnum=0)` | exact Hessian contraction | You want `H @ v` or a tensor contraction without materializing the whole matrix | `hessian_vector_product` is an alias |
| `make_ggnvp(f, g=..., f_argnum=0)` | generalized Gauss-Newton-vector product | You want curvature-like information for a model output | Default `g` gives the `JᵀJv` style product |
| `grad_and_aux(fun, argnum=0)` | `(grad, aux)` | You want a gradient plus nested side information | Only the first output is differentiated |
| `holomorphic_grad(fun, argnum=0)` | complex gradient | The function is holomorphic and you want the complex derivative | Warns when the input is not complex |
| `checkpoint(fun)` | recomputation wrapper | The function is deep and memory is the bottleneck | Saves memory by replaying forward work during backprop |

## Mode relationship

Reverse mode is the right mental model for `grad`, `value_and_grad`, and `make_vjp`: compute one scalar loss, then push a cotangent backward through the executed graph.

Forward mode is the right mental model for `deriv` and `make_jvp`: seed an input tangent, then propagate it forward alongside the primal value.

That means:

- `grad` is the scalar-output special case of reverse mode.
- `deriv` is the scalar-input special case of forward mode.
- `jacobian` is the matrix/tensor version of repeated VJP or JVP sweeps.
- `hessian`, `hessian_tensor_product`, and `make_ggnvp` are higher-order compositions of the same primitives.

## Gradient checking helpers

`autograd.test_util` provides two practical validators for this sub-skill:

- `check_grads(fun, modes=['fwd', 'rev'], order=2)(*args)` checks first- and higher-order derivatives numerically.
- `combo_check(fun)` sweeps candidate positional and keyword combinations and runs `check_grads` for each one.

Use them on tiny, deterministic examples before you trust a new differentiable workflow.

## Complex-number reminder

Autograd's complex convention is deliberately limited:

- `grad` and `value_and_grad` require a real scalar output.
- `holomorphic_grad` is for holomorphic complex functions.
- For non-holomorphic complex functions, split the real and imaginary parts explicitly.

## Shapes to remember

- `jacobian(fun)(x)` has shape `output_shape + input_shape`.
- `hessian(fun)(x)` has shape `input_shape + input_shape`.
- `hessian_tensor_product(fun)(x, v)` expects `v` to live in the same space as the differentiated input.
- `make_ggnvp(f)(x)(v)` expects a tangent in input space, not output space.
