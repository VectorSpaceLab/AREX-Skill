#!/usr/bin/env python3
"""Report ClearML configuration signals without printing secret values."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

SECRET_ENV = [
    "CLEARML_API_ACCESS_KEY",
    "CLEARML_API_SECRET_KEY",
    "TRAINS_API_ACCESS_KEY",
    "TRAINS_API_SECRET_KEY",
]
HOST_ENV = [
    "CLEARML_API_HOST",
    "CLEARML_WEB_HOST",
    "CLEARML_FILES_HOST",
    "TRAINS_API_HOST",
    "TRAINS_WEB_HOST",
    "TRAINS_FILES_HOST",
]
CONFIG_ENV = [
    "CLEARML_CONFIG_FILE",
    "TRAINS_CONFIG_FILE",
    "CLEARML_CONFIG_PATH",
    "TRAINS_CONFIG_PATH",
    "CLEARML_OFFLINE_MODE",
    "TRAINS_OFFLINE_MODE",
    "CLEARML_NO_DEFAULT_SERVER",
    "TRAINS_NO_DEFAULT_SERVER",
]
DEFAULT_CONFIG_FILES = [Path.home() / "trains.conf", Path.home() / "clearml.conf"]


def _present_env(names: Iterable[str]) -> Dict[str, bool]:
    return {name: bool(os.environ.get(name)) for name in names}


def _path_signal(raw_path: Optional[str]) -> Dict[str, Any]:
    if not raw_path:
        return {"set": False, "exists": False, "is_file": False, "is_dir": False}
    expanded = Path(os.path.expandvars(os.path.expanduser(raw_path)))
    return {
        "set": True,
        "exists": expanded.exists(),
        "is_file": expanded.is_file(),
        "is_dir": expanded.is_dir(),
    }


def _default_config_signals() -> List[Dict[str, Any]]:
    signals = []
    for path in DEFAULT_CONFIG_FILES:
        signals.append(
            {
                "name": path.name,
                "exists": path.exists(),
                "is_file": path.is_file(),
                "non_empty": path.is_file() and path.stat().st_size > 0,
            }
        )
    return signals


def collect_signals() -> Dict[str, Any]:
    secret_presence = _present_env(SECRET_ENV)
    host_presence = _present_env(HOST_ENV)
    config_presence = _present_env(CONFIG_ENV)

    config_file = os.environ.get("CLEARML_CONFIG_FILE") or os.environ.get("TRAINS_CONFIG_FILE")
    config_path = os.environ.get("CLEARML_CONFIG_PATH") or os.environ.get("TRAINS_CONFIG_PATH")

    has_access_key = secret_presence["CLEARML_API_ACCESS_KEY"] or secret_presence["TRAINS_API_ACCESS_KEY"]
    has_secret_key = secret_presence["CLEARML_API_SECRET_KEY"] or secret_presence["TRAINS_API_SECRET_KEY"]
    has_api_host = host_presence["CLEARML_API_HOST"] or host_presence["TRAINS_API_HOST"]
    default_configs = _default_config_signals()
    has_config_file = any(item["exists"] and item["non_empty"] for item in default_configs)
    override_file_signal = _path_signal(config_file)
    override_path_signal = _path_signal(config_path)

    likely_configured = (has_access_key and has_secret_key and has_api_host) or bool(
        override_file_signal["is_file"] or has_config_file
    )

    warnings: List[str] = []
    if has_access_key != has_secret_key:
        warnings.append("Only one credential key variable is present; both access and secret keys are needed.")
    if (has_access_key and has_secret_key) and not has_api_host:
        warnings.append("Credential variables are present but no API host variable was detected.")
    if override_file_signal["set"] and not override_file_signal["is_file"]:
        warnings.append("Config file override is set but does not point to an existing file.")
    if override_path_signal["set"] and not override_path_signal["is_dir"]:
        warnings.append("Config path override is set but does not point to an existing directory.")
    if not likely_configured:
        warnings.append("No complete credential+host env set or non-empty config file signal was detected.")

    return {
        "likely_configured": likely_configured,
        "credential_env_present": secret_presence,
        "host_env_present": host_presence,
        "config_env_present": config_presence,
        "config_file_override": override_file_signal,
        "config_path_override": override_path_signal,
        "default_config_files": default_configs,
        "offline_mode_env_present": bool(os.environ.get("CLEARML_OFFLINE_MODE") or os.environ.get("TRAINS_OFFLINE_MODE")),
        "demo_server_override_present": bool(
            os.environ.get("CLEARML_NO_DEFAULT_SERVER") or os.environ.get("TRAINS_NO_DEFAULT_SERVER")
        ),
        "warnings": warnings,
    }


def print_text(signals: Dict[str, Any]) -> None:
    print("ClearML environment signal check")
    print(f"Likely configured: {'yes' if signals['likely_configured'] else 'no'}")
    print("Credential variables present:")
    for name, present in signals["credential_env_present"].items():
        print(f"  {name}: {'present' if present else 'missing'}")
    print("Host variables present:")
    for name, present in signals["host_env_present"].items():
        print(f"  {name}: {'present' if present else 'missing'}")
    print("Config variables present:")
    for name, present in signals["config_env_present"].items():
        print(f"  {name}: {'present' if present else 'missing'}")
    print("Config file override:")
    print(
        "  set={set} exists={exists} is_file={is_file}".format(
            **signals["config_file_override"]
        )
    )
    print("Config path override:")
    print(
        "  set={set} exists={exists} is_dir={is_dir}".format(
            **signals["config_path_override"]
        )
    )
    print("Default config file signals:")
    for item in signals["default_config_files"]:
        print(
            "  {name}: exists={exists} is_file={is_file} non_empty={non_empty}".format(
                **item
            )
        )
    if signals["warnings"]:
        print("Warnings:")
        for warning in signals["warnings"]:
            print(f"  - {warning}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check ClearML credential/config signals without printing secret values."
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    signals = collect_signals()
    if args.json:
        print(json.dumps(signals, indent=2, sort_keys=True))
    else:
        print_text(signals)
    return 0 if signals["likely_configured"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
