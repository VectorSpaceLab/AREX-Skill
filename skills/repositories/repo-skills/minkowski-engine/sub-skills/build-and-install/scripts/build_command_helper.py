#!/usr/bin/env python3
"""Print safe dry-run build commands for MinkowskiEngine.

This helper never installs, imports, compiles, deletes, or uninstalls anything.
It only formats recommended commands for a user-controlled shell.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from typing import Iterable, List


class RawDefaultsFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    """Preserve examples while showing defaults."""


BLAS_CHOICES = ("auto", "flexiblas", "openblas", "mkl", "atlas", "blas")


def shell_join(parts: Iterable[str]) -> str:
    """Quote command tokens for display while preserving env assignments."""
    rendered: List[str] = []
    for part in parts:
        if not part:
            continue
        if "=" in part and not part.startswith("--") and part.split("=", 1)[0].isidentifier():
            name, value = part.split("=", 1)
            rendered.append(f"{name}={shlex.quote(value)}")
        else:
            rendered.append(shlex.quote(part))
    return " ".join(rendered)


def comma_join(values: List[str]) -> str:
    return ",".join(v for v in values if v)


def build_setup_flags(args: argparse.Namespace) -> List[str]:
    flags: List[str] = []
    if args.mode == "cpu":
        flags.append("--cpu_only")
    elif args.mode == "cuda":
        flags.append("--force_cuda")
        if args.cuda_home:
            flags.append(f"--cuda_home={args.cuda_home}")

    if args.blas != "auto":
        flags.append(f"--blas={args.blas}")
    if args.blas_include_dir:
        flags.append(f"--blas_include_dirs={comma_join(args.blas_include_dir)}")
    if args.blas_library_dir:
        flags.append(f"--blas_library_dirs={comma_join(args.blas_library_dir)}")
    if args.fast_math:
        flags.append("--fast_math")
    if args.debug:
        flags.append("--debug")
    if args.force_rebuild:
        flags.append("--force")
    return flags


def build_env(args: argparse.Namespace) -> List[str]:
    env: List[str] = []
    if args.max_jobs:
        env.append(f"MAX_JOBS={args.max_jobs}")
    if args.cxx:
        env.append(f"CXX={args.cxx}")
    if args.mode == "cuda" and args.cuda_home:
        env.append(f"CUDA_HOME={args.cuda_home}")
    if args.mode == "cuda" and args.torch_cuda_arch_list:
        env.append(f"TORCH_CUDA_ARCH_LIST={args.torch_cuda_arch_list}")
    return env


def print_header(args: argparse.Namespace) -> None:
    print("# MinkowskiEngine build command helper")
    print("# Dry run only: no command below was executed by this helper.")
    print(f"# Requested mode: {args.mode}")
    if args.mode == "cuda" and not args.cuda_home:
        print("# CUDA note: set CUDA_HOME in your shell before running the printed CUDA command.")
        print('# Example discovery command: export CUDA_HOME="$(dirname "$(dirname "$(command -v nvcc)")")"')
    if args.mode == "cuda" and not args.torch_cuda_arch_list:
        print("# CUDA note: consider setting TORCH_CUDA_ARCH_LIST for the target GPU.")
    if args.mode == "auto":
        print("# Auto note: setup.py will choose CPU-only if torch.cuda.is_available() is false.")
    if args.blas == "auto":
        print("# BLAS note: setup.py will ask numpy/distutils to auto-detect BLAS.")
    print()


def setup_command(args: argparse.Namespace, flags: List[str]) -> str:
    parts = [*build_env(args), args.python, "setup.py", "install", *flags]
    return shell_join(parts)


def pip_source_command(args: argparse.Namespace, flags: List[str]) -> str:
    parts = [args.python, "-m", "pip", "install", "-U", args.source_url, "-v", "--no-deps"]
    for flag in flags:
        parts.append(f"--install-option={flag}")
    return shell_join(parts)


def print_checks(args: argparse.Namespace) -> None:
    print("\n# Minimal post-install checks")
    print(shell_join([args.python, "-m", "pip", "check"]))
    print(
        f"{shlex.quote(args.python)} - <<'PY'\n"
        "from importlib.metadata import version\n"
        "import torch\n"
        "import MinkowskiEngine as ME\n"
        "print('MinkowskiEngine distribution:', version('MinkowskiEngine'))\n"
        "print('MinkowskiEngine module:', ME.__version__)\n"
        "print('torch:', torch.__version__)\n"
        "print('torch.cuda.is_available:', torch.cuda.is_available())\n"
        "print('MinkowskiEngine.is_cuda_available:', ME.is_cuda_available())\n"
        "PY"
    )


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Print dry-run setup.py or pip-source commands for MinkowskiEngine "
            "CPU/CUDA builds. The helper has no install side effects."
        ),
        formatter_class=RawDefaultsFormatter,
        epilog=(
            "Examples:\n"
            "  python scripts/build_command_helper.py --mode cpu --blas openblas --max-jobs 4\n"
            "  python scripts/build_command_helper.py --mode cuda --cuda-home $CUDA_HOME "
            "--torch-cuda-arch-list '8.0' --blas openblas --style both\n"
            "  python scripts/build_command_helper.py --mode cpu --blas mkl --force-rebuild"
        ),
    )
    parser.add_argument("--mode", choices=("cpu", "cuda", "auto"), default="cpu", help="Build mode to plan.")
    parser.add_argument(
        "--style",
        choices=("setup.py", "pip-source", "both"),
        default="setup.py",
        help="Command style to print. setup.py is best for custom flags.",
    )
    parser.add_argument("--python", default="python", help="Python executable name to print in commands.")
    parser.add_argument("--source-url", default="git+https://github.com/NVIDIA/MinkowskiEngine", help="Source URL for pip-source style.")
    parser.add_argument("--blas", choices=BLAS_CHOICES, default="openblas", help="BLAS selection; use auto to omit --blas.")
    parser.add_argument("--blas-include-dir", action="append", default=[], help="BLAS include directory; may be repeated.")
    parser.add_argument("--blas-library-dir", action="append", default=[], help="BLAS library directory; may be repeated.")
    parser.add_argument("--cuda-home", default="", help="CUDA toolkit root to print for CUDA builds.")
    parser.add_argument("--torch-cuda-arch-list", default="", help="Value for TORCH_CUDA_ARCH_LIST in CUDA builds.")
    parser.add_argument("--cxx", default="g++", help="C++ compiler to print via CXX.")
    parser.add_argument("--max-jobs", type=int, default=4, help="Ninja MAX_JOBS limit to print; use 0 to omit.")
    parser.add_argument("--fast-math", action="store_true", help="Include setup.py --fast_math.")
    parser.add_argument("--debug", action="store_true", help="Include setup.py --debug.")
    parser.add_argument("--force-rebuild", action="store_true", help="Include setup.py install --force.")
    parser.add_argument("--no-checks", action="store_true", help="Do not print post-install check commands.")
    parser.add_argument("--dry-run", action="store_true", help="Accepted for clarity; this helper is always dry-run.")
    args = parser.parse_args(argv)

    if (args.blas_include_dir or args.blas_library_dir) and args.blas == "auto":
        parser.error("--blas-include-dir/--blas-library-dir require --blas to be a concrete BLAS name")
    if args.max_jobs < 0:
        parser.error("--max-jobs must be non-negative")
    return args


def main(argv: List[str] | None = None) -> int:
    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    flags = build_setup_flags(args)
    print_header(args)

    if args.style in ("setup.py", "both"):
        print("# Source-tree setup.py command")
        print(setup_command(args, flags))
        print()

    if args.style in ("pip-source", "both"):
        print("# Legacy pip-source command")
        print("# If pip rejects --install-option, use the setup.py command instead.")
        print(pip_source_command(args, flags))
        print()

    if not args.no_checks:
        print_checks(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
