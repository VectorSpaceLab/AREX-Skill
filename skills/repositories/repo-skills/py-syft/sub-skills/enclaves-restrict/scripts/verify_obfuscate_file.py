#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
import syft_restrict


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify and optionally obfuscate syft-restrict marked Python source")
    parser.add_argument("path")
    parser.add_argument("--out")
    parser.add_argument("--allow-function", action="append", dest="allow_functions")
    parser.add_argument("--allow-operator", action="append", dest="allow_operators")
    parser.add_argument("--disallow-function", action="append", dest="disallow_functions")
    parser.add_argument("--non-strict", action="store_true")
    args = parser.parse_args()
    result = syft_restrict.run(
        Path(args.path),
        allow_functions=args.allow_functions,
        allow_operators=args.allow_operators,
        disallow_functions=args.disallow_functions,
        out=Path(args.out) if args.out else None,
        strict=not args.non_strict,
    )
    violations = getattr(result, "violations", []) or []
    if violations:
        for violation in violations:
            print(violation)
        return 1
    print("OK syft-restrict verification passed")
    if args.out:
        print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
