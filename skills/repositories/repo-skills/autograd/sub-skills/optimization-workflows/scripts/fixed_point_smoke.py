"""Synthetic fixed-point smoke for differentiable scalar recurrences.

Uses only a local Newton update for sqrt(a); no downloads or plotting.
"""

from autograd import grad
from autograd.misc.fixed_points import fixed_point
import autograd.numpy as np


def distance(x, y):
    return np.abs(x - y)



def newton_sqrt_iter(a):
    return lambda x: 0.5 * (x + a / x)



def sqrt_via_fixed_point(a, guess=1.0):
    return fixed_point(newton_sqrt_iter, a, guess, distance, 1e-12)



def main():
    a = 2.0
    value = sqrt_via_fixed_point(a)
    first = grad(sqrt_via_fixed_point)(a)
    second = grad(grad(sqrt_via_fixed_point))(a)

    print("value:", value)
    print("grad:", first)
    print("grad2:", second)

    assert np.allclose(value, np.sqrt(a), atol=1e-10)
    assert np.allclose(first, 0.5 / np.sqrt(a), atol=1e-10)
    assert np.allclose(second, -1.0 / (4.0 * a ** 1.5), atol=1e-10)


if __name__ == "__main__":
    main()
