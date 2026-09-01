#!/usr/bin/env python3
"""Smoke tests for proxy batch creation."""

from pathlib import Path
import importlib.util

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "create_proxy_batch.py"
spec = importlib.util.spec_from_file_location("create_proxy_batch", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

batch = module.create_batch(batch_size=4, height=8, width=8, seed=3)
assert batch["shape"] == [4, 1, 8, 8]
assert batch["synthetic_proxy"] is True
assert batch["value_range"] == [0.0, 1.0]
flat = [value for image in batch["images"] for channel in image for row in channel for value in row]
assert set(flat).issubset({0.0, 1.0})
assert 0.0 in flat and 1.0 in flat
assert module.create_batch(batch_size=4, height=8, width=8, seed=3) == batch
assert module.create_batch(batch_size=4, height=8, width=8, seed=4) != batch
