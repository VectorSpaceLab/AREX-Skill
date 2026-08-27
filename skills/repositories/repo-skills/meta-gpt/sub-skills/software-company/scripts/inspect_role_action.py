#!/usr/bin/env python3
"""Safely inspect MetaGPT software-company Role/Action APIs without LLM calls.

This script is adapted from MetaGPT's custom-agent examples, but it never calls
Action._aask(), Team.run(), generate_repo(), or any project-generation CLI path.
It first tries normal installed-package introspection, which may still validate
config2.yaml while constructing dry Role/Action objects. If imports, config
validation, or optional dependencies fail, it falls back to parsing local package
source signatures so agents can diagnose readiness without network or LLM calls.
"""

from __future__ import annotations

import argparse
import ast
import importlib.metadata
import inspect
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


CONSOLE_SCRIPT = "metagpt=metagpt.software_company:app"


def _stringify(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _stringify(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_stringify(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _find_source_root() -> Path | None:
    candidates: list[Path] = [Path.cwd()]
    try:
        candidates.append(Path(__file__).resolve().parent)
    except NameError:
        pass

    seen: set[Path] = set()
    for candidate in candidates:
        for parent in [candidate, *candidate.parents]:
            if parent in seen:
                continue
            seen.add(parent)
            if (parent / "metagpt" / "software_company.py").is_file():
                return parent
    return None


def _ensure_source_root_on_path() -> Path | None:
    source_root = _find_source_root()
    if source_root and str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))
    return source_root


def _distribution_version() -> str:
    try:
        return importlib.metadata.version("metagpt")
    except importlib.metadata.PackageNotFoundError:
        return "not-installed-as-distribution"


def _ast_module(source_root: Path, relative_path: str) -> ast.Module:
    return ast.parse((source_root / relative_path).read_text(encoding="utf-8"))


def _unparse(node: ast.AST | None) -> str:
    if node is None:
        return ""
    return ast.unparse(node)


def _format_arg(arg: ast.arg, default: ast.AST | None = None) -> str:
    text = arg.arg
    if arg.annotation is not None:
        text += f": {_unparse(arg.annotation)}"
    if default is not None:
        text += f"={_unparse(default)}"
    return text


def _format_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    args = node.args
    params: list[str] = []

    positional = [*args.posonlyargs, *args.args]
    defaults = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)
    for index, (arg, default) in enumerate(zip(positional, defaults)):
        if args.posonlyargs and index == len(args.posonlyargs):
            params.append("/")
        params.append(_format_arg(arg, default))

    if args.vararg:
        vararg = "*" + args.vararg.arg
        if args.vararg.annotation is not None:
            vararg += f": {_unparse(args.vararg.annotation)}"
        params.append(vararg)
    elif args.kwonlyargs:
        params.append("*")

    for arg, default in zip(args.kwonlyargs, args.kw_defaults):
        params.append(_format_arg(arg, default))

    if args.kwarg:
        kwarg = "**" + args.kwarg.arg
        if args.kwarg.annotation is not None:
            kwarg += f": {_unparse(args.kwarg.annotation)}"
        params.append(kwarg)

    signature = f"({', '.join(params)})"
    if node.returns is not None:
        signature += f" -> {_unparse(node.returns)}"
    return signature


def _find_function_signature(
    source_root: Path,
    relative_path: str,
    function_name: str,
    class_name: str | None = None,
) -> str | None:
    module = _ast_module(source_root, relative_path)
    body: list[ast.stmt]
    if class_name is None:
        body = module.body
    else:
        class_node = next(
            (node for node in module.body if isinstance(node, ast.ClassDef) and node.name == class_name),
            None,
        )
        if class_node is None:
            return None
        body = class_node.body

    for node in body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
            return _format_signature(node)
    return None


def _find_enum_values(source_root: Path, relative_path: str, class_name: str) -> list[str]:
    module = _ast_module(source_root, relative_path)
    for node in module.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            values: list[str] = []
            for stmt in node.body:
                if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Constant):
                    if isinstance(stmt.value.value, str):
                        values.append(stmt.value.value)
            return values
    return []


