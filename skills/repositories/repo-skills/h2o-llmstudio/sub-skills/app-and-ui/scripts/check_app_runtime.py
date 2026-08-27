#!/usr/bin/env python3
"""Safe preflight checks for the H2O LLM Studio Wave app runtime.

The script does not start a long-lived Wave server. By default it performs
read-only checks for imports, runtime-root assets, environment settings, workdir
layout, port state, and optional URL reachability. Pass --prepare-dirs to create
missing application data/output directories intentionally.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import os
import shutil
import socket
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SECRET_MARKERS = ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL")


@dataclass
class Check:
    name: str
    status: str
    detail: str


@dataclass
class Report:
    runtime_root: str
    workdir: str
    checks: list[Check] = field(default_factory=list)

    def add(self, name: str, status: str, detail: str) -> None:
        self.checks.append(Check(name=name, status=status, detail=detail))

    @property
    def failed(self) -> bool:
        return any(c.status == "fail" for c in self.checks)

    @property
    def warned(self) -> bool:
        return any(c.status == "warn" for c in self.checks)


def status_symbol(status: str) -> str:
    return {"pass": "OK", "warn": "WARN", "fail": "FAIL"}.get(status, status)


def is_secret_env(name: str) -> bool:
    upper = name.upper()
    return any(marker in upper for marker in SECRET_MARKERS)


def import_check(module: str) -> tuple[str, str]:
    try:
        imported = importlib.import_module(module)
    except Exception as exc:  # noqa: BLE001 - diagnostics should preserve message
        return "fail", f"could not import {module}: {exc.__class__.__name__}: {exc}"
    location = getattr(imported, "__file__", None)
    return "pass", f"imported {module}" + (f" from {location}" if location else "")


def distribution_detail(name: str) -> tuple[str, str]:
    try:
        version = importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "warn", f"distribution metadata for {name!r} was not found"
    except Exception as exc:  # noqa: BLE001
        return "warn", f"could not read distribution metadata: {exc}"
    return "pass", f"{name} distribution version: {version}"


def path_writable(path: Path) -> bool:
    if path.exists():
        return os.access(path, os.W_OK)
    parent = path.parent if path.parent != path else Path(".")
    while not parent.exists() and parent.parent != parent:
        parent = parent.parent
    return os.access(parent, os.W_OK)


def check_runtime_assets(report: Report, runtime_root: Path) -> None:
    required = [
        Path("llm_studio/app.py"),
        Path("llm_studio/app_utils/static/icon_300.svg"),
        Path("llm_studio/python_configs"),
        Path("pyproject.toml"),
        Path("prompts"),
        Path("model_cards"),
    ]
    missing = [str(rel) for rel in required if not (runtime_root / rel).exists()]
    if missing:
        report.add(
            "runtime assets",
            "fail",
            "missing expected runtime-root assets: " + ", ".join(missing),
        )
    else:
        report.add(
            "runtime assets",
            "pass",
            "runtime root contains app module, static icon, configs, prompts, and model-card assets",
        )


def check_workdir(report: Report, workdir: Path, prepare_dirs: bool) -> None:
    dirs = [
        workdir / "data" / "user",
        workdir / "data" / "dbs",
        workdir / "output" / "user",
        workdir / "output" / "download",
    ]
    missing = [p for p in dirs if not p.exists()]
    if missing and prepare_dirs:
        for path in missing:
            path.mkdir(parents=True, exist_ok=True)
        report.add("workdir directories", "pass", "created missing data/output directories")
    elif missing:
        report.add(
            "workdir directories",
            "warn",
            "missing directories (app creates them on first client request): "
            + ", ".join(str(p) for p in missing),
        )
    else:
        report.add("workdir directories", "pass", "data/output directories already exist")

    unwritable = [str(p) for p in dirs if p.exists() and not path_writable(p)]
    if unwritable:
        report.add("workdir writable", "fail", "not writable: " + ", ".join(unwritable))
    else:
        report.add("workdir writable", "pass", "existing workdir directories are writable or can be created")


def check_wave_private_dir(report: Report, workdir: Path) -> None:
    value = os.environ.get("H2O_WAVE_PRIVATE_DIR", "")
    expected_suffix = str(workdir / "output" / "download")
    if not value:
        report.add(
            "H2O_WAVE_PRIVATE_DIR",
            "warn",
            "not set; set it to /download/@<workdir>/output/download before running Wave for app downloads",
        )
        return
    if not value.startswith("/download/@"):
        report.add(
            "H2O_WAVE_PRIVATE_DIR",
            "warn",
            "set, but it does not start with /download/@; downloads may not be served as expected",
        )
        return
    if expected_suffix not in value:
        report.add(
            "H2O_WAVE_PRIVATE_DIR",
            "warn",
            "set, but it does not appear to target this workdir's output/download directory",
        )
        return
    report.add("H2O_WAVE_PRIVATE_DIR", "pass", "maps /download to this workdir's output/download directory")


def check_environment(report: Report) -> None:
    visible = [
        "H2O_LLM_STUDIO_WORKDIR",
        "H2O_LLM_STUDIO_ENABLE_HEAP",
        "H2O_LLM_STUDIO_DEFAULT_LM_MODELS",
        "H2O_LLM_STUDIO_DEFAULT_S2S_MODELS",
        "H2O_LLM_STUDIO_DEMO_DATASETS",
        "MIN_DISK_SPACE_FOR_EXPERIMENTS",
        "ALLOWED_FILE_EXTENSIONS",
        "H2O_WAVE_MAX_REQUEST_SIZE",
        "H2O_WAVE_NO_LOG",
        "H2O_WAVE_ALLOWED_ORIGINS",
        "H2O_WAVE_BASE_URL",
        "H2O_WAVE_APP_CONNECT_TIMEOUT",
        "H2O_WAVE_APP_WRITE_TIMEOUT",
        "H2O_WAVE_APP_READ_TIMEOUT",
        "H2O_WAVE_APP_POOL_TIMEOUT",
        "HF_HUB_DISABLE_TELEMETRY",
        "HF_HUB_ENABLE_HF_TRANSFER",
        "HF_HOME",
        "TRITON_CACHE_DIR",
    ]
    parts = []
    for name in visible:
        if name in os.environ:
            value = "<set>" if is_secret_env(name) else os.environ[name]
            parts.append(f"{name}={value}")
    if parts:
        report.add("environment", "pass", "; ".join(parts))
    else:
        report.add("environment", "warn", "no app-specific environment variables are set")

    secret_names = sorted(name for name in os.environ if is_secret_env(name))
    if secret_names:
        report.add(
            "secret environment",
            "pass",
            "secret-like variables present but values were not printed: " + ", ".join(secret_names),
        )


def check_commands(report: Report) -> None:
    wave = shutil.which("wave")
    if wave:
        report.add("wave command", "pass", f"found wave executable: {wave}")
    else:
        report.add("wave command", "warn", "wave executable not found on PATH; use the environment's wave command")

    nvidia_smi = shutil.which("nvidia-smi")
    if nvidia_smi:
        try:
            proc = subprocess.run(
                [nvidia_smi, "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                check=False,
            )
        except Exception as exc:  # noqa: BLE001
            report.add("nvidia-smi", "warn", f"found nvidia-smi but query failed: {exc}")
        else:
            if proc.returncode == 0:
                first = proc.stdout.strip().splitlines()[0] if proc.stdout.strip() else "no GPUs listed"
                report.add("nvidia-smi", "pass", first)
            else:
                report.add("nvidia-smi", "warn", proc.stderr.strip() or "nvidia-smi returned nonzero")
    else:
        report.add("nvidia-smi", "warn", "not found; make llmstudio will not pass its GPU guard")


def check_python(report: Report) -> None:
    version = sys.version_info
    if version.major == 3 and version.minor == 10:
        report.add("python version", "pass", sys.version.split()[0])
    else:
        report.add("python version", "fail", f"expected Python 3.10.*, found {sys.version.split()[0]}")

    for dist in ("h2o-llmstudio", "h2o-wave"):
        status, detail = distribution_detail(dist)
        report.add(f"distribution {dist}", status, detail)

    for module in ("h2o_wave", "llm_studio", "llm_studio.app", "llm_studio.app_utils.setting_utils"):
        status, detail = import_check(module)
        report.add(f"import {module}", status, detail)

    try:
        import keyring  # type: ignore

        backend = keyring.get_keyring().__class__.__name__
        report.add("keyring backend", "pass", f"keyring import succeeded; active backend class: {backend}")
    except Exception as exc:  # noqa: BLE001
        report.add("keyring backend", "warn", f"keyring import/backend check failed: {exc}")

    try:
        import torch  # type: ignore

        cuda_available = torch.cuda.is_available()
        devices = torch.cuda.device_count() if cuda_available else 0
        detail = f"torch {torch.__version__}; cuda_available={cuda_available}; device_count={devices}"
        report.add("torch", "pass" if cuda_available else "warn", detail)
    except Exception as exc:  # noqa: BLE001
        report.add("torch", "warn", f"torch check failed: {exc}")


def check_port(report: Report, host: str, port: int) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1.0)
    try:
        result = sock.connect_ex((host, port))
    finally:
        sock.close()
    if result == 0:
        report.add("port 10101", "warn", f"{host}:{port} is already accepting TCP connections")
    else:
        report.add("port 10101", "pass", f"{host}:{port} is free or not accepting connections")


def check_url(report: Report, url: str, timeout: float) -> None:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:  # noqa: S310 - user-requested diagnostic URL
            report.add("url", "pass", f"{url} returned HTTP {response.status}")
    except urllib.error.HTTPError as exc:
        report.add("url", "warn", f"{url} returned HTTP {exc.code}")
    except Exception as exc:  # noqa: BLE001
        report.add("url", "warn", f"could not reach {url}: {exc.__class__.__name__}: {exc}")


def print_report(report: Report, as_json: bool) -> None:
    if as_json:
        print(json.dumps(asdict(report), indent=2, sort_keys=True))
        return

    print("H2O LLM Studio app runtime preflight")
    print(f"runtime_root: {report.runtime_root}")
    print(f"workdir:      {report.workdir}")
    for check in report.checks:
        print(f"[{status_symbol(check.status):4}] {check.name}: {check.detail}")

    print("\nSuggested direct app command:")
    print("  H2O_WAVE_MAX_REQUEST_SIZE=25MB \\")
    print("  H2O_WAVE_NO_LOG=true \\")
    print("  H2O_WAVE_PRIVATE_DIR=\"/download/@${H2O_LLM_STUDIO_WORKDIR:-$PWD}/output/download\" \\")
    print("  wave run llm_studio.app")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check H2O LLM Studio Wave app prerequisites without starting a long-lived server. "
            "Defaults are read-only."
        )
    )
    parser.add_argument(
        "--runtime-root",
        default=".",
        help="Runtime root containing llm_studio/, pyproject.toml, prompts/, and model_cards/ (default: current directory).",
    )
    parser.add_argument(
        "--workdir",
        default=None,
        help="Application workdir to inspect. Defaults to H2O_LLM_STUDIO_WORKDIR, then runtime root.",
    )
    parser.add_argument(
        "--prepare-dirs",
        action="store_true",
        help="Create missing data/user, data/dbs, output/user, and output/download directories.",
    )
    parser.add_argument(
        "--check-url",
        default=None,
        help="Optional URL to probe after a server is already running, for example http://localhost:10101/.",
    )
    parser.add_argument("--timeout", type=float, default=5.0, help="Timeout in seconds for optional URL checks.")
    parser.add_argument("--host", default="127.0.0.1", help="Host for default port-open check (default: 127.0.0.1).")
    parser.add_argument("--port", type=int, default=10101, help="Port for default port-open check (default: 10101).")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit nonzero on warnings as well as failures. Default exits nonzero only on failures.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    runtime_root = Path(args.runtime_root).expanduser().resolve()
    workdir = Path(args.workdir or os.environ.get("H2O_LLM_STUDIO_WORKDIR") or runtime_root).expanduser().resolve()

    report = Report(runtime_root=str(runtime_root), workdir=str(workdir))
    check_runtime_assets(report, runtime_root)
    check_workdir(report, workdir, args.prepare_dirs)
    check_wave_private_dir(report, workdir)
    check_environment(report)
    check_commands(report)
    check_python(report)
    check_port(report, args.host, args.port)
    if args.check_url:
        check_url(report, args.check_url, args.timeout)

    print_report(report, args.json)

    if report.failed:
        return 2
    if args.strict and report.warned:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
