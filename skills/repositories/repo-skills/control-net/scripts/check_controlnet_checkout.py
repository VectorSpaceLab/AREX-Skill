#!/usr/bin/env python3
"""Safely inspect a ControlNet 1.0 source checkout without launching apps.

This helper checks file layout, parses ControlNet YAML configs, and optionally
imports safe namespace/core modules. It never loads checkpoints, starts Gradio,
uses CUDA tensors, downloads models, trains, or generates images.
"""
from __future__ import annotations

import argparse
import ast
import importlib
import json
import sys
from pathlib import Path

EXPECTED_FILES = [
    "README.md",
    "environment.yaml",
    "config.py",
    "share.py",
    "models/cldm_v15.yaml",
    "models/cldm_v21.yaml",
    "cldm/model.py",
    "cldm/cldm.py",
    "cldm/ddim_hacked.py",
    "annotator/util.py",
    "gradio_annotator.py",
    "tutorial_dataset.py",
    "tool_add_control.py",
    "tool_add_control_sd21.py",
    "tool_transfer_control.py",
]

SAFE_IMPORTS = [
    "cldm",
    "ldm",
    "annotator",
    "config",
    "share",
]

UNSAFE_TOP_LEVEL_PATTERNS = [
    "block.launch",
    ".cuda(",
    "create_model(",
    "load_state_dict(",
    "torch.load(",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safely inspect a ControlNet source checkout.")
    parser.add_argument("--repo-root", required=True, help="Path to a ControlNet checkout.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a text report.")
    parser.add_argument(
        "--skip-imports",
        action="store_true",
        help="Only check files/configs/static script patterns; do not import safe modules.",
    )
    return parser.parse_args()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def parse_yaml_targets(path: Path) -> dict:
    text = read_text(path)
    result = {"path": str(path), "exists": path.exists(), "targets": [], "keys": {}}
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("target:"):
            result["targets"].append(stripped.split(":", 1)[1].strip())
        for key in ("first_stage_key", "cond_stage_key", "control_key", "context_dim", "num_heads", "num_head_channels"):
            if stripped.startswith(f"{key}:"):
                result["keys"].setdefault(key, []).append(stripped.split(":", 1)[1].strip())
    return result


def function_defs(path: Path) -> list[str]:
    try:
        tree = ast.parse(read_text(path), filename=str(path))
    except SyntaxError as exc:
        return [f"SyntaxError: {exc}"]
    return [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]


def script_side_effect_markers(path: Path) -> list[str]:
    text = read_text(path)
    return [pattern for pattern in UNSAFE_TOP_LEVEL_PATTERNS if pattern in text]


def check_imports(repo_root: Path) -> list[dict]:
    sys.path.insert(0, str(repo_root))
    results = []
    for name in SAFE_IMPORTS:
        item = {"module": name, "ok": False}
        try:
            module = importlib.import_module(name)
            item.update({"ok": True, "file": getattr(module, "__file__", None)})
        except Exception as exc:  # pragma: no cover - environment-specific diagnostics.
            item["error"] = f"{type(exc).__name__}: {exc}"
        results.append(item)
    return results


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    files = []
    for rel in EXPECTED_FILES:
        path = repo_root / rel
        files.append({"path": rel, "exists": path.exists(), "size": path.stat().st_size if path.exists() else None})

    configs = []
    for rel in ["models/cldm_v15.yaml", "models/cldm_v21.yaml"]:
        path = repo_root / rel
        configs.append(parse_yaml_targets(path) if path.exists() else {"path": rel, "exists": False})

    script_patterns = []
    for path in sorted(repo_root.glob("gradio_*.py")) + [repo_root / "tutorial_train.py", repo_root / "tutorial_train_sd21.py", repo_root / "tool_add_control.py", repo_root / "tool_add_control_sd21.py", repo_root / "tool_transfer_control.py"]:
        if path.exists():
            script_patterns.append({
                "path": path.relative_to(repo_root).as_posix(),
                "functions": function_defs(path),
                "unsafe_markers": script_side_effect_markers(path),
            })

    imports = [] if args.skip_imports else check_imports(repo_root)
    ok = repo_root.is_dir() and all(item["exists"] for item in files if item["path"] in {"README.md", "config.py", "models/cldm_v15.yaml", "cldm/model.py"})
    if imports:
        ok = ok and all(item["ok"] for item in imports)

    output = {
        "ok": ok,
        "repo_root_exists": repo_root.is_dir(),
        "files": files,
        "configs": configs,
        "script_patterns": script_patterns,
        "safe_imports": imports,
        "notes": [
            "Unsafe markers are reasons to inspect scripts statically instead of importing them.",
            "This helper does not verify checkpoints, CUDA execution, Gradio launch, training, or generation.",
        ],
    }

    if args.json:
        print(json.dumps(output, indent=2, sort_keys=True))
    else:
        print(f"ControlNet checkout ok: {output['ok']}")
        print(f"Repo exists: {output['repo_root_exists']}")
        missing = [item["path"] for item in files if not item["exists"]]
        print("Missing expected files: " + (", ".join(missing) if missing else "none"))
        if imports:
            failed = [item for item in imports if not item["ok"]]
            print("Safe import failures: " + (json.dumps(failed) if failed else "none"))
        for config in configs:
            print(f"Config {config.get('path')}: targets={config.get('targets', [])} keys={config.get('keys', {})}")
        print("Static script inspection completed; unsafe markers are reported in JSON mode.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
