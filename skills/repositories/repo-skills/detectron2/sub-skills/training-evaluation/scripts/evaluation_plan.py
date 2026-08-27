#!/usr/bin/env python3
"""Print a Detectron2 evaluation plan without running evaluation."""

from __future__ import annotations

import argparse
import shlex
from typing import List


EVALUATOR_NOTES = {
    "coco": "Use COCOEvaluator for bbox/segm/keypoint AP when metadata has json_file or output_dir is provided.",
    "sem_seg": "Use SemSegEvaluator for semantic segmentation datasets in Detectron2 standard format.",
    "panoptic": "Use DatasetEvaluators with semantic, instance, and panoptic evaluators when the config produces panoptic outputs.",
    "lvis": "Use LVISEvaluator for LVIS-style annotations and metrics.",
    "pascal_voc": "Use PascalVOCDetectionEvaluator for Pascal VOC detection metrics.",
    "cityscapes_instance": "Use CityscapesInstanceEvaluator and follow Cityscapes result-format constraints.",
    "cityscapes_sem_seg": "Use CityscapesSemSegEvaluator and follow Cityscapes result-format constraints.",
    "custom": "Implement DatasetEvaluator or combine built-ins with DatasetEvaluators. Ensure evaluate() returns a dict on the main process.",
}


def quote_join(parts: List[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts if str(part) != "")


def command_preview(args: argparse.Namespace) -> str:
    script = args.script or (
        "PROJECT_LAZY_TRAIN_DRIVER.py" if args.config_style == "lazy" else "PROJECT_TRAIN_DRIVER.py"
    )
    command = [args.python, script, "--config-file", args.config_file, "--eval-only", "--num-gpus", str(args.num_gpus)]
    if args.resume:
        command.append("--resume")
    if args.config_style == "yacs":
        command.extend(["MODEL.WEIGHTS", args.checkpoint, "OUTPUT_DIR", args.output_dir])
        if args.dataset_name:
            command.extend(["DATASETS.TEST", f'("{args.dataset_name}",)'])
    else:
        command.extend([f"train.init_checkpoint={args.checkpoint}", f"train.output_dir={args.output_dir}"])
    return quote_join(command)


def plan_items(args: argparse.Namespace) -> List[str]:
    items = [
        "Confirm dataset registration code runs before this evaluation command or API call.",
        "Confirm the evaluator matches model outputs and dataset metadata.",
        "Confirm the checkpoint path exists or is a resolvable model-zoo/PathManager path.",
        "Confirm class count and metadata mappings match the trained checkpoint.",
        "Confirm output directory is writable and acceptable for evaluator artifacts.",
    ]
    if args.resume:
        items.append("Because --resume is selected, confirm last_checkpoint points to the intended checkpoint.")
    if args.num_gpus > 1:
        items.append("Because multiple GPUs are selected, get user approval before running full evaluation.")
    if args.config_style == "lazy":
        items.append("For LazyConfig, confirm cfg.dataloader.evaluator exists or evaluation will have no evaluator.")
    return items


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a Detectron2 evaluation plan without running it.")
    parser.add_argument("--dataset-name", required=True, help="Registered dataset name to evaluate.")
    parser.add_argument("--evaluator-type", choices=sorted(EVALUATOR_NOTES), required=True)
    parser.add_argument("--config-style", choices=["yacs", "lazy"], required=True)
    parser.add_argument("--config-file", required=True, help="Config file for the planned eval command.")
    parser.add_argument("--checkpoint", required=True, help="Checkpoint/weights path or URL placeholder.")
    parser.add_argument("--output-dir", required=True, help="Output directory placeholder.")
    parser.add_argument("--num-gpus", type=int, default=1, help="GPUs per machine for command preview.")
    parser.add_argument("--resume", action="store_true", help="Plan eval-only with --resume semantics.")
    parser.add_argument("--python", default="python", help="Python executable placeholder to print.")
    parser.add_argument(
        "--script",
        help=(
            "Project-local evaluation driver to print. Defaults to a placeholder; replace it "
            "with your own driver that follows Detectron2's standard parser shape."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print("Evaluation plan (not executed):")
    print(f"- Dataset: {args.dataset_name}")
    print(f"- Evaluator: {args.evaluator_type} - {EVALUATOR_NOTES[args.evaluator_type]}")
    print(f"- Config style: {args.config_style}")
    print(f"- Checkpoint field: {'train.init_checkpoint' if args.config_style == 'lazy' else 'MODEL.WEIGHTS'}")
    print("\nCommand preview:")
    print(command_preview(args))
    print("\nPre-run checks:")
    for item in plan_items(args):
        print(f"- {item}")
    print(
        "\nSafety: this helper only prints a plan; it does not import detectron2, "
        "depend on the original source checkout, or run evaluation."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