def _check_cli_help() -> dict[str, Any]:
    executable = shutil.which("metagpt")
    if not executable:
        return {"ok": False, "error": "metagpt executable not found on PATH"}

    completed = subprocess.run(
        [executable, "--help"],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    return {
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout_first_lines": completed.stdout.splitlines()[:30],
        "stderr_first_lines": completed.stderr.splitlines()[:20],
    }


def _collect_from_imports(check_cli_help: bool) -> dict[str, Any]:
    _ensure_source_root_on_path()

    import metagpt
    from metagpt.actions import Action
    from metagpt.roles.role import Role, RoleReactMode
    from metagpt.schema import Message
    from metagpt.software_company import app, generate_repo, startup
    from metagpt.team import Team
    from metagpt.utils.project_repo import ProjectRepo

    class InspectAction(Action):
        name: str = "InspectAction"

        async def run(self, instruction: str = "") -> str:
            return f"dry-run:{instruction}"

    class InspectRole(Role):
        name: str = "Inspector"
        profile: str = "DryRunInspector"

        def __init__(self, **kwargs: Any):
            super().__init__(**kwargs)
            self.set_actions([InspectAction])

    role = InspectRole()
    message = Message(content="dry inspection only", role="user")

    result: dict[str, Any] = {
        "ok": True,
        "mode": "imported-core-apis",
        "metagpt_module": getattr(metagpt, "__name__", "metagpt"),
        "distribution_version": _distribution_version(),
        "console_script": CONSOLE_SCRIPT,
        "generate_repo_signature": str(inspect.signature(generate_repo)),
        "startup_signature": str(inspect.signature(startup)),
        "team_run_signature": str(inspect.signature(Team.run)),
        "team_methods": ["hire", "invest", "run_project", "run", "serialize", "deserialize"],
        "role_react_modes": RoleReactMode.values(),
        "inspect_role": {
            "name": role.name,
            "profile": role.profile,
            "actions": [str(action) for action in role.actions],
            "watch": sorted(role.rc.watch),
            "react_mode": str(role.rc.react_mode),
            "is_idle": role.is_idle,
        },
        "inspect_action_signature": str(inspect.signature(InspectAction.run)),
        "message_fields_sample": _stringify(message.model_dump()),
        "project_repo_class": ProjectRepo.__name__,
        "typer_app_type": type(app).__name__,
        "cli_help": None,
    }

    if check_cli_help:
        result["cli_help"] = _check_cli_help()

    return result


def _collect_from_source_fallback(check_cli_help: bool, import_error: BaseException) -> dict[str, Any]:
    source_root = _find_source_root()
    if source_root is None:
        return {
            "ok": False,
            "mode": "unavailable",
            "error": f"{type(import_error).__name__}: {import_error}",
            "hint": "Install MetaGPT or run this script from a MetaGPT source checkout.",
        }

    result: dict[str, Any] = {
        "ok": True,
        "mode": "source-fallback-no-core-imports",
        "import_error": f"{type(import_error).__name__}: {import_error}",
        "distribution_version": _distribution_version(),
        "console_script": CONSOLE_SCRIPT,
        "generate_repo_signature": _find_function_signature(source_root, "metagpt/software_company.py", "generate_repo"),
        "startup_signature": _find_function_signature(source_root, "metagpt/software_company.py", "startup"),
        "team_run_signature": _find_function_signature(source_root, "metagpt/team.py", "run", "Team"),
        "team_methods": ["hire", "invest", "run_project", "run", "serialize", "deserialize"],
        "role_react_modes": _find_enum_values(source_root, "metagpt/roles/role.py", "RoleReactMode"),
        "inspect_role": {
            "name": "Inspector",
            "profile": "DryRunInspector",
            "actions": ["InspectAction"],
            "watch": ["UserRequirement"],
            "react_mode": "react",
            "is_idle": True,
        },
        "inspect_action_signature": "(self, instruction: str='') -> str",
        "message_fields_sample": {"content": "dry inspection only", "role": "user"},
        "project_repo_class": "ProjectRepo",
        "typer_app_type": "Typer (source fallback)",
        "cli_help": None,
    }

    if check_cli_help:
        result["cli_help"] = _check_cli_help()

    missing = [
        key
        for key in ["generate_repo_signature", "startup_signature", "team_run_signature"]
        if not result.get(key)
    ]
    if missing:
        result["ok"] = False
        result["missing"] = missing

    return result


def collect_inspection(check_cli_help: bool = False) -> dict[str, Any]:
    try:
        return _collect_from_imports(check_cli_help=check_cli_help)
    except BaseException as exc:  # noqa: BLE001 - report environment readiness without triggering LLM work.
        return _collect_from_source_fallback(check_cli_help=check_cli_help, import_error=exc)


def print_text_report(result: dict[str, Any]) -> None:
    print("MetaGPT software-company dry inspection")
    print(f"ok: {result['ok']}")
    print(f"mode: {result.get('mode')}")
    if result.get("import_error"):
        print(f"import_error: {result['import_error']}")
    if result.get("error"):
        print(f"error: {result['error']}")
    print(f"distribution_version: {result.get('distribution_version')}")
    print(f"console_script: {result.get('console_script')}")
    print(f"generate_repo: {result.get('generate_repo_signature')}")
    print(f"startup: {result.get('startup_signature')}")
    print(f"team.run: {result.get('team_run_signature')}")
    print(f"role_react_modes: {', '.join(result.get('role_react_modes') or [])}")
    inspect_role = result.get("inspect_role") or {}
    print(f"inspect_role_actions: {', '.join(inspect_role.get('actions') or [])}")
    if result.get("cli_help") is not None:
        cli = result["cli_help"]
        print(f"cli_help_ok: {cli.get('ok')}")
        if not cli.get("ok"):
            print(f"cli_help_error: {cli.get('error') or cli.get('stderr_first_lines')}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument(
        "--check-cli-help",
        action="store_true",
        help="Run `metagpt --help` as a no-LLM console entry-point check.",
    )
    args = parser.parse_args(argv)

    result = collect_inspection(check_cli_help=args.check_cli_help)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_text_report(result)

    if not result.get("ok"):
        return 1
    cli_help = result.get("cli_help")
    if cli_help is not None and not cli_help.get("ok"):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
