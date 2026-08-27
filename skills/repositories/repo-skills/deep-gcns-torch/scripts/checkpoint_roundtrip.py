#!/usr/bin/env python3
"""Verify a tiny PyTorch state-dict save/load round trip in a temp directory.

The helper has no dataset, network, credential, or source-checkout dependency.
It checks serialization mechanics only; task-specific checkpoint compatibility
still belongs to the owning workflow.
"""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a temporary PyTorch checkpoint round trip.")
    parser.add_argument("--seed", type=int, default=0, help="deterministic model seed")
    args = parser.parse_args(argv)
    try:
        import torch
        from torch import nn

        torch.manual_seed(args.seed)
        model = nn.Sequential(nn.Linear(3, 4), nn.ReLU(), nn.Linear(4, 2))
        state = model.state_dict()
        with tempfile.TemporaryDirectory(prefix="deep-gcns-checkpoint-") as temp:
            path = Path(temp) / "state.pth"
            torch.save({"state_dict": state}, path)
            restored = torch.load(path, map_location="cpu")
        if set(restored["state_dict"]) != set(state):
            raise RuntimeError("checkpoint keys changed during round trip")
        for key, value in state.items():
            if not torch.equal(value, restored["state_dict"][key]):
                raise RuntimeError(f"checkpoint tensor mismatch for {key}")
    except Exception as exc:  # pragma: no cover - environment dependent
        print(f"CHECKPOINT_ROUNDTRIP_FAILED: {type(exc).__name__}: {exc}")
        return 1
    print("OK checkpoint state_dict round trip")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
