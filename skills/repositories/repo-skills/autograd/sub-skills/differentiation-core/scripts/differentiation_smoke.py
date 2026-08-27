#!/usr/bin/env python3
"""Small smoke for Autograd's core differentiation operators.

This script exercises scalar and vector differentiation, higher-order helpers,
gradient checking, complex holomorphic derivatives, auxiliary outputs, and
checkpointing without plotting or touching the source repository.
"""

import warnings

import autograd.numpy as np
import autograd.numpy.random as npr
from autograd import (
    checkpoint,
    deriv,
    elementwise_grad,
    grad,
    grad_and_aux,
    hessian,
    hessian_tensor_product,
    hessian_vector_product,
    holomorphic_grad,
    jacobian,
    make_ggnvp,
    make_jvp,
    make_vjp,
    value_and_grad,
)
from autograd.test_util import check_grads

npr.seed(0)


def tanh(x):
    return (1.0 - np.exp(-2 * x)) / (1.0 + np.exp(-2 * x))


def taylor_sine(x):
    ans = currterm = x
    i = 0
    while np.abs(currterm) > 1e-3:
        currterm = -currterm * x**2 / ((2 * i + 3) * (2 * i + 2))
        ans = ans + currterm
        i += 1
    return ans


def vector_fun(x):
    return np.array([np.tanh(x[0] + x[1]), x[0] * x[1], x[0] - x[1]])


def scalar_with_aux(x):
    return np.sum(np.tanh(x)), {
        "meta": {"size": np.array(float(x.size)), "stats": (np.sum(x), np.mean(x))},
        "trace": (x[0], x[-1]),
    }


def complex_fun(z):
    return z * (1.0 + 0.2j)


def deep_chain(x):
    for _ in range(5):
        x = np.tanh(x + 0.1)
    return np.sum(x)


def main():
    scalar_x = 0.3
    vec_x = np.array([0.2, -0.4])
    vec_y = np.array([0.1, -0.3, 0.7])
    direction = np.array([1.5, -0.5])

    # Scalar output + control flow + gradient checking.
    scalar_value, scalar_grad = value_and_grad(taylor_sine)(scalar_x)
    assert np.allclose(scalar_value, taylor_sine(scalar_x))
    assert np.allclose(scalar_grad, grad(taylor_sine)(scalar_x))
    assert np.allclose(scalar_grad, deriv(taylor_sine)(scalar_x))
    check_grads(taylor_sine)(scalar_x)

    # Vector output / Jacobian / elementwise grad.
    assert np.allclose(elementwise_grad(tanh)(vec_y), grad(lambda z: np.sum(tanh(z)))(vec_y))
    J = jacobian(vector_fun)(vec_x)
    assert J.shape == (3, 2)

    pullback, primal = make_vjp(vector_fun)(vec_x)
    primal2, tangent = make_jvp(vector_fun)(vec_x)(direction)
    assert np.allclose(primal, primal2)
    assert np.allclose(tangent, np.dot(J, direction))
    assert np.allclose(pullback(np.ones_like(primal)), grad(lambda z: np.sum(vector_fun(z)))(vec_x))
    assert np.allclose(jacobian(lambda z: np.sum(tanh(z)))(vec_y), grad(lambda z: np.sum(tanh(z)))(vec_y))

    # Hessian / HVP / GGN.
    A = np.array([[1.0, -2.0], [0.5, 1.5]])
    B = np.array([[1.0, -2.0], [0.5, 1.5], [-0.7, 0.25]])
    scalar_quadratic = lambda z: np.sum(np.tanh(np.dot(A, z)) ** 2)
    f = lambda z: np.tanh(np.dot(B, z))

    H = hessian(scalar_quadratic)(vec_x)
    hvp = hessian_tensor_product(scalar_quadratic)(vec_x, direction)
    assert np.allclose(hvp, np.dot(H, direction))
    assert np.allclose(hessian_vector_product(scalar_quadratic)(vec_x, direction), hvp)

    Jf = jacobian(f)(vec_x)
    ggnvp = make_ggnvp(f)(vec_x)(direction)
    assert np.allclose(ggnvp, np.dot(Jf.T, np.dot(Jf, direction)))

    # Auxiliary outputs.
    grad_aux, aux = grad_and_aux(scalar_with_aux)(vec_y)
    assert np.allclose(grad_aux, grad(lambda z: np.sum(np.tanh(z)))(vec_y))
    assert np.allclose(aux["meta"]["size"], float(vec_y.size))
    assert np.allclose(aux["meta"]["stats"][0], np.sum(vec_y))
    assert np.allclose(aux["trace"][0], vec_y[0])

    # Complex numbers and holomorphic gradients.
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        real_grad = holomorphic_grad(complex_fun)(1.0)
    assert any("Input to holomorphic_grad is not complex" in str(item.message) for item in caught)
    assert np.allclose(real_grad, 1.0)
    assert np.allclose(holomorphic_grad(complex_fun)(1.0 + 0.0j), 1.0 + 0.2j)

    # Checkpointed recomputation.
    checkpointed = checkpoint(deep_chain)
    assert np.allclose(checkpointed(vec_y), deep_chain(vec_y))
    assert np.allclose(grad(checkpointed)(vec_y), grad(deep_chain)(vec_y))

    print("differentiation smoke ok")


if __name__ == "__main__":
    main()
