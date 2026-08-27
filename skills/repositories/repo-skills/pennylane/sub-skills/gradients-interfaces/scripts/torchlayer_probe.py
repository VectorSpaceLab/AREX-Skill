#!/usr/bin/env python3
"""Optional TorchLayer probe for PennyLane.

Exits with code 3 when Torch is not installed, so callers can distinguish an
optional dependency absence from a PennyLane failure.
"""

import sys

try:
    import torch
except ModuleNotFoundError:
    print("torch_not_installed=optional", file=sys.stderr)
    raise SystemExit(3)

import pennylane as qp


def main() -> None:
    dev = qp.device("default.qubit", wires=2)

    @qp.qnode(dev, interface="torch")
    def qnode(inputs, weights):
        qp.AngleEmbedding(inputs, wires=[0, 1])
        qp.StronglyEntanglingLayers(weights, wires=[0, 1])
        return qp.expval(qp.Z(0))

    layer = qp.qnn.TorchLayer(qnode, weight_shapes={"weights": (1, 2, 3)})
    out = layer(torch.zeros(2, dtype=torch.float64))
    print("torchlayer_probe=ok")
    print(out)


if __name__ == "__main__":
    main()
