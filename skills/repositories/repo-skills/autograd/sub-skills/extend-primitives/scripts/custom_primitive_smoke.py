"""Smoke test for authoring a custom primitive with a staged VJP."""

import autograd.numpy as np
import autograd.numpy.random as npr
from autograd import grad
from autograd.extend import defvjp, primitive
from autograd.test_util import check_grads


@primitive
def stable_logsumexp(x):
    """Numerically stable log(sum(exp(x)))."""
    max_x = np.max(x)
    return max_x + np.log(np.sum(np.exp(x - max_x)))


def stable_logsumexp_vjp(ans, x):
    x_shape = x.shape
    ans_full = np.full(x_shape, ans)

    def vjp(g):
        return np.full(x_shape, g) * np.exp(x - ans_full)

    return vjp


defvjp(stable_logsumexp, stable_logsumexp_vjp)


def example_func(y):
    z = y**2
    lse = stable_logsumexp(z)
    return np.sum(lse)


if __name__ == "__main__":
    npr.seed(0)
    x = npr.randn(10)
    print("value:", example_func(x))
    print("grad:", grad(example_func)(x))
    check_grads(example_func, modes=["rev"])(x)
    print("check_grads: ok")
