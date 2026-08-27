#!/usr/bin/env python3
"""Tiny QuTiP solver smoke check.

Run this after installing QuTiP to verify the time-evolution layer:
- Schrödinger and master-equation evolution
- steady-state solving
- runtime-compiled coefficients
- helper-map fallback behavior
"""

from __future__ import annotations

import sys

from qutip import basis, sigmax, sigmaz, sigmam, sesolve, mesolve, steadystate
from qutip.core.coefficient import coefficient
from qutip.solver.parallel import parallel_map


def square(value: int) -> int:
    """Top-level function so multiprocessing backends can pickle it."""
    return value * value


def main() -> int:
    psi0 = basis(2, 0)
    H = 0.5 * sigmax()

    ses = sesolve(H, psi0, [0, 0.1, 0.2], e_ops=[sigmaz()])
    print(f"sesolve_expect={list(ses.expect[0])}")

    mes = mesolve(H, psi0, [0, 0.1, 0.2], [0.1 * sigmam()], e_ops=[sigmaz()])
    print(f"mesolve_expect={list(mes.expect[0])}")

    rho_ss = steadystate(sigmaz(), [sigmam()])
    print(f"steadystate_trace={rho_ss.tr()}")

    coeff = coefficient('sin(w * t)', args={'w': 2.0})
    print(f"coefficient_value={coeff(0.25)}")

    squares = parallel_map(square, range(5), map_kw={"num_cpus": 1})
    print(f"parallel_map={squares}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
