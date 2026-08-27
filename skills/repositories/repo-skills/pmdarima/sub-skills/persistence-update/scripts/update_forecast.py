#!/usr/bin/env python3
"""Fit, update, persist, and forecast a deterministic pmdarima pipeline.

This bounded local smoke test uses raw observations for the update, lets a
FourierFeaturizer advance its position, records a compact manifest, and only
deserializes an artifact created by this invocation. The default artifact is
under a temporary directory. An explicit ``--output`` is a destination for a
new artifact, never an input path.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib
import json
import os
from pathlib import Path
import pickle
import sys
import tempfile
import warnings

import numpy as np


def _make_data() -> np.ndarray:
    """Return deterministic positive data with a small periodic component."""
    t = np.arange(32, dtype=float)
    return 20.0 + 0.35 * t + 1.5 * np.sin(2.0 * np.pi * t / 4.0)


def _build_pipeline():
    from pmdarima.arima import ARIMA
    from pmdarima.pipeline import Pipeline
    from pmdarima.preprocessing import BoxCoxEndogTransformer, FourierFeaturizer

    return Pipeline([
        ("boxcox", BoxCoxEndogTransformer(lmbda=0.0)),
        ("fourier", FourierFeaturizer(m=4, k=1)),
        ("arima", ARIMA(order=(1, 0, 0), maxiter=5,
                        suppress_warnings=True)),
    ])


def _versions() -> dict[str, str]:
    import pmdarima

    values = {"python": sys.version.split()[0],
              "pmdarima": str(pmdarima.__version__)}
    for module_name in ("numpy", "scipy", "statsmodels", "sklearn", "pandas", "joblib"):
        try:
            module = importlib.import_module(module_name)
            values[module_name] = str(getattr(module, "__version__", "unknown"))
        except Exception as exc:  # diagnostic metadata only
            values[module_name] = f"unavailable: {type(exc).__name__}"
    return values


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stage_pickle(value, destination: Path) -> Path:
    """Create a same-directory temporary pickle without replacing destination."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="wb", prefix=f".{destination.name}.", suffix=".tmp",
        dir=destination.parent, delete=False,
    )
    temporary = Path(handle.name)
    try:
        with handle:
            pickle.dump(value, handle, protocol=pickle.HIGHEST_PROTOCOL)
            handle.flush()
            os.fsync(handle.fileno())
        return temporary
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _atomic_json_dump(value: dict, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", prefix=f".{destination.name}.",
            suffix=".tmp", dir=destination.parent, delete=False,
        ) as handle:
            temporary = Path(handle.name)
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def _manifest(pipeline, y: np.ndarray, observed: np.ndarray,
              forecast_horizon: int, maxiter: int) -> dict:
    fitted = dict(pipeline.steps_)
    final = fitted["arima"]
    return {
        "updated_utc": datetime.now(timezone.utc).isoformat(),
        "versions": _versions(),
        "model": {
            "class": type(final).__name__,
            "order": list(final.order),
            "seasonal_order": list(final.seasonal_order),
            "pkg_version_at_fit": str(getattr(final, "pkg_version_", "unknown")),
        },
        "transformers": [
            {"name": name, "class": type(transformer).__name__}
            for name, transformer in pipeline.steps_[:-1]
        ],
        "schema": {
            "target_dtype": str(y.dtype),
            "training_rows": int(y.shape[0]),
            "updated_rows": int(observed.shape[0]),
            "external_exog": False,
            "fitted_transformed_features": list(pipeline.x_feats_ or []),
            "forecast_horizon": int(forecast_horizon),
            "public_target_scale": "raw",
            "update_maxiter": int(maxiter),
            "fourier_position": int(fitted["fourier"].n_),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fit a tiny Fourier-plus-ARIMA pipeline, update it, and forecast."
    )
    parser.add_argument(
        "--maxiter", type=int, default=1,
        help="bounded ARIMA update iterations (default: 1)",
    )
    parser.add_argument(
        "--output", type=Path,
        help="Optional destination for the newly generated artifact; default is temporary.",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Allow replacing an existing --output artifact and manifest.",
    )
    args = parser.parse_args()
    if args.maxiter < 1:
        parser.error("--maxiter must be positive")

    data = _make_data()
    train, observed = data[:24], data[24:27]
    pipeline = _build_pipeline()
    pipeline.fit(train)
    fitted = dict(pipeline.steps_)
    boxcox_lambda = float(fitted["boxcox"].lam1_)
    before_position = int(fitted["fourier"].n_)
    before = np.asarray(pipeline.predict(n_periods=5), dtype=float)
    assert before.shape == (5,), f"unexpected pre-update shape: {before.shape}"
    assert np.all(np.isfinite(before)), "pre-update forecast contains non-finite values"

    # Pipeline.update expects raw y. Its pinned-source return value is the
    # final estimator, so continue using the mutated pipeline for prediction.
    result = pipeline.update(observed, maxiter=args.maxiter)
    assert result is pipeline.steps_[-1][1], "Pipeline.update return contract changed"

    after_position = int(dict(pipeline.steps_)["fourier"].n_)
    assert after_position == before_position + observed.shape[0], (
        f"Fourier position did not advance: {before_position} -> {after_position}"
    )
    after = np.asarray(pipeline.predict(n_periods=5), dtype=float)
    assert after.shape == (5,), f"unexpected post-update shape: {after.shape}"
    assert np.all(np.isfinite(after)), "post-update forecast contains non-finite values"
    assert not np.array_equal(before, after), "forecast did not change after update"

    with tempfile.TemporaryDirectory(prefix="pmdarima-update-") as directory:
        if args.output is None:
            artifact = Path(directory) / "updated-pipeline.pkl"
            artifact_label = "temporary (cleaned on exit)"
        else:
            artifact = args.output.expanduser()
            if artifact.exists() and artifact.is_dir():
                parser.error("--output must be a file path, not a directory")
            if artifact.exists() and not args.force:
                parser.error(f"refusing to replace existing output: {artifact}; use --force")
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact_label = str(artifact)

        staged = _stage_pickle(pipeline, artifact)
        try:
            # Safe only because this script created staged. Never generalize
            # this load to an arbitrary user-provided pickle.
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                with staged.open("rb") as handle:
                    restored = pickle.load(handle)
            assert hasattr(restored, "steps_"), "reloaded pipeline is not fitted"
            reloaded = np.asarray(restored.predict(n_periods=5), dtype=float)
            assert reloaded.shape == (5,), (
                f"unexpected reloaded forecast shape: {reloaded.shape}"
            )
            assert np.all(np.isfinite(reloaded)), "reloaded forecast is not finite"
            np.testing.assert_allclose(after, reloaded, rtol=1e-10, atol=1e-10)
            assert float(dict(restored.steps_)["boxcox"].lam1_) == boxcox_lambda
            manifest = _manifest(restored, train, observed, 5, args.maxiter)
            manifest["artifact_sha256"] = _sha256(staged)
            manifest["reload_warnings"] = [type(item.message).__name__ for item in caught]
            os.replace(staged, artifact)
            staged = None
        finally:
            if staged is not None:
                staged.unlink(missing_ok=True)

        if args.output is not None:
            _atomic_json_dump(manifest, Path(f"{artifact}.json"))

    print(json.dumps({
        "artifact": artifact_label,
        "observed": int(observed.shape[0]),
        "fourier_position": after_position,
        "boxcox_lambda": boxcox_lambda,
        "forecast_shape": list(after.shape),
        "first_forecast": float(after[0]),
        "reload_equal": True,
        "manifest": manifest,
    }, sort_keys=True))
    print("Bounded fit/update/forecast smoke check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
