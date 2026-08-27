#!/usr/bin/env python3
"""Check that Mctx imports cleanly and JAX is usable."""

from importlib.metadata import version

import jax
import mctx

PUBLIC_SYMBOLS = [
    "search",
    "muzero_policy",
    "gumbel_muzero_policy",
    "stochastic_muzero_policy",
    "RootFnOutput",
    "RecurrentFnOutput",
    "DecisionRecurrentFnOutput",
    "ChanceRecurrentFnOutput",
    "PolicyOutput",
    "Tree",
    "qtransform_by_min_max",
    "qtransform_by_parent_and_siblings",
    "qtransform_completed_by_mix_value",
]


def main() -> None:
  print(f"mctx-version: {version('mctx')}")
  print(f"mctx-module: {mctx.__file__}")
  print(f"jax-backend: {jax.default_backend()}")
  print(f"jax-devices: {jax.devices()}")
  for name in PUBLIC_SYMBOLS:
    print(f"{name}: {hasattr(mctx, name)}")


if __name__ == "__main__":
  main()
