#!/usr/bin/env python3
"""Static sanity checker for a DARTS-style checkout or source copy.

The checker is safe and stdlib-only. It does not import the DARTS code. Use it
before planning native runs or modernization work to catch missing files, absent
package metadata, legacy syntax, and missing dataset placeholders.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import tokenize
from pathlib import Path
from typing import Dict, List, Tuple

EXPECTED_FILES = [
    "README.md",
    "LICENSE",
    "cnn/train_search.py",
    "cnn/train.py",
    "cnn/test.py",
    "cnn/train_imagenet.py",
    "cnn/test_imagenet.py",
    "cnn/model_search.py",
    "cnn/model.py",
    "cnn/operations.py",
    "cnn/architect.py",
    "cnn/utils.py",
    "cnn/genotypes.py",
    "cnn/visualize.py",
    "rnn/train_search.py",
    "rnn/train.py",
    "rnn/test.py",
    "rnn/data.py",
    "rnn/model_search.py",
    "rnn/model.py",
    "rnn/architect.py",
    "rnn/utils.py",
    "rnn/genotypes.py",
    "rnn/visualize.py",
]

RUNNER_FILES = [
    "cnn/train_search.py",
    "cnn/train.py",
    "cnn/test.py",
    "cnn/train_imagenet.py",
    "cnn/test_imagenet.py",
    "rnn/train_search.py",
    "rnn/train.py",
    "rnn/test.py",
]

DATA_EXPECTATIONS = {
    "PTB": ["data/penn/train.txt", "data/penn/valid.txt", "data/penn/test.txt"],
    "WikiText-2": ["data/wikitext-2/train.txt", "data/wikitext-2/valid.txt", "data/wikitext-2/test.txt"],
    "ImageNet": ["data/imagenet/train", "data/imagenet/val"],
}


def scan_python(path: Path) -> Dict[str, object]:
    result: Dict[str, object] = {"exists": path.exists()}
    if not path.exists():
        return result
    try:
        with path.open("rb") as handle:
            result["token_count"] = sum(1 for _ in tokenize.tokenize(handle.readline))
    except tokenize.TokenError as exc:
        result["token_error"] = str(exc)
    text = path.read_text(errors="replace")
    result["uses_cuda_async_keyword"] = bool(re.search(r"\.cuda\([^)]*\basync\s*=", text))
    result["uses_variable_volatile"] = "volatile=True" in text
    result["uses_loss_data_index"] = ".data[0]" in text or "total_loss[0]" in text
    try:
        ast.parse(text)
        result["ast_status"] = "ok"
    except SyntaxError as exc:
        result["ast_status"] = "syntax-error"
        result["syntax_error"] = {"line": exc.lineno, "offset": exc.offset, "message": exc.msg}
    return result


def inspect_repo(root: Path) -> Dict[str, object]:
    root = root.resolve()
    missing = [rel for rel in EXPECTED_FILES if not (root / rel).exists()]
    py_files = sorted([p for p in (root / "cnn").glob("*.py")] + [p for p in (root / "rnn").glob("*.py")])
    syntax = {str(p.relative_to(root)): scan_python(p) for p in py_files}
    metadata = {
        name: (root / name).exists()
        for name in ["pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "environment.yml"]
    }
    runner_flags = {}
    for rel in RUNNER_FILES:
        p = root / rel
        if not p.exists():
            continue
        flags = sorted(set(re.findall(r"parser\.add_argument\(['\"](--[A-Za-z0-9_-]+)", p.read_text(errors="replace"))))
        runner_flags[rel] = flags
    data_status = {
        group: {rel: (root / rel).exists() for rel in rels}
        for group, rels in DATA_EXPECTATIONS.items()
    }
    warnings: List[str] = []
    if missing:
        warnings.append("Missing expected DARTS files: " + ", ".join(missing))
    if not any(metadata.values()):
        warnings.append("No package metadata detected; treat this as a script-style research repo, not an installable package.")
    async_files = [rel for rel, info in syntax.items() if info.get("uses_cuda_async_keyword")]
    if async_files:
        warnings.append("Legacy .cuda(async=True) syntax appears in: " + ", ".join(async_files))
    syntax_errors = [rel for rel, info in syntax.items() if info.get("ast_status") == "syntax-error"]
    if syntax_errors:
        warnings.append("Modern Python AST parse fails for: " + ", ".join(syntax_errors))
    return {
        "root": str(root),
        "expected_files_missing": missing,
        "metadata_present": metadata,
        "python_file_count": len(py_files),
        "python_scan": syntax,
        "runner_flags": runner_flags,
        "data_status": data_status,
        "warnings": warnings,
    }


def print_summary(report: Dict[str, object]) -> None:
    print("DARTS static inspection")
    print("Root: {}".format(report["root"]))
    print("Python files: {}".format(report["python_file_count"]))
    print("Missing expected files: {}".format(", ".join(report["expected_files_missing"]) or "none"))
    metadata = report["metadata_present"]
    print("Package metadata present: {}".format(", ".join(k for k, v in metadata.items() if v) or "none"))
    print("Warnings:")
    for warning in report["warnings"] or ["none"]:
        print("  - " + warning)
    print("Dataset layout quick check:")
    for group, entries in report["data_status"].items():
        ok = [rel for rel, exists in entries.items() if exists]
        missing = [rel for rel, exists in entries.items() if not exists]
        print("  - {}: present [{}]; missing [{}]".format(group, ", ".join(ok) or "none", ", ".join(missing) or "none"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Statically inspect a DARTS-style checkout without importing or running it.")
    parser.add_argument("--repo-root", default=".", help="Path to a DARTS checkout/source copy. Default: current directory.")
    parser.add_argument("--json", action="store_true", help="Emit JSON report.")
    args = parser.parse_args()
    report = inspect_repo(Path(args.repo_root))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_summary(report)
    # Missing source files are a hard failure; legacy syntax/data warnings are informational.
    return 1 if report["expected_files_missing"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
