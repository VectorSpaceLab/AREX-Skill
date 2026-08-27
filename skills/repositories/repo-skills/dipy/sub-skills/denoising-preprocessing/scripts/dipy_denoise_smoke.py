#!/usr/bin/env python3
"""Deterministic tiny Dipy denoising/preprocessing smoke test.

This script uses only in-memory arrays and prints JSON by default. It validates
that core denoising imports work, small array shape checks behave as expected,
and safe tiny calls for sigma estimation, NLMeans, LPCA/MPPCA, Gibbs removal,
Patch2Self, and DWI bias correction can run without downloads or persistent IO.
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
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


def _make_gradients(n_vols: int):
    import numpy as np
    from dipy.core.gradients import gradient_table

    if n_vols < 10:
        raise ValueError("smoke gradient table expects at least 10 volumes")

    bvals = np.concatenate(([0.0, 0.0], np.full(n_vols - 2, 1000.0)))
    directions = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [1.0, 1.0, 0.0],
            [1.0, 0.0, 1.0],
            [0.0, 1.0, 1.0],
            [1.0, -1.0, 0.0],
            [1.0, 0.0, -1.0],
            [0.0, 1.0, -1.0],
            [1.0, 1.0, 1.0],
        ],
        dtype=float,
    )
    directions /= np.linalg.norm(directions, axis=1)[:, None]
    repeats = int(np.ceil((n_vols - 2) / directions.shape[0]))
    non_b0 = np.tile(directions, (repeats, 1))[: n_vols - 2]
    bvecs = np.vstack((np.zeros((2, 3), dtype=float), non_b0))
    gtab = gradient_table(bvals, bvecs=bvecs, b0_threshold=50, atol=0.01)
    return bvals, bvecs, gtab


def _make_data(shape=(7, 7, 7), n_vols=12):
    import numpy as np

    rng = np.random.default_rng(20260624)
    grid = np.indices(shape, dtype=float)
    base = 100.0 + 8.0 * grid[0] + 5.0 * grid[1] + 2.0 * grid[2]
    base /= base.mean() / 100.0
    volumes = []
    for vol_idx in range(n_vols):
        attenuation = 1.0 if vol_idx < 2 else 0.72 + 0.015 * (vol_idx % 5)
        volumes.append(base * attenuation + rng.normal(0.0, 1.5, size=shape))
    data = np.stack(volumes, axis=-1).astype(np.float32)
    mask = np.zeros(shape, dtype=bool)
    mask[1:-1, 1:-1, 1:-1] = True
    return data, mask


def _record_exception(result: dict[str, Any], key: str, exc: BaseException) -> None:
    result["checks"][key] = False
    result.setdefault("errors", {})[key] = {
        "type": type(exc).__name__,
        "message": str(exc),
    }


def run_smoke(include_patch2self: bool = True, include_bias: bool = True) -> dict[str, Any]:
    import numpy as np
    from dipy.denoise.gibbs import gibbs_removal
    from dipy.denoise.localpca import localpca, mppca
    from dipy.denoise.nlmeans import nlmeans
    from dipy.denoise.noise_estimate import estimate_sigma
    from dipy.denoise import patch2self as patch2self_module

    data, mask = _make_data()
    bvals, bvecs, gtab = _make_gradients(data.shape[-1])
    result: dict[str, Any] = {
        "ok": False,
        "checks": {},
        "versions": {"dipy": __import__("dipy").__version__},
        "shapes": {
            "data": list(data.shape),
            "mask": list(mask.shape),
            "bvals": list(bvals.shape),
            "bvecs": list(bvecs.shape),
        },
        "metrics": {},
        "skipped": [],
    }

    result["checks"]["gradient_length_matches_data"] = len(bvals) == data.shape[-1]
    result["checks"]["has_b0"] = bool(gtab.b0s_mask.any())
    result["checks"]["mask_shape_matches"] = mask.shape == data.shape[:3]
    result["checks"]["data_finite"] = bool(np.isfinite(data).all())

    try:
        sigma = estimate_sigma(data, N=0)
        result["checks"]["estimate_sigma_shape"] = sigma.shape == (data.shape[-1],)
        result["checks"]["estimate_sigma_finite"] = bool(np.isfinite(sigma).all())
        result["metrics"]["sigma_mean"] = float(np.mean(sigma))
    except Exception as exc:  # pragma: no cover - environment/version dependent
        _record_exception(result, "estimate_sigma", exc)
        sigma = np.full(data.shape[-1], 1.0, dtype=np.float32)

    try:
        nlmeans_out = nlmeans(
            data[..., :2],
            sigma=np.full(2, max(float(np.mean(sigma)), 1e-3), dtype=float),
            mask=mask,
            patch_radius=1,
            block_radius=1,
            rician=False,
            num_threads=1,
            method="blockwise",
        )
        result["checks"]["nlmeans_shape"] = nlmeans_out.shape == data[..., :2].shape
        result["checks"]["nlmeans_finite"] = bool(np.isfinite(nlmeans_out).all())
    except Exception as exc:  # pragma: no cover - environment/version dependent
        _record_exception(result, "nlmeans", exc)

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            lpca_out = localpca(
                data,
                sigma=max(float(np.mean(sigma)), 1e-3),
                mask=mask,
                patch_radius=1,
                pca_method="eig",
                suppress_warning=True,
            )
        result["checks"]["localpca_shape"] = lpca_out.shape == data.shape
        result["checks"]["localpca_finite"] = bool(np.isfinite(lpca_out).all())
    except Exception as exc:  # pragma: no cover - environment/version dependent
        _record_exception(result, "localpca", exc)

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            mppca_out, mppca_sigma = mppca(
                data,
                mask=mask,
                patch_radius=1,
                return_sigma=True,
                suppress_warning=True,
            )
        result["checks"]["mppca_shape"] = mppca_out.shape == data.shape
        result["checks"]["mppca_sigma_shape"] = mppca_sigma.shape == data.shape[:3]
        result["checks"]["mppca_finite"] = bool(np.isfinite(mppca_out).all())
    except Exception as exc:  # pragma: no cover - environment/version dependent
        _record_exception(result, "mppca", exc)

    try:
        unring = gibbs_removal(data[..., 0], slice_axis=2, inplace=False, num_processes=1)
        result["checks"]["gibbs_shape"] = unring.shape == data.shape[:3]
        result["checks"]["gibbs_finite"] = bool(np.isfinite(unring).all())
    except Exception as exc:  # pragma: no cover - environment/version dependent
        _record_exception(result, "gibbs_removal", exc)

    if include_patch2self:
        if not getattr(patch2self_module, "has_sklearn", False):
            result["skipped"].append("patch2self: sklearn is not available")
        else:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    p2s_out = patch2self_module.patch2self(
                        data,
                        bvals,
                        model="ols",
                        version=3,
                        patch_radius=(0, 0, 0),
                        b0_denoising=False,
                        verbose=False,
                    )
                result["checks"]["patch2self_shape"] = p2s_out.shape == data.shape
                result["checks"]["patch2self_finite"] = bool(np.isfinite(p2s_out).all())
            except Exception as exc:  # pragma: no cover - optional sklearn/version dependent
                _record_exception(result, "patch2self", exc)
    else:
        result["skipped"].append("patch2self")

    if include_bias:
        try:
            from dipy.denoise.bias_correction import bias_field_correction

            corrected, bias = bias_field_correction(
                data,
                gtab,
                mask=mask,
                method="poly",
                order=1,
                pyramid_levels=(1,),
                n_iter=1,
                robust=False,
                gradient_weighting=False,
                return_bias_field=True,
                zero_background=True,
            )
            result["checks"]["bias_corrected_shape"] = corrected.shape == data.shape
            result["checks"]["bias_field_shape"] = bias.shape == data.shape[:3]
            result["checks"]["bias_finite_positive"] = bool(
                np.isfinite(bias[mask]).all() and np.all(bias[mask] > 0)
            )
        except Exception as exc:  # pragma: no cover - environment/version dependent
            _record_exception(result, "bias_field_correction", exc)
    else:
        result["skipped"].append("bias_field_correction")

    result["metrics"].update(
        {
            "data_min": float(np.min(data)),
            "data_max": float(np.max(data)),
            "mask_voxels": int(np.count_nonzero(mask)),
            "b0_count": int(gtab.b0s_mask.sum()),
        }
    )
    result["ok"] = all(result["checks"].values())
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print compact JSON output")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    parser.add_argument(
        "--skip-patch2self",
        action="store_true",
        help="Skip Patch2Self if sklearn/runtime is intentionally unavailable",
    )
    parser.add_argument(
        "--skip-bias",
        action="store_true",
        help="Skip DWI bias correction if only denoising primitives are being checked",
    )
    args = parser.parse_args()

    try:
        result = run_smoke(
            include_patch2self=not args.skip_patch2self,
            include_bias=not args.skip_bias,
        )
    except Exception as exc:  # pragma: no cover - exercised by broken environments
        result = {"ok": False, "error": type(exc).__name__, "message": str(exc)}

    indent = 2 if args.pretty or not args.json else None
    print(json.dumps(result, indent=indent, sort_keys=True, default=_json_default))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
