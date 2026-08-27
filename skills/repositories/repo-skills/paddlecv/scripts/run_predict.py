#!/usr/bin/env python3
"""Run PaddleCV inference from either a config file or a built-in task name.

Examples:
  python skills/disco/paddlecv/scripts/run_predict.py --config paddlecv/configs/single_op/PP-YOLOE+.yml --input paddlecv/demo/000000014439.jpg
  python skills/disco/paddlecv/scripts/run_predict.py --task-name PP-OCRv3 --input paddlecv/demo/00056221.jpg
"""
from __future__ import annotations

import argparse
import pprint
from pathlib import Path

import yaml

from paddlecv import PaddleCV
from ppcv.engine.pipeline import Pipeline


def parse_opt(tokens: list[str]) -> dict:
    config: dict = {}
    for raw in tokens:
        key, value = raw.split("=", 1)
        cursor = config
        parts = key.split(".")
        for part in parts[:-1]:
            cursor = cursor.setdefault(part, {})
        cursor[parts[-1]] = yaml.safe_load(value)
    return config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a PaddleCV config or task-name workflow.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--config", help="Path to a PaddleCV YAML config file.")
    group.add_argument("--task-name", help="Built-in PaddleCV task name, such as PP-OCRv3.")
    parser.add_argument("--input", required=True, help="Image path, image directory, or video path.")
    parser.add_argument("--output-dir", default="output", help="Output directory for saved results.")
    parser.add_argument("--run-mode", default="paddle", help="Inference mode such as paddle or mkldnn.")
    parser.add_argument("--device", default="CPU", help="Device name: CPU, GPU, or XPU.")
    parser.add_argument("-o", "--opt", nargs="*", default=[], help="Nested config overrides in KEY=VALUE form.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    input_path = str(Path(args.input))

    if args.task_name:
        runner = PaddleCV(
            task_name=args.task_name,
            output_dir=args.output_dir,
            run_mode=args.run_mode,
            device=args.device,
        )
        result = runner(input_path)
    else:
        namespace = argparse.Namespace(
            config=args.config,
            input=input_path,
            output_dir=args.output_dir,
            run_mode=args.run_mode,
            device=args.device,
            opt=parse_opt(args.opt),
        )
        pipeline = Pipeline(namespace)
        result = pipeline.run(input_path)

    pprint.pp(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
