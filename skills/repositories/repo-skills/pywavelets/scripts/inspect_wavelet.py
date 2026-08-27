#!/usr/bin/env python3
"""Inspect a PyWavelets wavelet object without plotting.

This helper prints the verified properties, catalog membership, and wavefun
output shapes for a discrete or continuous wavelet. It is safe to run without
network access and can optionally prepend a local checkout to `sys.path` with
`--repo-root`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _maybe_add_repo_root(repo_root: str | None) -> None:
    if not repo_root:
        return
    root = Path(repo_root).expanduser().resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wavelet", nargs="?", default="db2", help="Wavelet name to inspect.")
    parser.add_argument("--level", type=int, default=5, help="Wavefun refinement level for discrete wavelets and the sample length exponent for continuous ones.")
    parser.add_argument("--repo-root", help="Optional checkout root to prepend to sys.path before importing.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    _maybe_add_repo_root(args.repo_root)

    try:
        import numpy as np
        import pywt
    except Exception as exc:  # pragma: no cover - diagnostic path
        payload = {"ok": False, "error": f"import failed: {type(exc).__name__}: {exc}"}
        _print(payload, args.json)
        return 1

    try:
        obj = pywt.DiscreteContinuousWavelet(args.wavelet)
    except Exception as exc:  # pragma: no cover - diagnostic path
        payload = {"ok": False, "error": f"wavelet construction failed: {type(exc).__name__}: {exc}"}
        _print(payload, args.json)
        return 1

    payload: dict = {
        "ok": True,
        "requested": args.wavelet,
        "type": type(obj).__name__,
        "name": getattr(obj, "name", None),
        "family_name": getattr(obj, "family_name", None),
        "short_family_name": getattr(obj, "short_family_name", None),
        "orthogonal": getattr(obj, "orthogonal", None),
        "biorthogonal": getattr(obj, "biorthogonal", None),
        "symmetry": getattr(obj, "symmetry", None),
        "is_continuous": isinstance(obj, pywt.ContinuousWavelet),
    }

    if isinstance(obj, pywt.ContinuousWavelet):
        payload["center_frequency"] = getattr(obj, "center_frequency", None)
        payload["bandwidth_frequency"] = getattr(obj, "bandwidth_frequency", None)
        payload["lower_bound"] = getattr(obj, "lower_bound", None)
        payload["upper_bound"] = getattr(obj, "upper_bound", None)
        payload["complex_cwt"] = getattr(obj, "complex_cwt", None)
        psi, x = obj.wavefun(length=2 ** args.level)
        payload["wavefun_kind"] = "continuous"
        payload["wavefun_shapes"] = [list(np.asarray(psi).shape), list(np.asarray(x).shape)]
    else:
        payload["dec_len"] = getattr(obj, "dec_len", None)
        payload["rec_len"] = getattr(obj, "rec_len", None)
        payload["vanishing_moments_phi"] = getattr(obj, "vanishing_moments_phi", None)
        payload["vanishing_moments_psi"] = getattr(obj, "vanishing_moments_psi", None)
        result = obj.wavefun(level=args.level)
        payload["wavefun_kind"] = "discrete"
        payload["wavefun_arity"] = len(result)
        payload["wavefun_shapes"] = [list(np.asarray(arr).shape) for arr in result]

    _print(payload, args.json)
    return 0


def _print(payload: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    if not payload.get("ok", False):
        print(payload.get("error", "unknown error"))
        return

    print(f"requested={payload['requested']}")
    print(f"type={payload['type']}")
    print(f"name={payload['name']}")
    print(f"family_name={payload['family_name']}")
    print(f"short_family_name={payload['short_family_name']}")
    print(f"orthogonal={payload['orthogonal']}")
    print(f"biorthogonal={payload['biorthogonal']}")
    print(f"symmetry={payload['symmetry']}")
    if payload["is_continuous"]:
        print(f"center_frequency={payload['center_frequency']}")
        print(f"bandwidth_frequency={payload['bandwidth_frequency']}")
        print(f"lower_bound={payload['lower_bound']}")
        print(f"upper_bound={payload['upper_bound']}")
        print(f"complex_cwt={payload['complex_cwt']}")
    else:
        print(f"dec_len={payload['dec_len']}")
        print(f"rec_len={payload['rec_len']}")
        print(f"vanishing_moments_phi={payload['vanishing_moments_phi']}")
        print(f"vanishing_moments_psi={payload['vanishing_moments_psi']}")
    print(f"wavefun_kind={payload['wavefun_kind']}")
    print(f"wavefun_shapes={payload['wavefun_shapes']}")


if __name__ == "__main__":
    raise SystemExit(main())
