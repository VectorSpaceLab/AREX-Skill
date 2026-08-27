#!/usr/bin/env python3
"""Small PennyLane package smoke test.

Run with the Python environment that should use PennyLane. It avoids network,
optional ML frameworks, and accelerators.
"""

import math

import pennylane as qp


def main() -> None:
    print(f"pennylane_version={qp.version()}")
    dev = qp.device("default.qubit", wires=2)

    @qp.qnode(dev)
    def circuit(theta):
        qp.RX(theta, wires=0)
        qp.CNOT(wires=[0, 1])
        return qp.expval(qp.Z(1))

    theta = qp.numpy.array(0.123, requires_grad=True)
    value = circuit(theta)
    grad = qp.grad(circuit)(theta)
    expected = math.cos(0.123)
    if not qp.math.allclose(value, expected, atol=1e-9, rtol=0):
        raise SystemExit(f"unexpected QNode value: {value!r} != {expected!r}")
    if not qp.math.allclose(grad, -math.sin(0.123), atol=1e-9, rtol=0):
        raise SystemExit(f"unexpected QNode gradient: {grad!r}")
    print(f"qnode_value={value}")
    print(f"qnode_grad={grad}")
    print("pennylane_smoke=ok")


if __name__ == "__main__":
    main()
