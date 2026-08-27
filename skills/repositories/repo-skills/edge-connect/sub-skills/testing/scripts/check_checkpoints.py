#!/usr/bin/env python3
"""Validate an EdgeConnect checkpoint directory for test.py inference.

This helper performs filesystem checks only. It does not download models,
import torch, or inspect checkpoint tensors.
"""

import argparse
import json
import re
import sys
from pathlib import Path


STAGES = {
    1: {
        "label": "edge",
        "generators": ["EdgeModel_gen.pth"],
        "discriminators": ["EdgeModel_dis.pth"],
    },
    2: {
        "label": "inpaint",
        "generators": ["InpaintingModel_gen.pth"],
        "discriminators": ["InpaintingModel_dis.pth"],
    },
    3: {
        "label": "edge-inpaint",
        "generators": ["EdgeModel_gen.pth", "InpaintingModel_gen.pth"],
        "discriminators": ["EdgeModel_dis.pth", "InpaintingModel_dis.pth"],
    },
    4: {
        "label": "joint",
        "generators": ["EdgeModel_gen.pth", "InpaintingModel_gen.pth"],
        "discriminators": ["EdgeModel_dis.pth", "InpaintingModel_dis.pth"],
    },
}

CONFIG_KEYS = ("MODE", "MODEL", "EDGE", "NMS", "SIGMA", "GPU", "DEBUG", "RESULTS")


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description=(
            "Check an EdgeConnect checkpoint directory for the config.yml and "
            "stage-specific weight filenames needed by test.py."
        )
    )
    parser.add_argument(
        "--checkpoints",
        "--path",
        dest="checkpoints",
        default="./checkpoints",
        help="checkpoint directory to validate (default: ./checkpoints)",
    )
    parser.add_argument(
        "--model",
        type=int,
        choices=sorted(STAGES),
        default=3,
        help="EdgeConnect stage to validate: 1=edge, 2=inpaint, 3=edge-inpaint, 4=joint (default: 3)",
    )
    parser.add_argument(
        "--require-discriminators",
        action="store_true",
        help="fail when stage discriminator files are missing; by default they are reported as warnings because test.py does not load them",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit a machine-readable JSON report",
    )
    return parser.parse_args(argv)


def status_for(path):
    if path.is_file():
        return "ok"
    if path.exists():
        return "not-a-file"
    return "missing"


def read_config_summary(config_path):
    summary = {"readable": False, "empty": False, "keys": {}, "error": None}
    try:
        text = config_path.read_text(encoding="utf-8")
    except Exception as exc:  # pragma: no cover - defensive for permissions/encoding
        summary["error"] = str(exc)
        return summary

    summary["readable"] = True
    if not text.strip():
        summary["empty"] = True
        return summary

    for key in CONFIG_KEYS:
        pattern = r"^\s*" + re.escape(key) + r"\s*:\s*(.*?)\s*(?:#.*)?$"
        match = re.search(pattern, text, flags=re.MULTILINE)
        if match:
            summary["keys"][key] = match.group(1).strip()
    return summary


def make_report(args):
    checkpoint_dir = Path(args.checkpoints).expanduser()
    stage = STAGES[args.model]
    required = ["config.yml"] + stage["generators"]
    expected_discriminators = list(stage["discriminators"])

    entries = []
    errors = []
    warnings = []

    if not checkpoint_dir.exists():
        errors.append("checkpoint directory does not exist")
    elif not checkpoint_dir.is_dir():
        errors.append("checkpoint path exists but is not a directory")

    for filename in required:
        path = checkpoint_dir / filename
        status = status_for(path)
        entries.append({"file": filename, "role": "required", "status": status})
        if status != "ok":
            errors.append("missing required file: %s" % filename if status == "missing" else "required path is not a file: %s" % filename)

    for filename in expected_discriminators:
        path = checkpoint_dir / filename
        status = status_for(path)
        role = "required" if args.require_discriminators else "expected"
        entries.append({"file": filename, "role": role, "status": status})
        if status != "ok":
            message = "missing discriminator file: %s" % filename if status == "missing" else "discriminator path is not a file: %s" % filename
            if args.require_discriminators:
                errors.append(message)
            else:
                warnings.append(message + " (not loaded by test.py)")

    config_summary = None
    config_path = checkpoint_dir / "config.yml"
    if config_path.is_file():
        config_summary = read_config_summary(config_path)
        if config_summary["error"]:
            errors.append("config.yml is not readable: %s" % config_summary["error"])
        elif config_summary["empty"]:
            errors.append("config.yml is empty")
        elif not config_summary["keys"]:
            warnings.append("config.yml was readable, but no common EdgeConnect keys were detected")

    return {
        "ok": not errors,
        "checkpoint_dir": str(checkpoint_dir),
        "model": args.model,
        "stage": stage["label"],
        "entries": entries,
        "warnings": warnings,
        "errors": errors,
        "config_summary": config_summary,
        "require_discriminators": args.require_discriminators,
    }


def print_human(report):
    print("EdgeConnect checkpoint check")
    print("checkpoint_dir: %s" % report["checkpoint_dir"])
    print("model: %s (%s)" % (report["model"], report["stage"]))
    print("")

    for entry in report["entries"]:
        marker = "OK" if entry["status"] == "ok" else "MISSING" if entry["status"] == "missing" else "BAD"
        print("[%s] %-8s %s" % (marker, entry["role"], entry["file"]))

    config_summary = report["config_summary"]
    if config_summary and config_summary.get("keys"):
        print("")
        print("config keys detected:")
        for key in CONFIG_KEYS:
            if key in config_summary["keys"]:
                print("  %s: %s" % (key, config_summary["keys"][key]))

    if report["warnings"]:
        print("")
        print("warnings:")
        for warning in report["warnings"]:
            print("  - %s" % warning)

    if report["errors"]:
        print("")
        print("errors:")
        for error in report["errors"]:
            print("  - %s" % error)
        print("")
        print("advice:")
        print("  - Put config.yml directly inside the selected checkpoint directory.")
        print("  - For model 1, provide EdgeModel_gen.pth.")
        print("  - For model 2, provide InpaintingModel_gen.pth.")
        print("  - For model 3 or 4, provide both EdgeModel_gen.pth and InpaintingModel_gen.pth.")
        print("  - Discriminator files are useful for full training bundles but do not replace generator files for testing.")
    else:
        print("")
        print("status: ok for test.py inference layout")


def main(argv=None):
    args = parse_args(argv if argv is not None else sys.argv[1:])
    report = make_report(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
