#!/usr/bin/env python3
"""Smoke-check Detectron2/fvcore registry mechanics without building models."""

from __future__ import annotations

import argparse
import sys


def _import_registry_tools():
    try:
        from detectron2.utils.registry import Registry, locate

        return Registry, locate, "detectron2.utils.registry", None
    except Exception as detectron2_error:  # pragma: no cover - diagnostic path
        try:
            from fvcore.common.registry import Registry
        except Exception as fvcore_error:  # pragma: no cover - diagnostic path
            return None, None, None, (detectron2_error, fvcore_error)
        return Registry, None, "fvcore.common.registry", detectron2_error


def run_smoke_check(verbose: bool = True) -> int:
    Registry, locate, registry_source, import_error = _import_registry_tools()
    if Registry is None:
        detectron2_error, fvcore_error = import_error
        print("FAIL: could not import Detectron2 or fvcore registry utilities.", file=sys.stderr)
        print(f"Detectron2 import error: {detectron2_error}", file=sys.stderr)
        print(f"fvcore import error: {fvcore_error}", file=sys.stderr)
        print(
            "Install or activate an environment containing detectron2 and its runtime dependencies, "
            "or at least fvcore, then retry.",
            file=sys.stderr,
        )
        return 1

    registry = Registry("DISCO_TOY_EXTENSION")

    @registry.register()
    class ToyExtension:
        def __init__(self, value: int = 7) -> None:
            self.value = value

        def compute(self) -> int:
            return self.value * 2

    @registry.register()
    def build_toy_extension(value: int = 11) -> ToyExtension:
        return ToyExtension(value=value)

    resolved_class = registry.get("ToyExtension")
    if resolved_class is not ToyExtension:
        print("FAIL: class registry lookup returned the wrong object", file=sys.stderr)
        return 2

    instance = resolved_class(value=5)
    if instance.compute() != 10:
        print("FAIL: registered class did not instantiate or execute correctly", file=sys.stderr)
        return 3

    resolved_factory = registry.get("build_toy_extension")
    made = resolved_factory(value=13)
    if not isinstance(made, ToyExtension) or made.compute() != 26:
        print("FAIL: registered factory did not return the expected ToyExtension", file=sys.stderr)
        return 4

    if locate is not None:
        located = locate("detectron2.config.get_cfg")
        if located is None or getattr(located, "__name__", None) != "get_cfg":
            print("FAIL: detectron2.utils.registry.locate could not resolve get_cfg", file=sys.stderr)
            return 5

    if verbose:
        print(f"OK: registry registration and lookup work via {registry_source}.")
        if locate is None:
            print("Note: Detectron2 import failed, so only shared fvcore Registry mechanics were checked.")
            print(f"Detectron2 import error: {import_error}")
        print("Guidance:")
        print("- Import modules containing @REGISTRY.register() before building from config.")
        print("- Match config keys to the correct registry, e.g. MODEL.BACKBONE.NAME -> BACKBONE_REGISTRY.")
        print("- Add project config keys before merging project YAML files.")
        print("- This script intentionally does not build, train, load data, or download weights.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quiet", action="store_true", help="Only print failures.")
    args = parser.parse_args()
    return run_smoke_check(verbose=not args.quiet)


if __name__ == "__main__":
    raise SystemExit(main())
