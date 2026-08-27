#!/usr/bin/env python3
"""Safely inspect pytorch-yolo-v3 video/camera demo argparse help.

The checker is intentionally preflight-only: it runs each demo with ``-h`` and
parses source text. It does not open a GUI, camera, video file, model, weights,
network connection, or any user output path.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


EXPECTED_FLAGS: Dict[str, List[str]] = {
    "video_demo.py": [
        "--video",
        "--dataset",
        "--confidence",
        "--nms_thresh",
        "--cfg",
        "--weights",
        "--reso",
    ],
    "video_demo_half.py": [
        "--video",
        "--dataset",
        "--confidence",
        "--nms_thresh",
        "--cfg",
        "--weights",
        "--reso",
    ],
    "cam_demo.py": ["--confidence", "--nms_thresh", "--reso"],
}


HELP_FLAG_RE = re.compile(r"--[A-Za-z0-9_\-]+")


def node_to_text(node: ast.AST) -> str:
    """Return a deterministic readable representation for an AST value."""
    try:
        value = ast.literal_eval(node)
        return repr(value)
    except Exception:
        unparse = getattr(ast, "unparse", None)
        if unparse is not None:
            try:
                return unparse(node)
            except Exception:
                pass
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        return type(node).__name__


def call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = call_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return ""


def parse_argparse_source(source: str) -> Tuple[List[Dict[str, str]], List[str], Optional[str], Optional[str]]:
    """Extract argparse add_argument calls without importing the target file."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [], [], None, f"source parse failed: {exc}"

    arguments: List[Dict[str, str]] = []
    descriptions: List[str] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = call_name(node.func)
        if name.endswith("ArgumentParser"):
            for keyword in node.keywords:
                if keyword.arg == "description":
                    descriptions.append(node_to_text(keyword.value))
        if not name.endswith("add_argument"):
            continue
        option_strings: List[str] = []
        for positional in node.args:
            if isinstance(positional, ast.Constant) and isinstance(positional.value, str):
                if positional.value.startswith("-"):
                    option_strings.append(positional.value)
            elif isinstance(positional, ast.Str):  # pragma: no cover for old AST compatibility
                if positional.s.startswith("-"):
                    option_strings.append(positional.s)
        if not option_strings:
            continue
        record: Dict[str, str] = {"options": ", ".join(option_strings)}
        for keyword in node.keywords:
            if keyword.arg in {"dest", "default", "type", "help"}:
                record[keyword.arg] = node_to_text(keyword.value)
        arguments.append(record)

    parsed_flags = []
    for record in arguments:
        parsed_flags.extend(flag.strip() for flag in record["options"].split(","))
    return arguments, parsed_flags, descriptions[0] if descriptions else None, None


def run_help(repo_root: Path, script_name: str, timeout: float) -> Dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.setdefault("OPENCV_LOG_LEVEL", "ERROR")
    command = [sys.executable, script_name, "-h"]
    try:
        completed = subprocess.run(
            command,
            cwd=str(repo_root),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            env=env,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "returncode": None,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "error": f"help timed out after {timeout:g}s",
            "flags": [],
        }

    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    flags = sorted(set(HELP_FLAG_RE.findall(stdout)))
    return {
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "error": None if completed.returncode == 0 else f"help exited {completed.returncode}",
        "flags": flags,
    }


def without_comments(source: str) -> str:
    kept: List[str] = []
    for line in source.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        kept.append(line)
    return "\n".join(kept)


def known_pitfalls(script_name: str, source: str, parsed_flags: Sequence[str]) -> List[str]:
    pitfalls: List[str] = []
    uncommented = without_comments(source)

    if "cv2.imshow" in source or "cv2.waitKey" in source:
        pitfalls.append("Full run requires an OpenCV GUI/display because frames are shown with imshow/waitKey.")
    if "assert cap.isOpened" in source:
        pitfalls.append("Capture failure raises AssertionError: Cannot capture source.")
    if "model.load_weights" in source:
        pitfalls.append("Full run loads model weights; parser checks do not require weights.")
    if "yolov3.weights" in source:
        pitfalls.append("Default or hard-coded weights path includes yolov3.weights.")
    if "video.avi" in source:
        pitfalls.append("Default video-name assumption includes video.avi; actual codec support depends on OpenCV.")

    if script_name == "cam_demo.py":
        if "cv2.VideoCapture(0)" in source:
            pitfalls.append("Webcam demo opens OpenCV camera device 0 and has no CLI flag for another camera index.")
        if re.search(r"if\s+CUDA\s*:\s*\n\s*im_dim\s*=\s*im_dim\.cuda\(\)", uncommented):
            pitfalls.append("CUDA branch references im_dim before assignment in cam_demo.py.")
        if 'default = "160"' in source or "default = '160'" in source:
            pitfalls.append("Camera demo default network resolution is 160.")

    if script_name == "video_demo_half.py":
        if "--video" in parsed_flags and re.search(r"videofile\s*=\s*['\"]video\.avi['\"]", uncommented):
            pitfalls.append("Half demo parses --video but hard-codes videofile = 'video.avi' at runtime.")
        if "YOLO v2 Video Detection Module" in source:
            pitfalls.append("Half demo help description says YOLO v2 Video Detection Module despite the file name.")
        if ".half()" in source or "write_results_half" in source:
            pitfalls.append("Half precision path is meaningful only with CUDA and fp16-capable GPU support.")

    return pitfalls


