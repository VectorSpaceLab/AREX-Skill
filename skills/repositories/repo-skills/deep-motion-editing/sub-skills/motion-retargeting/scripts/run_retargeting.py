#!/usr/bin/env python3
"""Build or explicitly run retargeting entry points from a user checkout.

The helper contains no model, checkpoint, or dataset. By default it validates
arguments and prints an argv-style command. ``--run`` is an explicit opt-in to
execute the selected upstream script in its retargeting module directory.
"""
from __future__ import annotations

import argparse
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable

try:
    from validate_retargeting_data import inspect_bvh
except ImportError:
    inspect_bvh = None  # type: ignore[assignment]


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Safely construct or run retargeting inference/evaluation commands.")
    p.add_argument("--repo-root", type=Path, required=True, help="user-supplied repository root or its retargeting directory")
    p.add_argument("--workflow", choices=("single-pair", "demo", "eval", "test"), default="single-pair")
    p.add_argument("--input-bvh", type=Path, help="source motion BVH for single-pair inference")
    p.add_argument("--target-bvh", type=Path, help="target/reference BVH for single-pair inference")
    p.add_argument("--output-filename", type=Path, help="destination BVH for single-pair inference")
    p.add_argument("--test-type", choices=("intra", "cross"), help="single-pair structural setup")
    p.add_argument("--save-dir", type=Path, default=Path("./pretrained"), help="checkpoint/config directory (upstream default: ./pretrained)")
    p.add_argument("--cuda-device", default="cuda:0", help="requested device; upstream parser default is cuda:0")
    p.add_argument("--eval-seq", type=int, default=0, help="evaluation sequence index (default: 0)")
    p.add_argument("--path-mode", choices=("auto", "source-encoded", "literal"), default="auto",
                   help="handle eval_single_pair.py's underscore-to-space recovery")
    p.add_argument("--python", dest="python_executable", default=sys.executable,
                   help="Python executable for the user checkout")
    p.add_argument("--skip-asset-check", action="store_true", help="construct without checking para/checkpoint files")
    p.add_argument("--run", action="store_true", help="execute the command; otherwise print it only")
    p.add_argument("--allow-literal-legacy-path", action="store_true",
                   help="allow --run with literal paths; requires a patched eval_single_pair.py")
    p.add_argument("--allow-destructive-test", action="store_true",
                   help="permit upstream test.py, which removes results/bvh after metrics")
    return p


def locate_retargeting(root: Path) -> Path:
    root = root.expanduser().resolve()
    if (root / "eval_single_pair.py").is_file() and (root / "option_parser.py").is_file():
        return root
    candidate = root / "retargeting"
    if (candidate / "eval_single_pair.py").is_file() and (candidate / "option_parser.py").is_file():
        return candidate
    raise ValueError("--repo-root must contain retargeting/eval_single_pair.py and retargeting/option_parser.py")


def resolve_under_retargeting(path: Path, retargeting: Path) -> Path:
    return path.expanduser().resolve() if path.is_absolute() else (retargeting / path).resolve()


def _source_path(path: Path, retargeting: Path, mode: str) -> str:
    """Encode spaces for the unmodified single-pair entry point.

    ``eval_single_pair.py`` calls ``recover_space`` and replaces *every*
    underscore with a space. There is no lossless escape for a literal
    underscore, so fail early in auto/encoded mode instead of selecting a
    different file. Relative paths avoid unrelated parent-directory names.
    """
    # The source command runs with cwd=retargeting. A relative path avoids
    # unrelated parent-directory names and is accepted by the source loader.
    value = os.path.relpath(path, retargeting)
    if mode in {"auto", "source-encoded"}:
        if "_" in value:
            raise ValueError(
                f"path contains '_' and cannot survive eval_single_pair.py recovery: {value!r}; "
                "use --path-mode literal only with a patched upstream script, or rename the path"
            )
        return value.replace(" ", "_")
    return value


def _checkpoint_errors(save_dir: Path) -> list[str]:
    required = [
        save_dir / "para.txt",
        save_dir / "models" / "topology0" / "20000" / "auto_encoder.pt",
        save_dir / "models" / "topology0" / "20000" / "static_encoder.pt",
        save_dir / "models" / "topology1" / "20000" / "auto_encoder.pt",
        save_dir / "models" / "topology1" / "20000" / "static_encoder.pt",
    ]
    return [str(item) for item in required if not item.is_file()]


