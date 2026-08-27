#!/usr/bin/env python3
"""Plan iGAN AlexNet artifact URLs and targets without downloading.

This helper adapts the repository's download_alexnet.sh into a deterministic
URL/target planner. It performs no network access and writes no files.
"""

from __future__ import annotations

import argparse
import json
from typing import Dict, Iterable, List

BASE_URL = "http://efrosgans.eecs.berkeley.edu/iGAN/models/alexnet"
KNOWN_LAYERS = ("conv1", "conv2", "conv3", "conv4", "conv5", "fc6", "fc7", "fc8")


def normalize_layers(values: Iterable[str]) -> List[str]:
    """Normalize repeated/comma-separated layer arguments."""
    layers: List[str] = []
    for value in values:
        for item in value.split(","):
            layer = item.strip()
            if layer:
                layers.append(layer)
    if not layers:
        layers.append("conv4")
    return layers


def artifact_plan(layer: str, models_dir: str) -> Dict[str, str]:
    """Return the source URL and local target for one AlexNet layer."""
    filename = "caffe_reference_%s.pkl" % layer
    return {
        "layer": layer,
        "filename": filename,
        "url": "%s/%s" % (BASE_URL, filename),
        "target": "%s/%s" % (models_dir.rstrip("/"), filename),
    }


def predictor_note() -> str:
    return (
        "AlexNet files provide feature-network weights only. They do not contain "
        "the DCGAN predictor params or predictor batchnorm required by cnn/cnn_opt; "
        "those must be packed inside the selected DCGAN model file."
    )


def build_plan(args: argparse.Namespace) -> Dict[str, object]:
    layers = normalize_layers(args.layer)
    unknown = [layer for layer in layers if layer not in KNOWN_LAYERS]
    return {
        "dry_run": True,
        "network": False,
        "models_dir": args.models_dir,
        "artifacts": [artifact_plan(layer, args.models_dir) for layer in layers],
        "known_layers": list(KNOWN_LAYERS),
        "unknown_layers": unknown,
        "notes": [
            "The documented iGAN projection workflow uses conv4.",
            "The original shell script maps FILE to http://.../caffe_reference_$FILE.pkl and ./models/caffe_reference_$FILE.pkl.",
            predictor_note(),
        ],
    }


def print_table(data: Dict[str, object]) -> None:
    print("iGAN AlexNet artifact plan (dry-run; no download)")
    print("layer\turl\ttarget")
    for item in data["artifacts"]:
        print("{layer}\t{url}\t{target}".format(**item))
    if data["unknown_layers"]:
        print("warning: unknown layers requested: %s" % ", ".join(data["unknown_layers"]))
    print("note: %s" % predictor_note())


def print_shell(data: Dict[str, object]) -> None:
    print("# Dry-run only: commands below are for manual review and are not executed by this helper.")
    for item in data["artifacts"]:
        print("# layer: {layer}".format(**item))
        print("# url: {url}".format(**item))
        print("# target: {target}".format(**item))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plan iGAN AlexNet pickle URLs/targets without network access."
    )
    parser.add_argument(
        "--layer",
        action="append",
        default=[],
        help="AlexNet layer to plan. Repeat or comma-separate. Default: conv4.",
    )
    parser.add_argument(
        "--models-dir",
        default="./models",
        help="Directory used in the planned target paths.",
    )
    parser.add_argument(
        "--emit",
        choices=("table", "json", "shell"),
        default="table",
        help="Output format. All formats are dry-run only.",
    )
    parser.add_argument(
        "--strict-known-layer",
        action="store_true",
        help="Fail if a requested layer is not in the known AlexNet layer list.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = build_plan(args)
    if args.strict_known_layer and data["unknown_layers"]:
        raise SystemExit("unknown AlexNet layer(s): %s" % ", ".join(data["unknown_layers"]))
    if args.emit == "json":
        print(json.dumps(data, indent=2, sort_keys=True))
    elif args.emit == "shell":
        print_shell(data)
    else:
        print_table(data)


if __name__ == "__main__":
    main()
