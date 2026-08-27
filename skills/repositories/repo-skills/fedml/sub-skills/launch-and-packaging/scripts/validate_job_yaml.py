#!/usr/bin/env python3
"""FedML job YAML preflight helper.

This helper only reads the YAML and local filesystem. It does not build,
launch, upload, or contact FedML/TensorOpera services.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

try:
    import yaml
except Exception as exc:  # pragma: no cover - environment failure path
    print(f"[FAIL] PyYAML is required: {exc!r}", file=sys.stderr)
    raise SystemExit(2)


KNOWN_TASK_KEYS = {"task_type", "job_type"}
KNOWN_SECTION_KEYS = {
    "workspace",
    "job",
    "bootstrap",
    "task_type",
    "job_type",
    "job_subtype",
    "computing",
    "data_args",
    "model_args",
    "training_params",
    "serving_args",
    "environment_args",
    "job_args",
    "job_name",
    "containerize",
    "server_job",
}


def as_mapping(value: Any, name: str, errors: list[str]) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        errors.append(f"section `{name}` must be a mapping, got {type(value).__name__}")
        return {}
    return value


def validate(path: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    info: dict[str, Any] = {"path": str(path)}

    if not path.exists():
        return {"ok": False, "errors": [f"YAML file does not exist: {path}"], "warnings": [], "info": info}

    try:
        data = yaml.safe_load(path.read_text())
    except Exception as exc:
        return {"ok": False, "errors": [f"failed to parse YAML: {exc}"], "warnings": [], "info": info}

    if not isinstance(data, dict):
        return {"ok": False, "errors": ["top-level YAML document must be a mapping"], "warnings": [], "info": info}

    unknown_keys = sorted(set(data) - KNOWN_SECTION_KEYS)
    if unknown_keys:
        warnings.append(f"unknown top-level keys are present: {unknown_keys}")

    workspace = data.get("workspace", "")
    if workspace is None:
        workspace = ""
    if not isinstance(workspace, str):
        errors.append("`workspace` must be a string path or empty string")
    elif workspace.strip():
        workspace_path = Path(workspace)
        if not workspace_path.is_absolute():
            workspace_path = path.parent / workspace_path
        info["workspace_resolved"] = str(workspace_path)
        if not workspace_path.exists():
            warnings.append(f"workspace path does not exist locally: {workspace_path}")
    else:
        warnings.append("workspace is empty; this is allowed only for jobs without source files")

    job = data.get("job")
    if not isinstance(job, str) or not job.strip():
        errors.append("`job` must be a non-empty shell command string")
    else:
        info["job_lines"] = len([line for line in job.splitlines() if line.strip()])

    if "server_job" in data and (not isinstance(data.get("server_job"), str) or not data.get("server_job", "").strip()):
        warnings.append("`server_job` is present but empty; remove it or provide a command")

    task_value = data.get("task_type", data.get("job_type"))
    if task_value is None:
        warnings.append("neither `task_type` nor `job_type` is set; launch may infer defaults, but explicit intent is safer")
    elif str(task_value) not in {"train", "serve", "deploy", "federate", "dev-environment", "dev_environment"}:
        warnings.append(f"unusual task/job type: {task_value!r}")
    info["task_or_job_type"] = task_value
    info["job_subtype"] = data.get("job_subtype")

    computing = as_mapping(data.get("computing"), "computing", errors)
    if computing:
        min_gpus = computing.get("minimum_num_gpus")
        if min_gpus is not None:
            try:
                if int(min_gpus) < 0:
                    errors.append("computing.minimum_num_gpus must be >= 0")
            except Exception:
                warnings.append("computing.minimum_num_gpus is not an integer-like value")
        info["computing_keys"] = sorted(computing.keys())
    else:
        warnings.append("no `computing` section found; remote resource matching may rely on defaults")

    for section in ("data_args", "model_args", "training_params", "serving_args", "environment_args", "job_args"):
        as_mapping(data.get(section), section, errors)

    ok = not errors
    return {"ok": ok, "errors": errors, "warnings": warnings, "info": info}


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline preflight check for a FedML launch job YAML.")
    parser.add_argument("yaml_file", type=Path)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args()

    result = validate(args.yaml_file)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"FedML job YAML: {result['info']['path']}")
        print(f"Status: {'PASS' if result['ok'] else 'FAIL'}")
        for msg in result["errors"]:
            print(f"[ERROR] {msg}")
        for msg in result["warnings"]:
            print(f"[WARN] {msg}")
        for key, value in sorted(result["info"].items()):
            if key != "path":
                print(f"[INFO] {key}: {value}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
