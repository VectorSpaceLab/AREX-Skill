#!/usr/bin/env python3
"""Tiny QuTiP specialized open-system smoke check.

This validates imports and small constructors only; it does not launch an
expensive HEOM or large PIQS solve.
"""

from __future__ import annotations

import numpy as np

from qutip import sigmaz
from qutip.core.environment import DrudeLorentzEnvironment
from qutip.piqs.piqs import Dicke, jspin, num_dicke_states
from qutip.solver.heom import DrudeLorentzBath


def main() -> int:
    env = DrudeLorentzEnvironment(T=1.0, lam=0.5, gamma=2.0)
    print(f"drude_spectral_density={env.spectral_density(np.array([0.5, 1.0]))}")

    n = 4
    jx, jy, jz = jspin(n)
    system = Dicke(n, hamiltonian=0.1 * jz, emission=0.01, dephasing=0.02)
    liouvillian = system.liouvillian()
    print(f"num_dicke_states={num_dicke_states(n)}")
    print(f"piqs_liouvillian_shape={liouvillian.shape}")

    bath = DrudeLorentzBath(sigmaz(), lam=0.1, gamma=1.0, T=1.0, Nk=2)
    print(f"heom_bath_exponents={len(bath.exponents)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
