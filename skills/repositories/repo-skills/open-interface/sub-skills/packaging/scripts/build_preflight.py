#!/usr/bin/env python3
"""Safe Open Interface packaging preflight.

This helper inspects packaging expectations without importing PyInstaller,
without running build.py, without creating dist/build artifacts, and without
signing or notarizing anything.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

COMMON_OPTIONS = [
    "--clean",
    "--noconfirm",
    "--name=Open Interface",
    "--icon=app/resources/icon.png",
    "--windowed",
    "--paths=./env/lib/python3.12/site-packages",
]

COMMON_HIDDEN_IMPORTS = [
    "pyautogui",
    "appdirs",
    "pyparsing",
    "ttkbootstrap",
    "openai",
    "google_genai",
    "google",
    "google.genai",
]

PLATFORM_HIDDEN_IMPORTS = {
    "Linux": ["PIL._tkinter_finder"],
    "Darwin": [],
    "Windows": [],
}

ADD_DATA_ENTRIES = [
    "app/resources/*:resources",
    "app/*.py:.",
    "app/utils/*.py:utils",
    "app/models/*.py:models",
]

REQUIRED_PATHS = [
    ("build.py", "file", "source build helper"),
    ("requirements.txt", "file", "dependency pins"),
    ("app/app.py", "file", "PyInstaller entry point"),
    ("app/version.py", "file", "release version module"),
    ("app/resources/icon.png", "file", "PyInstaller icon"),
    ("app/resources/context.txt", "file", "LLM prompt resource bundled as data"),
    ("app/models", "dir", "model backend modules bundled as data"),
    ("app/utils", "dir", "utility modules bundled as data"),
]

IMPORTANT_REQUIREMENTS = [
    "pyinstaller",
    "pyinstaller-hooks-contrib",
    "pyautogui",
    "pyaudio",
    "pillow",
    "ttkbootstrap",
    "openai",
    "google-genai",
    "packaging",
]

MACOS_REQUIREMENTS = [
    "pyobjc-core",
    "pyobjc-framework-cocoa",
    "pyobjc-framework-quartz",
    "rubicon-objc",
]

STATUS_RANK = {"pass": 0, "info": 0, "warn": 1, "fail": 2}


def normalize_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(errors="replace")
    except FileNotFoundError:
        return ""


def add_check(checks: list[dict[str, Any]], check_id: str, status: str, message: str, **details: Any) -> None:
    check: dict[str, Any] = {"id": check_id, "status": status, "message": message}
    if details:
        check["details"] = details
    checks.append(check)


def overall_status(checks: list[dict[str, Any]]) -> str:
    rank = max((STATUS_RANK.get(check["status"], 0) for check in checks), default=0)
    if rank >= STATUS_RANK["fail"]:
        return "fail"
    if rank >= STATUS_RANK["warn"]:
        return "warn"
    return "pass"


def check_required_paths(root: Path, checks: list[dict[str, Any]]) -> None:
    for rel, kind, label in REQUIRED_PATHS:
        path = root / rel
        exists = path.is_file() if kind == "file" else path.is_dir()
        add_check(
            checks,
            f"path:{rel}",
            "pass" if exists else "fail",
            f"Found {label}." if exists else f"Missing {label}: {rel}.",
            expected=kind,
        )


def check_globs(root: Path, checks: list[dict[str, Any]]) -> None:
    glob_map = {
        "app/resources/*": "resources add-data source",
        "app/*.py": "top-level app modules add-data source",
        "app/utils/*.py": "utils modules add-data source",
        "app/models/*.py": "model modules add-data source",
    }
    for pattern, label in glob_map.items():
        matches = sorted(str(path.relative_to(root)) for path in root.glob(pattern) if path.is_file())
        add_check(
            checks,
            f"glob:{pattern}",
            "pass" if matches else "fail",
            f"{label} has {len(matches)} file(s)." if matches else f"No files matched {pattern}.",
            matches=matches[:20],
            truncated=len(matches) > 20,
        )


def check_build_tokens(build_text: str, checks: list[dict[str, Any]]) -> None:
    if not build_text:
        add_check(checks, "build-text:present", "fail", "Cannot inspect build.py text because it is missing or unreadable.")
        return

    add_check(checks, "build-text:present", "pass", "build.py text is readable.")

    for option in COMMON_OPTIONS:
        add_check(
            checks,
            f"pyinstaller-option:{option}",
            "pass" if option in build_text else "fail",
            f"Expected common PyInstaller option present: {option}." if option in build_text else f"Expected common PyInstaller option missing: {option}.",
        )

    for hidden in COMMON_HIDDEN_IMPORTS:
        token = f"--hidden-import={hidden}"
        add_check(
            checks,
            f"hidden-import:{hidden}",
            "pass" if token in build_text else "fail",
            f"Expected hidden import present: {hidden}." if token in build_text else f"Expected hidden import missing: {hidden}.",
        )

    for entry in ADD_DATA_ENTRIES:
        token = f"--add-data={entry}"
        add_check(
            checks,
            f"add-data:{entry}",
            "pass" if token in build_text else "fail",
            f"Expected add-data entry present: {entry}." if token in build_text else f"Expected add-data entry missing: {entry}.",
        )

    platform_tokens = {
        "linux-branch": "platform.system() == 'Linux'",
        "linux-pil-tk-hidden-import": "--hidden-import=PIL._tkinter_finder",
        "linux-onefile": "--onefile",
        "windows-branch": "platform.system() == 'Windows'",
        "darwin-branch": "platform.system() == 'Darwin'",
        "macos-codesign-option": "--codesign-identity=",
        "macos-codesign-command": "codesign --deep --force --verbose --sign",
        "macos-notary-command": "xcrun notarytool submit --wait",
        "macos-staple-command": "xcrun stapler staple",
        "macos-ditto-archive": "ditto -c -k --sequesterRsrc --keepParent",
        "linux-zip-command": "zip -r9",
        "windows-compress-archive": "Compress-Archive",
    }
    for check_id, token in platform_tokens.items():
        add_check(
            checks,
            f"platform-token:{check_id}",
            "pass" if token in build_text else "fail",
            f"Expected platform/release token present: {token}." if token in build_text else f"Expected platform/release token missing: {token}.",
        )

    side_effect_tokens = {
        "pyinstaller-run": "PyInstaller.__main__.run",
        "dependency-install": "pip install -r requirements.txt",
        "interactive-input": "input(",
        "shell-system": "os.system(",
    }
    for check_id, token in side_effect_tokens.items():
        add_check(
            checks,
            f"side-effect-marker:{check_id}",
            "warn" if token in build_text else "info",
            f"Source build helper contains side-effect marker `{token}`; preflight did not execute it."
            if token in build_text
            else f"Side-effect marker `{token}` was not found.",
        )


def parse_requirements(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    if not path.is_file():
        return result
    for raw_line in read_text(path).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        package_part = re.split(r"[<>=;\[]", line, maxsplit=1)[0].strip()
        if package_part:
            result[normalize_name(package_part)] = line
    return result


def check_requirements(root: Path, target_platform: str, checks: list[dict[str, Any]]) -> dict[str, str]:
    requirements = parse_requirements(root / "requirements.txt")
    if not requirements:
        add_check(checks, "requirements:read", "fail", "requirements.txt is missing or has no parseable package entries.")
        return requirements
    add_check(checks, "requirements:read", "pass", f"Parsed {len(requirements)} requirement entries.")

    for package in IMPORTANT_REQUIREMENTS:
        norm = normalize_name(package)
        add_check(
            checks,
            f"requirement:{package}",
            "pass" if norm in requirements else "warn",
            f"Requirement entry found: {requirements.get(norm, package)}."
            if norm in requirements
            else f"Expected build/runtime package not listed directly: {package}.",
        )

    if target_platform == "Darwin":
        for package in MACOS_REQUIREMENTS:
            norm = normalize_name(package)
            add_check(
                checks,
                f"requirement-macos:{package}",
                "pass" if norm in requirements else "warn",
                f"macOS requirement entry found: {requirements.get(norm, package)}."
                if norm in requirements
                else f"macOS helper package not listed directly: {package}.",
            )
    return requirements


def check_version(root: Path, checks: list[dict[str, Any]]) -> dict[str, Any]:
    version_text = read_text(root / "app" / "version.py")
    match = re.search(r"Version\(\s*['\"]([^'\"]+)['\"]\s*\)", version_text)
    if match:
        value = match.group(1)
        add_check(
            checks,
            "version:app-version",
            "pass",
            f"Found app/version.py Version('{value}'). Confirm this is intended for the next release.",
            value=value,
            note="Snapshot evidence only; do not treat as eternal truth.",
        )
        return {"value": value, "source": "app/version.py", "status": "found"}
    add_check(
        checks,
        "version:app-version",
        "fail",
        "Could not find a packaging.version.Version('...') assignment in app/version.py.",
    )
    return {"value": None, "source": "app/version.py", "status": "missing"}


def check_freeze_support(root: Path, checks: list[dict[str, Any]]) -> None:
    app_text = read_text(root / "app" / "app.py")
    has_import = "from multiprocessing import freeze_support" in app_text or "multiprocessing.freeze_support" in app_text
    has_call = "freeze_support()" in app_text
    add_check(
        checks,
        "multiprocessing:freeze-support",
        "pass" if has_import and has_call else "warn",
        "App entry point includes multiprocessing freeze_support()."
        if has_import and has_call
        else "Could not confirm multiprocessing freeze_support() in app entry point.",
    )


def check_gitignore(root: Path, checks: list[dict[str, Any]]) -> None:
    text = read_text(root / ".gitignore")
    if not text:
        add_check(checks, "gitignore:present", "warn", ".gitignore is missing or unreadable; stale artifact ignore policy not confirmed.")
        return
    for token in ["dist/", "build/", "*.spec", "env/", "venv/"]:
        add_check(
            checks,
            f"gitignore:{token}",
            "pass" if token in text else "warn",
            f".gitignore lists {token}." if token in text else f".gitignore does not list expected build/env artifact {token}.",
        )


def check_relative_env_path(root: Path, checks: list[dict[str, Any]]) -> None:
    rel = Path("env") / "lib" / "python3.12" / "site-packages"
    exists = (root / rel).is_dir()
    add_check(
        checks,
        "build-env-path:relative-env-python312",
        "pass" if exists else "warn",
        "Relative build environment path used by --paths exists."
        if exists
        else "Relative --paths target ./env/lib/python3.12/site-packages does not exist; adapt it or create the documented build environment before a manual build.",
        relative_path=str(rel),
    )


def run_compileall(root: Path, checks: list[dict[str, Any]]) -> dict[str, Any]:
    targets: list[str] = []
    for rel in ["app", "tests", "build.py"]:
        if (root / rel).exists():
            targets.append(rel)
    if not targets:
        add_check(checks, "compileall:targets", "fail", "No compileall targets found.")
        return {"requested": True, "status": "fail", "targets": []}

    with tempfile.TemporaryDirectory(prefix="open_interface_preflight_pycache_") as pycache_dir:
        env = os.environ.copy()
        env["PYTHONPYCACHEPREFIX"] = pycache_dir
        proc = subprocess.run(
            [sys.executable, "-m", "compileall", "-q", *targets],
            cwd=str(root),
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

    status = "pass" if proc.returncode == 0 else "fail"
    add_check(
        checks,
        "compileall:syntax",
        status,
        "compileall passed for available app/tests/build.py targets using a temporary pycache prefix."
        if status == "pass"
        else "compileall failed for one or more app/tests/build.py targets.",
        targets=targets,
        returncode=proc.returncode,
        stdout=proc.stdout[-4000:],
        stderr=proc.stderr[-4000:],
    )
    return {
        "requested": True,
        "status": status,
        "targets": targets,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "pycache": "temporary",
    }


def build_expectation_payload(target_platform: str) -> dict[str, Any]:
    branch_options: list[str] = []
    branch_hidden = PLATFORM_HIDDEN_IMPORTS.get(target_platform, [])
    if target_platform in {"Linux", "Windows"}:
        branch_options.append("--onefile")
    if target_platform == "Darwin":
        branch_options.append("--codesign-identity=<signing key> when signing is requested")
    return {
        "commonOptions": COMMON_OPTIONS,
        "commonHiddenImports": COMMON_HIDDEN_IMPORTS,
        "addData": ADD_DATA_ENTRIES,
        "entryPoint": "app/app.py",
        "targetPlatform": target_platform,
        "platformHiddenImports": branch_hidden,
        "platformOptions": branch_options,
        "macosReleaseFlow": [
            "codesign --deep --force --verbose --sign <identity> dist/Open Interface.app --options runtime",
            "ditto archive before notary submission",
            "xcrun notarytool submit --wait --keychain-profile <profile>",
            "xcrun stapler staple dist/Open Interface.app",
            "ditto archive signed and stapled app",
        ],
        "manualOnly": [
            "source build.py",
            "PyInstaller execution",
            "pip install -r requirements.txt",
            "codesign/notary/staple",
            "dist/build cleanup or archive overwrite",
            "GUI launch or API-key tests",
        ],
    }


def make_report(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.repo_root).expanduser().resolve()
    target_platform = platform.system() if args.target_platform == "auto" else args.target_platform
    checks: list[dict[str, Any]] = []

    add_check(
        checks,
        "repo-root:exists",
        "pass" if root.is_dir() else "fail",
        "Repository root exists." if root.is_dir() else "Repository root does not exist or is not a directory.",
    )

    check_required_paths(root, checks)
    check_globs(root, checks)

    build_text = read_text(root / "build.py")
    check_build_tokens(build_text, checks)
    requirements = check_requirements(root, target_platform, checks)
    version_info = check_version(root, checks)
    check_freeze_support(root, checks)
    check_gitignore(root, checks)
    check_relative_env_path(root, checks)

    compile_result = {"requested": False, "status": "skipped"}
    if args.compile:
        compile_result = run_compileall(root, checks)

    report = {
        "schemaVersion": 1,
        "tool": "open-interface packaging build_preflight",
        "safety": {
            "importsPyInstaller": False,
            "runsBuildPy": False,
            "createsDistOrBuildArtifacts": False,
            "signsOrNotarizes": False,
            "launchesGuiOrUsesApiKeys": False,
        },
        "repoRoot": str(root),
        "host": {
            "system": platform.system(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python": sys.version.split()[0],
        },
        "targetPlatform": target_platform,
        "status": overall_status(checks),
        "checks": checks,
        "version": version_info,
        "requirementsFound": requirements,
        "expectedPyInstaller": build_expectation_payload(target_platform),
        "compileall": compile_result,
    }
    return report


def print_human(report: dict[str, Any]) -> None:
    print(f"Open Interface packaging preflight: {report['status'].upper()}")
    print(f"Target platform: {report['targetPlatform']} (host: {report['host']['system']} {report['host']['machine']})")
    version = report.get("version", {})
    if version.get("value"):
        print(f"Version evidence: app/version.py -> {version['value']} (confirm before release)")
    print("Safety: did not import PyInstaller, run build.py, create dist/build, sign/notarize, launch GUI, or use API keys.")
    print()
    for check in report["checks"]:
        status = check["status"].upper()
        print(f"[{status}] {check['id']}: {check['message']}")
    print()
    expected = report["expectedPyInstaller"]
    print("Expected common PyInstaller options:")
    for option in expected["commonOptions"]:
        print(f"  - {option}")
    print("Expected common hidden imports:")
    for hidden in expected["commonHiddenImports"]:
        print(f"  - {hidden}")
    if expected["platformOptions"] or expected["platformHiddenImports"]:
        print(f"Expected {report['targetPlatform']} branch additions:")
        for option in expected["platformOptions"]:
            print(f"  - {option}")
        for hidden in expected["platformHiddenImports"]:
            print(f"  - --hidden-import={hidden}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Safely inspect Open Interface packaging expectations without running build.py, "
            "PyInstaller, signing/notarization, GUI automation, or API calls."
        )
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Path to the Open Interface source tree to inspect (default: current directory).",
    )
    parser.add_argument(
        "--target-platform",
        choices=["auto", "Linux", "Darwin", "Windows"],
        default="auto",
        help="Platform branch to report expectations for; auto uses the current host platform.",
    )
    parser.add_argument(
        "--compile",
        action="store_true",
        help="Also run python -m compileall over available app/tests/build.py targets using a temporary pycache prefix.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of the human-readable report.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    report = make_report(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)
    return 1 if report["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
