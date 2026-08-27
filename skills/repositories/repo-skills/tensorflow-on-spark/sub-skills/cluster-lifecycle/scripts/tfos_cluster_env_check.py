#!/usr/bin/env python3
"""Safe environment checker for TensorFlowOnSpark cluster-lifecycle workflows.

The script is intentionally conservative:
- `--help` works without importing TensorFlowOnSpark.
- No Spark cluster is started.
- GPU allocation is not attempted; only visibility is checked.
- Background-mode guidance is reported without mutating Spark config.
"""

from __future__ import annotations

import argparse
import inspect
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _truthy(value: Optional[str]) -> Optional[bool]:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return None


def _find_command(name: str, env_var: Optional[str] = None) -> Optional[str]:
    candidate = shutil.which(name)
    if candidate:
        return candidate
    if env_var:
        root = os.environ.get(env_var)
        if root:
            path = Path(root) / "bin" / name
            if path.exists():
                return str(path)
    return None


def _run_command(command: List[str], timeout: int) -> Dict[str, Any]:
    try:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except Exception as exc:  # pragma: no cover - best-effort diagnostics
        return {"ok": False, "error": str(exc)}


def _count_visible_gpus(timeout: int) -> Dict[str, Any]:
    command = _find_command("nvidia-smi")
    if not command:
        return {"available": False, "count": None, "command": None, "error": "nvidia-smi not found"}

    result = _run_command([command, "--list-gpus"], timeout=timeout)
    if not result.get("ok"):
        result.update({"available": False, "count": None, "command": command})
        return result

    lines = [line for line in result.get("stdout", "").splitlines() if line.strip()]
    return {"available": True, "count": len(lines), "command": command, "lines": lines}


def _check_env_vars(names: List[str]) -> Dict[str, Any]:
    return {name: os.environ.get(name) for name in names}


def _import_tfos() -> Tuple[Optional[Dict[str, Any]], List[str]]:
    warnings: List[str] = []
    try:
        from tensorflowonspark import TFCluster, TFParallel, gpu_info, reservation, util, TFSparkNode
    except Exception as exc:
        return None, [f"failed to import tensorflowonspark: {exc}"]

    try:
        signatures = {
            "TFCluster.run": str(inspect.signature(TFCluster.run)),
            "TFCluster.TFCluster.train": str(inspect.signature(TFCluster.TFCluster.train)),
            "TFCluster.TFCluster.inference": str(inspect.signature(TFCluster.TFCluster.inference)),
            "TFCluster.TFCluster.shutdown": str(inspect.signature(TFCluster.TFCluster.shutdown)),
            "TFCluster.TFCluster.tensorboard_url": str(inspect.signature(TFCluster.TFCluster.tensorboard_url)),
            "TFParallel.run": str(inspect.signature(TFParallel.run)),
            "TFSparkNode.TFNodeContext.__init__": str(inspect.signature(TFSparkNode.TFNodeContext.__init__)),
            "reservation.Server.start": str(inspect.signature(reservation.Server.start)),
            "reservation.Client.request_stop": str(inspect.signature(reservation.Client.request_stop)),
            "gpu_info.get_gpus": str(inspect.signature(gpu_info.get_gpus)),
            "util.single_node_env": str(inspect.signature(util.single_node_env)),
        }
    except Exception as exc:
        warnings.append(f"import succeeded but signature inspection was incomplete: {exc}")
        signatures = {}

    return {
        "version": getattr(__import__("tensorflowonspark"), "__version__", None),
        "signatures": signatures,
    }, warnings


