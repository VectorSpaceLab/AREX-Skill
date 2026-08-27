#!/usr/bin/env python3
"""Safe local smoke for PennyLane I/O/data/debug/logging surfaces."""

import pennylane as qp


def main() -> None:
    dev = qp.device("default.qubit", wires=2)

    @qp.qnode(dev)
    def circuit(theta):
        qp.RX(theta, 0)
        qp.CNOT([0, 1])
        return qp.expval(qp.Z(1))

    qasm = qp.to_openqasm(circuit, precision=4)(0.2)
    if "OPENQASM" not in qasm:
        raise SystemExit("OpenQASM export did not contain OPENQASM header")
    print(qasm.splitlines()[0])
    print("data_module=", qp.data.__name__)
    print("debugging_snapshots=", qp.snapshots.__name__)
    print("io_data_smoke=ok")


if __name__ == "__main__":
    main()
