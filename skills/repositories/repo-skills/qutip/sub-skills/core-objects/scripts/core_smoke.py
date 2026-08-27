#!/usr/bin/env python3
"""Tiny QuTiP core-object smoke check.

Run this after installing QuTiP to verify the basic object layer:
- state/operator construction
- tensor composition
- measurement helpers
- state-comparison metrics
"""

from __future__ import annotations

import sys

from qutip import basis, fidelity, qeye, sigmaz, tensor, ket2dm
from qutip.measurement import measurement_statistics_observable


def main() -> int:
    psi = tensor(basis(2, 0), basis(2, 1))
    rho = ket2dm(psi)
    op = tensor(sigmaz(), qeye(2))

    print(f"psi.dims={psi.dims}")
    print(f"rho.isoper={rho.isoper}")
    print(f"op.isherm={op.isherm}")

    eigenvalues, projectors, probabilities = measurement_statistics_observable(
        basis(2, 0),
        sigmaz(),
    )
    print(f"measurement_probabilities={list(probabilities)}")
    print(f"measurement_eigenvalues={list(eigenvalues)}")
    print(f"measurement_projectors={len(projectors)}")

    print(f"fidelity(rho, rho)={fidelity(rho, rho)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
