#!/usr/bin/env python3
"""Validate a Jina Flow YAML file with the installed parser."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="Flow/Deployment YAML/JAML file to validate.")
    args = parser.parse_args()
    path = Path(args.path)

    from jina.orchestrate.flow.base import Flow
    from jina.orchestrate.deployments import Deployment

    result = {"path": str(path), "status": "ok", "kind": None, "notes": []}
    text = path.read_text(encoding="utf-8")
    if "jtype: Flow" in text:
        result["kind"] = "Flow"
        Flow.load_config(str(path))
    elif "jtype: Deployment" in text:
        result["kind"] = "Deployment"
        Deployment.load_config(str(path))
    else:
        result["status"] = "warn"
        result["notes"].append("Could not infer Flow/Deployment kind from text; parser not run.")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
