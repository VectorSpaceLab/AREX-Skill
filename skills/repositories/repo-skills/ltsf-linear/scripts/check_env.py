#!/usr/bin/env python3
"""Cross-cutting environment and import smoke for the LTSF-Linear skill.

This helper is safe to run from an arbitrary current directory. It searches for
an LTSF-Linear checkout, imports the requested workflow family in an isolated
child Python, and optionally performs a tiny CUDA availability check.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT_IMPORTS = [
    "exp.exp_main",
    "data_provider.data_loader",
    "models.Linear",
    "models.DLinear",
    "models.NLinear",
    "models.Autoformer",
    "models.Informer",
    "models.Transformer",
    "models.Stat_models",
    "utils.tools",
    "utils.metrics",
    "utils.timefeatures",
]
FEDFORMER_IMPORTS = [
    "exp.exp_main",
    "data_provider.data_loader",
    "models.FEDformer",
    "models.Autoformer",
    "models.Informer",
    "models.Transformer",
    "layers.AutoCorrelation",
    "layers.FourierCorrelation",
    "layers.MultiWaveletCorrelation",
    "layers.utils",
    "utils.tools",
    "utils.metrics",
    "utils.timefeatures",
]
PYRAFORMER_IMPORTS = [
    "data_loader",
    "long_range_main",
    "single_step_main",
    "pyraformer.Pyraformer_LR",
    "pyraformer.Pyraformer_SS",
    "pyraformer.Layers",
    "pyraformer.SubLayers",
    "pyraformer.embed",
    "utils.tools",
    "utils.timefeatures",
]


def find_repo_root(anchor: Path) -> Path:
    candidates = [anchor, *anchor.parents]
    cwd = Path.cwd().resolve()
    candidates.extend([cwd, *cwd.parents])
    seen: set[Path] = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        if (candidate / "run_longExp.py").is_file() and (candidate / "Pyraformer" / "long_range_main.py").is_file():
            return candidate
    raise FileNotFoundError(
        "Could not locate the repository root. Pass --repo-root when running from outside the checkout."
    )


def make_import_code(package_root: Path, imports: list[str]) -> str:
    lines = [
        "import sys",
        f"sys.path.insert(0, {str(package_root)!r})",
    ]
    for module in imports:
        lines.append(f"__import__({module!r})")
        lines.append(f"print('OK {module}')")
    return "\n".join(lines)


def run_child(python: str, package_root: Path, imports: list[str], label: str) -> int:
    code = make_import_code(package_root, imports)
    command = [python, "-I", "-c", code]
    print(f"[{label}] {package_root}")
    print("  cmd:", " ".join(repr(part) for part in command))
    completed = subprocess.run(command, cwd=str(package_root), capture_output=True, text=True)
    if completed.stdout:
        for line in completed.stdout.rstrip().splitlines():
            print("  stdout:", line)
    if completed.stderr:
        for line in completed.stderr.rstrip().splitlines():
            print("  stderr:", line)
    if completed.returncode != 0:
        print(f"  status: failed ({completed.returncode})")
    else:
        print("  status: ok")
    return completed.returncode


def run_cuda_smoke(python: str) -> int:
    code = """
import torch
print('torch', torch.__version__)
print('cuda_version', torch.version.cuda)
print('cuda_available', torch.cuda.is_available())
print('device_count', torch.cuda.device_count())
if torch.cuda.is_available():
    x = torch.empty((1,), device='cuda')
    print('tensor_device', x.device)
""".strip()
    command = [python, "-I", "-c", code]
    print("[cuda-smoke]")
    print("  cmd:", " ".join(repr(part) for part in command))
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.stdout:
        for line in completed.stdout.rstrip().splitlines():
            print("  stdout:", line)
    if completed.stderr:
        for line in completed.stderr.rstrip().splitlines():
            print("  stderr:", line)
    if completed.returncode != 0:
        print(f"  status: failed ({completed.returncode})")
    else:
        print("  status: ok")
    return completed.returncode


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run shared import and CUDA readiness checks for the LTSF-Linear skill.")
    parser.add_argument("--repo-root", type=Path, default=None, help="Repository root containing the source checkout.")
    parser.add_argument("--python", default=sys.executable, help="Python interpreter to use for the child checks.")
    parser.add_argument("--scope", choices=("root", "fedformer", "pyraformer", "all"), default="all", help="Workflow family to check.")
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto", help="Whether to run a tiny CUDA smoke.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve() if args.repo_root else find_repo_root(Path(__file__).resolve())

    scopes = [args.scope] if args.scope != "all" else ["root", "fedformer", "pyraformer"]
    failures = 0
    for scope in scopes:
        if scope == "root":
            failures += 1 if run_child(args.python, repo_root, ROOT_IMPORTS, "root-imports") else 0
        elif scope == "fedformer":
            failures += 1 if run_child(args.python, repo_root / "FEDformer", FEDFORMER_IMPORTS, "fedformer-imports") else 0
        elif scope == "pyraformer":
            failures += 1 if run_child(args.python, repo_root / "Pyraformer", PYRAFORMER_IMPORTS, "pyraformer-imports") else 0

    if args.device == "cuda":
        failures += 1 if run_cuda_smoke(args.python) else 0
    elif args.device == "auto":
        cuda_ok = run_cuda_smoke(args.python)
        if cuda_ok != 0:
            failures += 1
    else:
        print("[cuda-smoke] skipped by request")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
