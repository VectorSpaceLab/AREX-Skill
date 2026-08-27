#!/usr/bin/env python3
"""Safe CPU QNode smoke for PennyLane circuit/device workflows."""

import pennylane as qp


def main() -> None:
    dev = qp.device("default.qubit", wires=["a", "b"])

    @qp.qnode(dev)
    def circuit(theta):
        qp.RX(theta, "a")
        qp.CNOT(["a", "b"])
        return qp.expval(qp.Z("b")), qp.probs(wires=["a", "b"])

    result = circuit(0.321)
    print("expval=", result[0])
    print("probs=", result[1])
    print(qp.draw(circuit)(0.321))


if __name__ == "__main__":
    main()
