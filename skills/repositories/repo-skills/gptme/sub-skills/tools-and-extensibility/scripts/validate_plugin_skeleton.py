#!/usr/bin/env python3
"""Statically validate a gptme plugin skeleton without importing plugin code."""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    tomllib = None  # type: ignore[assignment]


OLD_HOOK_NAMES = {
    "TOOL_PRE_EXECUTE": "TOOL_EXECUTE_PRE",
    "TOOL_POST_EXECUTE": "TOOL_EXECUTE_POST",
}


@dataclass
class Finding:
    severity: str
    path: str
    message: str


class Reporter:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.findings: list[Finding] = []

    def add(self, severity: str, path: Path | str, message: str) -> None:
        if isinstance(path, Path):
            try:
                path_str = str(path.relative_to(self.root)) or "."
            except ValueError:
                path_str = str(path)
        else:
            path_str = path
        self.findings.append(Finding(severity.upper(), path_str, message))

    def error(self, path: Path | str, message: str) -> None:
        self.add("ERROR", path, message)

    def warn(self, path: Path | str, message: str) -> None:
        self.add("WARN", path, message)

    def info(self, path: Path | str, message: str) -> None:
        self.add("INFO", path, message)


# ── Parsing helpers ──────────────────────────────────────────────────────────


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(errors="replace")


def _parse_python(path: Path, reporter: Reporter) -> ast.Module | None:
    try:
        return ast.parse(_read_text(path), filename=str(path))
    except SyntaxError as exc:
        reporter.error(path, f"Python syntax error: {exc.msg} at line {exc.lineno}")
        return None


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _call_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return None


