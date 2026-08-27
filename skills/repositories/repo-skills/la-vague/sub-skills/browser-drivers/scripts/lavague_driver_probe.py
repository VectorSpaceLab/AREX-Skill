#!/usr/bin/env python3
"""Safe LaVague browser-driver probe.

Default behavior:
- report import/signature status for Selenium and/or Playwright
- report browser-binary availability hints
- do NOT launch a browser unless --construct is passed

This script is designed to be safe by default. It only probes installed
packages and local executables unless explicit construction is requested.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import inspect
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

os.environ.setdefault("LAVAGUE_TELEMETRY", "NONE")


SELENIUM_COMMANDS = [
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
    "chrome",
    "chromedriver",
]


def package_version(dist_name: str) -> Optional[str]:
    try:
        return metadata.version(dist_name)
    except metadata.PackageNotFoundError:
        return None


def safe_signature(obj: Any) -> Optional[str]:
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError):
        return None


def try_import(path: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {"module": path}
    try:
        module = importlib.import_module(path)
        result["status"] = "ok"
        result["module_file"] = getattr(module, "__file__", None)
        result["module_name"] = getattr(module, "__name__", path)
        return result
    except Exception as exc:  # pragma: no cover - surfaced in JSON output
        result["status"] = "missing"
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)
        return result


def probe_driver_module(driver: str) -> Dict[str, Any]:
    if driver == "selenium":
        module_name = "lavague.drivers.selenium"
        class_name = "SeleniumDriver"
        package_names = ["lavague-drivers-selenium", "selenium"]
    elif driver == "playwright":
        module_name = "lavague.drivers.playwright"
        class_name = "PlaywrightDriver"
        package_names = ["lavague-drivers-playwright", "playwright"]
    else:
        raise ValueError(f"Unsupported driver: {driver}")

    module_status = try_import(module_name)
    package_status = {
        name: {"version": package_version(name)} for name in package_names
    }

    class_status: Dict[str, Any] = {"name": class_name}
    if module_status.get("status") == "ok":
        module = importlib.import_module(module_name)
        cls = getattr(module, class_name, None)
        if cls is None:
            class_status.update(
                {
                    "status": "missing",
                    "error": f"{class_name} not exported by {module_name}",
                }
            )
        else:
            class_status.update(
                {
                    "status": "ok",
                    "signature": safe_signature(cls),
                }
            )
            if driver == "selenium":
                browserbase = getattr(module, "BrowserbaseRemoteConnection", None)
                if browserbase is not None:
                    class_status["browserbase_signature"] = safe_signature(browserbase)
    else:
        class_status.update({"status": "skipped"})

    return {
        "driver": driver,
        "imports": module_status,
        "packages": package_status,
        "class": class_status,
    }


def report_selenium_binaries() -> Dict[str, Any]:
    binaries = []
    for command in SELENIUM_COMMANDS:
        binaries.append({"command": command, "path": shutil.which(command)})
    return {"commands": binaries}


def report_playwright_binaries() -> Dict[str, Any]:
    report: Dict[str, Any] = {"cache_roots": [], "playwright_cli": None}

    try:
        module_status = try_import("playwright")
        report["playwright_import"] = module_status
        if module_status.get("status") == "ok":
            completed = subprocess.run(
                [sys.executable, "-m", "playwright", "--version"],
                capture_output=True,
                text=True,
                check=False,
            )
            report["playwright_cli"] = {
                "returncode": completed.returncode,
                "stdout": completed.stdout.strip(),
                "stderr": completed.stderr.strip(),
            }
    except Exception as exc:  # pragma: no cover - surfaced in JSON output
        report["playwright_import"] = {
            "module": "playwright",
            "status": "missing",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }

    candidate_roots: List[Path] = []
    env_root = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if env_root and env_root != "0":
        candidate_roots.append(Path(env_root).expanduser())
    candidate_roots.append(Path.home() / ".cache" / "ms-playwright")
    if os.name == "nt":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            candidate_roots.append(Path(local_app_data) / "ms-playwright")

    seen = set()
    roots = []
    for root in candidate_roots:
        normalized = str(root)
        if normalized in seen:
            continue
        seen.add(normalized)
        if root.exists():
            executables = []
            for path in root.rglob("*"):
                if path.is_file() and path.name.lower() in {
                    "chromium",
                    "chrome",
                    "chrome.exe",
                    "msedge",
                    "msedge.exe",
                }:
                    executables.append(str(path))
            roots.append(
                {
                    "path": str(root),
                    "exists": True,
                    "executables": executables[:10],
                    "child_dirs": [p.name for p in list(root.iterdir())[:20] if p.is_dir()],
                }
            )
        else:
            roots.append({"path": str(root), "exists": False})
    report["cache_roots"] = roots
    return report


def close_driver_instance(driver_obj: Any) -> Dict[str, Any]:
    result: Dict[str, Any] = {"closed": False, "cleanup": []}
    raw = None
    try:
        raw = driver_obj.get_driver()
    except Exception as exc:
        result["cleanup"].append(
            {"step": "get_driver", "status": "error", "error": str(exc)}
        )

    try:
        if raw is not None and hasattr(raw, "context"):
            context = raw.context
            browser = getattr(context, "browser", None)
            if browser is not None:
                try:
                    browser.close()
                    result["cleanup"].append(
                        {"step": "browser.close", "status": "ok"}
                    )
                except Exception as exc:
                    result["cleanup"].append(
                        {
                            "step": "browser.close",
                            "status": "error",
                            "error": str(exc),
                        }
                    )
            try:
                context.close()
                result["cleanup"].append({"step": "context.close", "status": "ok"})
            except Exception as exc:
                result["cleanup"].append(
                    {"step": "context.close", "status": "error", "error": str(exc)}
                )
    except Exception as exc:
        result["cleanup"].append(
            {"step": "context inspection", "status": "error", "error": str(exc)}
        )

    try:
        driver_obj.destroy()
        result["closed"] = True
        result["cleanup"].append({"step": "destroy", "status": "ok"})
    except Exception as exc:
        result["cleanup"].append(
            {"step": "destroy", "status": "error", "error": str(exc)}
        )

    return result


def construct_driver(driver: str, headless: bool, url: Optional[str]) -> Dict[str, Any]:
    if driver == "selenium":
        module_name = "lavague.drivers.selenium"
        class_name = "SeleniumDriver"
    elif driver == "playwright":
        module_name = "lavague.drivers.playwright"
        class_name = "PlaywrightDriver"
    else:
        raise ValueError(f"Unsupported driver: {driver}")

    module_status = try_import(module_name)
    if module_status.get("status") != "ok":
        return {
            "driver": driver,
            "constructed": False,
            "skipped": True,
            "reason": module_status.get("error", "module import failed"),
        }

    module = importlib.import_module(module_name)
    cls = getattr(module, class_name)
    kwargs: Dict[str, Any] = {"headless": headless}
    if url is not None:
        kwargs["url"] = url

    driver_obj = None
    try:
        driver_obj = cls(**kwargs)
        raw = None
        try:
            raw = driver_obj.get_driver()
        except Exception:
            raw = None
        summary: Dict[str, Any] = {
            "driver": driver,
            "constructed": True,
            "headless": headless,
            "url": url,
            "driver_class": class_name,
            "raw_type": type(raw).__name__ if raw is not None else None,
        }
        try:
            summary["current_url"] = driver_obj.get_url()
        except Exception as exc:
            summary["current_url_error"] = str(exc)
        return summary
    except Exception as exc:
        return {
            "driver": driver,
            "constructed": False,
            "headless": headless,
            "url": url,
            "driver_class": class_name,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
    finally:
        if driver_obj is not None:
            close_driver_instance(driver_obj)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Probe LaVague Selenium and Playwright drivers safely.")
    parser.add_argument(
        "--driver",
        choices=("selenium", "playwright", "both"),
        default="both",
        help="Which driver(s) to inspect or construct.",
    )
    parser.add_argument(
        "--check-imports",
        action="store_true",
        help="Include import and signature checks. These are already part of the default safe probe.",
    )
    parser.add_argument(
        "--check-browser-binaries",
        action="store_true",
        help="Include local browser/driver binary hints. These are already part of the default safe probe.",
    )
    parser.add_argument(
        "--construct",
        action="store_true",
        help="Explicitly attempt driver construction. This may launch a browser.",
    )
    headless_group = parser.add_mutually_exclusive_group()
    headless_group.add_argument(
        "--headless",
        dest="headless",
        action="store_true",
        default=True,
        help="Construct the browser in headless mode (default).",
    )
    headless_group.add_argument(
        "--headed",
        dest="headless",
        action="store_false",
        help="Construct the browser in headed mode.",
    )
    parser.add_argument(
        "--url",
        default=None,
        help="Optional URL to pass during explicit construction. Omit for a blank-page construction check.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    report: Dict[str, Any] = {
        "probe": "lavague_driver_probe",
        "python": {
            "version": sys.version.split()[0],
            "platform": sys.platform,
        },
        "requested": {
            "driver": args.driver,
            "construct": args.construct,
            "headless": args.headless,
            "url": args.url,
        },
        "imports": {},
        "browser_binaries": {},
        "construct": [],
    }

    # Safe probe always reports imports and local binary hints.
    if args.driver in ("selenium", "both"):
        report["imports"]["selenium"] = probe_driver_module("selenium")
        report["browser_binaries"]["selenium"] = report_selenium_binaries()
    if args.driver in ("playwright", "both"):
        report["imports"]["playwright"] = probe_driver_module("playwright")
        report["browser_binaries"]["playwright"] = report_playwright_binaries()

    if args.construct:
        targets = [args.driver] if args.driver != "both" else ["selenium", "playwright"]
        for target in targets:
            report["construct"].append(construct_driver(target, args.headless, args.url))

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
