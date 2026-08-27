#!/usr/bin/env python3
"""Tiny QuTiP visualization and I/O smoke check.

Run this after installing QuTiP with Matplotlib available.  The script uses the
non-interactive Agg backend, creates small figures, computes a Wigner grid, and
round-trips a QuTiP object through qsave/qload.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from qutip import Bloch, basis, hinton, qload, qsave, rand_dm, wigner


def main() -> int:
    fig, ax = hinton(rand_dm(4))
    print(f"hinton={fig.__class__.__name__}/{ax.__class__.__name__}")
    plt.close(fig)

    bloch = Bloch()
    bloch.add_states(basis(2, 0))
    bloch.add_vectors([1, 0, 0])
    bloch.render()
    print("bloch_rendered=True")
    plt.close('all')

    grid = np.linspace(-3, 3, 11)
    W = wigner(basis(6, 0), grid, grid)
    print(f"wigner_shape={W.shape}")

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "psi0"
        psi = basis(2, 0)
        qsave(psi, path)
        loaded = qload(path)
        print(f"qsave_qload_equal={loaded == psi}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
