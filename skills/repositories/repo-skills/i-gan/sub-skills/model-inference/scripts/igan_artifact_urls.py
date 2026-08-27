#!/usr/bin/env python3
"""Plan iGAN pretrained DCGAN artifact URLs and target paths without downloading.

This helper adapts the repository's model download shell script into a read-only
planner. It emits public URLs, conventional target paths, and optional local
presence checks, but never performs network access or writes files.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Dict, Iterable, List, Optional

BASE_URL = "http://efrosgans.eecs.berkeley.edu/iGAN/models/theano_dcgan"
SAMPLE_BASE_URL = "http://efrosgans.eecs.berkeley.edu/iGAN/samples"

MODEL_ZOO: Dict[str, Dict[str, object]] = {
    "outdoor_64": {"resolution": 64, "channels": 3, "dataset": "MIT Places landscapes"},
    "church_64": {"resolution": 64, "channels": 3, "dataset": "LSUN churches"},
    "handbag_64": {"resolution": 64, "channels": 3, "dataset": "Amazon handbag images"},
    "shoes_64": {"resolution": 64, "channels": 3, "dataset": "UT Zappos50K shoe photos"},
    "hed_shoes_64": {"resolution": 64, "channels": 1, "dataset": "HED shoe sketches"},
}


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Emit iGAN DCGAN model artifact URL/target plans without downloading.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("model_name", nargs="?", help="Model name to plan, such as outdoor_64.")
    parser.add_argument("--all", action="store_true", help="Emit plans for every bundled model-zoo entry.")
    parser.add_argument("--model-dir", default="models", help="Directory used for conventional local targets.")
    parser.add_argument("--base-url", default=BASE_URL, help="Base URL for dcgan_theano model artifacts.")
    parser.add_argument("--include-samples", action="store_true", help="Also emit real-vs-generated preview sample URLs.")
    parser.add_argument("--check-existing", action="store_true", help="Check whether each local target file exists.")
    parser.add_argument("--allow-unknown", action="store_true", help="Allow a custom model name outside the bundled model zoo.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")
    return parser.parse_args(argv)


def iter_names(args: argparse.Namespace) -> Iterable[str]:
    if args.all:
        return sorted(MODEL_ZOO)
    if not args.model_name:
        raise SystemExit("Provide model_name or use --all.")
    if args.model_name not in MODEL_ZOO and not args.allow_unknown:
        raise SystemExit(
            "Unknown model_name {!r}. Use one of {} or pass --allow-unknown for a custom artifact.".format(
                args.model_name, ", ".join(sorted(MODEL_ZOO))
            )
        )
    return [args.model_name]


def plan_one(name: str, args: argparse.Namespace) -> Dict[str, object]:
    filename = "{}.dcgan_theano".format(name)
    model_dir = args.model_dir.rstrip("/") or "."
    target = "{}/{}".format(model_dir, filename) if model_dir != "." else filename
    url = "{}/{}".format(args.base_url.rstrip("/"), filename)
    plan: Dict[str, object] = {
        "model_name": name,
        "known_model": name in MODEL_ZOO,
        "filename": filename,
        "url": url,
        "target": target,
        "metadata": MODEL_ZOO.get(name),
        "side_effects": "none; this helper does not download or write files",
    }
    if args.include_samples:
        plan["sample_urls"] = {
            "real": "{}/{}_real.png".format(SAMPLE_BASE_URL, name),
            "dcgan": "{}/{}_dcgan.png".format(SAMPLE_BASE_URL, name),
        }
    if args.check_existing:
        exists = os.path.isfile(target)
        plan["local_status"] = {"checked": True, "exists": exists, "status": "present" if exists else "missing"}
    else:
        plan["local_status"] = {"checked": False, "target": target}
    return plan


def emit_text(plans: List[Dict[str, object]]) -> None:
    for index, plan in enumerate(plans):
        if index:
            print("")
        print("iGAN DCGAN artifact plan")
        print("model_name: {}{}".format(plan["model_name"], " (known)" if plan["known_model"] else " (custom/unknown)"))
        metadata = plan.get("metadata")
        if metadata:
            print("metadata: resolution={resolution}, channels={channels}, dataset={dataset}".format(**metadata))
        print("filename: {}".format(plan["filename"]))
        print("url: {}".format(plan["url"]))
        print("target: {}".format(plan["target"]))
        status = plan["local_status"]
        if status.get("checked"):
            print("local_status: {}".format(status["status"]))
        else:
            print("local_status: not checked (use --check-existing to test local presence)")
        if "sample_urls" in plan:
            print("sample_real_url: {}".format(plan["sample_urls"]["real"]))
            print("sample_dcgan_url: {}".format(plan["sample_urls"]["dcgan"]))
        print("side_effects: {}".format(plan["side_effects"]))


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    plans = [plan_one(name, args) for name in iter_names(args)]
    if args.json:
        print(json.dumps(plans[0] if len(plans) == 1 else plans, indent=2, sort_keys=True))
    else:
        emit_text(plans)
    return 0


if __name__ == "__main__":
    sys.exit(main())
