#!/usr/bin/env python3
"""Serialize a deterministic GEOS LineString without a database or network.

The helper configures the minimum Django settings before importing DRF or
``rest_framework_gis``. It is safe to run from any current working directory
when Django, DRF, GeoDjango's GEOS/GDAL libraries, and djangorestframework-gis
are installed in the selected Python environment.
"""

import argparse
import json
import sys


def build_parser():
    """Build the command-line parser without importing Django or DRF."""
    parser = argparse.ArgumentParser(
        description="Serialize a deterministic LineString as GeoJSON geometry."
    )
    parser.add_argument(
        "--precision",
        type=int,
        default=None,
        help="round coordinate numbers to this many decimal places",
    )
    parser.add_argument(
        "--remove-duplicates",
        action="store_true",
        help="remove sequential duplicate coordinates",
    )
    parser.add_argument(
        "--auto-bbox",
        action="store_true",
        help="include the geometry extent as bbox",
    )
    return parser


def configure_django():
    """Configure and initialize Django before importing DRF-dependent code."""
    try:
        from django.conf import settings

        if not settings.configured:
            settings.configure(
                SECRET_KEY="geometry-smoke",
                INSTALLED_APPS=(
                    "django.contrib.gis",
                    "rest_framework",
                    "rest_framework_gis",
                ),
                DEFAULT_CHARSET="utf-8",
                USE_I18N=False,
                USE_TZ=True,
            )

        import django

        django.setup()
    except Exception as exc:
        raise ImportError(
            "Could not initialize Django for the geometry smoke check. "
            "Install Django >=4.2, djangorestframework >=3.12,<3.19, and "
            "djangorestframework-gis 1.3.0a0; ensure GeoDjango can load its "
            f"GEOS/GDAL libraries. Original error: {exc}"
        ) from exc


def import_runtime():
    """Import public runtime APIs and turn setup failures into useful errors."""
    try:
        from django.contrib.gis.geos import LineString
        from rest_framework import serializers
        from rest_framework_gis.fields import GeometryField
    except Exception as exc:
        raise ImportError(
            "Could not import the geometry serialization APIs. Install "
            "Django >=4.2, djangorestframework >=3.12,<3.19, and "
            "djangorestframework-gis 1.3.0a0 with compatible GEOS/GDAL "
            f"libraries. Original error: {exc}"
        ) from exc
    return LineString, serializers, GeometryField


def serialize_geometry(precision, remove_duplicates, auto_bbox):
    """Return deterministic serializer data using only GEOS and DRF APIs."""
    LineString, serializers, GeometryField = import_runtime()

    class GeometrySerializer(serializers.Serializer):
        geometry = GeometryField(
            precision=precision,
            remove_duplicates=remove_duplicates,
            auto_bbox=auto_bbox,
        )

    geometry = LineString(
        (12.34567, 45.67891),
        (12.34567, 45.67891),
        (12.34678, 45.67999),
    )
    return GeometrySerializer({"geometry": geometry}).data


def main(argv=None):
    """Parse options, run the GEOS-only check, and print compact JSON."""
    args = build_parser().parse_args(argv)
    try:
        configure_django()
        result = serialize_geometry(
            precision=args.precision,
            remove_duplicates=args.remove_duplicates,
            auto_bbox=args.auto_bbox,
        )
    except ImportError as exc:
        print(f"ImportError: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
