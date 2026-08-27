#!/usr/bin/env python3
"""Check img2dataset distributed optional backends without running downloads."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import importlib.util
import json
import shutil
import subprocess
import tempfile
import time
from typing import Any, Dict, Iterable, List


MODULES = [
    {
        "name": "img2dataset",
        "distributions": ["img2dataset"],
        "purpose": "base package and multiprocessing distributor",
        "heavy": False,
    },
    {"name": "pyspark", "distributions": ["pyspark"], "purpose": "PySpark distributor", "heavy": False},
    {"name": "ray", "distributions": ["ray"], "purpose": "Ray distributor", "heavy": False},
    {
        "name": "tensorflow",
        "distributions": ["tensorflow", "tensorflow-cpu"],
        "purpose": "TFRecord writer availability check",
        "heavy": True,
    },
    {
        "name": "tensorflow_io",
        "distributions": ["tensorflow-io", "tensorflow_io"],
        "purpose": "TensorFlow IO optional plugin visibility",
        "heavy": True,
    },
    {"name": "wandb", "distributions": ["wandb"], "purpose": "W&B logging", "heavy": False},
    {"name": "fsspec", "distributions": ["fsspec"], "purpose": "remote/local filesystem dispatch", "heavy": False},
]


def first_version(distributions: Iterable[str]) -> str | None:
    for distribution in distributions:
        try:
            return metadata.version(distribution)
        except metadata.PackageNotFoundError:
            continue
    return None


def check_module(module_info: Dict[str, Any], *, import_heavy: bool, skip_imports: bool, show_paths: bool) -> Dict[str, Any]:
    name = module_info["name"]
    spec = importlib.util.find_spec(name)
    result: Dict[str, Any] = {
        "available": spec is not None,
        "version": first_version(module_info["distributions"]),
        "purpose": module_info["purpose"],
        "heavy": module_info["heavy"],
    }
    if show_paths and spec is not None:
        result["origin"] = getattr(spec, "origin", None)

    if spec is None:
        result["import"] = "not-available"
        return result

    should_import = not skip_imports and (import_heavy or not module_info["heavy"])
    if not should_import:
        result["import"] = "skipped-heavy" if module_info["heavy"] else "skipped"
        return result

    try:
        module = importlib.import_module(name)
        result["import"] = "ok"
        module_version = getattr(module, "__version__", None)
        if module_version is not None:
            result["module_version"] = str(module_version)
    except Exception as exc:  # pylint: disable=broad-except
        result["import"] = "error"
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def check_java(timeout: int) -> Dict[str, Any]:
    if shutil.which("java") is None:
        return {"available": False, "error": "java command not found on PATH"}
    try:
        started = time.perf_counter()
        proc = subprocess.run(
            ["java", "-version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = proc.stderr or proc.stdout or ""
        first_line = output.splitlines()[0] if output.splitlines() else ""
        return {
            "available": proc.returncode == 0,
            "returncode": proc.returncode,
            "version_line": first_line,
            "elapsed_sec": round(time.perf_counter() - started, 3),
        }
    except Exception as exc:  # pylint: disable=broad-except
        return {"available": False, "error": f"{type(exc).__name__}: {exc}"}


def module_ready(modules: Dict[str, Dict[str, Any]], name: str) -> bool:
    item = modules.get(name, {})
    return bool(item.get("available")) and item.get("import") != "error"


def spark_smoke(timeout: int) -> Dict[str, Any]:  # pylint: disable=unused-argument
    try:
        from pyspark.sql import SparkSession  # pylint: disable=import-outside-toplevel

        spark = SparkSession.builder.master("local[1]").appName("img2dataset-backend-smoke").getOrCreate()
        try:
            count = spark.range(1).count()
        finally:
            spark.stop()
        return {"ok": count == 1, "result": count, "note": "local[1] Spark range count; no download run"}
    except Exception as exc:  # pylint: disable=broad-except
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def ray_smoke(timeout: int) -> Dict[str, Any]:
    try:
        import ray  # pylint: disable=import-outside-toplevel

        already_initialized = ray.is_initialized()
        if not already_initialized:
            ray.init(num_cpus=1, include_dashboard=False, ignore_reinit_error=True, logging_level="ERROR")

        @ray.remote
        def _one() -> int:
            return 1

        try:
            value = ray.get(_one.remote(), timeout=timeout)
        finally:
            if not already_initialized:
                ray.shutdown()
        return {"ok": value == 1, "result": value, "note": "current Ray API; no local_mode; no download run"}
    except Exception as exc:  # pylint: disable=broad-except
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def tfrecord_smoke() -> Dict[str, Any]:
    try:
        import tensorflow as tf  # pylint: disable=import-outside-toplevel

        with tempfile.NamedTemporaryFile(suffix=".tfrecord") as handle:
            with tf.io.TFRecordWriter(handle.name) as writer:
                writer.write(b"tiny")
        return {"ok": True, "note": "TensorFlow wrote one tiny TFRecord; no image download run"}
    except Exception as exc:  # pylint: disable=broad-except
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def build_report(args: argparse.Namespace) -> Dict[str, Any]:
    modules = {
        module_info["name"]: check_module(
            module_info,
            import_heavy=args.import_heavy or args.tfrecord_smoke,
            skip_imports=args.skip_imports,
            show_paths=args.show_paths,
        )
        for module_info in MODULES
    }
    java = check_java(args.timeout)
    ready = {
        "multiprocessing": {
            "ready": module_ready(modules, "img2dataset"),
            "needs": ["img2dataset"],
        },
        "pyspark": {
            "ready": module_ready(modules, "img2dataset") and module_ready(modules, "pyspark") and bool(java.get("available")),
            "needs": ["img2dataset", "pyspark", "java"],
        },
        "ray": {
            "ready": module_ready(modules, "img2dataset") and module_ready(modules, "ray"),
            "needs": ["img2dataset", "ray", "ray.init(...) for cluster use"],
            "warning": "avoid deprecated local_mode=True; initialize Ray with current APIs",
        },
        "tfrecord_cpu": {
            "ready": module_ready(modules, "tensorflow"),
            "needs": ["tensorflow"],
            "tensorflow_io_visible": module_ready(modules, "tensorflow_io"),
        },
        "wandb_logging": {"ready": module_ready(modules, "wandb"), "needs": ["wandb", "account/anonymous/offline policy"]},
        "fsspec_filesystems": {"ready": module_ready(modules, "fsspec"), "needs": ["fsspec", "backend-specific packages for cloud/SSH/HF paths"]},
    }

    smokes: Dict[str, Any] = {}
    if args.spark_smoke:
        smokes["spark_local"] = spark_smoke(args.timeout)
    if args.ray_smoke:
        smokes["ray_local"] = ray_smoke(args.timeout)
    if args.tfrecord_smoke:
        smokes["tfrecord"] = tfrecord_smoke()

    return {
        "schema_version": 1,
        "modules": modules,
        "java": java,
        "ready": ready,
        "smokes": smokes,
        "notes": [
            "This checker does not run img2dataset downloads.",
            "TensorFlow and TensorFlow IO imports are skipped by default; pass --import-heavy or --tfrecord-smoke if needed.",
            "Ray smoke uses ray.init(num_cpus=1) and never uses deprecated local_mode=True.",
            "Missing optional backends only block the corresponding distributor or output/logging feature.",
        ],
    }


def print_text(report: Dict[str, Any]) -> None:
    print("img2dataset distributed backend check")
    print("\nJava:")
    java = report["java"]
    if java.get("available"):
        print(f"  ok: {java.get('version_line', '')}")
    else:
        print(f"  missing/error: {java.get('error', 'java -version failed')}")

    print("\nModules:")
    for name, result in report["modules"].items():
        version = result.get("version") or "unknown"
        print(f"  {name}: available={result.get('available')} version={version} import={result.get('import')}")
        if result.get("error"):
            print(f"    error: {result['error']}")

    print("\nReadiness:")
    for name, result in report["ready"].items():
        print(f"  {name}: ready={result.get('ready')} needs={', '.join(result.get('needs', []))}")
        if result.get("warning"):
            print(f"    warning: {result['warning']}")

    if report["smokes"]:
        print("\nSmokes:")
        for name, result in report["smokes"].items():
            print(f"  {name}: ok={result.get('ok')} {result.get('note', '')}")
            if result.get("error"):
                print(f"    error: {result['error']}")

    print("\nNotes:")
    for note in report["notes"]:
        print(f"  - {note}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text.")
    parser.add_argument("--import-heavy", action="store_true", help="Import TensorFlow and TensorFlow IO instead of metadata-only checks.")
    parser.add_argument("--skip-imports", action="store_true", help="Use metadata/spec checks only; do not import Python modules.")
    parser.add_argument("--spark-smoke", action="store_true", help="Run a tiny local Spark range count; no download.")
    parser.add_argument("--ray-smoke", action="store_true", help="Run a tiny local Ray remote function; no download and no local_mode.")
    parser.add_argument("--tfrecord-smoke", action="store_true", help="Write one tiny TFRecord with TensorFlow; no download.")
    parser.add_argument("--timeout", type=int, default=20, help="Timeout in seconds for Java and tiny local smokes.")
    parser.add_argument("--show-paths", action="store_true", help="Include module origin paths in the report.")
    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    report = build_report(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