def _has_toolspec_call(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = _call_name(node.func)
            if name in {"ToolSpec", "gptme.tools.ToolSpec"} or (name or "").endswith(".ToolSpec"):
                return True
            if name in {"ToolSpec.from_function", "gptme.tools.ToolSpec.from_function"}:
                return True
    return False


def _tool_calls(tree: ast.Module) -> list[ast.Call]:
    calls: list[ast.Call] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = _call_name(node.func)
            if name in {"ToolSpec", "gptme.tools.ToolSpec"} or (name or "").endswith(".ToolSpec"):
                calls.append(node)
    return calls


def _keyword_names(call: ast.Call) -> set[str]:
    return {kw.arg for kw in call.keywords if kw.arg}


def _module_exposes_name(tree: ast.Module, name: str) -> bool:
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name == name:
                return True
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return True
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == name:
                return True
        elif isinstance(node, ast.Import):
            for alias in node.names:
                exposed = alias.asname or alias.name.split(".", 1)[0]
                if exposed == name:
                    return True
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                exposed = alias.asname or alias.name
                if exposed == name:
                    return True
    return False


def _public_py_files(path: Path) -> list[Path]:
    if not path.is_dir():
        return []
    return sorted(
        p
        for p in path.glob("*.py")
        if p.name != "__init__.py" and not p.name.startswith("_")
    )


def _all_python_files(path: Path) -> list[Path]:
    if not path.is_dir():
        return []
    return sorted(p for p in path.rglob("*.py") if "__pycache__" not in p.parts)


# ── Validation ───────────────────────────────────────────────────────────────


def _validate_tool_file(path: Path, reporter: Reporter) -> None:
    tree = _parse_python(path, reporter)
    if tree is None:
        return
    text = _read_text(path)
    if not _has_toolspec_call(tree):
        reporter.warn(path, "No ToolSpec call found; gptme tool discovery only registers ToolSpec instances.")
        return

    for call in _tool_calls(tree):
        keywords = _keyword_names(call)
        if "name" not in keywords:
            reporter.warn(path, "ToolSpec call has no explicit name= keyword; explicit names are easier to inventory and allowlist.")
        if "desc" not in keywords:
            reporter.warn(path, "ToolSpec call has no desc= keyword; descriptions appear in prompts and inventories.")
        if "execute" not in keywords and "functions" not in keywords:
            reporter.warn(path, "ToolSpec has neither execute= nor functions=; it may be discoverable but not useful.")
        if "available" in keywords and "available_hint" not in keywords:
            reporter.warn(path, "ToolSpec uses available= without available_hint=; users may not know how to repair unavailable tools.")

    if "subprocess.run(" in text and "timeout=" not in text:
        reporter.warn(path, "subprocess.run call without timeout=; plugin tools should bound external commands.")


def _validate_tools_dir(tools_dir: Path, reporter: Reporter) -> None:
    if not tools_dir.exists():
        return
    if not tools_dir.is_dir():
        reporter.error(tools_dir, "tools exists but is not a directory.")
        return

    init_file = tools_dir / "__init__.py"
    public_files = _public_py_files(tools_dir)

    if init_file.exists() and not public_files:
        init_tree = _parse_python(init_file, reporter)
        if init_tree is not None and _has_toolspec_call(init_tree):
            reporter.warn(
                init_file,
                "ToolSpec appears only in tools/__init__.py. Folder-plugin discovery may skip an otherwise empty tools package; add a public tool module.",
            )
        else:
            reporter.warn(tools_dir, "tools package has no public tool modules.")
    elif not init_file.exists() and not public_files:
        reporter.warn(tools_dir, "tools directory has no public .py modules.")

    for file in ([init_file] if init_file.exists() else []) + public_files:
        _validate_tool_file(file, reporter)


def _check_old_hook_names(path: Path, reporter: Reporter) -> None:
    text = _read_text(path)
    for old, new in OLD_HOOK_NAMES.items():
        if old in text:
            reporter.warn(path, f"Found old hook name {old}; current HookType member is {new}.")
    if "TOOL_EXECUTE_" in text and re.search(r"def\s+\w+\s*\(\s*log\s*,\s*workspace\s*,\s*tool_use", text):
        reporter.warn(
            path,
            "Tool execution hook appears to use old positional (log, workspace, tool_use) signature; current pre/post hooks receive data objects.",
        )


def _validate_register_module(path: Path, reporter: Reporter, kind: str) -> None:
    tree = _parse_python(path, reporter)
    if tree is None:
        return
    if not _module_exposes_name(tree, "register"):
        reporter.error(path, f"{kind} module does not expose register(); gptme will import it but not register anything.")
        return
    text = _read_text(path)
    expected = "register_hook" if kind == "hook" else "register_command"
    if expected not in text:
        reporter.warn(path, f"register() module does not mention {expected}; confirm registration is delegated intentionally.")
    if kind == "hook":
        _check_old_hook_names(path, reporter)


def _validate_registry_dir(component_dir: Path, reporter: Reporter, kind: str) -> None:
    if not component_dir.exists():
        return
    if not component_dir.is_dir():
        reporter.error(component_dir, f"{kind}s exists but is not a directory.")
        return

    init_file = component_dir / "__init__.py"
    public_files = _public_py_files(component_dir)

    if init_file.exists():
        # Folder discovery imports the package module for hook/command packages.
        _validate_register_module(init_file, reporter, kind)
        if public_files and not _module_exposes_name(_parse_python(init_file, reporter) or ast.Module(body=[], type_ignores=[]), "register"):
            reporter.error(
                init_file,
                f"{kind}s package has public modules but package __init__.py does not expose register(); individual files will not be called in package mode.",
            )
        for file in public_files:
            if kind == "hook":
                _check_old_hook_names(file, reporter)
    else:
        if not public_files:
            reporter.warn(component_dir, f"{kind}s directory has no public .py modules.")
        for file in public_files:
            _validate_register_module(file, reporter, kind)


def _parse_pyproject(pyproject: Path, reporter: Reporter) -> dict[str, Any]:
    if not pyproject.exists():
        return {}
    if tomllib is None:
        reporter.warn(pyproject, "tomllib is unavailable; cannot parse pyproject.toml on this Python version.")
        return {}
    try:
        with pyproject.open("rb") as fh:
            return tomllib.load(fh)
    except Exception as exc:
        reporter.error(pyproject, f"Could not parse pyproject.toml: {type(exc).__name__}: {exc}")
        return {}


def _entrypoints_from_pyproject(data: dict[str, Any]) -> dict[str, str]:
    project = data.get("project", {}) if isinstance(data.get("project", {}), dict) else {}
    ep_root = project.get("entry-points", {}) if isinstance(project.get("entry-points", {}), dict) else {}
    gptme_eps = ep_root.get("gptme.plugins", {}) if isinstance(ep_root.get("gptme.plugins", {}), dict) else {}
    return {str(k): str(v) for k, v in gptme_eps.items()}


def _src_packages(root: Path) -> list[Path]:
    src = root / "src"
    if not src.is_dir():
        return []
    return sorted(p for p in src.iterdir() if p.is_dir() and (p / "__init__.py").exists())


def _validate_pyproject(root: Path, reporter: Reporter) -> dict[str, str]:
    pyproject = root / "pyproject.toml"
    data = _parse_pyproject(pyproject, reporter)
    entrypoints = _entrypoints_from_pyproject(data)
    if entrypoints:
        for name, target in entrypoints.items():
            if not name.isidentifier():
                reporter.warn(pyproject, f"Entry-point name {name!r} is not a Python identifier; prefer stable identifier names.")
            if ":" not in target:
                reporter.error(pyproject, f"Entry point {name!r} target {target!r} should be 'module:object' or 'module:factory'.")
        reporter.info(pyproject, f"Found {len(entrypoints)} gptme.plugins entry point(s).")
    return entrypoints


def _validate_src_layout(root: Path, reporter: Reporter) -> None:
    packages = _src_packages(root)
    if not packages:
        return
    for package in packages:
        if not package.name.isidentifier():
            reporter.error(package, "src package name is not importable as a Python identifier.")
        py_files = _all_python_files(package)
        if not py_files:
            reporter.warn(package, "src package has no Python modules beyond package marker.")
            continue
        if not any(_has_toolspec_call(tree) for file in py_files if (tree := _parse_python(file, reporter)) is not None):
            reporter.warn(package, "No ToolSpec found under src package; this is fine for hook/command/provider-only entry-point plugins.")


def validate(root: Path) -> Reporter:
    reporter = Reporter(root)
    if not root.exists():
        reporter.error(root, "Path does not exist.")
        return reporter
    if not root.is_dir():
        reporter.error(root, "Path is not a directory.")
        return reporter

    entrypoints = _validate_pyproject(root, reporter)
    src_packages = _src_packages(root)
    is_folder_plugin = (root / "__init__.py").exists()
    component_dirs = [root / "tools", root / "hooks", root / "commands"]
    has_component = any(p.exists() for p in component_dirs)

    if is_folder_plugin:
        if not root.name.isidentifier():
            reporter.error(root, "Folder plugin directory name is not importable as a Python identifier; use underscores or an entry-point package.")
        if not has_component:
            reporter.warn(root, "Folder plugin has no tools/, hooks/, or commands/ directory.")
        _validate_tools_dir(root / "tools", reporter)
        _validate_registry_dir(root / "hooks", reporter, "hook")
        _validate_registry_dir(root / "commands", reporter, "command")
    else:
        if has_component:
            reporter.error(root, "tools/hooks/commands directories are present but root __init__.py is missing; folder plugin discovery will skip this directory.")

    if src_packages:
        _validate_src_layout(root, reporter)

    if not is_folder_plugin and not entrypoints and not src_packages:
        reporter.error(root, "No folder plugin, src-layout package, or gptme.plugins entry point detected.")
    elif src_packages and not entrypoints and not is_folder_plugin:
        reporter.warn(root, "src-layout package detected without gptme.plugins entry point; ensure this directory is configured as a plugin path if relying on folder discovery.")

    if not has_component and not entrypoints and not src_packages:
        reporter.error(root, "No plugin components found. Add tools/, hooks/, commands/, src package, or gptme.plugins entry point.")

    return reporter


# ── Output ──────────────────────────────────────────────────────────────────


def summarize_findings(findings: list[Finding], strict: bool) -> dict[str, Any]:
    errors = sum(1 for item in findings if item.severity == "ERROR")
    warnings = sum(1 for item in findings if item.severity == "WARN")
    infos = sum(1 for item in findings if item.severity == "INFO")
    ok = errors == 0 and (warnings == 0 or not strict)
    return {
        "ok": ok,
        "errors": errors,
        "warnings": warnings,
        "infos": infos,
        "strict": strict,
        "findings": [asdict(item) for item in findings],
    }


def render_text(summary: dict[str, Any], root: Path) -> str:
    status = "OK" if summary["ok"] else "FAILED"
    lines = [
        f"gptme plugin skeleton validation: {status}",
        f"target: {root}",
        f"errors={summary['errors']} warnings={summary['warnings']} infos={summary['infos']}",
    ]
    if not summary["findings"]:
        lines.append("No findings.")
    else:
        lines.append("")
        for item in summary["findings"]:
            lines.append(f"[{item['severity']}] {item['path']}: {item['message']}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Statically validate a gptme plugin folder or installable plugin package.",
    )
    parser.add_argument("path", help="Plugin directory or package root to validate.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as validation failures.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of text.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(args.path).expanduser().resolve()
    reporter = validate(root)
    summary = summarize_findings(reporter.findings, strict=args.strict)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(render_text(summary, root))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
