#!/usr/bin/env python3
"""Safe CPU smoke for PennyLane resource specs and tiny qchem object."""

import pennylane as qp


def main() -> None:
    dev = qp.device("default.qubit", wires=2)

    @qp.qnode(dev)
    def circuit(theta):
        qp.RX(theta, 0)
        qp.CNOT([0, 1])
        return qp.expval(qp.Z(1))

    specs = qp.specs(circuit)(0.2)
    print("specs=", specs)

    symbols = ["H", "H"]
    coordinates = qp.numpy.array([[0.0, 0.0, -0.35], [0.0, 0.0, 0.35]])
    mol = qp.qchem.Molecule(symbols, coordinates, unit="angstrom")
    print("molecule_n_electrons=", mol.n_electrons)
    print("resource_and_qchem_smoke=ok")


if __name__ == "__main__":
    main()
