#!/usr/bin/env python3
"""Check img2img-turbo source-checkout imports, CUDA visibility, and CLI help.

This helper is safe by default: it does not download checkpoints, launch Gradio,
or run model inference/training. It only imports source modules, checks selected
source CLI `--help` outputs, and optionally performs a tiny CUDA allocation.
"""

from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

BASE_IMPORTS = [
    "torch",
    "torchvision",
    "torchaudio",
    "numpy",
    "PIL.Image",
    "cv2",
    "accelerate",
    "diffusers",
    "transformers",
    "peft",
    "huggingface_hub",
    "requests",
    "tqdm",
]

SCOPED_IMPORTS = {
    "paired": [
        "gradio",
        "image_prep",
        "pix2pix_turbo",
    ],
    "unpaired": [
        "xformers",
        "cyclegan_turbo",
        "model",
        "my_utils.training_utils",
    ],
    "training": [
        "clip",
        "lpips",
        "cleanfid",
        "vision_aided_loss",
        "my_utils.dino_struct",
        "my_utils.training_utils",
        "cyclegan_turbo",
        "model",
    ],
}

SCOPED_HELP = {
    "paired": ["src/inference_paired.py"],
    "unpaired": ["src/inference_unpaired.py"],
    "training": ["src/train_pix2pix_turbo.py", "src/train_cyclegan_turbo.py"],
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Check img2img-turbo source-checkout imports, CUDA visibility, and "
            "selected source CLI help outputs."
        )
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Repository root to inspect. Defaults to the current working directory.",
    )
    parser.add_argument(
        "--scope",
        choices=("paired", "unpaired", "training", "all"),
        default="all",
        help="Which workflow stack to validate (default: all).",
    )
    parser.add_argument(
        "--check-help",
        action="store_true",
        help="Run safe --help checks for the selected source CLI scripts.",
    )
    parser.add_argument(
        "--require-cuda",
        action="store_true",
        help="Require CUDA visibility and a tiny allocation smoke check.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of a human-readable summary.",
    )
    return parser


def resolve_repo_root(value: str | None) -> Path:
    if value:
        return Path(value).expanduser().resolve()
    return Path.cwd().resolve()


def scope_imports(scope: str) -> list[str]:
    imports = list(BASE_IMPORTS)
    if scope == "all":
        for names in SCOPED_IMPORTS.values():
            imports.extend(names)
        return imports
    imports.extend(SCOPED_IMPORTS[scope])
    return imports


def scope_help_scripts(scope: str) -> list[str]:
    if scope == "all":
        return [script for scripts in SCOPED_HELP.values() for script in scripts]
    return SCOPED_HELP[scope]


def import_name(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # pragma: no cover - depends on caller env
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    detail: dict[str, Any] = {"ok": True}
    version = getattr(module, "__version__", None)
    if version is not None:
        detail["version"] = str(version)
    return detail


def run_help(script: Path, repo_root: Path) -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, str(script), "--help"],
        cwd=repo_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return {
        "script": str(script.as_posix()),
        "returncode": proc.returncode,
        "ok": proc.returncode == 0,
        "stdout_tail": proc.stdout.splitlines()[-12:],
        "stderr_tail": proc.stderr.splitlines()[-12:],
    }


def cuda_smoke() -> dict[str, Any]:
    try:
        import torch
    except Exception as exc:  # pragma: no cover - depends on caller env
        return {"ok": False, "error": f"torch import failed: {type(exc).__name__}: {exc}"}

    result: dict[str, Any] = {
        "ok": bool(torch.cuda.is_available()),
        "available": bool(torch.cuda.is_available()),
        "device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
    }
    if torch.cuda.is_available():
        try:
            device_name = torch.cuda.get_device_name(0)
            result["device_name"] = device_name
            torch.empty(1, device="cuda")
            result["allocation_ok"] = True
        except Exception as exc:  # pragma: no cover - depends on caller env
            result["ok"] = False
            result["allocation_ok"] = False
            result["error"] = f"{type(exc).__name__}: {exc}"
    elif result["ok"] is False:
        result["error"] = "CUDA not available"
    return result


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    repo_root = resolve_repo_root(args.repo_root)

    src_root = repo_root / "src"
    if src_root.is_dir():
        sys.path.insert(0, str(src_root))

    imports = {name: import_name(name) for name in scope_imports(args.scope)}
    import_failures = [name for name, data in imports.items() if not data.get("ok")]

    help_checks: list[dict[str, Any]] = []
    if args.check_help:
        for script_rel in scope_help_scripts(args.scope):
            script = repo_root / script_rel
            if not script.exists():
                help_checks.append(
                    {
                        "script": script_rel,
                        "ok": False,
                        "returncode": None,
                        "stderr_tail": [f"missing script: {script}"],
                        "stdout_tail": [],
                    }
                )
                import_failures.append(script_rel)
                continue
            help_checks.append(run_help(script, repo_root))

    cuda = None
    if args.require_cuda:
        cuda = cuda_smoke()
        if not cuda.get("ok"):
            import_failures.append("cuda")

    report = {
        "repo_root": str(repo_root),
        "scope": args.scope,
        "imports": imports,
        "help_checks": help_checks,
        "cuda": cuda,
        "ok": not import_failures,
        "failures": import_failures,
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"repo_root: {repo_root}")
        print(f"scope: {args.scope}")
        print(f"imports_ok: {not import_failures}")
        if import_failures:
            print("failures:")
            for item in import_failures:
                print(f"  - {item}")
        if cuda is not None:
            print(f"cuda: {cuda}")
        if help_checks:
            print("help_checks:")
            for entry in help_checks:
                status = "ok" if entry.get("ok") else "fail"
                print(f"  - {entry['script']}: {status}")
    return 0 if not import_failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
