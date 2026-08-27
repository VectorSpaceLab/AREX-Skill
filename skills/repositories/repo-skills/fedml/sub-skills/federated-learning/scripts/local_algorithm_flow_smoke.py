#!/usr/bin/env python3
"""Offline FedML federated-learning executor/Params smoke.

FedMLAlgorithmFlow itself wires a communication backend at construction time, so
this helper imports it but uses local FedMLExecutor + Params steps to validate the
same task-shape without MPI/MQTT/NCCL or backend services.
"""

from __future__ import annotations

from fedml.core import FedMLAlgorithmFlow, FedMLExecutor, Params


class ToyExecutor(FedMLExecutor):
    def __init__(self) -> None:
        super().__init__(id=0, neighbor_id_list=[0])
        self.events: list[str] = []

    def init_global_model(self) -> Params:
        self.events.append("init_global_model")
        params = Params()
        params.add(Params.KEY_MODEL_PARAMS, {"weight": 1.0})
        return params

    def local_training(self) -> Params:
        self.events.append("local_training")
        params = self.get_params()
        weights = dict(params.get(Params.KEY_MODEL_PARAMS))
        weights["weight"] += 2.0
        out = Params()
        out.add(Params.KEY_MODEL_PARAMS, weights)
        return out

    def server_aggregate(self) -> Params:
        self.events.append("server_aggregate")
        params = self.get_params()
        weights = dict(params.get(Params.KEY_MODEL_PARAMS))
        weights["weight"] /= 3.0
        out = Params()
        out.add(Params.KEY_MODEL_PARAMS, weights)
        return out


def main() -> int:
    assert FedMLAlgorithmFlow is not None  # prove the public symbol imports
    executor = ToyExecutor()

    params = executor.init_global_model()
    executor.set_params(params)
    params = executor.local_training()
    executor.set_params(params)
    params = executor.server_aggregate()

    result = params.get(Params.KEY_MODEL_PARAMS)
    assert result == {"weight": 1.0}, result
    assert executor.events == ["init_global_model", "local_training", "server_aggregate"], executor.events

    print("[PASS] FedMLExecutor + Params local algorithm-flow smoke")
    print(f"events={executor.events}")
    print(f"model_params={result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
