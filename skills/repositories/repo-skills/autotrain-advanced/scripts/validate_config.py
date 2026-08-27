#!/usr/bin/env python3
"""Parse an AutoTrain YAML config without launching training.

Example:

    python skills/disco/autotrain-advanced/scripts/validate_config.py configs/llm_finetuning/config.yml

The helper imports AutoTrain's own config parser and prints the resolved task/backend
plus top-level parsed keys. It intentionally does not call `.run()`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def make_jsonable(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {str(k): make_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [make_jsonable(v) for v in value]
    return repr(value)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", help="Local YAML config path or URL accepted by AutoTrainConfigParser")
    parser.add_argument("--show-parsed", action="store_true", help="Print the full parsed_config payload")
    args = parser.parse_args()

    config_arg = args.config
    if not (config_arg.startswith("http://") or config_arg.startswith("https://")):
        config_path = Path(config_arg)
        if not config_path.exists():
            parser.error(f"config path does not exist: {config_arg}")
        config_arg = str(config_path)

    try:
        from autotrain.parser import AutoTrainConfigParser  # type: ignore

        parsed = AutoTrainConfigParser(config_arg)
    except Exception as exc:  # pragma: no cover - environment/config triage
        print(f"ERROR: AutoTrainConfigParser failed: {exc!r}", file=sys.stderr)
        return 2

    payload = {
        "task": getattr(parsed, "task", None),
        "backend": getattr(parsed, "backend", None),
        "config_file": getattr(parsed, "config_file", None),
        "parsed_config_keys": sorted(getattr(parsed, "parsed_config", {}).keys()),
    }
    if args.show_parsed:
        payload["parsed_config"] = make_jsonable(getattr(parsed, "parsed_config", {}))

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
