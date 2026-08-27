#!/usr/bin/env python3
"""Deterministic tiny Dipy TensorModel smoke test.

This script uses only in-memory arrays and prints JSON by default. It validates
that core reconstruction imports work, a GradientTable can be built, a synthetic
multi-tensor signal can be generated, and TensorModel returns finite FA and
eigenvalues for a tiny masked fit.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def _json_default(value: Any) -> Any:
    try:
        import numpy as np
    except Exception:  # pragma: no cover - only used when numpy import itself fails
        np = None

    if np is not None:
        if isinstance(value, np.ndarray):
            return value.tolist()
        if isinstance(value, np.generic):
            return value.item()
    return str(value)


def run_smoke() -> dict[str, Any]:
    import numpy as np
    from dipy.core.gradients import gradient_table
    from dipy.reconst.dti import TensorModel, fractional_anisotropy
    from dipy.sims.voxel import multi_tensor

    bvals = np.array([0, 1000, 1000, 1000, 1000, 1000, 1000.0], dtype=float)
    bvecs = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [1.0, 1.0, 0.0],
            [1.0, 0.0, 1.0],
            [0.0, 1.0, 1.0],
        ],
        dtype=float,
    )
    bvecs[1:] /= np.linalg.norm(bvecs[1:], axis=1)[:, None]

    gtab = gradient_table(bvals, bvecs=bvecs, b0_threshold=50, atol=0.01)
    mevals = np.array([[1.7e-3, 0.3e-3, 0.3e-3]], dtype=float)
    signal, sticks = multi_tensor(
        gtab,
        mevals,
        S0=100.0,
        angles=((0, 0),),
        fractions=(100,),
        snr=None,
    )

    if signal.shape != (len(bvals),):
        raise RuntimeError(f"unexpected signal shape {signal.shape}")
    if not np.isfinite(signal).all() or signal.min() <= 0:
        raise RuntimeError("synthetic signal must be finite and positive")

    data = signal.reshape((1, 1, 1, len(bvals)))
    mask = np.ones(data.shape[:-1], dtype=bool)
    fit = TensorModel(gtab, fit_method="OLS", min_signal=1e-6).fit(data, mask=mask)
    evals = fit.evals[0, 0, 0]
    fa = float(np.nan_to_num(fractional_anisotropy(evals)))

    checks = {
        "gtab_length_matches_data": len(gtab.bvals) == data.shape[-1],
        "has_b0": bool(gtab.b0s_mask.any()),
        "mask_shape_matches": mask.shape == data.shape[:-1],
        "signal_finite_positive": bool(np.isfinite(signal).all() and signal.min() > 0),
        "evals_finite_positive": bool(np.isfinite(evals).all() and np.all(evals > 0)),
        "fa_finite_in_range": bool(np.isfinite(fa) and 0.0 <= fa <= 1.0),
    }

    return {
        "ok": all(checks.values()),
        "checks": checks,
        "versions": {"dipy": __import__("dipy").__version__},
        "shapes": {
            "data": list(data.shape),
            "mask": list(mask.shape),
            "signal": list(signal.shape),
            "sticks": list(np.asarray(sticks).shape),
        },
        "metrics": {
            "fa": fa,
            "evals": evals,
            "signal_min": float(signal.min()),
            "signal_max": float(signal.max()),
            "b0_count": int(gtab.b0s_mask.sum()),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print compact JSON output")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = parser.parse_args()

    try:
        result = run_smoke()
    except Exception as exc:  # pragma: no cover - exercised by broken environments
        result = {"ok": False, "error": type(exc).__name__, "message": str(exc)}

    indent = 2 if args.pretty or not args.json else None
    print(json.dumps(result, indent=indent, sort_keys=True, default=_json_default))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
