#!/usr/bin/env python3
"""Print the active rdagent package location and version without importing scenarios."""

from __future__ import annotations

import importlib.metadata

import rdagent


try:
    version = importlib.metadata.version("rdagent")
except importlib.metadata.PackageNotFoundError:
    version = "unknown"

print(f"version={version}")
print(f"module={getattr(rdagent, '__file__', 'unknown')}")