def short_text(text: str, limit: int = 700) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def inspect_script(repo_root: Path, script_name: str, timeout: float) -> Dict[str, Any]:
    path = repo_root / script_name
    result: Dict[str, Any] = {
        "script": script_name,
        "exists": path.is_file(),
        "expected_flags": EXPECTED_FLAGS[script_name],
        "source_arguments": [],
        "source_flags": [],
        "source_description": None,
        "help_ok": False,
        "help_returncode": None,
        "help_flags": [],
        "pitfalls": [],
        "errors": [],
    }

    if not path.is_file():
        result["errors"].append("expected script is missing")
        return result

    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        result["errors"].append(f"could not read source: {exc}")
        return result

    source_arguments, source_flags, description, parse_error = parse_argparse_source(source)
    result["source_arguments"] = source_arguments
    result["source_flags"] = sorted(set(source_flags))
    result["source_description"] = description
    if parse_error:
        result["errors"].append(parse_error)

    help_result = run_help(repo_root, script_name, timeout)
    result["help_ok"] = bool(help_result["ok"])
    result["help_returncode"] = help_result["returncode"]
    result["help_flags"] = help_result["flags"]
    if not help_result["ok"]:
        result["errors"].append(help_result["error"] or "help failed")
        if help_result.get("stderr"):
            result["help_stderr"] = short_text(help_result["stderr"])
        if help_result.get("stdout"):
            result["help_stdout"] = short_text(help_result["stdout"])

    expected = set(EXPECTED_FLAGS[script_name])
    missing_source = sorted(expected.difference(result["source_flags"]))
    missing_help = sorted(expected.difference(result["help_flags"])) if help_result["ok"] else []
    if missing_source:
        result["errors"].append("expected flags missing from source parse: " + ", ".join(missing_source))
    if missing_help:
        result["errors"].append("expected flags missing from -h output: " + ", ".join(missing_help))

    result["pitfalls"] = known_pitfalls(script_name, source, source_flags)
    return result


def print_text_report(repo_root: Path, results: Sequence[Dict[str, Any]], errors: Sequence[str]) -> None:
    print("pytorch-yolo-v3 video/camera demo argparse preflight")
    print(f"repo_root: {repo_root}")
    print("mode: source inspection plus '-h'; no GUI, camera, video, weights, downloads, or inference")
    print("")

    for result in results:
        status = "OK" if result["exists"] and result["help_ok"] and not result["errors"] else "FAIL"
        print(f"[{status}] {result['script']}")
        if result.get("source_description"):
            print(f"  argparse description: {result['source_description']}")
        print("  expected flags: " + ", ".join(result["expected_flags"]))
        print("  source flags:   " + (", ".join(result["source_flags"]) or "<none>"))
        print("  help flags:     " + (", ".join(result["help_flags"]) or "<none>"))
        if result["source_arguments"]:
            print("  parsed source arguments:")
            for arg in result["source_arguments"]:
                extras = []
                for key in ("dest", "default", "type"):
                    if key in arg:
                        extras.append(f"{key}={arg[key]}")
                suffix = f" ({'; '.join(extras)})" if extras else ""
                print(f"    - {arg['options']}{suffix}")
        if result["pitfalls"]:
            print("  known source pitfalls:")
            for pitfall in result["pitfalls"]:
                print(f"    - {pitfall}")
        if result["errors"]:
            print("  errors:")
            for error in result["errors"]:
                print(f"    - {error}")
            if result.get("help_stderr"):
                print("  help stderr excerpt:")
                print("    " + result["help_stderr"].replace("\n", "\n    "))
            if result.get("help_stdout"):
                print("  help stdout excerpt:")
                print("    " + result["help_stdout"].replace("\n", "\n    "))
        print("")

    if errors:
        print("overall: FAIL")
        for error in errors:
            print(f"- {error}")
    else:
        print("overall: OK")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safely inspect pytorch-yolo-v3 video/camera demo argparse help without opening capture or display.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Path to the user's pytorch-yolo-v3 checkout containing video_demo.py, video_demo_half.py, and cam_demo.py.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=20.0,
        help="Seconds allowed for each '<script> -h' subprocess.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON report instead of the text report.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = Path(args.repo_root).expanduser()
    errors: List[str] = []

    if not repo_root.exists():
        errors.append("repo root does not exist")
    elif not repo_root.is_dir():
        errors.append("repo root is not a directory")

    results: List[Dict[str, Any]] = []
    if not errors:
        for script_name in EXPECTED_FLAGS:
            results.append(inspect_script(repo_root, script_name, timeout=args.timeout))
        for result in results:
            for error in result["errors"]:
                errors.append(f"{result['script']}: {error}")

    report = {
        "repo_root": str(repo_root),
        "mode": "source inspection plus -h; no GUI, camera, video, weights, downloads, or inference",
        "scripts": results,
        "errors": errors,
        "ok": not errors,
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text_report(repo_root, results, errors)

    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
