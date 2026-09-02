#!/usr/bin/env python3
"""Validate fully test-time adaptation metadata."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

FORBIDDEN_DURING_ADAPTATION = {"source_inputs", "source_labels", "target_labels", "evaluation_labels"}
ALLOWED_DURING_ADAPTATION = {"target_inputs", "pretrained_parameters", "target_batch_statistics", "entropy_loss"}


def validate_protocol(metadata: dict) -> dict:
    adaptation_inputs = set(metadata.get("adaptation_inputs", []))
    loss_inputs = set(metadata.get("loss_inputs", []))
    consumed = adaptation_inputs | loss_inputs
    violations = sorted(consumed & FORBIDDEN_DURING_ADAPTATION)
    unknown = sorted(item for item in consumed if item not in ALLOWED_DURING_ADAPTATION and item not in FORBIDDEN_DURING_ADAPTATION)
    if "target_inputs" not in adaptation_inputs:
        violations.append("missing_target_inputs")
    return {
        "ok": not violations,
        "mode": metadata.get("mode", "unspecified"),
        "violations": violations,
        "unknown_inputs": unknown,
        "allowed_adaptation_inputs": sorted(consumed - set(violations)),
    }


def self_test() -> None:
    valid = {"mode": "online", "adaptation_inputs": ["target_inputs", "target_batch_statistics"], "loss_inputs": ["entropy_loss"], "evaluation_inputs": ["target_labels"]}
    invalid = {"mode": "offline", "adaptation_inputs": ["target_inputs", "source_inputs"], "loss_inputs": ["target_labels"]}
    assert validate_protocol(valid)["ok"] is True
    report = validate_protocol(invalid)
    assert report["ok"] is False
    assert "source_inputs" in report["violations"]
    assert "target_labels" in report["violations"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("metadata", nargs="?", help="Path to metadata JSON.")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print(json.dumps({"ok": True, "self_test": True}))
        return 0
    if not args.metadata:
        raise SystemExit("metadata path is required unless --self-test is used")
    report = validate_protocol(json.loads(Path(args.metadata).read_text(encoding="utf-8")))
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