def _format_summary(report: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("TensorFlowOnSpark cluster environment check")
    lines.append(f"- python: {report['python']['version']} ({report['python']['executable']})")
    lines.append(f"- platform: {report['platform']['system']} {report['platform']['release']} ({report['platform']['machine']})")

    tfos = report.get("tensorflowonspark") or {}
    if tfos.get("version"):
        lines.append(f"- tensorflowonspark: {tfos['version']}")
    else:
        lines.append("- tensorflowonspark: import failed")

    if tfos.get("signatures"):
        lines.append("- signatures:")
        for name, sig in sorted(tfos["signatures"].items()):
            lines.append(f"  - {name}{sig}")

    commands = report.get("commands", {})
    for name in ("java", "spark-submit", "nvidia-smi"):
        block = commands.get(name, {})
        if block.get("available"):
            lines.append(f"- {name}: {block.get('command')} ({block.get('summary', 'available')})")
        else:
            lines.append(f"- {name}: not available")

    env = report.get("env", {})
    interesting = ["MASTER", "SPARK_WORKER_INSTANCES", "SPARK_CLASSPATH", "SPARK_HOME", "SPARK_REUSE_WORKER", "CUDA_VISIBLE_DEVICES", "TFOS_SERVER_HOST", "TFOS_SERVER_PORT"]
    env_bits = []
    for key in interesting:
        value = env.get(key)
        if value not in (None, ""):
            env_bits.append(f"{key}={value}")
    if env_bits:
        lines.append("- env: " + "; ".join(env_bits))

    if report.get("warnings"):
        lines.append("Warnings:")
        for item in report["warnings"]:
            lines.append(f"- {item}")

    if report.get("errors"):
        lines.append("Errors:")
        for item in report["errors"]:
            lines.append(f"- {item}")

    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check TensorFlowOnSpark cluster-lifecycle prerequisites without starting a cluster.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of a text summary.")
    parser.add_argument("--timeout", type=int, default=15, help="Timeout in seconds for version/probe commands.")
    parser.add_argument("--require-spark-native", action="store_true", help="Treat Spark/Java/cluster prerequisites as required.")
    parser.add_argument("--expect-background", action="store_true", help="Report checks relevant to SPARK-mode background execution.")
    parser.add_argument("--expect-gpus", type=int, default=None, help="Require at least this many visible GPUs.")
    args = parser.parse_args(argv)

    report: Dict[str, Any] = {
        "python": {
            "version": sys.version.split()[0],
            "executable": sys.executable,
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "env": _check_env_vars([
            "MASTER",
            "SPARK_WORKER_INSTANCES",
            "SPARK_CLASSPATH",
            "SPARK_HOME",
            "SPARK_REUSE_WORKER",
            "CUDA_VISIBLE_DEVICES",
            "TFOS_SERVER_HOST",
            "TFOS_SERVER_PORT",
            "SPARK_EXECUTOR_POD_IP",
        ]),
        "commands": {},
        "warnings": [],
        "errors": [],
    }

    tfos_report, tfos_warnings = _import_tfos()
    if tfos_report is None:
        report["errors"].extend(tfos_warnings)
    else:
        report["tensorflowonspark"] = tfos_report
        report["warnings"].extend(tfos_warnings)

    java_cmd = _find_command("java", "JAVA_HOME")
    if java_cmd:
        java_result = _run_command([java_cmd, "-version"], timeout=args.timeout)
        java_result["available"] = java_result.get("ok", False)
        java_result["command"] = java_cmd
        java_result["summary"] = java_result.get("stderr") or java_result.get("stdout") or "available"
        report["commands"]["java"] = java_result
    else:
        report["commands"]["java"] = {"available": False, "command": None, "summary": "java not found"}

    spark_submit = _find_command("spark-submit", "SPARK_HOME")
    if spark_submit:
        spark_result = _run_command([spark_submit, "--version"], timeout=args.timeout)
        spark_result["available"] = spark_result.get("ok", False)
        spark_result["command"] = spark_submit
        spark_result["summary"] = spark_result.get("stderr") or spark_result.get("stdout") or "available"
        report["commands"]["spark-submit"] = spark_result
    else:
        report["commands"]["spark-submit"] = {"available": False, "command": None, "summary": "spark-submit not found"}

    gpus = _count_visible_gpus(timeout=args.timeout)
    if gpus.get("available"):
        gpus["summary"] = f"{gpus.get('count')} visible GPU(s)"
    report["commands"]["nvidia-smi"] = gpus

    if args.require_spark_native:
        required_vars = ["MASTER", "SPARK_WORKER_INSTANCES", "SPARK_CLASSPATH"]
        missing = [name for name in required_vars if not report["env"].get(name)]
        if missing:
            report["errors"].append("missing Spark-native env vars: " + ", ".join(missing))
        if not report["commands"]["java"].get("available"):
            report["errors"].append("java is required for Spark-native cluster workflows")
        if not report["commands"]["spark-submit"].get("available"):
            report["errors"].append("spark-submit is required for Spark-native cluster workflows")
        classpath = report["env"].get("SPARK_CLASSPATH") or ""
        if classpath and "tensorflow-hadoop" not in classpath:
            report["warnings"].append("SPARK_CLASSPATH does not obviously include the tensorflow-hadoop jar")

    if args.expect_background:
        if os.name == "nt" or platform.system().lower().startswith("win"):
            report["errors"].append("background mode is not supported on Windows")
        reuse_state = _truthy(report["env"].get("SPARK_REUSE_WORKER"))
        if reuse_state is False:
            report["errors"].append("SPARK_REUSE_WORKER is set to a false value; background mode needs Spark worker reuse")
        elif reuse_state is None:
            report["warnings"].append("background mode needs Spark worker reuse; confirm spark.python.worker.reuse=true in the Spark config used by the job")

    if args.expect_gpus is not None:
        visible = gpus.get("count")
        if visible is None:
            report["errors"].append("GPU visibility could not be verified because nvidia-smi is unavailable or failed")
        elif visible < args.expect_gpus:
            report["errors"].append(f"requested {args.expect_gpus} GPU(s) but only {visible} are visible")

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(_format_summary(report))

    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
