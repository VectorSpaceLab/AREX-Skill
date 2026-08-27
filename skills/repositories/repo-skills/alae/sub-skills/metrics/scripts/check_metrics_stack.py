#!/usr/bin/env python3
"""Safe readiness checker for ALAE legacy metric scripts.

This script intentionally does not import metrics/*.py, model.py, defaults.py,
launcher.py, or any repository module. It performs no downloads and no metric
runs. It only imports torch, tensorflow, and dnnlib after argument parsing.
"""

from __future__ import annotations

import argparse
import importlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

DEFAULT_METRIC_PKLS = ("inception_v3_features.pkl", "vgg16_zhang_perceptual.pkl")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Check whether an ALAE checkout appears ready for legacy FID, "
            "FID reconstruction, PPL, or LPIPS metrics without importing "
            "metrics/*.py or downloading artifacts."
        )
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="ALAE repository root to inspect. Defaults to the current directory.",
    )
    parser.add_argument(
        "--config",
        default="ffhq",
        help=(
            "Config name or path to verify, matching the repository launcher semantics. "
            "Examples: ffhq, celeba, configs/celeba-hq256.yaml."
        ),
    )
    parser.add_argument(
        "--metrics-dir",
        default="metrics",
        help="Metric artifact directory relative to --repo-root, or an explicit path.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help=(
            "Optional checkpoint output directory. If omitted, the checker reads "
            "OUTPUT_DIR from the selected config when possible."
        ),
    )
    parser.add_argument(
        "--metric-pkl",
        action="append",
        dest="metric_pkls",
        default=None,
        help=(
            "Metric pickle filename to check inside --metrics-dir. May be supplied "
            "more than once. Defaults to the pickle files used by the supported source scripts."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a human-readable report.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with status 1 when a required readiness check fails.",
    )
    return parser


def as_path_under(root: Path, value: str) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return root / path


def resolve_config(repo_root: Path, config_arg: str) -> Tuple[Path, List[str]]:
    raw = Path(config_arg).expanduser()
    candidates: List[Path] = []

    if raw.is_absolute():
        candidates.append(raw)
    elif raw.suffix:
        candidates.append(repo_root / raw)
        if len(raw.parts) == 1:
            candidates.append(repo_root / "configs" / raw.name)
    else:
        candidates.append(repo_root / raw)
        candidates.append(repo_root / "configs" / f"{config_arg}.yaml")

    seen = set()
    unique_candidates: List[Path] = []
    for candidate in candidates:
        key = str(candidate)
        if key not in seen:
            seen.add(key)
            unique_candidates.append(candidate)

    for candidate in unique_candidates:
        if candidate.exists():
            return candidate, [str(p) for p in unique_candidates]
    return unique_candidates[-1] if unique_candidates else repo_root / config_arg, [str(p) for p in unique_candidates]


def clean_yaml_scalar(value: str) -> str:
    value = value.strip()
    if not value:
        return value
    quote = None
    if value[0] in {"'", '"'}:
        quote = value[0]
    if quote:
        end = value.find(quote, 1)
        if end != -1:
            return value[1:end]
    if "#" in value:
        value = value.split("#", 1)[0].strip()
    return value.strip().strip("'\"")


def parse_config_fields(config_path: Path) -> Dict[str, str]:
    fields: Dict[str, str] = {}
    if not config_path.exists() or not config_path.is_file():
        return fields

    section: Optional[str] = None
    pattern = re.compile(r"^(?P<indent>\s*)(?P<key>[A-Za-z0-9_]+):(?P<value>.*)$")
    try:
        lines = config_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return fields

    for line in lines:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = pattern.match(line)
        if not match:
            continue
        indent = len(match.group("indent"))
        key = match.group("key")
        value = clean_yaml_scalar(match.group("value"))
        if indent == 0:
            if value:
                fields[key] = value
                section = None
            else:
                section = key
        elif section and value:
            fields[f"{section}.{key}"] = value
    return fields


def import_module_status(name: str) -> Tuple[Optional[Any], Dict[str, Any]]:
    try:
        module = importlib.import_module(name)
        version = getattr(module, "__version__", None)
        return module, {"name": name, "ok": True, "version": version}
    except Exception as exc:  # noqa: BLE001 - report readiness, do not crash.
        return None, {
            "name": name,
            "ok": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }


def check_torch() -> Dict[str, Any]:
    torch, status = import_module_status("torch")
    if not status["ok"]:
        return status

    cuda: Dict[str, Any] = {"checked_with": "torch.cuda"}
    try:
        cuda["available"] = bool(torch.cuda.is_available())
        cuda["device_count"] = int(torch.cuda.device_count())
        cuda["torch_cuda_version"] = getattr(getattr(torch, "version", None), "cuda", None)
        if cuda["available"] and cuda["device_count"]:
            names = []
            for idx in range(cuda["device_count"]):
                try:
                    names.append(torch.cuda.get_device_name(idx))
                except Exception as exc:  # noqa: BLE001
                    names.append(f"<unavailable: {type(exc).__name__}: {exc}>")
            cuda["device_names"] = names
    except Exception as exc:  # noqa: BLE001
        cuda["available"] = False
        cuda["error_type"] = type(exc).__name__
        cuda["error"] = str(exc)
    status["cuda"] = cuda
    return status


def check_tensorflow() -> Dict[str, Any]:
    tf, status = import_module_status("tensorflow")
    if not status["ok"]:
        return status

    tf1_apis: Dict[str, Any] = {}
    for attr in ("Session", "python_io", "Graph", "get_default_graph"):
        tf1_apis[attr] = hasattr(tf, attr)
    compat_v1 = getattr(getattr(tf, "compat", None), "v1", None)
    if compat_v1 is not None:
        tf1_apis["compat.v1.Session"] = hasattr(compat_v1, "Session")
        tf1_apis["compat.v1.python_io"] = hasattr(compat_v1, "python_io")
    try:
        tf1_apis["built_with_cuda"] = bool(tf.test.is_built_with_cuda())
    except Exception as exc:  # noqa: BLE001
        tf1_apis["built_with_cuda_error"] = f"{type(exc).__name__}: {exc}"
    status["tf1_apis"] = tf1_apis
    status["gpu_note"] = (
        "This checker does not initialize TensorFlow GPU sessions; PyTorch CUDA "
        "visibility is reported separately."
    )
    return status


def check_dnnlib() -> Dict[str, Any]:
    _dnnlib, status = import_module_status("dnnlib")
    _tflib, tflib_status = import_module_status("dnnlib.tflib")
    status["tflib"] = tflib_status
    status["init_tf_called"] = False
    return status


def check_metric_pickles(repo_root: Path, metrics_dir_arg: str, names: Iterable[str]) -> Dict[str, Any]:
    metrics_dir = as_path_under(repo_root, metrics_dir_arg)
    files = []
    for name in names:
        path = metrics_dir / name
        item: Dict[str, Any] = {
            "name": name,
            "path": str(path),
            "exists": path.is_file(),
        }
        if path.is_file():
            try:
                item["size_bytes"] = path.stat().st_size
            except OSError as exc:
                item["stat_error"] = f"{type(exc).__name__}: {exc}"
        files.append(item)
    return {
        "metrics_dir": str(metrics_dir),
        "exists": metrics_dir.is_dir(),
        "files": files,
    }


def resolve_checkpoint_pointer(repo_root: Path, output_dir: Path, pointer: str) -> List[Dict[str, Any]]:
    raw = Path(pointer).expanduser()
    candidates: List[Path]
    if raw.is_absolute():
        candidates = [raw]
    else:
        candidates = [repo_root / raw, output_dir / raw]

    seen = set()
    resolved = []
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        resolved.append({"path": key, "exists": candidate.is_file()})
    return resolved


def check_checkpoint(repo_root: Path, output_dir_arg: Optional[str], fields: Dict[str, str]) -> Dict[str, Any]:
    raw_output_dir = output_dir_arg or fields.get("OUTPUT_DIR")
    result: Dict[str, Any] = {
        "output_dir_source": "argument" if output_dir_arg else "config" if fields.get("OUTPUT_DIR") else "missing",
        "output_dir_value": raw_output_dir,
    }
    if not raw_output_dir:
        result["ready"] = False
        result["message"] = "No --output-dir was supplied and OUTPUT_DIR was not found in the config."
        return result

    output_dir = as_path_under(repo_root, raw_output_dir)
    last_checkpoint = output_dir / "last_checkpoint"
    result.update(
        {
            "output_dir": str(output_dir),
            "output_dir_exists": output_dir.is_dir(),
            "last_checkpoint": str(last_checkpoint),
            "last_checkpoint_exists": last_checkpoint.is_file(),
        }
    )
    if not last_checkpoint.is_file():
        result["ready"] = False
        result["message"] = "Missing OUTPUT_DIR/last_checkpoint."
        return result

    try:
        pointer = last_checkpoint.read_text(encoding="utf-8", errors="replace").strip()
    except OSError as exc:
        result["ready"] = False
        result["message"] = f"Could not read last_checkpoint: {type(exc).__name__}: {exc}"
        return result

    result["pointer"] = pointer
    result["pointer_candidates"] = resolve_checkpoint_pointer(repo_root, output_dir, pointer) if pointer else []
    result["pointer_exists"] = any(item["exists"] for item in result["pointer_candidates"])
    result["ready"] = bool(pointer and result["pointer_exists"])
    if not pointer:
        result["message"] = "last_checkpoint is empty."
    elif not result["pointer_exists"]:
        result["message"] = "last_checkpoint points to a file that was not found."
    else:
        result["message"] = "Checkpoint pointer resolved."
    return result


def check_fid_sep_exclusion(repo_root: Path) -> Dict[str, Any]:
    model_separate = repo_root / "model_separate.py"
    sep_config = repo_root / "configs" / "experiment_celeba_sep.yaml"
    return {
        "script": "metrics/fid_sep.py",
        "routed": False,
        "model_separate_py_exists": model_separate.is_file(),
        "experiment_celeba_sep_config_exists": sep_config.is_file(),
        "reason": (
            "Excluded unless both the separate-model implementation and separate-model "
            "config are supplied by a refreshed checkout."
        ),
    }


def readiness_failures(report: Dict[str, Any]) -> List[str]:
    failures: List[str] = []

    torch = report["imports"].get("torch", {})
    if not torch.get("ok"):
        failures.append("torch import failed")
    elif not torch.get("cuda", {}).get("available"):
        failures.append("torch CUDA is not visible")

    tensorflow = report["imports"].get("tensorflow", {})
    if not tensorflow.get("ok"):
        failures.append("tensorflow import failed")
    else:
        tf1_apis = tensorflow.get("tf1_apis", {})
        if not tf1_apis.get("Session") or not tf1_apis.get("python_io"):
            failures.append("TensorFlow top-level TF1 APIs are missing")

    dnnlib = report["imports"].get("dnnlib", {})
    if not dnnlib.get("ok"):
        failures.append("dnnlib import failed")
    elif not dnnlib.get("tflib", {}).get("ok"):
        failures.append("dnnlib.tflib import failed")

    config = report.get("config", {})
    if not config.get("exists"):
        failures.append("config file is missing")

    for item in report.get("metric_pickles", {}).get("files", []):
        if not item.get("exists"):
            failures.append(f"metric pickle missing: {item.get('name')}")

    checkpoint = report.get("checkpoint", {})
    if not checkpoint.get("ready"):
        failures.append(f"checkpoint not ready: {checkpoint.get('message')}")

    return failures


def emit_text(report: Dict[str, Any]) -> None:
    print("ALAE metrics stack readiness")
    print("============================")
    print("Safety: metrics/*.py were not imported; no downloads or metric runs were started.")
    print()

    print("Config:")
    config = report["config"]
    print(f"  requested: {config['requested']}")
    print(f"  resolved:  {config['path']}")
    print(f"  exists:    {config['exists']}")
    if config.get("fields"):
        for key in ("NAME", "OUTPUT_DIR", "DATASET.PATH", "DATASET.PATH_TEST"):
            if key in config["fields"]:
                print(f"  {key}: {config['fields'][key]}")
    print()

    print("Imports:")
    for key in ("torch", "tensorflow", "dnnlib"):
        status = report["imports"][key]
        if status.get("ok"):
            version = status.get("version") or "version unknown"
            print(f"  {key}: ok ({version})")
        else:
            print(f"  {key}: FAILED ({status.get('error_type')}: {status.get('error')})")
    torch = report["imports"].get("torch", {})
    cuda = torch.get("cuda", {})
    if cuda:
        print(
            "  torch.cuda: available={available} device_count={device_count} runtime={runtime}".format(
                available=cuda.get("available"),
                device_count=cuda.get("device_count"),
                runtime=cuda.get("torch_cuda_version"),
            )
        )
    tensorflow = report["imports"].get("tensorflow", {})
    if tensorflow.get("tf1_apis"):
        tf1 = tensorflow["tf1_apis"]
        print(f"  tensorflow TF1 APIs: Session={tf1.get('Session')} python_io={tf1.get('python_io')}")
    dnnlib = report["imports"].get("dnnlib", {})
    if dnnlib.get("tflib"):
        print(f"  dnnlib.tflib: ok={dnnlib['tflib'].get('ok')}")
    print()

    print("Metric pickle files:")
    metric_pickles = report["metric_pickles"]
    print(f"  directory: {metric_pickles['metrics_dir']} exists={metric_pickles['exists']}")
    for item in metric_pickles["files"]:
        size = f" size={item['size_bytes']}" if item.get("size_bytes") is not None else ""
        print(f"  {item['name']}: exists={item['exists']}{size}")
    print()

    print("Checkpoint:")
    checkpoint = report["checkpoint"]
    print(f"  output_dir: {checkpoint.get('output_dir_value')} ({checkpoint.get('output_dir_source')})")
    print(f"  ready:      {checkpoint.get('ready')}")
    print(f"  message:    {checkpoint.get('message')}")
    if checkpoint.get("pointer"):
        print(f"  pointer:    {checkpoint.get('pointer')}")
        for item in checkpoint.get("pointer_candidates", []):
            print(f"  candidate:  {item['path']} exists={item['exists']}")
    print()

    exclusion = report["fid_sep_exclusion"]
    print("Excluded route:")
    print(
        "  metrics/fid_sep.py routed=False "
        f"model_separate.py={exclusion['model_separate_py_exists']} "
        f"sep_config={exclusion['experiment_celeba_sep_config_exists']}"
    )
    print()

    failures = report["failures"]
    if failures:
        print("Overall: NOT READY")
        for failure in failures:
            print(f"  - {failure}")
    else:
        print("Overall: READY for dependency/artifact checks; native metric runs are still expensive and optional.")


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = Path(args.repo_root).expanduser().resolve()
    config_path, config_candidates = resolve_config(repo_root, args.config)
    fields = parse_config_fields(config_path)
    metric_pkls = tuple(args.metric_pkls) if args.metric_pkls else DEFAULT_METRIC_PKLS

    report: Dict[str, Any] = {
        "safety": {
            "metrics_modules_imported": False,
            "downloads_started": False,
            "metric_runs_started": False,
        },
        "repo_root": str(repo_root),
        "config": {
            "requested": args.config,
            "path": str(config_path),
            "exists": config_path.is_file(),
            "candidates": config_candidates,
            "fields": fields,
        },
        "imports": {
            "torch": check_torch(),
            "tensorflow": check_tensorflow(),
            "dnnlib": check_dnnlib(),
        },
        "metric_pickles": check_metric_pickles(repo_root, args.metrics_dir, metric_pkls),
        "checkpoint": check_checkpoint(repo_root, args.output_dir, fields),
        "fid_sep_exclusion": check_fid_sep_exclusion(repo_root),
    }
    report["failures"] = readiness_failures(report)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        emit_text(report)

    if args.strict and report["failures"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
