#!/usr/bin/env python3
"""Safe Superduper import/config/Datalayer smoke helper.

Default mode imports Superduper and reports package facts. Optional --build-db
constructs a scratch Datalayer through the public Python API. The helper never
uses the Superduper console script and never drops a database unless --drop-db is
explicitly supplied for the scratch database you created for this smoke.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from importlib import metadata
from typing import Any


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Superduper imports and optionally build a scratch Datalayer."
    )
    parser.add_argument(
        "--check-imports",
        action="store_true",
        help="Import public Superduper modules and report versions/signatures.",
    )
    parser.add_argument(
        "--build-db",
        action="store_true",
        help="Build a scratch Datalayer using --uri or the selected config.",
    )
    parser.add_argument(
        "--uri",
        default="mongomock://superduper-skill-smoke",
        help="Data backend URI for --build-db when --config-path is not supplied.",
    )
    parser.add_argument(
        "--config-path",
        default=None,
        help="Optional Superduper YAML config path. Set before importing Superduper.",
    )
    parser.add_argument(
        "--drop-db",
        action="store_true",
        help="After --build-db, call db.drop(force=True, data=True). Use only scratch URIs.",
    )
    parser.add_argument(
        "--as-json",
        action="store_true",
        help="Emit JSON instead of a readable summary.",
    )
    return parser.parse_args(argv)


def configure_environment(args: argparse.Namespace, tempdir: str) -> None:
    if args.config_path:
        os.environ["SUPERDUPER_CONFIG"] = args.config_path
    else:
        # Set artifact path before importing because this Superduper version reads
        # artifact_store from process-global config during Datalayer construction.
        os.environ.setdefault(
            "SUPERDUPER_ARTIFACT_STORE", f"filesystem://{tempdir}/artifact_store"
        )
        os.environ.setdefault("SUPERDUPER_LOG_LEVEL", "ERROR")


def import_superduper() -> dict[str, Any]:
    try:
        import inspect
        import superduper
        from superduper import Document, ObjectModel, Schema, Table, superduper as connect
    except Exception as exc:  # pragma: no cover - diagnostic path
        raise RuntimeError(
            "Could not import Superduper. Install `superduper-framework` and any "
            f"selected backend plugin in the active Python environment. Original error: {exc}"
        ) from exc

    try:
        framework_version = metadata.version("superduper-framework")
    except metadata.PackageNotFoundError:
        framework_version = getattr(superduper, "__version__", "unknown")

    return {
        "framework_version": framework_version,
        "public_module_version": getattr(superduper, "__version__", "unknown"),
        "objects": {
            "superduper": str(inspect.signature(connect)),
            "Document": str(inspect.signature(Document)),
            "Schema": str(inspect.signature(Schema)),
            "Table": str(inspect.signature(Table)),
            "ObjectModel": str(inspect.signature(ObjectModel)),
        },
    }


def build_db(uri: str, *, drop_db: bool) -> dict[str, Any]:
    from superduper import ObjectModel, superduper as connect

    model = ObjectModel(identifier="skill-double", object=lambda x: x * 2)
    prediction = model.predict(3)
    db = connect(uri, force_apply=True, initialize_cluster=False)
    try:
        shown = db.show(render=False)
        return {
            "uri": uri,
            "datalayer_type": type(db).__name__,
            "databackend_type": type(db.databackend).__name__,
            "cluster_type": type(db.cluster).__name__ if db.cluster else None,
            "component_rows": len(shown) if shown is not None else None,
            "object_model_prediction": prediction,
        }
    finally:
        if drop_db:
            db.drop(force=True, data=True)
        else:
            disconnect = getattr(db, "disconnect", None)
            if callable(disconnect):
                disconnect()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if not args.check_imports and not args.build_db:
        args.check_imports = True

    with tempfile.TemporaryDirectory(prefix="superduper-datalayer-smoke-") as tempdir:
        configure_environment(args, tempdir)
        result: dict[str, Any] = {
            "checks": [],
            "warnings": [],
        }
        try:
            if args.check_imports:
                result["imports"] = import_superduper()
                result["checks"].append("imports")
            else:
                import_superduper()

            if args.build_db:
                result["datalayer"] = build_db(args.uri, drop_db=args.drop_db)
                result["checks"].append("build-db")
        except Exception as exc:
            result["error_type"] = type(exc).__name__
            result["error"] = str(exc)
            if "superduper_mongodb" in str(exc):
                result["hint"] = "Install the MongoDB plugin for mongomock/mongodb URIs."
            elif "superduper_sql" in str(exc):
                result["hint"] = "Install the SQL plugin for sqlite/duckdb/postgresql/mysql/mssql URIs."
            elif "No support for uri" in str(exc) or "valid connection string" in str(exc):
                result["hint"] = "Use a supported URI scheme such as mongomock://, mongodb://, sqlite://, duckdb://, redis://, snowflake://, or inmemory://."
            else:
                result["hint"] = "Check package installation, config path, backend plugin, and selected URI."
            print(json.dumps(result, indent=2, sort_keys=True))
            return 1

        if args.as_json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print("Superduper Datalayer smoke")
            print("===========================")
            print(json.dumps(result, indent=2, sort_keys=True))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
