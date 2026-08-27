#!/usr/bin/env python3
"""Plan and sanity-check the MuseCoco stage-1 / stage-2 pipeline.

This helper does not import the Muzic source tree. It only inspects user-
provided files and prints a stage plan that matches the public workflow.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, asdict
from typing import Dict, Iterable, List, Optional, Sequence


@dataclass
class PipelineCheck:
    ok: bool
    errors: List[str]
    warnings: List[str]
    summary: Dict[str, object]


def _load_json(path: Optional[str], errors: List[str]) -> Optional[object]:
    if not path:
        return None
    if not os.path.exists(path):
        errors.append(f"missing file: {path}")
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:  # pragma: no cover - defensive
        errors.append(f"failed to parse JSON {path}: {exc}")
        return None


def _check_predict_json(path: Optional[str], errors: List[str], warnings: List[str]) -> Dict[str, object]:
    info: Dict[str, object] = {}
    data = _load_json(path, errors)
    if data is None:
        return info
    if not isinstance(data, list):
        errors.append("predict JSON must be a list of prompt objects")
        return info
    info["predict_count"] = len(data)
    if data:
        first = data[0]
        if not isinstance(first, dict) or "text" not in first:
            errors.append("predict JSON entries must contain a text field")
        else:
            info["first_text_preview"] = str(first["text"])[:120]
    else:
        warnings.append("predict JSON is empty")
    return info


def _check_att_key(path: Optional[str], errors: List[str], warnings: List[str]) -> Dict[str, object]:
    info: Dict[str, object] = {}
    data = _load_json(path, errors)
    if data is None:
        return info
    if not isinstance(data, list):
        errors.append("att_key JSON must be a list of attribute labels")
        return info
    info["att_key_count"] = len(data)
    info["has_I1s2_labels"] = any(isinstance(x, str) and x.startswith("I1s2_") for x in data)
    info["has_S4_labels"] = any(isinstance(x, str) and x.startswith("S4_") for x in data)
    if not info["has_I1s2_labels"]:
        warnings.append("att_key JSON does not contain grouped I1s2 labels")
    if not info["has_S4_labels"]:
        warnings.append("att_key JSON does not contain grouped S4 labels")
    return info


def _check_path(path: Optional[str], label: str, errors: List[str]) -> Dict[str, object]:
    info: Dict[str, object] = {}
    if not path:
        return info
    if os.path.exists(path):
        info[f"{label}_exists"] = True
        if os.path.isdir(path):
            info[f"{label}_kind"] = "dir"
        else:
            info[f"{label}_kind"] = "file"
    else:
        errors.append(f"missing {label}: {path}")
    return info


def build_plan(args: argparse.Namespace) -> List[Dict[str, object]]:
    stage1_dir = args.stage1_output_dir.rstrip("/")
    stage2_dir = args.stage2_model_dir.rstrip("/")
    predict_json = args.predict_json or "data/predict.json"
    att_key = args.att_key or "data/att_key.json"
    num_labels = args.num_labels or "num_labels.json"
    stage1_tmp = args.stage1_tmp_dir or "tmp"
    infer_bin = args.infer_bin or "infer_test.bin"
    stage2_input = args.stage2_input_bin or "data/infer_input/infer_test.bin"
    checkpoint = args.stage2_checkpoint or "checkpoints/linear_mask-1billion/checkpoint_2_280000.pt"
    generation_root = args.generation_root or "generation"
    evaluation_root = generation_root if os.path.isabs(generation_root) else f"../{stage2_dir}/{generation_root}"

    return [
        {
            "stage": "text-to-attribute prediction",
            "cwd": "1-text2attribute_model",
            "command": (
                "python main.py --do_predict --model_name_or_path XinXuNLPer/MuseCoco_text2attribute "
                f"--test_file {predict_json} --attributes {att_key} --num_labels {num_labels} "
                f"--output_dir {stage1_tmp} --overwrite_output_dir"
            ),
            "outputs": [
                f"{stage1_tmp}/predict_attributes.json",
                f"{stage1_tmp}/softmax_probs.json",
            ],
        },
        {
            "stage": "stage-1 postprocess",
            "cwd": "1-text2attribute_model",
            "command": "python stage2_pre.py",
            "outputs": [infer_bin],
        },
        {
            "stage": "stage-2 handoff",
            "cwd": "2-attribute2music_model",
            "command": f"cp ../{stage1_dir}/{infer_bin} {stage2_input}",
            "outputs": [stage2_input],
        },
        {
            "stage": "attribute-to-music generation",
            "cwd": "2-attribute2music_model",
            "command": (
                f"bash interactive_1billion.sh {args.start} {args.end}"
                if args.end is not None
                else f"bash interactive_1billion.sh {args.start} {args.start + args.default_span}"
            ),
            "outputs": [generation_root],
            "checkpoint": checkpoint,
        },
        {
            "stage": "evaluation",
            "cwd": "musecoco/evaluation",
            "command": f"python eval_acc_v3.py --root {evaluation_root}",
            "outputs": ["acc_result.json", "midiinfo.json"],
        },
    ]


def _print_plan(plan: List[Dict[str, object]], as_json: bool) -> int:
    if as_json:
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        for idx, step in enumerate(plan, start=1):
            print(f"[{idx}] {step['stage']}")
            print(f"  cwd: {step['cwd']}")
            print(f"  command: {step['command']}")
            if "checkpoint" in step:
                print(f"  checkpoint: {step['checkpoint']}")
            if step.get("outputs"):
                print("  outputs:")
                for out in step["outputs"]:
                    print(f"    - {out}")
    return 0


def validate(args: argparse.Namespace) -> PipelineCheck:
    errors: List[str] = []
    warnings: List[str] = []
    summary: Dict[str, object] = {}

    summary.update(_check_predict_json(args.predict_json, errors, warnings))
    summary.update(_check_att_key(args.att_key, errors, warnings))
    summary.update(_check_path(args.num_labels, "num_labels", errors))
    summary.update(_check_path(args.stage2_checkpoint, "stage2_checkpoint", errors))
    summary.update(_check_path(args.infer_bin, "infer_bin", errors))
    summary.update(_check_path(args.generation_root, "generation_root", errors))

    if args.stage2_checkpoint and not args.stage2_checkpoint.endswith(".pt"):
        warnings.append("stage-2 checkpoint does not end in .pt")
    if args.infer_bin and not args.infer_bin.endswith(".bin"):
        warnings.append("infer bundle does not end in .bin")

    return PipelineCheck(ok=not errors, errors=errors, warnings=warnings, summary=summary)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plan or validate the MuseCoco pipeline.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--predict-json", default=None, help="stage-1 input JSON")
    common.add_argument("--att-key", default=None, help="attribute key JSON")
    common.add_argument("--num-labels", default=None, help="stage-1 num_labels JSON")
    common.add_argument("--stage1-output-dir", default="1-text2attribute_model", help="stage-1 model folder")
    common.add_argument("--stage1-tmp-dir", default=None, help="stage-1 temp output directory")
    common.add_argument("--infer-bin", default=None, help="stage-1 postprocess output infer_test.bin")
    common.add_argument("--stage2-model-dir", default="2-attribute2music_model", help="stage-2 model folder")
    common.add_argument("--stage2-input-bin", default=None, help="stage-2 infer_input bin path")
    common.add_argument("--stage2-checkpoint", default=None, help="stage-2 checkpoint path")
    common.add_argument("--generation-root", default=None, help="expected generation root")
    common.add_argument("--start", type=int, default=0, help="stage-2 generation start index")
    common.add_argument("--end", type=int, default=None, help="stage-2 generation end index")
    common.add_argument("--default-span", type=int, default=200, help="default span when --end is omitted")
    common.add_argument("--json", action="store_true", help="print JSON output")

    check = subparsers.add_parser("check", parents=[common], help="validate files and artifacts")

    plan = subparsers.add_parser("plan", parents=[common], help="print the stage-by-stage pipeline plan")

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "check":
        result = validate(args)
        payload = asdict(result)
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"ok: {result.ok}")
            if result.summary:
                print("summary:")
                for key, value in result.summary.items():
                    print(f"  {key}: {value}")
            if result.warnings:
                print("warnings:")
                for item in result.warnings:
                    print(f"  - {item}")
            if result.errors:
                print("errors:")
                for item in result.errors:
                    print(f"  - {item}")
        return 0 if result.ok else 1

    if args.command == "plan":
        plan_steps = build_plan(args)
        return _print_plan(plan_steps, args.json)

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
