#!/usr/bin/env python3
"""Non-mutating Mycodo environment summary.

This helper can run from any directory. It does not install, upgrade, restart, or
modify Mycodo. It optionally inspects a Mycodo install/release root supplied with
--repo-root, otherwise it checks the public installed root /opt/Mycodo if present
and then tries an installed Python package import.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
from types import ModuleType
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple

PUBLIC_INSTALL_ROOT = Path("/opt/Mycodo")
PUBLIC_PATHS = {
    "install_root": PUBLIC_INSTALL_ROOT,
    "virtualenv_python": PUBLIC_INSTALL_ROOT / "env/bin/python",
    "settings_database": PUBLIC_INSTALL_ROOT / "databases/mycodo.db",
    "setup_log": PUBLIC_INSTALL_ROOT / "install/setup.log",
    "log_dir": Path("/var/log/mycodo"),
    "backup_dir": Path("/var/Mycodo-backups"),
    "nginx_access_log": Path("/var/log/nginx/access.log"),
    "nginx_error_log": Path("/var/log/nginx/error.log"),
    "flask_socket": Path("/usr/local/mycodoflask.sock"),
    "flask_pid": Path("/var/run/mycodoflask.pid"),
    "mycodo_commands": Path("/usr/bin/mycodo-commands"),
    "mycodo_client": Path("/usr/bin/mycodo-client"),
    "mycodo_python": Path("/usr/bin/mycodo-python"),
}
LOG_FILES = [
    "mycodo.log",
    "mycodoupgrade.log",
    "mycodobackup.log",
    "mycodorestore.log",
    "mycododependency.log",
    "mycodoimport.log",
    "mycodokeepup.log",
    "login.log",
]
SERVICE_NAMES = ["mycodo", "mycodoflask", "nginx", "influxdb", "influxd", "pigpiod"]


@contextlib.contextmanager
def temporary_sys_path(paths: Iterable[Path]) -> Iterator[None]:
    """Temporarily prepend paths to sys.path for optional config imports."""
    original = list(sys.path)
    for path in reversed([str(p) for p in paths if p]):
        if path not in sys.path:
            sys.path.insert(0, path)
    try:
        yield
    finally:
        sys.path[:] = original


def path_status(path: Path) -> Dict[str, Any]:
    try:
        stat = path.lstat()
        return {
            "path": str(path),
            "exists": True,
            "is_dir": path.is_dir(),
            "is_file": path.is_file(),
            "is_symlink": path.is_symlink(),
            "mode_octal": oct(stat.st_mode & 0o777),
        }
    except FileNotFoundError:
        return {
            "path": str(path),
            "exists": False,
            "is_dir": False,
            "is_file": False,
            "is_symlink": False,
            "mode_octal": None,
        }
    except OSError as exc:
        return {"path": str(path), "exists": None, "error": str(exc)}


def parse_config_constants(config_path: Path) -> Dict[str, Any]:
    """Best-effort parse for constants when importing config.py is unavailable."""
    result: Dict[str, Any] = {"source": str(config_path), "method": "regex-parse"}
    try:
        text = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        return {"source": str(config_path), "method": "regex-parse", "error": str(exc)}

    for name in ["MYCODO_VERSION", "ALEMBIC_VERSION", "BACKUP_PATH", "LOG_PATH"]:
        match = re.search(rf"^\s*{name}\s*=\s*['\"]([^'\"]+)['\"]", text, re.MULTILINE)
        if match:
            result[name.lower()] = match.group(1)

    docker = os.environ.get("DOCKER_CONTAINER", "").upper() == "TRUE"
    result["docker_container_env"] = docker
    result["pyro_uri_assumed"] = (
        "PYRO:mycodo.pyro_server@mycodo_daemon:9080"
        if docker
        else "PYRO:mycodo.pyro_server@127.0.0.1:9080"
    )
    return result


def module_to_config(module: ModuleType, source: str, method: str) -> Dict[str, Any]:
    names = [
        "MYCODO_VERSION",
        "ALEMBIC_VERSION",
        "INSTALL_DIRECTORY",
        "SQL_DATABASE_MYCODO",
        "MYCODO_DB_PATH",
        "BACKUP_PATH",
        "LOG_PATH",
        "DAEMON_LOG_FILE",
        "UPGRADE_LOG_FILE",
        "RESTORE_LOG_FILE",
        "IMPORT_LOG_FILE",
        "FRONTEND_PID_FILE",
        "PYRO_URI",
        "DOCKER_CONTAINER",
    ]
    data: Dict[str, Any] = {"source": source, "method": method, "import_ok": True}
    for name in names:
        if hasattr(module, name):
            value = getattr(module, name)
            data[name.lower()] = str(value) if isinstance(value, Path) else value
    return data


def import_config_from_root(root: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    config_path = root / "mycodo" / "config.py"
    if not config_path.exists():
        return None, f"No config.py found at {config_path}"

    try:
        with temporary_sys_path([root, root / "mycodo"]):
            spec = importlib.util.spec_from_file_location("mycodo_config_probe", config_path)
            if spec is None or spec.loader is None:
                return None, f"Could not create import spec for {config_path}"
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)  # type: ignore[union-attr]
        return module_to_config(module, str(config_path), "file-import"), None
    except Exception as exc:  # noqa: BLE001 - report import failures, do not crash
        parsed = parse_config_constants(config_path)
        parsed["import_ok"] = False
        parsed["import_error"] = repr(exc)
        return parsed, f"Config import failed; used best-effort parse: {exc}"


def import_installed_config() -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    try:
        module = importlib.import_module("mycodo.config")
        return module_to_config(module, "mycodo.config", "package-import"), None
    except Exception as exc:  # noqa: BLE001
        return None, f"Installed package config import failed: {exc}"


def service_status() -> Dict[str, Any]:
    if not shutil.which("systemctl"):
        return {"available": False, "reason": "systemctl not found"}
    statuses: Dict[str, Any] = {"available": True, "services": {}}
    for service in SERVICE_NAMES:
        item: Dict[str, Any] = {}
        for subcommand in ["is-active", "is-enabled"]:
            try:
                proc = subprocess.run(
                    ["systemctl", subcommand, service],
                    check=False,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=5,
                )
                item[subcommand.replace("-", "_")] = {
                    "returncode": proc.returncode,
                    "stdout": proc.stdout.strip(),
                    "stderr": proc.stderr.strip(),
                }
            except Exception as exc:  # noqa: BLE001
                item[subcommand.replace("-", "_")] = {"error": str(exc)}
        statuses["services"][service] = item
    return statuses


def build_report(args: argparse.Namespace) -> Dict[str, Any]:
    warnings: List[str] = [
        "Inspection only: this script does not install, upgrade, restart, restore, import, or modify Mycodo.",
        "This script does not prove Raspberry Pi GPIO/I2C/UART/1-Wire/Bluetooth/camera, systemd, nginx, InfluxDB, Docker, backup/restore, or full installer behavior.",
    ]

    python_info = {
        "executable": sys.executable,
        "version": sys.version.split()[0],
        "version_info": list(sys.version_info[:3]),
        "meets_mycodo_minimum_3_8": sys.version_info >= (3, 8),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python_implementation": platform.python_implementation(),
    }
    if sys.version_info < (3, 8):
        warnings.append("Mycodo install/upgrade checks require Python 3.8 or newer.")

    roots_checked: List[str] = []
    config: Optional[Dict[str, Any]] = None

    if args.repo_root:
        root = Path(args.repo_root).expanduser().resolve()
        roots_checked.append(str(root))
        config, warning = import_config_from_root(root)
        if warning:
            warnings.append(warning)
    elif PUBLIC_INSTALL_ROOT.exists():
        roots_checked.append(str(PUBLIC_INSTALL_ROOT))
        config, warning = import_config_from_root(PUBLIC_INSTALL_ROOT)
        if warning:
            warnings.append(warning)

    if config is None and not args.no_package_import:
        config, warning = import_installed_config()
        if warning:
            warnings.append(warning)

    public_paths = {name: path_status(path) for name, path in PUBLIC_PATHS.items()}
    log_paths = {name: path_status(Path("/var/log/mycodo") / name) for name in LOG_FILES}

    report: Dict[str, Any] = {
        "python": python_info,
        "roots_checked": roots_checked,
        "mycodo_config": config,
        "public_paths": public_paths,
        "log_files": log_paths,
        "public_service_names": SERVICE_NAMES,
        "expected_layout_notes": {
            "install_root": "/opt/Mycodo",
            "settings_database": "/opt/Mycodo/databases/mycodo.db",
            "backup_dir": "/var/Mycodo-backups",
            "log_dir": "/var/log/mycodo",
            "flask_socket": "/usr/local/mycodoflask.sock",
            "web_ports": [80, 443],
            "influxdb_port": 8086,
            "bare_metal_pyro_uri": "PYRO:mycodo.pyro_server@127.0.0.1:9080",
            "docker_pyro_uri": "PYRO:mycodo.pyro_server@mycodo_daemon:9080",
        },
        "warnings": warnings,
    }

    if args.systemd:
        report["systemd"] = service_status()

    return report


def print_text(report: Dict[str, Any]) -> None:
    py = report["python"]
    print("Mycodo environment summary (inspection only)")
    print("=" * 44)
    print(f"Python: {py['version']} ({py['executable']})")
    print(f"Python >= 3.8: {py['meets_mycodo_minimum_3_8']}")
    print(f"Platform: {py['platform']} [{py['machine']}]")
    print()

    roots = report.get("roots_checked") or []
    print("Roots checked:")
    if roots:
        for root in roots:
            print(f"  - {root}")
    else:
        print("  - none supplied/found")
    print()

    config = report.get("mycodo_config")
    print("Mycodo config:")
    if config:
        for key in [
            "source",
            "method",
            "import_ok",
            "mycodo_version",
            "alembic_version",
            "install_directory",
            "sql_database_mycodo",
            "mycodo_db_path",
            "backup_path",
            "log_path",
            "daemon_log_file",
            "upgrade_log_file",
            "restore_log_file",
            "import_log_file",
            "frontend_pid_file",
            "pyro_uri",
            "pyro_uri_assumed",
            "docker_container",
            "docker_container_env",
            "import_error",
        ]:
            if key in config:
                print(f"  {key}: {config[key]}")
    else:
        print("  unavailable")
    print()

    print("Public path status:")
    for name, status in report["public_paths"].items():
        exists = status.get("exists")
        marker = "exists" if exists else "missing" if exists is False else "unknown"
        extra = ""
        if status.get("is_symlink"):
            extra = " symlink"
        print(f"  {name}: {status.get('path')} [{marker}{extra}]")
    print()

    print("Known Mycodo log files:")
    for name, status in report["log_files"].items():
        exists = status.get("exists")
        marker = "exists" if exists else "missing" if exists is False else "unknown"
        print(f"  {name}: {marker}")
    print()

    if "systemd" in report:
        print("systemd service status:")
        systemd = report["systemd"]
        if not systemd.get("available"):
            print(f"  unavailable: {systemd.get('reason')}")
        else:
            for service, item in systemd["services"].items():
                active = item.get("is_active", {}).get("stdout")
                enabled = item.get("is_enabled", {}).get("stdout")
                print(f"  {service}: active={active!r} enabled={enabled!r}")
        print()

    print("Warnings:")
    for warning in report.get("warnings", []):
        print(f"  - {warning}")


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Report non-mutating Mycodo environment facts: Python version, optional "
            "config import/parse, public installed paths, log paths, and optional "
            "systemd status. Does not prove hardware or service behavior."
        )
    )
    parser.add_argument(
        "--repo-root",
        help=(
            "Path to a Mycodo install or release root containing mycodo/config.py. "
            "If omitted, /opt/Mycodo is checked when present, then an installed "
            "mycodo.config import is attempted."
        ),
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    parser.add_argument(
        "--systemd",
        action="store_true",
        help="Also run read-only systemctl is-active/is-enabled checks for public Mycodo-related services.",
    )
    parser.add_argument(
        "--no-package-import",
        action="store_true",
        help="Do not try importing mycodo.config from the active Python environment.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    report = build_report(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
