#!/usr/bin/env python3
"""Safe schema checker for robosuite demo.hdf5 files."""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
from pathlib import Path
from typing import Any

import numpy as np

try:
    import h5py
except ModuleNotFoundError:
    h5py = None

REQUIRED_ROOT_ATTRS = ("date", "time", "repository_version", "env")
ROOT_ATTR_ORDER = ("date", "time", "repository_version", "env", "env_info")


def require_h5py() -> None:
    if h5py is None:
        raise SystemExit("error: h5py is required for demo HDF5 inspection. Install h5py and retry.")


def resolve_demo_file(path_text: str) -> Path:
    path = Path(path_text).expanduser()
    if path.is_dir():
        path = path / "demo.hdf5"
    return path


def to_jsonable(value: Any) -> Any:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        if value.ndim == 0:
            return to_jsonable(value.item())
        return [to_jsonable(item) for item in value.tolist()]
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    return value


def classify_model_file(value: str) -> str:
    stripped = value.lstrip()
    if stripped.startswith("<"):
        return "inline_xml"
    if stripped.lower().endswith(".xml"):
        return "xml_filename"
    return "string"


def dataset_summary(dataset) -> dict[str, Any]:
    return {
        "shape": [int(dim) for dim in dataset.shape],
        "dtype": str(dataset.dtype),
        "ndim": int(dataset.ndim),
        "length": int(dataset.shape[0]) if dataset.ndim >= 1 else 0,
    }


def build_report(demo_path: Path, check_lengths: bool = False) -> dict[str, Any]:
    require_h5py()

    report: dict[str, Any] = {
        "path": str(demo_path),
        "ok": False,
        "errors": [],
        "root_attrs": {},
        "missing_root_attrs": [],
        "demo_count": 0,
        "demos": [],
    }

    try:
        with h5py.File(demo_path, "r") as handle:
            if "data" not in handle:
                report["errors"].append("missing root group 'data'")
                return report

            data_group = handle["data"]
            root_attrs = {str(key): to_jsonable(value) for key, value in data_group.attrs.items()}
            report["root_attrs"] = root_attrs

            missing_root_attrs = [name for name in REQUIRED_ROOT_ATTRS if name not in data_group.attrs]
            report["missing_root_attrs"] = missing_root_attrs
            if missing_root_attrs:
                report["errors"].append("data group is missing required attrs: " + ", ".join(missing_root_attrs))

            demo_names = [name for name in data_group.keys() if isinstance(data_group[name], h5py.Group)]
            if not demo_names:
                report["errors"].append("no demo groups found under data")

            for demo_name in sorted(demo_names):
                demo_group = data_group[demo_name]
                demo_report: dict[str, Any] = {
                    "name": demo_name,
                    "attrs": {str(key): to_jsonable(value) for key, value in demo_group.attrs.items()},
                    "datasets": {},
                    "missing": [],
                }

                for dataset_name in ("states", "actions"):
                    if dataset_name not in demo_group:
                        demo_report["missing"].append(dataset_name)
                        report["errors"].append(f"{demo_name}: missing dataset '{dataset_name}'")
                        continue

                    dataset = demo_group[dataset_name]
                    if not isinstance(dataset, h5py.Dataset) or dataset.ndim < 1:
                        demo_report["missing"].append(dataset_name)
                        report["errors"].append(
                            f"{demo_name}: dataset '{dataset_name}' has invalid shape {list(getattr(dataset, 'shape', ())) }"
                        )
                        continue

                    demo_report["datasets"][dataset_name] = dataset_summary(dataset)

                model_file = demo_report["attrs"].get("model_file")
                if isinstance(model_file, str):
                    demo_report["model_file_kind"] = classify_model_file(model_file)

                if check_lengths and "states" in demo_report["datasets"] and "actions" in demo_report["datasets"]:
                    states_length = demo_report["datasets"]["states"]["length"]
                    actions_length = demo_report["datasets"]["actions"]["length"]
                    demo_report["length_match"] = states_length == actions_length
                    if states_length != actions_length:
                        report["errors"].append(
                            f"{demo_name}: states length {states_length} != actions length {actions_length}"
                        )

                report["demos"].append(demo_report)

    except OSError as exc:
        report["errors"].append(f"failed to open HDF5 file: {exc}")

    report["demo_count"] = len(report["demos"])
    report["ok"] = len(report["errors"]) == 0
    return report


def _format_value(value: Any) -> list[str]:
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except Exception:
            parsed = None
        if parsed is not None:
            value = parsed

    if isinstance(value, (dict, list)):
        pretty = json.dumps(value, indent=2, ensure_ascii=False)
        return pretty.splitlines()
    return [str(value)]


def render_human_report(report: dict[str, Any], include_playback_note: bool = False) -> str:
    lines: list[str] = []
    lines.append(f"file: {report['path']}")
    lines.append(f"status: {'OK' if report['ok'] else 'ERROR'}")
    lines.append(f"demo_count: {report['demo_count']}")

    missing_root_attrs = report.get("missing_root_attrs", [])
    if missing_root_attrs:
        lines.append("missing_root_attrs: " + ", ".join(missing_root_attrs))

    root_attrs = report.get("root_attrs", {})
    if root_attrs:
        lines.append("root attrs:")
        seen = set()
        for attr_name in ROOT_ATTR_ORDER:
            if attr_name in root_attrs:
                seen.add(attr_name)
                lines.append(f"  {attr_name}:")
                lines.extend(textwrap.indent("\n".join(_format_value(root_attrs[attr_name])), "    ").splitlines())
        for attr_name in sorted(name for name in root_attrs.keys() if name not in seen):
            lines.append(f"  {attr_name}:")
            lines.extend(textwrap.indent("\n".join(_format_value(root_attrs[attr_name])), "    ").splitlines())

    demos = report.get("demos", [])
    if demos:
        lines.append("demos:")
        for demo in demos:
            lines.append(f"  - {demo['name']}")
            model_file_kind = demo.get("model_file_kind")
            if model_file_kind:
                lines.append(f"    model_file: {model_file_kind}")
            for dataset_name in ("states", "actions"):
                dataset = demo["datasets"].get(dataset_name)
                if dataset:
                    lines.append(
                        f"    {dataset_name}: shape={dataset['shape']} dtype={dataset['dtype']} length={dataset['length']}"
                    )
            if demo.get("length_match") is not None:
                lines.append(f"    length_match: {demo['length_match']}")
            if demo.get("missing"):
                lines.append("    missing: " + ", ".join(demo["missing"]))

    errors = report.get("errors", [])
    if errors:
        lines.append("errors:")
        for error in errors:
            lines.append(f"  - {error}")

    if include_playback_note:
        lines.append("note: action playback is same-machine only; use state playback for exact reproduction.")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect a robosuite demo.hdf5 file safely.")
    parser.add_argument("demo_path", help="Path to demo.hdf5 or the directory that contains it")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of text")
    parser.add_argument("--check-lengths", action="store_true", help="Require states and actions to have matching lengths")
    args = parser.parse_args(argv)

    demo_path = resolve_demo_file(args.demo_path)
    if not demo_path.exists():
        print(f"error: demo file not found: {demo_path}", file=sys.stderr)
        return 2

    report = build_report(demo_path, check_lengths=args.check_lengths)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(render_human_report(report))

    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