def _require_pair(args: argparse.Namespace) -> tuple[Path, Path, Path]:
    missing = [name for name in ("input_bvh", "target_bvh", "output_filename", "test_type") if getattr(args, name) is None]
    if missing:
        raise ValueError("single-pair requires: " + ", ".join("--" + name.replace("_", "-") for name in missing))
    input_path = args.input_bvh.expanduser().resolve()
    target_path = args.target_bvh.expanduser().resolve()
    output_path = args.output_filename.expanduser().resolve()
    if not input_path.is_file() or not target_path.is_file():
        raise ValueError("--input-bvh and --target-bvh must be existing files")
    if input_path.suffix.lower() != ".bvh" or target_path.suffix.lower() != ".bvh":
        raise ValueError("single-pair inputs must have .bvh suffixes")
    return input_path, target_path, output_path


def build_command(args: argparse.Namespace) -> tuple[list[str], Path, Path | None]:
    retargeting = locate_retargeting(args.repo_root)
    save_dir = resolve_under_retargeting(args.save_dir, retargeting)
    if args.workflow == "single-pair":
        input_path, target_path, output_path = _require_pair(args)
        if args.path_mode != "literal":
            # Check all three paths before launching anything.
            _source_path(input_path, retargeting, args.path_mode)
            _source_path(target_path, retargeting, args.path_mode)
            _source_path(output_path, retargeting, args.path_mode)
        command = [
            args.python_executable, "eval_single_pair.py",
            "--input_bvh", _source_path(input_path, retargeting, args.path_mode),
            "--target_bvh", _source_path(target_path, retargeting, args.path_mode),
            "--output_filename", _source_path(output_path, retargeting, args.path_mode),
            "--test_type", args.test_type,
            "--save_dir", str(save_dir),
            "--cuda_device", args.cuda_device,
            "--eval_seq", str(args.eval_seq),
        ]
        return command, retargeting, output_path
    if args.workflow == "demo":
        if save_dir != (retargeting / "pretrained").resolve():
            raise ValueError("demo.py has no --save_dir option and always uses ./pretrained; use --workflow single-pair or eval for another run root")
        return [args.python_executable, "demo.py"], retargeting, None
    if args.workflow == "eval":
        return [args.python_executable, "eval.py", "--save_dir", str(save_dir),
                "--cuda_device", args.cuda_device, "--eval_seq", str(args.eval_seq)], retargeting, None
    return [args.python_executable, "test.py", "--save_dir", str(save_dir)], retargeting, None


def _preflight(args: argparse.Namespace, retargeting: Path, output: Path | None) -> None:
    if args.python_executable != sys.executable and not Path(args.python_executable).is_file() and shutil.which(args.python_executable) is None:
        raise ValueError(f"cannot find --python executable: {args.python_executable}")
    if not args.skip_asset_check:
        save_dir = resolve_under_retargeting(args.save_dir, retargeting)
        errors = _checkpoint_errors(save_dir)
        if errors:
            raise ValueError("incomplete para/checkpoint layout; missing:\n  " + "\n  ".join(errors) +
                             "\nUse --skip-asset-check only to construct a command or when assets are supplied another way.")
    if args.workflow == "single-pair" and args.path_mode == "literal" and args.run and not args.allow_literal_legacy_path:
        pair = _require_pair(args)
        encoded_values = [str(path) for path in pair]
        if any("_" in value for value in encoded_values):
            raise ValueError("literal paths containing '_' are unsafe with the unmodified script; add --allow-literal-legacy-path only after patching eval_single_pair.py")
    if args.workflow == "test" and args.run and not args.allow_destructive_test:
        raise ValueError("upstream test.py removes its generated results/bvh directory; add --allow-destructive-test to proceed")
    if output is not None and args.run:
        output.parent.mkdir(parents=True, exist_ok=True)


def main(argv: Iterable[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        command, retargeting, output = build_command(args)
        _preflight(args, retargeting, output)
    except (ValueError, OSError) as exc:
        print(f"retargeting preflight error: {exc}", file=sys.stderr)
        return 2
    print("Command:", shlex.join(command))
    print("Working directory:", retargeting)
    if args.workflow == "test":
        print("WARNING: upstream test.py deletes results/bvh after collecting errors.", file=sys.stderr)
    if not args.run:
        print("Dry run: nothing executed and no files were changed.")
        return 0
    try:
        subprocess.run(command, cwd=retargeting, check=True)
    except subprocess.CalledProcessError as exc:
        print(f"upstream retargeting command failed with exit status {exc.returncode}", file=sys.stderr)
        return exc.returncode or 1
    if output is not None:
        if not output.is_file():
            print(f"command completed but did not create {output}", file=sys.stderr)
            return 3
        if inspect_bvh is not None:
            try:
                info = inspect_bvh(output)
                print(f"Validated output: {info['frames']} frames, {info['joints']} joints")
            except Exception as exc:
                print(f"output exists but standalone BVH validation failed: {exc}", file=sys.stderr)
                return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
