#!/usr/bin/env python3
"""Inspect ai_data_science_team dataframe code-agent APIs without model calls.

Safe-by-default checks:
- import relevant modules/classes/functions
- inspect public signatures and expected wrapper methods
- exercise DataWranglingAgent input conversion without constructing an agent
- run tiny deterministic pandas snippets through the package sandbox
- confirm a blocked import is rejected by the sandbox

This script does not invoke any package agent, call any LLM/model, download data,
launch services, train models, or write files.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import os
import sys
from dataclasses import dataclass, asdict
from typing import Any

# Keep tiny pandas/numpy subprocess checks deterministic and memory-friendly.
for _thread_env in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_thread_env, "1")


@dataclass
class Check:
    name: str
    passed: bool
    detail: str


def _stringify_signature(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except Exception as exc:  # pragma: no cover - defensive
        return f"<signature unavailable: {exc}>"


def _has_method(obj: Any, method_name: str) -> bool:
    return callable(getattr(obj, method_name, None))


def inspect_dataframe_agents(run_sandbox: bool = True) -> dict[str, Any]:
    checks: list[Check] = []
    report: dict[str, Any] = {
        "package": "ai-data-science-team",
        "import": "ai_data_science_team",
        "version": None,
        "classes": {},
        "factories": {},
        "checks": [],
    }

    def record(name: str, passed: bool, detail: str = "") -> None:
        checks.append(Check(name=name, passed=bool(passed), detail=str(detail)))

    try:
        version_mod = importlib.import_module("ai_data_science_team._version")
        report["version"] = getattr(version_mod, "__version__", None)
        record("import version", True, str(report["version"]))
    except Exception as exc:
        record("import version", False, repr(exc))

    modules: dict[str, Any] = {}
    module_names = {
        "data_cleaning_agent": "ai_data_science_team.agents.data_cleaning_agent",
        "data_wrangling_agent": "ai_data_science_team.agents.data_wrangling_agent",
        "data_visualization_agent": "ai_data_science_team.agents.data_visualization_agent",
        "feature_engineering_agent": "ai_data_science_team.agents.feature_engineering_agent",
        "templates": "ai_data_science_team.templates.agent_templates",
        "sandbox": "ai_data_science_team.utils.sandbox",
        "logging": "ai_data_science_team.utils.logging",
    }
    for short, module_name in module_names.items():
        try:
            modules[short] = importlib.import_module(module_name)
            record(f"import {module_name}", True, "ok")
        except Exception as exc:
            modules[short] = None
            record(f"import {module_name}", False, repr(exc))

    class_specs = {
        "DataCleaningAgent": (
            modules.get("data_cleaning_agent"),
            [
                "invoke_agent",
                "ainvoke_agent",
                "invoke_messages",
                "ainvoke_messages",
                "get_data_cleaned",
                "get_data_raw",
                "get_data_cleaner_function",
                "get_recommended_cleaning_steps",
                "get_workflow_summary",
                "get_log_summary",
                "get_response",
                "update_params",
            ],
        ),
        "DataWranglingAgent": (
            modules.get("data_wrangling_agent"),
            [
                "invoke_agent",
                "ainvoke_agent",
                "invoke_messages",
                "ainvoke_messages",
                "get_data_wrangled",
                "get_data_raw",
                "get_data_wrangler_function",
                "get_recommended_wrangling_steps",
                "get_workflow_summary",
                "get_log_summary",
                "get_response",
                "update_params",
                "_convert_data_input",
            ],
        ),
        "DataVisualizationAgent": (
            modules.get("data_visualization_agent"),
            [
                "invoke_agent",
                "ainvoke_agent",
                "invoke_messages",
                "ainvoke_messages",
                "get_plotly_graph",
                "get_data_raw",
                "get_data_visualization_function",
                "get_recommended_visualization_steps",
                "run_smoke_tests",
                "get_workflow_summary",
                "get_log_summary",
                "get_response",
                "update_params",
            ],
        ),
        "FeatureEngineeringAgent": (
            modules.get("feature_engineering_agent"),
            [
                "invoke_agent",
                "ainvoke_agent",
                "invoke_messages",
                "ainvoke_messages",
                "get_data_engineered",
                "get_data_raw",
                "get_feature_engineer_function",
                "get_recommended_feature_engineering_steps",
                "get_workflow_summary",
                "get_log_summary",
                "get_response",
                "update_params",
            ],
        ),
    }

    for class_name, (module, expected_methods) in class_specs.items():
        if module is None or not hasattr(module, class_name):
            record(f"class {class_name}", False, "missing")
            continue
        cls = getattr(module, class_name)
        sig = _stringify_signature(cls)
        methods = {method: _has_method(cls, method) for method in expected_methods}
        report["classes"][class_name] = {"signature": sig, "methods": methods}
        record(f"signature {class_name}", "model" in sig, sig)
        missing = [method for method, ok in methods.items() if not ok]
        record(
            f"methods {class_name}",
            not missing,
            "ok" if not missing else "missing: " + ", ".join(missing),
        )

    factory_specs = {
        "make_data_cleaning_agent": modules.get("data_cleaning_agent"),
        "make_data_wrangling_agent": modules.get("data_wrangling_agent"),
        "make_data_visualization_agent": modules.get("data_visualization_agent"),
        "make_feature_engineering_agent": modules.get("feature_engineering_agent"),
    }
    for func_name, module in factory_specs.items():
        if module is None or not hasattr(module, func_name):
            record(f"factory {func_name}", False, "missing")
            continue
        func = getattr(module, func_name)
        sig = _stringify_signature(func)
        report["factories"][func_name] = {"signature": sig}
        record(f"signature {func_name}", "model" in sig and "max_retries" not in sig, sig)

    try:
        public_agents = importlib.import_module("ai_data_science_team.agents")
        public_names = list(class_specs) + list(factory_specs)
        missing_public = [name for name in public_names if not hasattr(public_agents, name)]
        record(
            "public ai_data_science_team.agents exports",
            not missing_public,
            "ok" if not missing_public else "missing: " + ", ".join(missing_public),
        )
    except Exception as exc:
        record("public ai_data_science_team.agents exports", False, repr(exc))

    try:
        import pandas as pd

        wrangling_mod = modules.get("data_wrangling_agent")
        if wrangling_mod is None:
            raise RuntimeError("data_wrangling_agent module unavailable")
        cls = getattr(wrangling_mod, "DataWranglingAgent")
        df = pd.DataFrame({"id": [1, 2], "value": [10, 20]})
        one = cls._convert_data_input(df)
        many = cls._convert_data_input([df, df])
        ok = isinstance(one, dict) and isinstance(many, list) and len(many) == 2
        record("DataWranglingAgent._convert_data_input", ok, "ok" if ok else repr((type(one), type(many))))
    except Exception as exc:
        record("DataWranglingAgent._convert_data_input", False, repr(exc))

    if run_sandbox:
        try:
            import pandas as pd

            sandbox_mod = modules.get("sandbox")
            if sandbox_mod is None:
                raise RuntimeError("sandbox module unavailable")
            run_code_sandboxed_subprocess = getattr(sandbox_mod, "run_code_sandboxed_subprocess")

            df = pd.DataFrame({"id": [1, 1, 2], "value": [10, 10, 20]})
            cleaning_code = """
