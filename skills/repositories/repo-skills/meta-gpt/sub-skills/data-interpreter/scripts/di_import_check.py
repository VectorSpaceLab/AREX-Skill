#!/usr/bin/env python3
"""Diagnostic-only import/signature checks for MetaGPT Data Interpreter modules.

This helper never runs DI tasks, starts notebook kernels, opens browsers, calls LLMs,
or executes generated code. It imports selected modules and inspects classes/methods
so agents can distinguish configuration/import failures from workflow failures.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import inspect
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

MODULES: tuple[str, ...] = (
    "metagpt.roles.di.data_interpreter",
    "metagpt.roles.di.role_zero",
    "metagpt.roles.di.data_analyst",
    "metagpt.roles.di.swe_agent",
    "metagpt.roles.di.engineer2",
    "metagpt.roles.di.team_leader",
    "metagpt.actions.di.execute_nb_code",
    "metagpt.actions.di.write_analysis_code",
    "metagpt.actions.di.write_plan",
    "metagpt.actions.di.run_command",
)

OBJECTS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("metagpt.roles.di.data_interpreter", "DataInterpreter", ("run", "_write_and_exec_code")),
    ("metagpt.roles.di.role_zero", "RoleZero", ("run", "_think", "_act", "ask_human")),
    ("metagpt.roles.di.data_analyst", "DataAnalyst", ("run", "write_and_exec_code")),
    ("metagpt.roles.di.swe_agent", "SWEAgent", ("run",)),
    ("metagpt.roles.di.engineer2", "Engineer2", ("run", "write_new_code")),
    ("metagpt.roles.di.team_leader", "TeamLeader", ("run", "publish_team_message")),
    ("metagpt.actions.di.execute_nb_code", "ExecuteNbCode", ("run", "terminate", "reset", "init_code")),
    ("metagpt.actions.di.write_analysis_code", "WriteAnalysisCode", ("run",)),
    ("metagpt.actions.di.write_analysis_code", "CheckData", ("run",)),
    ("metagpt.actions.di.write_plan", "WritePlan", ("run",)),
)

PLACEHOLDER_MARKERS = (
    "placeholder",
    "your api key",
    "your_api_key",
    "api_key",
    "config2.yaml",
    "llm api key",
    "openai_api_key",
    "please set",
    "not set",
)

OPTIONAL_DEPENDENCY_HINTS = (
    "No module named",
    "ModuleNotFoundError",
    "ImportError",
    "cannot import name",
)


@dataclass
class CheckResult:
    name: str
    ok: bool
    status: str
    detail: str = ""
    signatures: dict[str, str] = field(default_factory=dict)


def classify_exception(exc: BaseException) -> str:
    text = f"{type(exc).__name__}: {exc}"
    lowered = text.lower()
    if any(marker in lowered for marker in PLACEHOLDER_MARKERS):
        return "placeholder_config_or_api_key"
    if any(marker.lower() in lowered for marker in OPTIONAL_DEPENDENCY_HINTS):
        return "missing_dependency_or_import_error"
    return "import_or_signature_error"


def safe_detail(exc: BaseException) -> str:
    detail = f"{type(exc).__name__}: {exc}"
    return " ".join(detail.split())[:700]


def prepare_import_path(repo_root: str | None) -> str:
    candidates: list[Path] = []
    if repo_root:
        candidates.append(Path(repo_root).expanduser().resolve())

    for origin in (Path.cwd().resolve(), Path(__file__).resolve()):
        candidates.append(origin)
        candidates.extend(origin.parents)

    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if (candidate / "metagpt").is_dir():
            candidate_text = str(candidate)
            if candidate_text not in sys.path:
                sys.path.insert(0, candidate_text)
            return "local-checkout"
    return "environment"


def get_version() -> str:
    try:
        return importlib.metadata.version("metagpt")
    except importlib.metadata.PackageNotFoundError:
        try:
            module = importlib.import_module("metagpt")
            version = getattr(module, "__version__", None)
            return str(version) if version else "local-checkout-version-unknown"
        except Exception:
            return "not-installed"
    except Exception as exc:  # pragma: no cover - diagnostic fallback
        return f"unavailable ({type(exc).__name__})"


def check_module(module_name: str) -> CheckResult:
    try:
        importlib.import_module(module_name)
        return CheckResult(name=module_name, ok=True, status="imported")
    except Exception as exc:
        return CheckResult(name=module_name, ok=False, status=classify_exception(exc), detail=safe_detail(exc))


def check_object(module_name: str, object_name: str, methods: tuple[str, ...]) -> CheckResult:
    display_name = f"{module_name}.{object_name}"
    try:
        module = importlib.import_module(module_name)
        obj = getattr(module, object_name)
    except Exception as exc:
        return CheckResult(name=display_name, ok=False, status=classify_exception(exc), detail=safe_detail(exc))

    signatures: dict[str, str] = {}
    try:
        signatures[object_name] = str(inspect.signature(obj))
    except Exception as exc:
        signatures[object_name] = f"unavailable ({type(exc).__name__})"

    ok = True
    status = "signatures_available"
    details: list[str] = []
    for method_name in methods:
        try:
            method = getattr(obj, method_name)
            signatures[method_name] = str(inspect.signature(method))
        except Exception as exc:
            ok = False
            status = "signature_unavailable"
            details.append(f"{method_name}: {safe_detail(exc)}")

    return CheckResult(name=display_name, ok=ok, status=status, detail="; ".join(details), signatures=signatures)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safely check MetaGPT DI importability and signatures.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero when any checked import/signature fails.")
    parser.add_argument(
        "--modules-only",
        action="store_true",
        help="Only import modules; skip object and method signature inspection.",
    )
    parser.add_argument(
        "--repo-root",
        help="Optional local MetaGPT checkout root to prepend to sys.path for diagnostics.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    import_source = prepare_import_path(args.repo_root)
    module_results = [check_module(module_name) for module_name in MODULES]
    object_results: list[CheckResult] = [] if args.modules_only else [
        check_object(module_name, object_name, methods) for module_name, object_name, methods in OBJECTS
    ]
    all_results = module_results + object_results
    ok = all(result.ok for result in all_results)

    payload: dict[str, Any] = {
        "ok": ok,
        "metagpt_version": get_version(),
        "import_source": import_source,
        "modules": [asdict(result) for result in module_results],
        "objects": [asdict(result) for result in object_results],
        "notes": [
            "Diagnostic-only: no DI tasks, notebook kernels, LLM calls, browser sessions, or generated code were run.",
            "placeholder_config_or_api_key usually means root MetaGPT LLM config must be fixed before DI can run.",
            "missing_dependency_or_import_error may be optional unless the requested DI workflow needs that module.",
        ],
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"MetaGPT version: {payload['metagpt_version']}")
        print(f"Import source: {payload['import_source']}")
        print("Safety: no DI tasks, notebook kernels, LLM calls, browser sessions, or generated code were run.")
        print("\nModule imports:")
        for result in module_results:
            marker = "OK" if result.ok else "FAIL"
            print(f"  [{marker}] {result.name}: {result.status}")
            if result.detail:
                print(f"        {result.detail}")
        if object_results:
            print("\nObject signatures:")
            for result in object_results:
                marker = "OK" if result.ok else "FAIL"
                print(f"  [{marker}] {result.name}: {result.status}")
                for sig_name, signature in result.signatures.items():
                    print(f"        {sig_name}{signature}")
                if result.detail:
                    print(f"        {result.detail}")
        print("\nInterpretation:")
        print("  - placeholder_config_or_api_key: fix root MetaGPT LLM config/API keys before DI execution.")
        print("  - missing_dependency_or_import_error: install only if the requested workflow needs that optional surface.")
        print("  - signature_unavailable: API drift may require checking the installed package version.")

    return 1 if args.strict and not ok else 0


if __name__ == "__main__":
    raise SystemExit(main())
