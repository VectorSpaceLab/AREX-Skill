#!/usr/bin/env python3
"""Check a public einops installation and optional NumPy smoke behavior.

This helper is safe to run from any current working directory. It does not read
or execute an original repository checkout.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import sys


def import_check(skip_numpy: bool) -> dict[str, object]:
    try:
        import einops  # type: ignore
        from einops import asnumpy, einsum, pack, parse_shape, rearrange, reduce, repeat, unpack  # noqa: F401
    except ModuleNotFoundError as exc:  # pragma: no cover - environment dependent
        raise SystemExit(f"Missing package {exc.name!r}. Install with: pip install einops") from exc

    result: dict[str, object] = {
        "einops_version": getattr(einops, "__version__", None),
        "distribution_version": importlib.metadata.version("einops"),
        "core_imports": ["rearrange", "reduce", "repeat", "parse_shape", "pack", "unpack", "einsum", "asnumpy"],
    }

    if skip_numpy:
        result["numpy_smoke"] = "skipped"
        return result

    try:
        import numpy as np  # type: ignore
        from einops import einsum, pack, parse_shape, rearrange, reduce, repeat, unpack
    except ModuleNotFoundError as exc:  # pragma: no cover - environment dependent
        result["numpy_smoke"] = f"skipped: missing {exc.name}"
        return result

    x = np.arange(2 * 3 * 4).reshape(2, 3, 4)
    assert rearrange(x, "batch channel time -> batch time channel").shape == (2, 4, 3)
    assert reduce(x, "batch channel time -> batch time", "sum").shape == (2, 4)
    assert repeat(x, "batch channel time -> batch channel time copy", copy=2).shape == (2, 3, 4, 2)
    assert parse_shape(x, "batch _ time") == {"batch": 2, "time": 4}
    packed, ps = pack([np.zeros((2, 3)), np.ones((2, 4, 3))], "batch * channel")
    assert packed.shape == (2, 5, 3)
    assert ps == [(), (4,)]
    assert [a.shape for a in unpack(packed, ps, "batch * channel")] == [(2, 3), (2, 4, 3)]
    assert einsum(np.ones((2, 3)), np.ones((3, 4)), "batch channel, channel out -> batch out").shape == (2, 4)
    result["numpy_smoke"] = "passed"
    result["numpy_version"] = np.__version__
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check einops importability and an optional NumPy smoke test.")
    parser.add_argument("--skip-numpy", action="store_true", help="Only check einops imports and distribution metadata.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args(argv)
    result = import_check(skip_numpy=args.skip_numpy)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for key, value in result.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
