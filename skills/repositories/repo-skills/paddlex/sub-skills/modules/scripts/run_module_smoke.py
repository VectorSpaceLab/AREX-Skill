#!/usr/bin/env python3
"""Self-contained PaddleX module helper.

Use --dry-run or --show-engine-modes for safe checks. With --config and
--mode, the helper delegates to `paddlex.engine.Engine` in the current
environment. Real module runs may download weights or train models; only run
those with user approval.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ENGINE_MODES = [
    "check_dataset",
    "train",
    "evaluate",
    "export",
    "pdparams2safetensors",
    "predict",
]


def _signature_text(obj: Any) -> str:
    import inspect

    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError):
        return "<unavailable>"


def _api_snapshot() -> dict[str, Any]:
    from paddlex import create_model
    from paddlex.modules import (
        build_dataset_checker,
        build_evaluator,
        build_exportor,
        build_trainer,
        build_weight_converter,
    )

    return {
        "paddlex_version": getattr(sys.modules.get("paddlex"), "__version__", None),
        "apis": {
            "create_model": _signature_text(create_model),
            "build_dataset_checker": _signature_text(build_dataset_checker),
            "build_evaluator": _signature_text(build_evaluator),
            "build_exportor": _signature_text(build_exportor),
            "build_trainer": _signature_text(build_trainer),
            "build_weight_converter": _signature_text(build_weight_converter),
        },
        "engine_modes": ENGINE_MODES,
        "entrypoints": {
            "module_engine": "installed paddlex.engine.Engine().run() via this bundled helper",
            "public_cli": "paddlex (pipeline / serving / install / paddle2onnx)",
        },
    }


def _run_module_engine(config_path: Path, mode: str | None, overrides: list[str]) -> None:
    from paddlex.engine import Engine

    original_argv = sys.argv[:]
    sys.argv = [sys.argv[0], "-c", str(config_path)]
    if mode:
        sys.argv.extend(["-o", f"Global.mode={mode}"])
    for override in overrides:
        sys.argv.extend(["-o", override])

    try:
        Engine().run()
    finally:
        sys.argv = original_argv


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Import paddlex and inspect public module APIs only.",
    )
    parser.add_argument(
        "--show-engine-modes",
        action="store_true",
        help="Print the module engine mode map.",
    )
    parser.add_argument(
        "--model-name",
        help="Optional model name for create_model import-resolution smoke.",
    )
    parser.add_argument(
        "--model-dir",
        help="Optional local model_dir passed to create_model.",
    )
    parser.add_argument(
        "--config",
        help="Module config YAML for delegated module-engine execution.",
    )
    parser.add_argument(
        "--mode",
        choices=ENGINE_MODES,
        help="Global.mode override for delegated module-engine execution.",
    )
    parser.add_argument(
        "--override",
        action="append",
        default=[],
        help="Extra -o override, e.g. Dataset.dataset_dir=./data",
    )
    args = parser.parse_args()

    if args.show_engine_modes:
        print(json.dumps({"engine_modes": ENGINE_MODES}, indent=2, ensure_ascii=False))
        return 0

    import paddlex  # noqa: WPS433 - runtime check.
    from paddlex import create_model

    if args.dry_run:
        print(json.dumps(_api_snapshot(), indent=2, ensure_ascii=False))
        return 0

    if args.model_name:
        model = create_model(args.model_name, model_dir=args.model_dir)
        print(json.dumps({"created_model_type": type(model).__name__}, indent=2))
        return 0

    if args.config:
        config_path = Path(args.config)
        if not config_path.exists():
            raise SystemExit(f"Config does not exist: {config_path}")
        _run_module_engine(config_path, args.mode, args.override)
        return 0

    raise SystemExit(
        "Nothing to do. Use --dry-run, --show-engine-modes, --model-name, or --config."
    )


if __name__ == "__main__":
    raise SystemExit(main())
