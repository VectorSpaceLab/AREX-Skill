#!/usr/bin/env python3
"""Base PennyLane Autograd gradient smoke."""

import math

import pennylane as qp


def main() -> None:
    dev = qp.device("default.qubit", wires=1)

    @qp.qnode(dev, interface="autograd")
    def circuit(theta):
        qp.RX(theta, 0)
        return qp.expval(qp.Z(0))

    theta = qp.numpy.array(0.25, requires_grad=True)
    value = circuit(theta)
    gradient = qp.grad(circuit)(theta)
    assert qp.math.allclose(value, math.cos(0.25), atol=1e-9, rtol=0)
    assert qp.math.allclose(gradient, -math.sin(0.25), atol=1e-9, rtol=0)
    print("interface_gradient_smoke=ok")
    print("value=", value)
    print("gradient=", gradient)


if __name__ == "__main__":
    main()
