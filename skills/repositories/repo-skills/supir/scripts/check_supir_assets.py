#!/usr/bin/env python3
"""Safe SUPIR checkpoint/config preflight.

This script does not import SUPIR and does not load model weights. It parses a
SUPIR YAML config and/or a CKPT_PTH.py-style assignment file, then reports which
checkpoint fields are set, unset, or missing from the filesystem.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

YAML_FIELDS = ["SDXL_CKPT", "SUPIR_CKPT", "SUPIR_CKPT_Q", "SUPIR_CKPT_F"]
CKPT_MODULE_FIELDS = [
    "LLAVA_CLIP_PATH",
    "LLAVA_MODEL_PATH",
    "SDXL_CLIP1_PATH",
    "SDXL_CLIP2_CKPT_PTH",
]


def _load_yaml(path: Path) -> Dict[str, Any]:
    try:
        import yaml  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on host env
        raise SystemExit(
            "PyYAML is required to parse SUPIR YAML configs. Install PyYAML or run "
            "this script with only --ckpt-module. Original import error: " + repr(exc)
        )
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"Config {path} did not parse to a mapping")
    return data


def _parse_ckpt_module(path: Path) -> Dict[str, Any]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    values: Dict[str, Any] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        name = node.targets[0].id
        if name not in CKPT_MODULE_FIELDS:
            continue
        try:
            values[name] = ast.literal_eval(node.value)
        except Exception:
            values[name] = "<non-literal>"
    return values


def _status(value: Any) -> Tuple[str, str]:
    if value is None:
        return "none", "explicit None / download-or-default path"
    if value in ("", "~"):
        return "unset", "empty or YAML null-like placeholder"
    if not isinstance(value, (str, os.PathLike)):
        return "set-nonpath", repr(value)
    p = Path(os.path.expanduser(str(value)))
    if p.exists():
        return "exists", str(p)
    return "missing", str(p)


def _collect_config(path: Path) -> List[Dict[str, Any]]:
    data = _load_yaml(path)
    rows = []
    for field in YAML_FIELDS:
        value = data.get(field)
        status, detail = _status(value)
        rows.append({"source": str(path), "field": field, "value": value, "status": status, "detail": detail})
    sampler = data.get("model", {}).get("params", {}).get("sampler_config", {}) if isinstance(data.get("model"), dict) else {}
    target = sampler.get("target") if isinstance(sampler, dict) else None
    rows.append({"source": str(path), "field": "sampler_config.target", "value": target, "status": "info", "detail": str(target)})
    return rows


def _collect_ckpt_module(path: Path) -> List[Dict[str, Any]]:
    values = _parse_ckpt_module(path)
    rows = []
    for field in CKPT_MODULE_FIELDS:
        value = values.get(field, "<missing-assignment>")
        status, detail = _status(value) if value != "<missing-assignment>" else ("missing-assignment", "no literal assignment found")
        rows.append({"source": str(path), "field": field, "value": value, "status": status, "detail": detail})
    return rows


def _print_table(rows: Iterable[Dict[str, Any]]) -> None:
    print("source\tfield\tstatus\tdetail")
    for row in rows:
        print(f"{row['source']}\t{row['field']}\t{row['status']}\t{row['detail']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate SUPIR config and checkpoint path fields without loading models.")
    parser.add_argument("--config", action="append", type=Path, default=[], help="SUPIR YAML config to inspect. Repeatable.")
    parser.add_argument("--ckpt-module", type=Path, help="CKPT_PTH.py-style file to parse with AST, not import.")
    parser.add_argument("--validate-existing", action="store_true", help="Return non-zero if any non-None path field is missing.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a tab-separated table.")
    args = parser.parse_args()

    rows: List[Dict[str, Any]] = []
    for cfg in args.config:
        if not cfg.exists():
            rows.append({"source": str(cfg), "field": "<config>", "value": None, "status": "missing", "detail": "config file not found"})
            continue
        rows.extend(_collect_config(cfg))
    if args.ckpt_module:
        if args.ckpt_module.exists():
            rows.extend(_collect_ckpt_module(args.ckpt_module))
        else:
            rows.append({"source": str(args.ckpt_module), "field": "<ckpt-module>", "value": None, "status": "missing", "detail": "file not found"})

    if not rows:
        rows.append({"source": "<none>", "field": "usage", "value": None, "status": "info", "detail": "pass --config and/or --ckpt-module"})

    if args.json:
        print(json.dumps(rows, indent=2, sort_keys=True))
    else:
        _print_table(rows)

    if args.validate_existing:
        # `None` is allowed because the upstream README documents it as an
        # intentional download/default path for some CLIP assets. Empty strings,
        # '~', non-literal assignments, non-path values, missing assignments,
        # and missing files are validation failures.
        bad_statuses = {"missing", "missing-assignment", "unset", "set-nonpath"}
        bad = [r for r in rows if r["status"] in bad_statuses]
        return 2 if bad else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
