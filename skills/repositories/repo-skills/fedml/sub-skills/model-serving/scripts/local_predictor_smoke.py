#!/usr/bin/env python3
"""Offline FedML serving predictor smoke.

This helper imports FedML serving classes and exercises a tiny predictor directly.
It does not start uvicorn, create a model card, deploy an endpoint, or contact
FedML/TensorOpera services.
"""

from __future__ import annotations

import argparse
import asyncio
from typing import AsyncIterator

from fedml.serving import FedMLInferenceRunner, FedMLPredictor


class EchoPredictor(FedMLPredictor):
    def predict(self, payload: dict, *_args, **_kwargs) -> dict:
        values = payload.get("values", [])
        scale = payload.get("scale", 1)
        return {"scaled_sum": sum(values) * scale, "count": len(values)}


class StreamingEchoPredictor(FedMLPredictor):
    async def async_predict(self, payload: dict, *_args, **_kwargs) -> AsyncIterator[str]:
        for idx, token in enumerate(payload.get("tokens", [])):
            yield f"{idx}:{token}\n"


async def collect_stream(predictor: StreamingEchoPredictor) -> list[str]:
    stream = predictor.async_predict({"stream": True, "tokens": ["fed", "ml"]})
    return [chunk async for chunk in stream]


def run_normal() -> None:
    predictor = EchoPredictor()
    runner = FedMLInferenceRunner(predictor)
    assert runner.client_predictor.ready() is True
    result = runner.client_predictor.predict({"values": [1, 2, 3], "scale": 2})
    assert result == {"scaled_sum": 12, "count": 3}, result
    print("[PASS] FedMLPredictor normal predict smoke")
    print(f"result={result}")


def run_streaming() -> None:
    predictor = StreamingEchoPredictor()
    runner = FedMLInferenceRunner(predictor)
    assert runner.client_predictor.ready() is True
    chunks = asyncio.run(collect_stream(predictor))
    assert chunks == ["0:fed\n", "1:ml\n"], chunks
    print("[PASS] FedMLPredictor streaming async_predict smoke")
    print(f"chunks={chunks}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run an offline FedML serving predictor smoke.")
    parser.add_argument("--streaming", action="store_true", help="Exercise async streaming predictor instead of sync predict.")
    args = parser.parse_args()

    if args.streaming:
        run_streaming()
    else:
        run_normal()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
