#!/usr/bin/env python3
"""Safe decomposition/compile smoke for PennyLane transforms."""

import pennylane as qp


def main() -> None:
    dev = qp.device("default.qubit", wires=2)

    @qp.qnode(dev)
    def circuit(x):
        qp.Rot(x, x / 2, -x, wires=0)
        qp.CNOT([0, 1])
        return qp.expval(qp.Z(1))

    compiled = qp.compile(circuit, basis_set={"RX", "RY", "RZ", "CNOT"}, num_passes=1)
    print(qp.draw(compiled)(0.2))
    print("compiled_value=", compiled(0.2))


if __name__ == "__main__":
    main()
