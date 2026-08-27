#!/usr/bin/env python3
"""Emit a JSON-only, no-database/no-network GeoDjango environment report."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import platform
from typing import Any


PACKAGE_DISTRIBUTIONS = {
    "djangorestframework-gis": "djangorestframework-gis",
    "Django": "Django",
    "djangorestframework": "djangorestframework",
    "django-filter": "django-filter",
}

MODULES = (
    "rest_framework_gis",
    "rest_framework_gis.apps",
    "rest_framework_gis.fields",
    "rest_framework_gis.serializers",
    "rest_framework_gis.filters",
    "rest_framework_gis.filterset",
    "rest_framework_gis.pagination",
    "rest_framework_gis.schema",
    "rest_framework_gis.tilenames",
)


def _configure_minimal_django() -> None:
    """Make DRF-backed imports testable without loading a project database."""
    from django.conf import settings

    if not settings.configured:
        settings.configure(
            SECRET_KEY="drf-gis-environment-check",
            INSTALLED_APPS=(
                "django.contrib.contenttypes",
                "django.contrib.gis",
                "rest_framework",
                "rest_framework_gis",
            ),
            DEFAULT_CHARSET="utf-8",
            USE_I18N=False,
            USE_TZ=True,
            REST_FRAMEWORK={},
        )
    import django
    from django.apps import apps

    if not apps.ready:
        django.setup()


def _error(exc: BaseException, action: str) -> dict[str, str]:
    return {
        "type": type(exc).__name__,
        "message": str(exc) or repr(exc),
        "action": action,
    }


def _distribution_versions() -> dict[str, dict[str, Any]]:
    versions: dict[str, dict[str, Any]] = {}
    for label, distribution in PACKAGE_DISTRIBUTIONS.items():
        try:
            versions[label] = {
                "installed": True,
                "version": importlib.metadata.version(distribution),
            }
        except importlib.metadata.PackageNotFoundError as exc:
            versions[label] = {
                "installed": False,
                "version": None,
                "error": _error(
                    exc,
                    f"Install the missing distribution with: python -m pip install {distribution}",
                ),
            }
        except Exception as exc:  # pragma: no cover - metadata backend dependent
            versions[label] = {
                "installed": False,
                "version": None,
                "error": _error(
                    exc,
                    f"Inspect the installation metadata for {distribution}.",
                ),
            }
    return versions


def _module_facts() -> tuple[dict[str, dict[str, Any]], bool]:
    facts: dict[str, dict[str, Any]] = {}
    all_ok = True
    for name in MODULES:
        try:
            importlib.import_module(name)
        except Exception as exc:
            all_ok = False
            facts[name] = {
                "ok": False,
                "error": _error(
                    exc,
                    "Install the declared runtime dependencies, then rerun this checker. "
                    "The checker uses an internal minimal Django settings object; "
                    "configure the real project separately for application tests.",
                ),
            }
        else:
            facts[name] = {"ok": True}
    return facts, all_ok


def _package_fact() -> tuple[dict[str, Any], bool]:
    try:
        module = importlib.import_module("rest_framework_gis")
        version = module.get_version() if hasattr(module, "get_version") else None
        return {
            "ok": True,
            "module_version": version,
            "version_tuple": list(getattr(module, "VERSION", ())),
        }, True
    except Exception as exc:
        return {
            "ok": False,
            "error": _error(
                exc,
                "Install djangorestframework-gis in this environment and rerun the checker.",
            ),
        }, False


def _geos_fact() -> tuple[dict[str, Any], bool]:
    try:
        from django.contrib.gis.geos import GEOSGeometry, geos_version

        geometry = GEOSGeometry("POINT (12.5 41.9)")
        version = geos_version()
        if isinstance(version, bytes):
            version = version.decode("ascii", errors="replace")
        return {
            "available": True,
            "version": version,
            "geometry_smoke": {
                "geom_type": geometry.geom_type,
                "srid": geometry.srid,
                "valid": geometry.valid,
            },
        }, True
    except Exception as exc:
        return {
            "available": False,
            "error": _error(
                exc,
                "Install a compatible GEOS runtime and make its shared library "
                "discoverable, then rerun the checker.",
            ),
        }, False


def _gdal_fact() -> tuple[dict[str, Any], bool]:
    try:
        from django.contrib.gis import gdal

        version = gdal.GDAL_VERSION
        if not version:
            raise RuntimeError("Django did not expose a GDAL version")
        return {"available": True, "version": version}, True
    except Exception as exc:
        return {
            "available": False,
            "error": _error(
                exc,
                "Install a compatible GDAL runtime and make its shared library "
                "discoverable, then rerun the checker.",
            ),
        }, False


def _proj_fact() -> tuple[dict[str, Any], bool]:
    try:
        from django.contrib.gis.gdal import CoordTransform, SpatialReference

        source = SpatialReference("EPSG:4326")
        target = SpatialReference("EPSG:3857")
        CoordTransform(source, target)
        return {
            "available": True,
            "probe": "constructed EPSG:4326 to EPSG:3857 coordinate transform",
            "version": None,
            "version_note": "Django does not expose a portable PROJ version API.",
        }, True
    except Exception as exc:
        return {
            "available": False,
            "error": _error(
                exc,
                "Install or expose compatible PROJ data/libraries and verify the "
                "requested CRS transformation, then rerun the checker.",
            ),
        }, False


def build_report() -> tuple[dict[str, Any], int]:
    distributions = _distribution_versions()
    try:
        _configure_minimal_django()
    except Exception as exc:
        settings_ok = False
        settings_error = _error(
            exc,
            "Install Django and configure a minimal settings object before DRF-backed imports.",
        )
    else:
        settings_ok = True
        settings_error = None
    package, package_ok = _package_fact()
    modules, modules_ok = _module_facts()
    geos, geos_ok = _geos_fact()
    gdal, gdal_ok = _gdal_fact()
    proj, proj_ok = _proj_fact()

    report = {
        "ok": all((settings_ok, package_ok, modules_ok, geos_ok, gdal_ok, proj_ok)),
        "settings": {"configured": settings_ok, "error": settings_error},
        "scope": {
            "database": False,
            "network": False,
            "settings_required": False,
        },
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
        },
        "distributions": distributions,
        "package": package,
        "modules": modules,
        "native_gis": {
            "GEOS": geos,
            "GDAL": gdal,
            "PROJ": proj,
        },
        "next_step": (
            "Run a project-configured Django test against a spatial database; "
            "this report does not verify database connectivity or PostGIS."
        ),
    }
    return report, 0 if report["ok"] else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Report Python/package/module and GEOS/GDAL/PROJ facts as JSON. "
            "Performs no database access and no network access."
        )
    )
    parser.parse_args()
    report, status = build_report()
    print(json.dumps(report, indent=2, sort_keys=True))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
