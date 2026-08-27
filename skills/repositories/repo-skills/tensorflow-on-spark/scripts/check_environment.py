#!/usr/bin/env python3
"""Safe TensorFlowOnSpark environment diagnostic.

This helper checks imports, package versions, Java/Spark command visibility,
optional GPU visibility, and selected TensorFlowOnSpark signatures. It does not
start training, submit Spark jobs, download data, start Docker, mutate files, or
allocate GPUs.

Examples:
  python scripts/check_environment.py
  python scripts/check_environment.py --json --require tensorflowonspark --require pyspark --require tensorflow
  python scripts/check_environment.py --expect-spark-submit --expect-java --expect-gpus 1
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import platform
import shutil
import subprocess
import sys
from importlib import metadata
from typing import Any

DEFAULT_MODULES = ["tensorflowonspark", "tensorflow", "pyspark"]


def version_for(dist: str) -> str | None:
    try:
        return metadata.version(dist)
    except Exception:
        return None


def import_module(name: str) -> dict[str, Any]:
    item: dict[str, Any] = {"module": name, "ok": False}
    try:
        mod = importlib.import_module(name)
        item["ok"] = True
        item["file"] = getattr(mod, "__file__", None)
        item["version"] = getattr(mod, "__version__", None)
    except Exception as exc:  # pragma: no cover - diagnostic path
        item["error"] = f"{type(exc).__name__}: {exc}"
    return item


def run_command(argv: list[str], timeout: int) -> dict[str, Any]:
    exe = shutil.which(argv[0])
    result: dict[str, Any] = {"command": argv, "available": bool(exe), "path": exe}
    if not exe:
        return result
    try:
        proc = subprocess.run(argv, text=True, capture_output=True, timeout=timeout)
        result.update(
            ok=proc.returncode == 0,
            returncode=proc.returncode,
            stdout=proc.stdout.strip().splitlines()[:20],
            stderr=proc.stderr.strip().splitlines()[:20],
        )
    except Exception as exc:  # pragma: no cover - diagnostic path
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def tensorflowonspark_signatures() -> dict[str, str]:
    sigs: dict[str, str] = {}
    try:
        from tensorflowonspark import TFCluster, TFNode, TFParallel, dfutil
        from tensorflowonspark.pipeline import TFEstimator, TFModel

        objects = {
            "TFCluster.run": TFCluster.run,
            "TFCluster.train": TFCluster.TFCluster.train,
            "TFCluster.inference": TFCluster.TFCluster.inference,
            "TFCluster.shutdown": TFCluster.TFCluster.shutdown,
            "TFNode.DataFeed.__init__": TFNode.DataFeed.__init__,
            "TFNode.DataFeed.next_batch": TFNode.DataFeed.next_batch,
            "TFNode.DataFeed.batch_results": TFNode.DataFeed.batch_results,
            "TFNode.DataFeed.terminate": TFNode.DataFeed.terminate,
            "TFParallel.run": TFParallel.run,
            "TFEstimator.__init__": TFEstimator.__init__,
            "TFModel.__init__": TFModel.__init__,
            "dfutil.saveAsTFRecords": dfutil.saveAsTFRecords,
            "dfutil.loadTFRecords": dfutil.loadTFRecords,
            "dfutil.infer_schema": dfutil.infer_schema,
        }
        for name, obj in objects.items():
            sigs[name] = str(inspect.signature(obj))
    except Exception as exc:
        sigs["error"] = f"{type(exc).__name__}: {exc}"
    return sigs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check a TensorFlowOnSpark runtime without side effects.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a compact text report.")
    parser.add_argument("--timeout", type=int, default=10, help="Seconds for command probes.")
    parser.add_argument("--require", action="append", default=[], help="Module import that must succeed; may be repeated.")
    parser.add_argument("--expect-java", action="store_true", help="Fail if java -version is unavailable or fails.")
    parser.add_argument("--expect-spark-submit", action="store_true", help="Fail if spark-submit --version is unavailable or fails.")
    parser.add_argument("--expect-gpus", type=int, default=0, help="Fail if fewer than this many GPUs are visible through nvidia-smi.")
    args = parser.parse_args(argv)

    modules = sorted(set(DEFAULT_MODULES + args.require))
    imports = [import_module(m) for m in modules]
    distributions = {d: version_for(d) for d in ["tensorflowonspark", "tensorflow", "tensorflow-cpu", "pyspark", "py4j", "numpy", "scipy", "h5py"]}
    java = run_command(["java", "-version"], args.timeout)
    spark_submit = run_command(["spark-submit", "--version"], args.timeout)
    nvidia = run_command(["nvidia-smi", "--list-gpus"], args.timeout)
    gpu_count = len([line for line in nvidia.get("stdout", []) if line.startswith("GPU ")]) if nvidia.get("available") else 0

    report = {
        "python": {"executable": sys.executable, "version": sys.version.split()[0]},
        "platform": {"system": platform.system(), "release": platform.release(), "machine": platform.machine()},
        "imports": imports,
        "distributions": distributions,
        "commands": {"java": java, "spark-submit": spark_submit, "nvidia-smi": nvidia},
        "gpu_count": gpu_count,
        "tensorflowonspark_signatures": tensorflowonspark_signatures(),
    }

    failed: list[str] = []
    import_by_name = {item["module"]: item for item in imports}
    for module in args.require:
        if not import_by_name.get(module, {}).get("ok"):
            failed.append(f"required import failed: {module}")
    if args.expect_java and not java.get("ok"):
        failed.append("java -version did not pass")
    if args.expect_spark_submit and not spark_submit.get("ok"):
        failed.append("spark-submit --version did not pass")
    if args.expect_gpus and gpu_count < args.expect_gpus:
        failed.append(f"expected at least {args.expect_gpus} GPU(s), saw {gpu_count}")
    report["ok"] = not failed
    report["failures"] = failed

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Python: {report['python']['version']} ({report['python']['executable']})")
        for item in imports:
            print(f"import {item['module']}: {'ok' if item['ok'] else item.get('error')}")
        print(f"java: {'ok' if java.get('ok') else 'missing/failing'}")
        print(f"spark-submit: {'ok' if spark_submit.get('ok') else 'missing/failing'}")
        print(f"visible GPUs: {gpu_count}")
        if failed:
            print("Failures:")
            for failure in failed:
                print(f"- {failure}")
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
