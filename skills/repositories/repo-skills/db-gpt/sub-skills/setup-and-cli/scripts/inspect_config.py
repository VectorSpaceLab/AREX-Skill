#!/usr/bin/env python3
"""Read-only structural checker for a DB-GPT TOML configuration.

This helper deliberately uses only the Python standard library.  It does not
import DB-GPT, resolve environment variables, contact a provider, open a
 database, or write/normalize the input file.  It reports only redacted key
status and semantic configuration facts.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Any

_ENV_REF = re.compile(
    r"^\$\{env:(?P<name>[A-Za-z_][A-Za-z0-9_]*)(?::-?(?P<default>.*))?\}$"
)
_SECRET_NAMES = {"api_key", "api_keys", "password", "access_key_secret", "secret_key"}
_ALLOWED_TOP = {
    "system",
    "service",
    "models",
    "rag",
    "app",
    "hooks",
    "serve",
    "serves",
    "tracer",
    "embedding",
    "storage",
}


def _env_status(value: Any) -> dict[str, Any]:
    """Return a non-secret description of a credential-like value."""
    if value is None:
        return {"status": "missing"}
    if not isinstance(value, str):
        return {"status": "invalid-type", "type": type(value).__name__}
    if not value:
        return {"status": "empty"}
    match = _ENV_REF.fullmatch(value)
    if match:
        result: dict[str, Any] = {"status": "environment-reference", "name": match["name"]}
        if match["default"] is not None:
            result["has_default"] = True
        return result
    return {"status": "literal-redacted"}


def _table(value: Any, name: str) -> tuple[dict[str, Any] | None, list[str]]:
    if value is None:
        return None, [f"missing [{name}]"]
    if not isinstance(value, dict):
        return None, [f"[{name}] must be a TOML table"]
    return value, []


def _check(path: Path) -> tuple[dict[str, Any], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    except FileNotFoundError:
        return {"file": path.name, "valid": False}, ["file does not exist"], []
    except OSError as exc:
        return {"file": path.name, "valid": False}, [f"cannot read file: {exc}"], []
    except tomllib.TOMLDecodeError as exc:
        return {"file": path.name, "valid": False}, [f"invalid TOML: {exc}"], []

    if not isinstance(data, dict):
        return {"file": path.name, "valid": False}, ["top level must be a TOML table"], []

    unknown = sorted(set(data) - _ALLOWED_TOP)
    if unknown:
        warnings.append("unrecognized top-level tables: " + ", ".join(unknown))

    system = data.get("system")
    if system is not None and not isinstance(system, dict):
        errors.append("[system] must be a TOML table")

    service = data.get("service")
    if service is not None and not isinstance(service, dict):
        errors.append("[service] must be a TOML table")
    web = service.get("web") if isinstance(service, dict) else None
    if web is not None and not isinstance(web, dict):
        errors.append("[service.web] must be a TOML table")
    if isinstance(web, dict):
        port = web.get("port")
        if port is not None:
            if not isinstance(port, int) or isinstance(port, bool) or not 1 <= port <= 65535:
                errors.append("[service.web].port must be an integer from 1 to 65535")
        database = web.get("database")
        if database is not None and not isinstance(database, dict):
            errors.append("[service.web.database] must be a TOML table")
        elif isinstance(database, dict):
            db_type = database.get("type")
            if db_type is None:
                warnings.append("[service.web.database] has no type")
            elif not isinstance(db_type, str):
                errors.append("[service.web.database].type must be a string")
            if str(db_type).lower() == "sqlite" and not database.get("path"):
                errors.append("SQLite database configuration needs [service.web.database].path")

    models = data.get("models")
    if models is not None and not isinstance(models, dict):
        errors.append("[models] must be a TOML table")
    llms = models.get("llms") if isinstance(models, dict) else None
    embeddings = models.get("embeddings") if isinstance(models, dict) else None
    if models is not None and not isinstance(llms, list):
        errors.append("[models].llms must be an array of tables")
    if models is not None and not isinstance(embeddings, list):
        errors.append("[models].embeddings must be an array of tables")

    model_summary: list[dict[str, Any]] = []
    for kind, entries in (("llms", llms), ("embeddings", embeddings)):
        if not isinstance(entries, list):
            continue
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                errors.append(f"models.{kind}[{index}] must be a table")
                continue
            for field in ("name", "provider"):
                if field not in entry:
                    warnings.append(f"models.{kind}[{index}] has no {field}")
                elif not isinstance(entry[field], str):
                    errors.append(f"models.{kind}[{index}].{field} must be a string")
            item: dict[str, Any] = {"kind": kind, "index": index}
            for field in ("name", "provider"):
                if field in entry and isinstance(entry[field], str):
                    item[field] = entry[field]
            if "api_key" in entry:
                item["api_key"] = _env_status(entry["api_key"])
            elif "api_keys" in entry:
                item["api_keys"] = _env_status(entry["api_keys"])
            else:
                item["api_key"] = {"status": "not-specified"}
            model_summary.append(item)

    for section_name, section in (("system", system), ("service.web", web)):
        if isinstance(section, dict):
            for key in _SECRET_NAMES:
                if key in section:
                    # Do not include values, even redacted values, in the raw data.
                    warnings.append(f"{section_name}.{key} is credential-like; keep it redacted")

    result: dict[str, Any] = {
        "file": path.name,
        "valid": not errors,
        "top_level_tables": sorted(data),
        "web": {
            "host_configured": isinstance(web, dict) and "host" in web,
            "port": web.get("port") if isinstance(web, dict) and isinstance(web.get("port"), int) else None,
            "database_type": (
                web.get("database", {}).get("type")
                if isinstance(web, dict) and isinstance(web.get("database"), dict)
                else None
            ),
            "database_path_configured": (
                bool(web.get("database", {}).get("path"))
                if isinstance(web, dict) and isinstance(web.get("database"), dict)
                else False
            ),
        },
        "models": model_summary,
        "errors": errors,
        "warnings": warnings,
    }
    return result, errors, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only DB-GPT TOML structure checker")
    parser.add_argument("config", type=Path, help="TOML configuration file")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Emit machine-readable JSON")
    args = parser.parse_args(argv)
    result, errors, _ = _check(args.config)
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        state = "valid" if result["valid"] else "invalid"
        print(f"{state}: {result['file']}")
        web = result.get("web", {})
        if web.get("port") is not None:
            print(f"web.port: {web['port']}")
        if web.get("database_type"):
            print(f"database.type: {web['database_type']}")
        for model in result.get("models", []):
            provider = model.get("provider", "<missing>")
            name = model.get("name", "<missing>")
            key = model.get("api_key", model.get("api_keys", {"status": "not-specified"}))
            print(f"{model['kind']}[{model['index']}]: name={name!r} provider={provider!r} key={key.get('status')}")
        for warning in result.get("warnings", []):
            print(f"warning: {warning}", file=sys.stderr)
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
