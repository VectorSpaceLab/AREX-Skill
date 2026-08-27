#!/usr/bin/env python3
"""Read-only health check for an installed, standalone LabML stack.

The checker refuses to call a checkout (including an editable install) a
standalone installation. It still performs normal package import/version checks
for a wheel/site-packages installation. ``--check-server`` checks settings and
static prerequisites without starting the server or connecting to MongoDB.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import sys
from importlib import metadata
from pathlib import Path
from types import ModuleType


PACKAGES = {
    "labml": ("labml", "client/labml"),
    "labml-helpers": ("labml_helpers", "helpers/labml_helpers"),
    "labml-remote": ("labml_remote", "remote/labml_remote"),
    "labml-app": ("labml_app", "app/server/labml_app"),
}


def _version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "not-installed"


def _checkout_root() -> Path | None:
    """Find the checkout containing this bundled checker, if it is present."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "skills" / "disco").is_dir() and (parent / "client").is_dir():
            return parent
    return None


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _spec_origin(import_name: str) -> Path | None:
    try:
        spec = importlib.util.find_spec(import_name)
    except (ImportError, ModuleNotFoundError, ValueError):
        return None
    if spec is None or not spec.origin or spec.origin in {"built-in", "frozen"}:
        return None
    return Path(spec.origin).resolve()


def _import_package(import_name: str) -> tuple[ModuleType | None, str | None]:
    try:
        return importlib.import_module(import_name), None
    except Exception as exc:  # imports can fail because an optional dep is absent
        return None, f"{type(exc).__name__}: {exc}"


def _check_server(package: ModuleType | None, failures: list[str]) -> None:
    """Check server prerequisites without importing or starting the app server."""
    if package is None or not getattr(package, "__file__", None):
        print("server preflight: FAIL (labml_app did not import; cannot inspect prerequisites)")
        failures.append("server preflight")
        return

    package_root = Path(package.__file__).resolve().parent
    settings = package_root / "settings.py"
    analyses_settings = package_root / "analyses_settings.py"
    static_candidates = (
        package_root.parent.parent / "static",
        package_root.parent / "static",
        package_root / "static",
    )
    missing = []
    if not settings.exists():
        missing.append(f"{settings} (copy settings.sample.py to settings.py and configure it)")
    if not analyses_settings.exists():
        missing.append(
            f"{analyses_settings} (copy analyses_settings.sample.py to analyses_settings.py)"
        )
    static = next((path for path in static_candidates if path.is_dir()), None)
    if static is None:
        missing.append(
            "static frontend directory (build app/ui with `npm install && npm run build`, "
            "or install a wheel containing static assets)"
        )
    if missing:
        print("server preflight: FAIL (full server is not ready)")
        for item in missing:
            print(f"  missing: {item}")
        failures.append("server preflight")
    else:
        print(f"server preflight: PASS (settings and static assets at {static})")

    # A network/database probe would make this no longer a lightweight checker.
    print("server MongoDB: NOT_CHECKED (start MongoDB on MONGO_HOST or localhost:27017 before app-server)")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the LabML package stack.")
    parser.add_argument("--require-gpu", action="store_true", help="Exit non-zero if CUDA is unavailable.")
    parser.add_argument(
        "--check-server",
        action="store_true",
        help="Fail fast when labml_app settings/static prerequisites are absent (no MongoDB probe).",
    )
    args = parser.parse_args()

    print(f"python: {sys.version.split()[0]}")
    for distribution in PACKAGES:
        print(f"{distribution}: {_version(distribution)}")

    failures: list[str] = []
    imported: dict[str, ModuleType | None] = {}
    checkout = _checkout_root()
    if checkout is not None:
        print(f"checkout: {checkout}")

    for distribution, (import_name, source_relative) in PACKAGES.items():
        origin = _spec_origin(import_name)
        source_root = checkout / source_relative if checkout is not None else None
        if origin is not None and source_root is not None and _is_under(origin, source_root):
            print(f"{import_name} import: {origin}")
            print(
                f"NOT_STANDALONE: {import_name} resolves inside current checkout "
                f"({source_root}); install a wheel outside this source tree."
            )
            failures.append(f"{import_name} editable/source import")

        module, error = _import_package(import_name)
        imported[import_name] = module
        if module is None:
            print(f"{import_name} import: FAILED ({error})")
            failures.append(f"{import_name} import")
        else:
            origin = getattr(module, "__file__", None)
            print(f"{import_name} import: {Path(origin).resolve() if origin else origin}")

    if args.check_server:
        _check_server(imported.get("labml_app"), failures)

    try:
        import torch

        print(f"torch: {_version('torch')}")
        print(f"cuda_available: {torch.cuda.is_available()}")
        print(f"cuda_device_count: {torch.cuda.device_count()}")
        if args.require_gpu and not torch.cuda.is_available():
            failures.append("CUDA unavailable")
    except Exception as exc:  # pragma: no cover - best-effort summary
        print(f"torch: unavailable ({exc})")
        if args.require_gpu:
            failures.append("torch/CUDA")

    try:
        import py3nvml
        from py3nvml import py3nvml as nvml

        nvml.nvmlInit()
        print(f"py3nvml: {_version('py3nvml')}")
        print(f"nvidia_driver: {nvml.nvmlSystemGetDriverVersion()}")
        print(f"nvidia_device_count: {nvml.nvmlDeviceGetCount()}")
        nvml.nvmlShutdown()
    except Exception as exc:
        print(f"py3nvml: unavailable ({exc})")
        if args.require_gpu:
            failures.append("py3nvml/NVIDIA")

    if failures:
        print("FAIL: " + "; ".join(dict.fromkeys(failures)))
        return 1
    print("PASS: standalone package imports and optional checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