def data_cleaner(data_raw):
    import pandas as pd
    df = data_raw.copy()
    return df.drop_duplicates().reset_index(drop=True)
""".strip()
            result, error = run_code_sandboxed_subprocess(
                code_snippet=cleaning_code,
                function_name="data_cleaner",
                data=df.to_dict(),
                timeout=10,
                memory_limit_mb=4096,
                data_format="dataframe",
            )
            cleaned = pd.DataFrame(result) if error is None else pd.DataFrame()
            record(
                "sandbox dataframe execution",
                error is None and cleaned.shape == (2, 2),
                "ok" if error is None else str(error),
            )

            left = pd.DataFrame({"id": [1], "left": [10]})
            right = pd.DataFrame({"id": [2], "left": [20]})
            wrangling_code = """
def data_wrangler(data_list):
    import pandas as pd
    return pd.concat(data_list, ignore_index=True)
""".strip()
            result, error = run_code_sandboxed_subprocess(
                code_snippet=wrangling_code,
                function_name="data_wrangler",
                data=[left.to_dict(), right.to_dict()],
                timeout=10,
                memory_limit_mb=4096,
                data_format="dataframe_list",
            )
            wrangled = pd.DataFrame(result) if error is None else pd.DataFrame()
            record(
                "sandbox dataframe_list execution",
                error is None and wrangled.shape == (2, 2),
                "ok" if error is None else str(error),
            )

            blocked_code = """
def data_cleaner(data_raw):
    import os
    return data_raw
""".strip()
            _result, blocked_error = run_code_sandboxed_subprocess(
                code_snippet=blocked_code,
                function_name="data_cleaner",
                data=df.to_dict(),
                timeout=10,
                memory_limit_mb=256,
                data_format="dataframe",
            )
            record(
                "sandbox blocked import",
                isinstance(blocked_error, str) and "blocked" in blocked_error.lower(),
                str(blocked_error),
            )
        except Exception as exc:
            record("sandbox checks", False, repr(exc))
    else:
        record("sandbox checks", True, "skipped by --skip-sandbox")

    report["checks"] = [asdict(check) for check in checks]
    report["passed"] = all(check.passed for check in checks)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument(
        "--skip-sandbox",
        action="store_true",
        help="Skip subprocess sandbox smoke checks; still performs imports/signature checks.",
    )
    args = parser.parse_args(argv)

    report = inspect_dataframe_agents(run_sandbox=not args.skip_sandbox)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        status = "PASS" if report.get("passed") else "FAIL"
        print(f"dataframe-code-agents inspection: {status}")
        print(f"package version: {report.get('version')}")
        for check in report["checks"]:
            mark = "PASS" if check["passed"] else "FAIL"
            print(f"[{mark}] {check['name']}: {check['detail']}")

    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
