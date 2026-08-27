#!/usr/bin/env python3
"""Inspect PARL algorithm availability without training or installing packages.

The script is safe and read-only. It first tries to import PARL for the selected
backend, then falls back to static source inspection when a PARL source tree is
available. It intentionally avoids printing local interpreter paths or package
installation locations.
"""

from __future__ import annotations

import argparse
import ast
import contextlib
import importlib
import inspect
import io
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

DEFAULT_ALGORITHMS = [
    "PolicyGradient",
    "DQN",
    "DDQN",
    "DDPG",
    "TD3",
    "SAC",
    "OAC",
    "CQL",
    "PPO",
    "A2C",
    "A3C",
    "IMPALA",
    "QMIX",
    "MADDPG",
    "COMA",
    "MAPPO",
    "DecisionTransformer",
    "IQL",
]

MODULE_BY_CLASS = {
    "PolicyGradient": "policy_gradient",
    "DQN": "dqn",
    "DDQN": "ddqn",
    "DDPG": "ddpg",
    "TD3": "td3",
    "SAC": "sac",
    "OAC": "oac",
    "CQL": "cql",
    "PPO": "ppo",
    "A2C": "a2c",
    "A3C": "a3c",
    "IMPALA": "impala.impala",
    "QMIX": "qmix",
    "MADDPG": "maddpg",
    "COMA": "coma",
    "MAPPO": "mappo",
    "DecisionTransformer": "dt",
    "IQL": "iql",
}

BACKENDS = ("torch", "paddle", "fluid")


def sanitize(text: Any) -> str:
    """Remove machine-specific path fragments from a diagnostic string."""
    s = str(text)
    s = re.sub(r"/[\w.\-+@%:,=~]+(?:/[\w.\-+@%:,=~]+)+", "<path>", s)
    s = re.sub(r"[A-Za-z]:\\(?:[^\\\s]+\\)+[^\\\s]+", "<path>", s)
    return s


def wanted_algorithms(values: Optional[Sequence[str]]) -> List[str]:
    if not values:
        return list(DEFAULT_ALGORITHMS)
    requested: List[str] = []
    for value in values:
        for part in value.split(","):
            name = part.strip()
            if name:
                requested.append(name)
    return requested


def short_signature(cls: type, display_name: str) -> str:
    try:
        sig = inspect.signature(cls.__init__)
    except (TypeError, ValueError):
        return f"{display_name}(...)"
    params = list(sig.parameters.values())
    if params and params[0].name == "self":
        params = params[1:]
    return f"{display_name}({', '.join(str(p) for p in params)})"


def public_methods(cls: type) -> List[str]:
    names = []
    for name, member in inspect.getmembers(cls):
        if name.startswith("_"):
            continue
        if inspect.isfunction(member) or inspect.ismethoddescriptor(member):
            names.append(name)
    return sorted(set(names))


def try_import_backend(backend: str, algorithms: Sequence[str]) -> Dict[str, Any]:
    if backend != "auto":
        os.environ["PARL_BACKEND"] = backend
    captured_out = io.StringIO()
    captured_err = io.StringIO()
    result: Dict[str, Any] = {"status": "not-run", "records": [], "error": None}
    try:
        with contextlib.redirect_stdout(captured_out), contextlib.redirect_stderr(captured_err):
            parl = importlib.import_module("parl")
            alg_module = importlib.import_module("parl.algorithms")
        result["status"] = "ok"
        result["version"] = sanitize(getattr(parl, "__version__", "unknown"))
        for name in algorithms:
            obj = getattr(alg_module, name, None)
            source = "parl.algorithms"
            if obj is None and backend in BACKENDS:
                module_name = MODULE_BY_CLASS.get(name)
                if module_name:
                    try:
                        with contextlib.redirect_stdout(captured_out), contextlib.redirect_stderr(captured_err):
                            module = importlib.import_module(f"parl.algorithms.{backend}.{module_name}")
                        obj = getattr(module, name, None)
                        source = f"parl.algorithms.{backend}.{module_name}"
                    except Exception:
                        obj = None
            if inspect.isclass(obj):
                result["records"].append(
                    {
                        "backend": backend,
                        "name": name,
                        "source": source,
                        "signature": short_signature(obj, name),
                        "public_methods": public_methods(obj),
                        "required_model_methods": [],
                        "mode": "import",
                    }
                )
        return result
    except Exception as exc:  # noqa: BLE001 - report missing optional backends cleanly.
        result["status"] = "failed"
        result["error"] = f"{type(exc).__name__}: {sanitize(exc)}"
        return result


