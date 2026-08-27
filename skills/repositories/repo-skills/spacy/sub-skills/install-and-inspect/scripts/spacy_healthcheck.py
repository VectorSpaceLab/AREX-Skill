#!/usr/bin/env python3
"""Safe spaCy installed-package healthcheck.

Purpose:
  Verify the active Python environment can import the public ``spacy`` package,
  report ``spacy.__version__``, tokenize with ``spacy.blank("en")``, load the
  ``python -m spacy`` CLI, and optionally probe an installed model package/path
  or GPU backend.

Safe defaults:
  - No package installation.
  - No model downloads.
  - No training.
  - No writes except normal stdout/stderr.
  - No dependency on a spaCy source checkout or a specific current directory.

Examples:
  python spacy_healthcheck.py
  python spacy_healthcheck.py --json
  python spacy_healthcheck.py --model en_core_web_sm --require-model
  python spacy_healthcheck.py --prefer-gpu
  python spacy_healthcheck.py --require-gpu --gpu-id 0

``--run-validate`` executes ``python -m spacy validate``. That command may need
network access for compatibility metadata and may return non-zero for stale
pipeline packages even when base spaCy is healthy.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

Status = Dict[str, Any]


def result(name: str, status: str, message: str, **details: Any) -> Status:
    entry: Status = {"name": name, "status": status, "message": message}
    if details:
        entry["details"] = details
    return entry


def run_module_spacy(args: List[str], timeout: float) -> Tuple[int, str]:
    """Run ``python -m spacy ...`` without exposing interpreter paths."""
    display = "python -m spacy" + (" " + " ".join(args) if args else "")
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "spacy", *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return 124, f"{display} timed out after {timeout:g}s"
    except Exception as e:  # pragma: no cover - defensive environment report
        return 125, f"{display} could not be executed: {type(e).__name__}: {e}"
    if completed.returncode == 0:
        return 0, f"{display} exited 0"
    return completed.returncode, f"{display} exited {completed.returncode}"


def check_python_version() -> Status:
    version = sys.version_info
    version_text = f"{version.major}.{version.minor}.{version.micro}"
    if (version.major, version.minor) < (3, 9) or (version.major, version.minor) >= (3, 15):
        return result(
            "python-version",
            "fail",
            "Python is outside spaCy's supported range for this skill snapshot (>=3.9,<3.15).",
            python=version_text,
        )
    return result("python-version", "pass", "Python version is within >=3.9,<3.15.", python=version_text)


def check_import_and_blank() -> Tuple[Optional[Any], List[Status]]:
    checks: List[Status] = []
    try:
        import spacy  # type: ignore[import-not-found]
    except Exception as e:
        checks.append(
            result(
                "import-spacy",
                "fail",
                f"Could not import spacy: {type(e).__name__}: {e}",
                hint="Install the public spacy package in the active Python environment and run python -m pip check.",
            )
        )
        checks.append(result("blank-en", "skip", "Skipped because spacy import failed."))
        return None, checks

    checks.append(result("import-spacy", "pass", "Imported spacy.", version=getattr(spacy, "__version__", "unknown")))

    try:
        nlp = spacy.blank("en")
        doc = nlp("Hello, spaCy!")
        tokens = [token.text for token in doc]
        expected = ["Hello", ",", "spaCy", "!"]
        if tokens != expected:
            checks.append(
                result(
                    "blank-en",
                    "fail",
                    "Blank English tokenization returned unexpected tokens.",
                    tokens=tokens,
                    expected=expected,
                )
            )
        else:
            checks.append(
                result(
                    "blank-en",
                    "pass",
                    "spacy.blank('en') tokenized the sample text as expected.",
                    lang=getattr(nlp, "lang", None),
                    pipe_names=list(getattr(nlp, "pipe_names", [])),
                    tokens=tokens,
                )
            )
    except Exception as e:
        checks.append(result("blank-en", "fail", f"spacy.blank('en') failed: {type(e).__name__}: {e}"))

    return spacy, checks


def check_cli(timeout: float, run_validate: bool) -> List[Status]:
    checks: List[Status] = []
    code, message = run_module_spacy(["--help"], timeout)
    checks.append(result("cli-help", "pass" if code == 0 else "fail", message, exit_code=code))

    code, message = run_module_spacy(["info", "--silent"], timeout)
    checks.append(result("cli-info-silent", "pass" if code == 0 else "fail", message, exit_code=code))

    if run_validate:
        code, message = run_module_spacy(["validate"], timeout)
        if code == 0:
            checks.append(result("cli-validate", "pass", message, exit_code=code))
        else:
            checks.append(
                result(
                    "cli-validate",
                    "fail",
                    message,
                    exit_code=code,
                    note=(
                        "validate may fail for stale pipeline packages or unavailable compatibility metadata; "
                        "this is separate from base import/blank-pipeline health."
                    ),
                )
            )
    else:
        checks.append(result("cli-validate", "skip", "Skipped; pass --run-validate to execute python -m spacy validate."))
    return checks


def model_exists(model: str) -> bool:
    path = Path(model)
    if path.exists():
        return True
    # Treat only import-like names as packages. find_spec() can raise for invalid names.
    if not model.replace("_", "").replace(".", "").isalnum():
        return False
    try:
        return importlib.util.find_spec(model) is not None
    except (ImportError, AttributeError, ValueError):
        return False


def check_model(spacy: Any, model: Optional[str], require_model: bool) -> Status:
    if not model:
        return result("model-load", "skip", "Skipped; pass --model NAME_OR_PATH to check an installed pipeline.")

    exists = model_exists(model)
    if not exists:
        status = "fail" if require_model else "warn"
        return result(
            "model-load",
            status,
            f"Model package/path {model!r} was not found.",
            hint="Install the pipeline package, provide a valid pipeline directory, or use spacy.blank('en') for no-download checks.",
        )

    try:
        nlp = spacy.load(model)
        doc = nlp("This is a sentence.")
        return result(
            "model-load",
            "pass",
            f"Loaded pipeline {model!r} and processed a sample sentence.",
            pipe_names=list(getattr(nlp, "pipe_names", [])),
            doc_length=len(doc),
            lang=getattr(nlp, "lang", None),
        )
    except Exception as e:
        return result(
            "model-load",
            "fail",
            f"spacy.load({model!r}) failed: {type(e).__name__}: {e}",
            hint="Run python -m spacy validate for installed package compatibility or check that the path is a valid saved pipeline.",
        )


def check_gpu(spacy: Any, prefer_gpu: bool, require_gpu: bool, gpu_id: int) -> List[Status]:
    checks: List[Status] = []
    if prefer_gpu:
        try:
            ok = bool(spacy.prefer_gpu(gpu_id))
            checks.append(
                result(
                    "prefer-gpu",
                    "pass" if ok else "warn",
                    "spacy.prefer_gpu() returned True." if ok else "spacy.prefer_gpu() returned False; CPU workflow can continue.",
                    gpu_id=gpu_id,
                )
            )
        except Exception as e:
            checks.append(result("prefer-gpu", "warn", f"spacy.prefer_gpu() raised {type(e).__name__}: {e}", gpu_id=gpu_id))
    else:
        checks.append(result("prefer-gpu", "skip", "Skipped; pass --prefer-gpu to probe optional acceleration."))

    if require_gpu:
        try:
            ok = bool(spacy.require_gpu(gpu_id))
            checks.append(
                result(
                    "require-gpu",
                    "pass" if ok else "fail",
                    "spacy.require_gpu() returned True." if ok else "spacy.require_gpu() returned False.",
                    gpu_id=gpu_id,
                )
            )
        except Exception as e:
            checks.append(
                result(
                    "require-gpu",
                    "fail",
                    f"spacy.require_gpu() failed: {type(e).__name__}: {e}",
                    gpu_id=gpu_id,
                    hint="Install a matching CUDA/CuPy or Apple backend extra, or remove the hard GPU requirement.",
                )
            )
    else:
        checks.append(result("require-gpu", "skip", "Skipped; pass --require-gpu when GPU is a hard requirement."))
    return checks


def print_human(checks: List[Status]) -> None:
    icons = {"pass": "PASS", "fail": "FAIL", "warn": "WARN", "skip": "SKIP"}
    for item in checks:
        print(f"[{icons.get(item['status'], item['status'].upper())}] {item['name']}: {item['message']}")
        details = item.get("details") or {}
        for key in ("version", "python", "tokens", "pipe_names", "exit_code", "hint", "note"):
            if key in details:
                print(f"  - {key}: {details[key]}")


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run safe spaCy import, blank-pipeline, CLI, model, and optional GPU checks.")
    parser.add_argument("--model", help="Installed pipeline package name or local pipeline directory to load with spacy.load().")
    parser.add_argument("--require-model", action="store_true", help="Fail if --model is provided but missing.")
    parser.add_argument("--skip-cli", action="store_true", help="Skip python -m spacy --help and info --silent checks.")
    parser.add_argument("--run-validate", action="store_true", help="Also run python -m spacy validate; may need network and may fail for stale pipelines.")
    parser.add_argument("--prefer-gpu", action="store_true", help="Call spacy.prefer_gpu(gpu_id); False is reported as a warning, not a failure.")
    parser.add_argument("--require-gpu", action="store_true", help="Call spacy.require_gpu(gpu_id); failure makes the healthcheck fail.")
    parser.add_argument("--gpu-id", type=int, default=0, help="GPU id to pass to prefer_gpu/require_gpu. Default: 0.")
    parser.add_argument("--timeout", type=float, default=20.0, help="Timeout in seconds for each CLI subprocess. Default: 20.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of human-readable lines.")
    return parser.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    checks: List[Status] = [check_python_version()]

    spacy, import_checks = check_import_and_blank()
    checks.extend(import_checks)

    if args.skip_cli:
        checks.extend(
            [
                result("cli-help", "skip", "Skipped by --skip-cli."),
                result("cli-info-silent", "skip", "Skipped by --skip-cli."),
                result("cli-validate", "skip", "Skipped by --skip-cli."),
            ]
        )
    else:
        checks.extend(check_cli(args.timeout, args.run_validate))

    if spacy is None:
        checks.append(result("model-load", "skip", "Skipped because spacy import failed."))
        checks.append(result("prefer-gpu", "skip", "Skipped because spacy import failed."))
        checks.append(result("require-gpu", "skip", "Skipped because spacy import failed."))
    else:
        checks.append(check_model(spacy, args.model, args.require_model))
        checks.extend(check_gpu(spacy, args.prefer_gpu, args.require_gpu, args.gpu_id))

    failed = any(item["status"] == "fail" for item in checks)
    summary = {
        "ok": not failed,
        "checks": checks,
        "notes": [
            "Warnings for missing optional GPU/model capabilities do not fail the base CPU package healthcheck.",
            "This helper never downloads pretrained models or installs packages.",
        ],
    }

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_human(checks)
        print(f"[SUMMARY] {'ok' if not failed else 'failed'}")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
