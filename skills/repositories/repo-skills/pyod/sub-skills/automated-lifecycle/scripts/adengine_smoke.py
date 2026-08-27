#!/usr/bin/env python3
"""Safe deterministic PyOD ADEngine smoke test.

The script generates tiny synthetic data, runs ADEngine with a fixed seed, and
optionally probes the PyOD CLI and MCP module availability. It never starts an
MCP server and it does not read or write project files.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from typing import Any


def _json_safe(value: Any) -> Any:
    """Convert common NumPy/scalar objects into JSON-safe values."""
    if hasattr(value, "tolist"):
        return value.tolist()
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    try:
        import numpy as np  # type: ignore
        if isinstance(value, (np.integer, np.floating, np.bool_)):
            return value.item()
    except Exception:
        pass
    return value


def run_adengine_smoke(args: argparse.Namespace) -> dict[str, Any]:
    """Run a tiny deterministic ADEngine lifecycle."""
    from pyod.utils.ad_engine import ADEngine
    from pyod.utils.data import generate_data

    X_train, X_test, _y_train, _y_test = generate_data(
        n_train=args.n_train,
        n_test=args.n_test,
        n_features=args.n_features,
        contamination=args.contamination,
        random_state=args.seed,
    )

    engine = ADEngine(random_state=args.seed)

    profile = engine.profile_data(X_train, data_type="tabular")
    plan = engine.plan_detection(profile, priority=args.priority, top_k=2)
    result = engine.run_detection(X_train, plan, X_test=X_test)
    analysis = engine.analyze_results(result, X=X_train, top_k=3)
    explanations = engine.explain_findings(result, X=X_train, top_k=2)
    suggestion = engine.suggest_next_step(result, analysis)
    report_json = json.loads(engine.generate_report(result, analysis, format="json"))

    state = engine.start(X_train, data_type="tabular")
    state = engine.plan(state, priority=args.priority, constraints={"max_detectors": 2})
    state = engine.run(state)
    state = engine.analyze(state)
    session_report = engine.report(state, format="json")

    return {
        "profile": profile,
        "plan": {
            "detector_name": plan.get("detector_name"),
            "params": plan.get("params", {}),
            "n_alternatives": len(plan.get("alternatives", [])),
            "confidence": plan.get("confidence"),
        },
        "result": {
            "n_train_scores": int(len(result["scores_train"])),
            "n_test_scores": int(len(result["scores_test"]) if result.get("scores_test") is not None else 0),
            "n_anomalies": int(result["n_anomalies"]),
            "anomaly_ratio": float(result["anomaly_ratio"]),
            "threshold": float(result["threshold"]),
            "score_summary": _json_safe(result["score_summary"]),
        },
        "analysis": {
            "n_anomalies": int(analysis["n_anomalies"]),
            "anomaly_ratio": float(analysis["anomaly_ratio"]),
            "top_indices": [int(row["index"]) for row in analysis["top_anomalies"]],
            "has_feature_importance": "feature_importance" in analysis,
        },
        "explanations": [
            {
                "index": int(item["index"]),
                "label": item["label"],
                "n_contributing_features": len(item.get("contributing_features", [])),
            }
            for item in explanations
        ],
        "suggestion_action": suggestion.get("action"),
        "report": {
            "detector": report_json.get("detector"),
            "n_anomalies": report_json.get("n_anomalies"),
        },
        "session": {
            "phase": state.phase,
            "next_action": state.next_action.get("action"),
            "n_plans": len(state.plans),
            "n_results": len(state.results),
            "quality_verdict": state.quality.get("verdict") if state.quality else None,
            "best_detector": state.analysis.get("best_detector") if state.analysis else None,
            "json_report_keys": sorted(session_report.keys()),
        },
    }


def probe_cli(timeout: float) -> dict[str, Any]:
    """Probe PyOD CLI help/info with the current Python executable."""
    out: dict[str, Any] = {}
    commands = {
        "help": [sys.executable, "-m", "pyod.cli", "--help"],
        "info": [sys.executable, "-m", "pyod.cli", "info"],
    }
    for name, cmd in commands.items():
        try:
            proc = subprocess.run(
                cmd,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            out[name] = {
                "returncode": proc.returncode,
                "stdout_first_line": (proc.stdout.splitlines() or [""])[0],
                "stderr_first_line": (proc.stderr.splitlines() or [""])[0],
                "stdout_contains_pyod": "pyod" in proc.stdout.lower(),
            }
        except Exception as exc:  # noqa: BLE001 - smoke tool should report, not crash here.
            out[name] = {"error": type(exc).__name__, "details": str(exc)}
    return out


def probe_mcp() -> dict[str, Any]:
    """Probe MCP module availability without starting a server."""
    info: dict[str, Any] = {
        "mcp_parent_spec": importlib.util.find_spec("mcp") is not None,
    }
    try:
        import pyod.mcp_server as m
        fastmcp = m._check_mcp()
        info.update({
            "mcp_server_imported": True,
            "fastmcp_available": fastmcp is not None,
            "registered_tools": [fn.__name__ for fn in getattr(m, "_TOOL_FUNCTIONS", ())],
            "server_started": False,
        })
    except Exception as exc:  # noqa: BLE001 - availability probe should be JSON-oriented.
        info.update({
            "mcp_server_imported": False,
            "error": type(exc).__name__,
            "details": str(exc),
            "server_started": False,
        })
    return info


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a deterministic PyOD ADEngine smoke test. Optional CLI/MCP "
            "probes do not mutate files and do not start an MCP server."
        )
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for data and ADEngine.")
    parser.add_argument("--n-train", type=int, default=80, help="Synthetic training rows.")
    parser.add_argument("--n-test", type=int, default=20, help="Synthetic test rows.")
    parser.add_argument("--n-features", type=int, default=4, help="Synthetic feature count.")
    parser.add_argument(
        "--contamination",
        type=float,
        default=0.1,
        help="Synthetic contamination fraction and default detector contamination.",
    )
    parser.add_argument(
        "--priority",
        choices=("speed", "accuracy", "balanced"),
        default="speed",
        help="ADEngine planning priority.",
    )
    parser.add_argument("--probe-cli", action="store_true", help="Also run pyod CLI --help and info probes.")
    parser.add_argument("--probe-mcp", action="store_true", help="Also import-probe pyod.mcp_server; never starts the server.")
    parser.add_argument("--timeout", type=float, default=20.0, help="Seconds for each optional CLI subprocess.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload: dict[str, Any] = {
        "ok": False,
        "script": "adengine_smoke.py",
        "parameters": {
            "seed": args.seed,
            "n_train": args.n_train,
            "n_test": args.n_test,
            "n_features": args.n_features,
            "contamination": args.contamination,
            "priority": args.priority,
        },
    }
    try:
        payload["adengine"] = run_adengine_smoke(args)
        payload["ok"] = True
    except Exception as exc:  # noqa: BLE001 - emit structured failure for agents.
        payload["ok"] = False
        payload["error"] = {"type": type(exc).__name__, "details": str(exc)}

    if args.probe_cli:
        payload["cli_probe"] = probe_cli(args.timeout)
    if args.probe_mcp:
        payload["mcp_probe"] = probe_mcp()

    print(json.dumps(_json_safe(payload), indent=2, sort_keys=True))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
