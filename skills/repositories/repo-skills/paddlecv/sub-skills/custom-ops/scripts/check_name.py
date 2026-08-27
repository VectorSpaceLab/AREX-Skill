#!/usr/bin/env python3
"""Validate PaddleCV operator output names against a config graph."""
from __future__ import annotations

from argparse import ArgumentParser

import yaml

import paddlecv  # noqa: F401 - ensures the bundled package path is loaded
import ppcv
from ppcv.utils.helper import get_output_keys


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(description="Print registered PaddleCV output names and validate a config graph.")
    parser.add_argument("--config", type=str, default=None, help="Path to a PaddleCV config file.")
    return parser


def check_cfg_output(cfg: str, output_dict):
    with open(cfg, encoding="utf-8") as f:
        cfg_obj = yaml.safe_load(f)
    model_cfg = cfg_obj["MODEL"]
    output_set = {"image", "video", "fn"}
    for values in output_dict.values():
        for name in values:
            output_set.add(name)
    for ops in model_cfg:
        op_name = list(ops.keys())[0]
        cfg_dict = list(ops.values())[0]
        cfg_input = cfg_dict["Inputs"]
        for key in cfg_input:
            key = key.split(".")[-1]
            assert key in output_set, f"Illegal input: {key} in {op_name}."


def main() -> int:
    parser = build_parser()
    flags = parser.parse_args()
    output_dict = get_output_keys()
    print("----------- Op output names ---------")
    print(yaml.dump(output_dict, sort_keys=True))
    if flags.config is not None:
        check_cfg_output(flags.config, output_dict)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