def discover_source_root(user_value: Optional[str]) -> Optional[Path]:
    candidates: List[Path] = []
    if user_value:
        candidates.append(Path(user_value).expanduser())
    candidates.append(Path.cwd())
    candidates.extend(Path.cwd().parents)
    script_path = Path(__file__).resolve()
    candidates.append(script_path.parent)
    candidates.extend(script_path.parents)

    for candidate in candidates:
        try:
            path = candidate.resolve()
        except OSError:
            continue
        if (path / "parl" / "algorithms").is_dir():
            return path
        if path.name == "parl" and (path / "algorithms").is_dir():
            return path.parent
    return None


def literal_unparse(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except Exception:  # pragma: no cover - for very old Python fallback.
        if isinstance(node, ast.Constant):
            return repr(node.value)
        return "..."


def ast_signature(init: ast.FunctionDef, display_name: str) -> str:
    args = init.args
    positional = list(args.posonlyargs) + list(args.args)
    defaults = list(args.defaults)
    default_start = len(positional) - len(defaults)
    rendered: List[str] = []

    for idx, arg in enumerate(positional):
        if arg.arg == "self":
            continue
        if idx >= default_start:
            rendered.append(f"{arg.arg}={literal_unparse(defaults[idx - default_start])}")
        else:
            rendered.append(arg.arg)
    if args.vararg:
        rendered.append("*" + args.vararg.arg)
    if args.kwonlyargs:
        if not args.vararg:
            rendered.append("*")
        for arg, default in zip(args.kwonlyargs, args.kw_defaults):
            if default is None:
                rendered.append(arg.arg)
            else:
                rendered.append(f"{arg.arg}={literal_unparse(default)}")
    if args.kwarg:
        rendered.append("**" + args.kwarg.arg)
    return f"{display_name}({', '.join(rendered)})"


def call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def required_methods_from_class(cls: ast.ClassDef) -> List[str]:
    required: List[str] = []
    for node in ast.walk(cls):
        if isinstance(node, ast.Call) and call_name(node.func).endswith("check_model_method"):
            if len(node.args) >= 2:
                target = call_name(node.args[0]) or "model"
                method = node.args[1].value if isinstance(node.args[1], ast.Constant) else None
                if isinstance(method, str):
                    if target == "model":
                        required.append(method)
                    else:
                        required.append(f"{target}.{method}")
        if isinstance(node, ast.Call) and call_name(node.func) == "hasattr" and len(node.args) >= 2:
            target = call_name(node.args[0])
            attr = node.args[1].value if isinstance(node.args[1], ast.Constant) else None
            if target and isinstance(attr, str):
                required.append(f"{target}.{attr}")
    return sorted(set(required))


def ast_public_methods(cls: ast.ClassDef) -> List[str]:
    return sorted(
        node.name
        for node in cls.body
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
    )


def inspect_source_backend(source_root: Path, backend: str, algorithms: Sequence[str]) -> List[Dict[str, Any]]:
    base = source_root / "parl" / "algorithms" / backend
    if not base.is_dir():
        return []
    files = sorted(base.glob("*.py")) + sorted((base / "impala").glob("*.py"))
    wanted = set(algorithms)
    records: List[Dict[str, Any]] = []
    for file_path in files:
        if file_path.name == "__init__.py":
            continue
        try:
            tree = ast.parse(file_path.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError as exc:
            records.append(
                {
                    "backend": backend,
                    "name": file_path.stem,
                    "source": "source-ast",
                    "signature": "parse-failed",
                    "public_methods": [],
                    "required_model_methods": [],
                    "mode": "source",
                    "error": sanitize(exc),
                }
            )
            continue
        for cls in [node for node in tree.body if isinstance(node, ast.ClassDef)]:
            if cls.name.startswith("_") or cls.name not in wanted:
                continue
            init = next(
                (node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == "__init__"),
                None,
            )
            signature = ast_signature(init, cls.name) if init else f"{cls.name}(...)"
            records.append(
                {
                    "backend": backend,
                    "name": cls.name,
                    "source": "source-ast",
                    "signature": signature,
                    "public_methods": ast_public_methods(cls),
                    "required_model_methods": required_methods_from_class(cls),
                    "mode": "source",
                }
            )
    return records


def markdown_table(records: Sequence[Dict[str, Any]]) -> str:
    lines = [
        "| Backend | Algorithm | Mode | Signature | Public methods | Required model methods |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for rec in records:
        methods = ", ".join(rec.get("public_methods") or []) or "-"
        required = ", ".join(rec.get("required_model_methods") or []) or "-"
        lines.append(
            "| {backend} | {name} | {mode} | `{signature}` | {methods} | {required} |".format(
                backend=rec.get("backend", "?"),
                name=rec.get("name", "?"),
                mode=rec.get("mode", "?"),
                signature=str(rec.get("signature", "?")).replace("|", "\\|"),
                methods=methods.replace("|", "\\|"),
                required=required.replace("|", "\\|"),
            )
        )
    return "\n".join(lines)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect PARL algorithm class availability/signatures safely, with static fallback."
    )
    parser.add_argument(
        "--backend",
        choices=("auto",) + BACKENDS,
        default="auto",
        help="Backend to request before importing PARL. Use auto to leave PARL_BACKEND unchanged.",
    )
    parser.add_argument(
        "--algorithm",
        action="append",
        help="Algorithm class name to inspect. May be repeated or comma-separated. Defaults to major PARL classes.",
    )
    parser.add_argument(
        "--source-root",
        help="Optional PARL source/package root for static fallback. No source paths are printed.",
    )
    parser.add_argument(
        "--no-import",
        action="store_true",
        help="Skip importing PARL and use static source inspection only.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of Markdown.")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    algorithms = wanted_algorithms(args.algorithm)

    import_result: Dict[str, Any] = {"status": "skipped", "records": [], "error": None}
    if not args.no_import:
        import_result = try_import_backend(args.backend, algorithms)

    source_root = discover_source_root(args.source_root)
    source_records: List[Dict[str, Any]] = []
    source_backends = BACKENDS if args.backend == "auto" else (args.backend,)
    if source_root is not None:
        for backend in source_backends:
            source_records.extend(inspect_source_backend(source_root, backend, algorithms))

    records: List[Dict[str, Any]] = []
    records.extend(import_result.get("records", []))

    imported_keys = {(rec["backend"], rec["name"]) for rec in records}
    for rec in source_records:
        key = (rec["backend"], rec["name"])
        if key not in imported_keys:
            records.append(rec)

    payload = {
        "backend_request": args.backend,
        "import_status": import_result.get("status"),
        "import_error": import_result.get("error"),
        "source_status": "available" if source_root is not None else "not-found",
        "record_count": len(records),
        "records": records,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("# PARL algorithm catalog inspection")
        print()
        print(f"- backend request: `{args.backend}`")
        print(f"- import status: `{payload['import_status']}`")
        if payload["import_error"]:
            print(f"- import error: `{payload['import_error']}`")
        print(f"- source fallback: `{payload['source_status']}`")
        print(f"- records: `{len(records)}`")
        print()
        if records:
            print(markdown_table(records))
        else:
            print("No algorithms were discovered. Install/verify the selected backend or pass --source-root for static inspection.")

    return 0 if records else 2


if __name__ == "__main__":
    raise SystemExit(main())
