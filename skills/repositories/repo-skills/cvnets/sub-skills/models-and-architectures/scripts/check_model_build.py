#!/usr/bin/env python3
"""Build a CVNets model from a config and print a safe summary.

By default this avoids pretrained loading so the smoke stays deterministic and
network-free. Use `--allow-pretrained` only when you explicitly want to test the
checkpoint path.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
scripts_dir = ROOT / "scripts"
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from _bootstrap import activate_repo_root


def _jsonify(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, list):
        return [_jsonify(item) for item in value]
    if isinstance(value, tuple):
        return [_jsonify(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonify(val) for key, val in value.items()}
    return str(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, help="Path to a CVNets checkout.")
    parser.add_argument("--config-file", required=True, help="Config file path or name.")
    parser.add_argument(
        "--allow-pretrained",
        action="store_true",
        help="Keep pretrained weights from the config instead of clearing them for a safe build-only smoke.",
    )
    parser.add_argument(
        "--forward",
        action="store_true",
        help="Attempt a tiny forward pass after the model is built.",
    )
    args = parser.parse_args(argv)

    repo_root = activate_repo_root(args.repo_root)

    from options.opts import get_training_arguments
    from options.utils import load_config_file
    from cvnets import get_model
    from utils.tensor_utils import create_rand_tensor

    config_path = Path(args.config_file).expanduser()
    if not config_path.is_file():
        for candidate in [repo_root / args.config_file, repo_root / "config" / args.config_file]:
            if candidate.is_file():
                config_path = candidate
                break
    if not config_path.is_file():
        raise SystemExit(f"Could not find config file: {args.config_file}")

    parser_full = get_training_arguments(parse_args=False)
    opts = parser_full.parse_args([])
    setattr(opts, "common.config_file", str(config_path.resolve()))
    opts = load_config_file(opts)

    if not args.allow_pretrained:
        category = getattr(opts, "dataset.category", None)
        if category is not None:
            pretrained_key = f"model.{category}.pretrained"
            if hasattr(opts, pretrained_key):
                setattr(opts, pretrained_key, None)

    model = get_model(opts)
    summary = {
        "config": str(config_path.resolve()),
        "model_class": model.__class__.__name__,
        "dataset.category": getattr(opts, "dataset.category", None),
        "model.name": getattr(opts, f"model.{getattr(opts, 'dataset.category', '')}.name", None),
        "has_exportable_model": hasattr(model, "get_exportable_model"),
    }

    if hasattr(model, "info"):
        try:
            model.info()
        except Exception as exc:  # pragma: no cover - depends on optional helpers
            summary["model.info"] = f"failed: {exc.__class__.__name__}: {exc}"
        else:
            summary["model.info"] = "ok"

    if args.forward:
        try:
            example = create_rand_tensor(opts=opts, device="cpu", batch_size=1)
            with __import__("torch").no_grad():
                output = model(example)
            summary["forward"] = _jsonify(output if not hasattr(output, "shape") else tuple(output.shape))
        except Exception as exc:
            summary["forward"] = f"failed: {exc.__class__.__name__}: {exc}"
            print(json.dumps(summary, indent=2, sort_keys=True))
            return 2

    print(json.dumps(_jsonify(summary), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
