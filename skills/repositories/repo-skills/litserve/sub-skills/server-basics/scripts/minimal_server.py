#!/usr/bin/env python3
"""Minimal self-contained LitServe server.

Run:
    python minimal_server.py --host 127.0.0.1 --port 8000

Call:
    curl -X POST http://127.0.0.1:8000/predict \
      -H "Content-Type: application/json" \
      -d '{"input": 4.0}'

Response:
    {"output": 16.0, "device": "cpu"}
"""

from __future__ import annotations

import argparse
from typing import Literal

import litserve as ls


class SquareAPI(ls.LitAPI):
    """Toy API that squares numeric inputs.

    It is intentionally CPU-safe and batch-aware so it can be used as a small smoke
    server or as a starting point for replacing `setup` and `predict` with real model
    code.
    """

    def __init__(self, api_path: str, max_batch_size: int, batch_timeout: float) -> None:
        super().__init__(api_path=api_path, max_batch_size=max_batch_size, batch_timeout=batch_timeout)

    def setup(self, device):
        self.device = str(device)
        self.model = lambda x: x * x

    def decode_request(self, request):
        return float(request["input"])

    def predict(self, x):
        if isinstance(x, list):
            return [self.model(float(item)) for item in x]
        return self.model(float(x))

    def encode_response(self, output):
        return {"output": output, "device": self.device}


def parse_devices(raw: str):
    """Parse an argparse device value for LitServer.

    Accepts "auto", a single integer string, or a comma-separated list of integers.
    """
    if raw == "auto":
        return "auto"
    if "," in raw:
        return [int(part.strip()) for part in raw.split(",") if part.strip()]
    return int(raw)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a minimal LitServe square server.")
    parser.add_argument("--host", default="127.0.0.1", choices=["127.0.0.1", "0.0.0.0", "::"])
    parser.add_argument("--port", default=8000, type=int)
    parser.add_argument("--api-path", default="/predict", help="POST endpoint path; must start with '/'.")
    parser.add_argument(
        "--accelerator",
        default="cpu",
        choices=["auto", "cpu", "cuda", "mps"],
        help="Use 'cpu' for a guaranteed local smoke; choose a GPU backend only when available.",
    )
    parser.add_argument("--devices", default="1", help="'auto', an integer count, or comma-separated GPU ids.")
    parser.add_argument("--workers-per-device", default=1, type=int)
    parser.add_argument("--timeout", default=30.0, type=float)
    parser.add_argument("--max-batch-size", default=1, type=int)
    parser.add_argument("--batch-timeout", default=0.0, type=float)
    parser.add_argument("--num-api-servers", default=None, type=int)
    parser.add_argument("--log-level", default="info")
    parser.add_argument(
        "--generate-client",
        action="store_true",
        help="Write client.py in the current working directory if it does not already exist.",
    )
    parser.add_argument(
        "--api-server-worker-type",
        default="process",
        choices=["process", "thread"],
        help="Use 'thread' on platforms or debuggers where process workers are inconvenient.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    api = SquareAPI(
        api_path=args.api_path,
        max_batch_size=args.max_batch_size,
        batch_timeout=args.batch_timeout,
    )
    server = ls.LitServer(
        api,
        accelerator=args.accelerator,
        devices=parse_devices(args.devices),
        workers_per_device=args.workers_per_device,
        timeout=args.timeout,
        model_metadata={"name": "minimal-square", "kind": "toy"},
    )
    server.run(
        host=args.host,
        port=args.port,
        num_api_servers=args.num_api_servers,
        log_level=args.log_level,
        generate_client_file=args.generate_client,
        api_server_worker_type=args.api_server_worker_type,
    )


if __name__ == "__main__":
    main()
