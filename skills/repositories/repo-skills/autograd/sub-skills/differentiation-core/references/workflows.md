# Workflows

## Purpose

This reference turns the operator map into small, reusable differentiation recipes. The examples are intentionally tiny so you can adapt them without reopening the source repository.

## When to read

Read this when you know the general differentiation mode you need, but you want a concrete pattern for control flow, higher-order derivatives, complex values, or gradient checking.

## 1) Scalar loss with control flow

Use `grad`, `value_and_grad`, or `deriv` when the function returns a real scalar and the executed Python path is the one you want differentiated.

```python
import autograd.numpy as np
from autograd import deriv, grad, value_and_grad
from autograd.test_util import check_grads


def taylor_sine(x):
    ans = currterm = x
    i = 0
    while np.abs(currterm) > 1e-3:
        currterm = -currterm * x**2 / ((2 * i + 3) * (2 * i + 2))
        ans = ans + currterm
        i += 1
    return ans

x = 0.3
value, g = value_and_grad(taylor_sine)(x)
assert np.allclose(g, grad(taylor_sine)(x))
assert np.allclose(g, deriv(taylor_sine)(x))
check_grads(taylor_sine)(x)
```

Notes:

- Loops and branches are fine as long as the executed path is differentiable.
- If the loop threshold is too close to the test point, `check_grads` may fail because the perturbation changes the number of iterations.
- This is the cleanest way to route requests such as "differentiate my branchy scalar objective" or "does Autograd handle while loops?"

## 2) Vector output and Jacobians

Use `jacobian` when the output is a vector or array and you need the full sensitivity tensor. Use `elementwise_grad` when the function is real-valued and elementwise.

```python
import autograd.numpy as np
from autograd import elementwise_grad, grad, jacobian


def tanh(x):
    return (1.0 - np.exp(-2 * x)) / (1.0 + np.exp(-2 * x))


def vector_fun(x):
    return np.array([np.tanh(x[0] + x[1]), x[0] * x[1], x[0] - x[1]])

x = np.array([0.2, -0.4])
vec = np.array([0.1, -0.3, 0.7])

# Diagonal / column-sum behavior for an elementwise scalar function.
assert np.allclose(elementwise_grad(tanh)(vec), grad(lambda z: np.sum(tanh(z)))(vec))

# Full Jacobian for a vector-valued map.
J = jacobian(vector_fun)(x)
assert J.shape == (3, 2)
```

Notes:

- `jacobian(fun)(x)` has shape `output_shape + input_shape`.
- If you expected a 2D matrix but received a higher-rank tensor, flatten only for display; do not change the mathematical meaning.
- `grad` is the scalar-output special case of `jacobian`.

## 3) Reverse- and forward-mode comparison

Use `make_vjp` for reverse-mode pullbacks and `make_jvp` for forward-mode pushforwards. This is the best pattern when you want to compare an automatic directional derivative against an explicit Jacobian contraction.

```python
import autograd.numpy as np
from autograd import grad, jacobian, make_jvp, make_vjp

x = np.array([0.2, -0.4])
v = np.array([1.5, -0.5])

pullback, primal = make_vjp(vector_fun)(x)
primal2, tangent = make_jvp(vector_fun)(x)(v)
J = jacobian(vector_fun)(x)

assert np.allclose(primal, primal2)
assert np.allclose(tangent, np.dot(J, v))
assert np.allclose(pullback(np.ones_like(primal)), grad(lambda z: np.sum(vector_fun(z)))(x))
```

Notes:

- Reverse mode is usually the right choice for one scalar loss with many inputs.
- Forward mode is usually the right choice for one input direction or a scalar input.
- If you only need one directional derivative, `make_jvp` avoids constructing the full Jacobian.

## 4) Curvature and generalized Gauss-Newton

Use `hessian`, `hessian_tensor_product`, `hessian_vector_product`, and `make_ggnvp` when you need second-order information.

```python
import autograd.numpy as np
from autograd import hessian, hessian_tensor_product, hessian_vector_product, jacobian, make_ggnvp

A = np.array([[1.0, -2.0], [0.5, 1.5]])
B = np.array([[1.0, -2.0], [0.5, 1.5], [-0.7, 0.25]])

scalar_quadratic = lambda z: np.sum(np.tanh(np.dot(A, z)) ** 2)
f = lambda z: np.tanh(np.dot(B, z))

x = np.array([0.2, -0.4])
v = np.array([1.5, -0.5])

H = hessian(scalar_quadratic)(x)
hvp = hessian_tensor_product(scalar_quadratic)(x, v)
assert np.allclose(hvp, np.dot(H, v))
assert np.allclose(hessian_vector_product(scalar_quadratic)(x, v), hvp)

J = jacobian(f)(x)
ggnvp = make_ggnvp(f)(x)(v)
assert np.allclose(ggnvp, np.dot(J.T, np.dot(J, v)))
```

Notes:

- `hessian_vector_product` is just an alias for `hessian_tensor_product`.
- `make_ggnvp` is useful when a full Hessian would be too expensive but a curvature-like vector product is enough.
- For shape debugging, confirm that the tangent/vector argument lives in the same space as the differentiated input.

## 5) Complex values, aux payloads, and checkpointing

Use `holomorphic_grad` for holomorphic complex functions, `grad_and_aux` when you need side information, and `checkpoint` when memory matters more than recomputation.

```python
import warnings
import autograd.numpy as np
from autograd import checkpoint, grad, grad_and_aux, holomorphic_grad


def complex_fun(z):
    return z * (1.0 + 0.2j)


def scalar_with_aux(x):
    return np.sum(np.tanh(x)), {
        "meta": {"shape": x.shape, "stats": (np.sum(x), np.mean(x))},
        "trace": (x[0], x[-1]),
    }


def deep_chain(x):
    for _ in range(5):
        x = np.tanh(x + 0.1)
    return np.sum(x)

x = np.array([0.1, 0.2, -0.3])

with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    real_grad = holomorphic_grad(complex_fun)(1.0)
assert any("Input to holomorphic_grad is not complex" in str(item.message) for item in caught)
assert np.allclose(real_grad, 1.0)
assert np.allclose(holomorphic_grad(complex_fun)(1.0 + 0.0j), 1.0 + 0.2j)

grad_val, aux = grad_and_aux(scalar_with_aux)(x)
assert aux["meta"]["shape"] == x.shape
assert np.allclose(grad_val, grad(lambda z: np.sum(np.tanh(z)))(x))

checkpointed = checkpoint(deep_chain)
assert np.allclose(checkpointed(x), deep_chain(x))
assert np.allclose(grad(checkpointed)(x), grad(deep_chain)(x))
```

Notes:

- `holomorphic_grad` warns on non-complex input; that is expected behavior, not a bug.
- `grad_and_aux` differentiates only the first output, even if the aux payload is nested.
- `checkpoint` should produce the same values and gradients as the original function, but it may run more slowly because the forward pass is replayed during backprop.

## 6) Gradient-checking pattern

Use `check_grads` first, then `combo_check` when you want the same validation across multiple argument combinations.

```python
from autograd.test_util import check_grads, combo_check

check_grads(taylor_sine, modes=["rev"], order=2)(0.3)
combo_check(vector_fun)([np.array([0.1, 0.2]), np.array([0.3, -0.1])])
```

Practical advice:

- Stay away from branch thresholds when you test a branchy scalar loss.
- If `check_grads` fails on a control-flow-heavy function, first check whether the executed path changed under perturbation.
- Use `combo_check` when a function has several positional or keyword combinations that should all obey the same derivative contract.
