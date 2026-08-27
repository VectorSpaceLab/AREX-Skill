"""Report whether pymoo's compiled performance extensions are available."""

from __future__ import annotations

import argparse
import json

from pymoo.functions import is_compiled


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Check whether the active pymoo install exposes compiled Cython "
            "performance functions. Pure Python fallback can still be valid."
        )
    )
    parser.add_argument(
        "--require-compiled",
        action="store_true",
        help="exit with a non-zero status if compiled extensions are unavailable",
    )
    args = parser.parse_args()

    compiled = bool(is_compiled())
    report = {
        "compiled_extensions": compiled,
        "meaning": (
            "compiled pymoo functions are available"
            if compiled
            else "pymoo is using pure Python fallback for compiled functions"
        ),
        "next_step": (
            "use normal pymoo APIs and benchmark the workload"
            if compiled
            else "continue for correctness, or rebuild/reinstall if compiled speedups are required"
        ),
    }
    print(json.dumps(report, indent=2, sort_keys=True))

    if args.require_compiled and not compiled:
        raise SystemExit("compiled pymoo extensions are required but unavailable")


if __name__ == "__main__":
    main()
