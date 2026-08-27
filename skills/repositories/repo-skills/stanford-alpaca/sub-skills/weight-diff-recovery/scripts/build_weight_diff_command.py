#!/usr/bin/env python3
"""Build safe dry-run commands for Stanford Alpaca weight-diff workflows.

This helper is self-contained. It imports only the Python standard library,
never loads checkpoints, and prints commands targeting alpaca_weight_diff.py
with --dry-run enabled.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path
from typing import Optional

PLACEHOLDERS = {
    "path_raw": "YOUR_PATH_RAW",
    "path_tuned": "YOUR_PATH_TUNED",
    "path_diff": "YOUR_PATH_DIFF",
}
WEIGHT_PATTERNS = (
    "model.safetensors",
    "model-*.safetensors",
    "pytorch_model.bin",
    "pytorch_model-*.bin",
    "model.safetensors.index.json",
    "pytorch_model.bin.index.json",
)


def _shell_join(parts: list[str]) -> str:
    return " \\\n  ".join(shlex.quote(part) for part in parts)


def _is_placeholder(value: Optional[str]) -> bool:
    return value is None or value == "" or value in PLACEHOLDERS.values() or str(value).startswith("YOUR_")


def _canonical(path: str) -> str:
    return str(Path(path).expanduser().resolve(strict=False))


def _validate_role_aliasing(mode: str, roles: dict[str, Optional[str]]) -> None:
    seen: dict[str, str] = {}
    for role, value in roles.items():
        if _is_placeholder(value):
            continue
        normalized = _canonical(str(value))
        if normalized in seen:
            raise SystemExit(f"path-role collision in {mode}: {role} and {seen[normalized]} both use {value!r}")
        seen[normalized] = role


def _artifact_hints(path: Path) -> list[str]:
    hints: list[str] = []
    if (path / "config.json").exists():
        hints.append("config.json")
    if any(path.glob("tokenizer*")) or (path / "special_tokens_map.json").exists():
        hints.append("tokenizer assets")
    weight_hits: list[Path] = []
    for pattern in WEIGHT_PATTERNS:
        weight_hits.extend(path.glob(pattern))
    if weight_hits:
        hints.append(f"{len(weight_hits)} weight artifact(s)")
    return hints


def _summarize_path(role: str, path_value: Optional[str], strict: bool, optional_output: bool = False) -> str:
    if _is_placeholder(path_value):
        if optional_output:
            return f"# {role}: omitted (recover will not save unless you add --path-tuned)"
        return f"# {role}: {PLACEHOLDERS[role]} (placeholder)"

    path = Path(str(path_value)).expanduser()
    if not path.exists():
        if strict:
            raise SystemExit(f"{role} path does not exist locally: {path}")
        return f"# {role}: {path} (not found locally; command remains dry-run safe)"
    if path.is_file():
        message = f"{role} points to a file, but a Hugging Face checkpoint directory is expected: {path}"
        if strict:
            raise SystemExit(message)
        return f"# {role}: {path} (file; expected directory)"
    hints = _artifact_hints(path)
    hint_text = f"; hints: {', '.join(hints)}" if hints else "; no obvious HF checkpoint artifacts found"
    return f"# {role}: {path} (directory{hint_text})"


def _value_or_placeholder(role: str, value: Optional[str]) -> str:
    if _is_placeholder(value):
        return PLACEHOLDERS[role]
    return str(value)


def _runner_script_path() -> str:
    script_path = Path(__file__).resolve().with_name("alpaca_weight_diff.py")
    cwd = Path.cwd().resolve()
    try:
        return str(script_path.relative_to(cwd))
    except ValueError:
        return str(script_path)


def _build_command(args: argparse.Namespace) -> list[str]:
    parts = ["python", _runner_script_path(), args.mode]
    parts += ["--path-raw", _value_or_placeholder("path_raw", args.path_raw)]

    if args.mode == "recover":
        parts += ["--path-diff", _value_or_placeholder("path_diff", args.path_diff)]
        if not _is_placeholder(args.path_tuned):
            parts += ["--path-tuned", str(args.path_tuned)]
        parts += ["--device", args.device]
        parts.append("--test-inference" if args.test_inference else "--no-test-inference")
        parts.append("--check-integrity-naively" if args.check_integrity_naively else "--no-check-integrity-naively")
    else:
        parts += ["--path-tuned", _value_or_placeholder("path_tuned", args.path_tuned)]
        parts += ["--path-diff", _value_or_placeholder("path_diff", args.path_diff)]
        parts += ["--device", args.device]

    parts.append("--dry-run")
    return parts


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--path-raw", help="HF-converted raw LLaMA checkpoint directory.")
    parser.add_argument("--path-diff", help="Weight-diff directory: input for recover, output for make_diff.")
    parser.add_argument("--path-tuned", help="Tuned input for make_diff, optional output for recover.")
    parser.add_argument("--device", default="cpu", help="Torch device string to include in the printed command.")
    parser.add_argument("--strict", action="store_true", help="Fail on provided local paths that are missing, files, or aliased.")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="mode", required=True)

    recover = subparsers.add_parser("recover", help="Print a safe dry-run recovery command.")
    _add_common(recover)
    recover.add_argument("--test-inference", action=argparse.BooleanOptionalAction, default=True)
    recover.add_argument("--check-integrity-naively", action=argparse.BooleanOptionalAction, default=True)

    make_diff = subparsers.add_parser("make_diff", help="Print a safe dry-run make_diff command.")
    _add_common(make_diff)
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    roles = {"path_raw": args.path_raw, "path_diff": args.path_diff, "path_tuned": args.path_tuned}
    _validate_role_aliasing(args.mode, roles)

    print("# Stanford Alpaca weight-diff dry-run command")
    print(f"# mode: {args.mode}")
    print(_summarize_path("path_raw", args.path_raw, args.strict))
    print(_summarize_path("path_diff", args.path_diff, args.strict))
    print(_summarize_path("path_tuned", args.path_tuned, args.strict, optional_output=args.mode == "recover" and _is_placeholder(args.path_tuned)))
    print(f"# device: {args.device}")
    if args.mode == "recover":
        print("# algorithm: diff-plus-raw")
        print(f"# path_tuned save behavior: {'save to provided output' if not _is_placeholder(args.path_tuned) else 'omitted; no save in live mode'}")
        print(f"# naive checksum in live mode: {args.check_integrity_naively}")
        print(f"# inference smoke in live mode: {args.test_inference}")
    else:
        print("# algorithm: diff-minus-raw")
        print("# path_diff save behavior: output diff directory")
    print("# safe: printed command includes --dry-run and will not load checkpoint tensors")
    print(_shell_join(_build_command(args)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
