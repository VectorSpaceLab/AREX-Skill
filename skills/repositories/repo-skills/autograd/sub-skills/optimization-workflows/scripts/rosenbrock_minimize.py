"""Synthetic Rosenbrock minimize smoke.

Uses only a tiny analytic objective and no downloads or plotting.
"""

from scipy.optimize import minimize

import autograd.numpy as np
from autograd import value_and_grad


def rosenbrock(x):
    return 100.0 * (x[1] - x[0] ** 2) ** 2 + (1.0 - x[0]) ** 2



def main():
    x0 = np.array([0.0, 0.0])
    result = minimize(value_and_grad(rosenbrock), x0=x0, jac=True, method="CG")

    print("success:", result.success)
    print("x:", result.x)
    print("fun:", result.fun)

    assert result.success
    assert np.allclose(result.x, np.array([1.0, 1.0]), atol=1e-3)
    assert result.fun < 1e-6


if __name__ == "__main__":
    main()
