#!/usr/bin/env python3
"""Fit a tiny pmdarima pipeline and verify a trusted pickle round trip.

The script creates its own artifact. By default both the artifact and its
manifest live in a temporary directory that is removed on exit. ``--output``
only names a destination for the newly generated artifact; it is never used as
an input artifact.
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


def _build_pipeline():
    """Return a pipeline and its deterministic training data."""
    from pmdarima.arima import ARIMA
    from pmdarima.pipeline import Pipeline
    from pmdarima.preprocessing import BoxCoxEndogTransformer

    y = np.array(
        [10.0, 10.8, 11.5, 12.4, 13.1, 13.9, 14.8, 15.4,
         16.2, 17.1, 17.7, 18.6, 19.3, 20.1, 20.9, 21.6,
         22.4, 23.0, 23.9, 24.7, 25.4, 26.3, 27.0, 27.8],
        dtype=float,
    )
    pipeline = Pipeline([
        ("boxcox", BoxCoxEndogTransformer(lmbda=0.0)),
        ("arima", ARIMA(order=(1, 0, 0), maxiter=5,
                        suppress_warnings=True)),
    ])
    pipeline.fit(y)
    return pipeline, y


def _versions() -> dict[str, str]:
    import pmdarima

    versions = {"python": sys.version.split()[0],
                "pmdarima": str(pmdarima.__version__)}
    for module_name in ("numpy", "scipy", "statsmodels", "sklearn", "pandas", "joblib"):
        try:
            module = importlib.import_module(module_name)
            versions[module_name] = str(getattr(module, "__version__", "unknown"))
        except Exception as exc:  # diagnostic metadata only
            versions[module_name] = f"unavailable: {type(exc).__name__}"
    return versions


def _manifest(pipeline, y: np.ndarray, horizon: int) -> dict:
    final = pipeline.steps_[-1][1]
    return {
        "created_utc": datetime.now(timezone.utc).isoformat(),
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
            "external_exog": False,
            "fitted_transformed_features": list(pipeline.x_feats_ or []),
            "forecast_horizon": int(horizon),
            "public_target_scale": "raw",
        },
    }


def _stage_pickle(value, destination: Path) -> Path:
    """Write a same-directory temporary pickle without replacing destination."""
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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _round_trip(pipeline, y: np.ndarray, artifact: Path) -> tuple[dict, np.ndarray]:
    horizon = 4
    expected = np.asarray(pipeline.predict(n_periods=horizon), dtype=float)
    assert expected.shape == (horizon,), f"unexpected pre-save shape: {expected.shape}"
    assert np.all(np.isfinite(expected)), "pre-save forecast is not finite"

    staged = _stage_pickle(pipeline, artifact)
    try:
        # This staged path was written by this invocation; no user-supplied
        # artifact is read. Validate before replacing an existing artifact.
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            with staged.open("rb") as handle:
                restored = pickle.load(handle)
        assert hasattr(restored, "steps_"), "reloaded pipeline is not fitted"
        actual = np.asarray(restored.predict(n_periods=horizon), dtype=float)
        assert actual.shape == (horizon,), f"unexpected reloaded shape: {actual.shape}"
        assert np.all(np.isfinite(actual)), "reloaded forecast is not finite"
        np.testing.assert_allclose(expected, actual, rtol=1e-10, atol=1e-10)

        manifest = _manifest(restored, y, horizon)
        manifest["artifact_sha256"] = _sha256(staged)
        manifest["reload_warnings"] = [type(item.message).__name__ for item in caught]
        os.replace(staged, artifact)
        staged = None
    finally:
        if staged is not None:
            staged.unlink(missing_ok=True)
    return manifest, actual


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fit a deterministic pmdarima pipeline and verify a trusted pickle round trip."
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

    if args.output is not None:
        artifact = args.output.expanduser()
        if artifact.exists() and artifact.is_dir():
            parser.error("--output must be a file path, not a directory")
        if artifact.exists() and not args.force:
            parser.error(f"refusing to replace existing output: {artifact}; use --force")
        manifest, forecast = _round_trip(*_build_pipeline(), artifact)
        _atomic_json_dump(manifest, Path(f"{artifact}.json"))
        artifact_label = str(artifact)
    else:
        with tempfile.TemporaryDirectory(prefix="pmdarima-roundtrip-") as directory:
            artifact = Path(directory) / "pipeline.pkl"
            manifest, forecast = _round_trip(*_build_pipeline(), artifact)
            artifact_label = "temporary (cleaned on exit)"

    print(json.dumps({
        "artifact": artifact_label,
        "forecast_shape": list(forecast.shape),
        "first_forecast": float(forecast[0]),
        "manifest": manifest,
        "round_trip_equal": True,
    }, sort_keys=True))
    print("Trusted same-environment pipeline round trip passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
