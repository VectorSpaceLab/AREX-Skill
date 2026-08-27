#!/usr/bin/env python3
"""Validate a tiny custom PennyLane operator."""

import pennylane as qp
from pennylane.ops.functions import assert_valid


class FlipAndRotate(qp.operation.Operation):
    """Example custom operation with a decomposition."""

    grad_method = None

    def __init__(self, angle, wire_rot, wire_flip=None, do_flip=False):
        if do_flip and wire_flip is None:
            raise ValueError("Expected a wire to flip; got None.")
        self._hyperparameters = {"do_flip": do_flip}
        wires = qp.wires.Wires(wire_rot) + qp.wires.Wires(wire_flip)
        super().__init__(angle, wires=wires)

    @property
    def num_params(self):
        return 1

    @staticmethod
    def compute_decomposition(angle, wires, do_flip):
        ops = []
        if do_flip:
            ops.append(qp.PauliX(wires=wires[1]))
        ops.append(qp.RX(angle, wires=wires[0]))
        return ops

    @classmethod
    def _unflatten(cls, data, metadata):
        wires = metadata[0]
        hyperparameters = dict(metadata[1])
        wire_flip = wires[1] if len(wires) > 1 else None
        return cls(data[0], wire_rot=wires[0], wire_flip=wire_flip, **hyperparameters)


def main() -> None:
    op = FlipAndRotate(0.1, wire_rot=0, wire_flip=1, do_flip=True)
    assert_valid(op, skip_capture=True)
    print("custom_operator_valid=ok")
    print("decomposition=", op.decomposition())


if __name__ == "__main__":
    main()
