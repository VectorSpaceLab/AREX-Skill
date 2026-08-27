#!/usr/bin/env python3
"""Run a local loopback smoke test for the remote dataset helpers.

This script starts a tiny in-memory dataset server in a child process, fetches
samples through `RemoteDataset`, and then shuts the server down again.

Example:
    python scripts/remote_dataset_smoke.py
"""

from __future__ import annotations

import argparse
import multiprocessing as mp
import socket
import time
from dataclasses import dataclass

from torch.utils.data import Dataset

from labml_helpers.datasets.remote import DatasetServer, RemoteDataset


@dataclass
class ToyItem:
    x: int
    y: int


class ToyDataset(Dataset):
    def __init__(self):
        self.items = [ToyItem(1, 10), ToyItem(2, 20), ToyItem(3, 30), ToyItem(4, 40)]

    def __len__(self):
        return len(self.items)

    def __getitem__(self, idx):
        item = self.items[idx]
        return (item.x, item.y)


def _serve(port: int):
    server = DatasetServer()
    server.add_dataset("toy", ToyDataset())
    server.start(host="127.0.0.1", port=port)


def _pick_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a loopback remote-dataset smoke test.")
    parser.add_argument("--port", type=int, default=0, help="Port to use; default picks a free port.")
    args = parser.parse_args()

    port = args.port or _pick_port()
    proc = mp.Process(target=_serve, args=(port,), daemon=True)
    proc.start()

    try:
        time.sleep(1.5)
        dataset = RemoteDataset("toy", host="127.0.0.1", port=port)
        length = len(dataset)
        first = dataset[0]
        last = dataset[length - 1]
        print(f"port={port}")
        print(f"length={length}")
        print(f"first={first}")
        print(f"last={last}")
        if length != 4 or first != (1, 10) or last != (4, 40):
            return 1
        return 0
    finally:
        proc.terminate()
        proc.join(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
