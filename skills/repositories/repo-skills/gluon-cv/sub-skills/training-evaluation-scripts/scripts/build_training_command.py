#!/usr/bin/env python3
"""Build safe GluonCV training/evaluation flag templates.

This helper does not import GluonCV, inspect data, touch GPUs, download weights,
or execute training. It prints a non-executable flag skeleton plus a prerequisite
checklist for common GluonCV script families distilled into this skill.
"""
from __future__ import annotations

import argparse
import json
import shlex
from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class Template:
    source_family: str
    flags: List[str]
    warnings: List[str]
    checklist: List[str]


TEMPLATES: Dict[str, Template] = {
    "classification-cifar": Template(
        source_family="classification CIFAR train/demo family",
        flags=["<script-family>", "--model", "{model}", "--batch-size", "{batch_size}", "--num-gpus", "{num_gpus}", "--num-epochs", "{epochs}", "--num-data-workers", "{num_workers}"],
        warnings=["Downloads/loads CIFAR data and trains; not a no-op dry run."],
        checklist=["MXNet backend installed", "CIFAR data/cache policy approved", "Output/checkpoint location chosen"],
    ),
    "classification-imagenet": Template(
        source_family="classification ImageNet train/eval family",
        flags=["<script-family>", "--model", "{model}", "--data-dir", "{data_dir}", "--batch-size", "{batch_size}", "--num-gpus", "{num_gpus}", "--num-epochs", "{epochs}", "--num-data-workers", "{num_workers}"],
        warnings=["Requires prepared ImageNet or RecordIO data; long-running training.", "DALI/Horovod variants need extra dependencies and are not included in this template."],
        checklist=["ImageNet layout or RecordIO paths verified", "MXNet backend installed", "GPU/CPU choice explicit", "Storage budget approved"],
    ),
    "detection-yolo": Template(
        source_family="YOLOv3 detection train/eval/demo family",
        flags=["<script-family>", "--network", "{network}", "--dataset", "{dataset}", "--dataset-root", "{dataset_root}", "--data-shape", "{data_shape}", "--batch-size", "{batch_size}", "--gpus", "{gpus}", "--epochs", "{epochs}", "--num-workers", "{num_workers}"],
        warnings=["Needs detection annotations and often pretrained weights/GPU for practical runs."],
        checklist=["Detection boxes/classes validated", "MXNet model name checked", "VOC/COCO/custom layout verified", "GPU memory budget checked"],
    ),
    "detection-ssd": Template(
        source_family="SSD detection train/eval/demo family",
        flags=["<script-family>", "--network", "{network}", "--dataset", "{dataset}", "--dataset-root", "{dataset_root}", "--data-shape", "{data_shape}", "--batch-size", "{batch_size}", "--gpus", "{gpus}", "--epochs", "{epochs}", "--num-workers", "{num_workers}"],
        warnings=["Training/evaluation requires prepared detection data and can run for hours."],
        checklist=["Detection boxes/classes validated", "Anchors/input shape chosen", "MXNet backend installed", "Cache/network policy for pretrained base"],
    ),
    "detection-faster-rcnn": Template(
        source_family="Faster R-CNN detection train/eval/demo family",
        flags=["<script-family>", "--network", "{network}", "--dataset", "{dataset}", "--dataset-root", "{dataset_root}", "--batch-size", "{batch_size}", "--gpus", "{gpus}", "--epochs", "{epochs}", "--num-workers", "{num_workers}"],
        warnings=["Often memory-heavy; use small batch sizes and confirm dataset metrics dependencies."],
        checklist=["VOC/COCO/custom layout verified", "RPN/RCNN checkpoint compatibility checked", "GPU/CPU resource choice explicit"],
    ),
    "detection-center-net": Template(
        source_family="CenterNet detection train/eval/demo family",
        flags=["<script-family>", "--network", "{network}", "--dataset", "{dataset}", "--dataset-root", "{dataset_root}", "--data-shape", "{data_shape}", "--batch-size", "{batch_size}", "--gpus", "{gpus}", "--epochs", "{epochs}", "--num-workers", "{num_workers}"],
        warnings=["DCNv2 variants may require optional compiled MXNet contrib support."],
        checklist=["Dataset layout verified", "DCNv2 availability checked if selected", "Input shape and batch size sized to hardware"],
    ),
    "instance-mask-rcnn": Template(
        source_family="Mask R-CNN instance segmentation train/eval family",
        flags=["<script-family>", "--network", "{network}", "--dataset", "{dataset}", "--batch-size", "{batch_size}", "--gpus", "{gpus}", "--epochs", "{epochs}", "--num-workers", "{num_workers}"],
        warnings=["Requires instance masks, often COCO/pycocotools, and substantial GPU memory."],
        checklist=["Mask annotations and pycocotools verified", "Class count/checkpoint compatibility checked", "Output paths approved"],
    ),
    "segmentation": Template(
        source_family="semantic segmentation train/test family",
        flags=["<script-family>", "--model", "{model}", "--backbone", "{backbone}", "--dataset", "{dataset}", "--batch-size", "{batch_size}", "--ngpus", "{num_gpus}", "--epochs", "{epochs}", "--workers", "{num_workers}"],
        warnings=["Needs segmentation masks and may use large crops/base sizes."],
        checklist=["Segmentation dataset root and masks verified", "Backbone/pretrained policy chosen", "Crop/base size fits memory"],
    ),
    "pose-simple": Template(
        source_family="simple pose train/validate/demo family",
        flags=["<script-family>", "--data-dir", "{data_dir}", "--num-joints", "{num_joints}", "--batch-size", "{batch_size}", "--num-gpus", "{num_gpus}", "--num-epochs", "{epochs}", "--num-data-workers", "{num_workers}"],
        warnings=["Requires COCO-style keypoint annotations and detector/model weights for demos."],
        checklist=["Keypoint annotation layout verified", "num-joints matches dataset", "Detector/pose pretrained policy chosen"],
    ),
    "action-torch": Template(
        source_family="PyTorch action-recognition train/test/DDP family",
        flags=["<script-family>", "--config-file", "{config_file}"],
        warnings=["Config-file workflow; DDP/GPU/data requirements are controlled by the config and overrides.", "Use torch-video-workflows smoke helper before real training."],
        checklist=["Torch model config name verified", "Video frame/list layout verified", "DDP rank/GPU settings reviewed", "decord/torchvision optional deps checked"],
    ),
    "action-mxnet": Template(
        source_family="MXNet action-recognition train/test/inference family",
        flags=["<script-family>", "--dataset", "{dataset}", "--model", "{model}", "--data-dir", "{data_dir}", "--batch-size", "{batch_size}", "--num-gpus", "{num_gpus}", "--num-epochs", "{epochs}"],
        warnings=["Requires frame/video lists, optional decord, and substantial compute for training."],
        checklist=["Video frames/lists prepared", "Model name checked", "Clip length/input size reviewed", "Network/cache policy for pretrained weights"],
    ),
}


def shell_join(parts: List[str]) -> str:
    return " ".join(shlex.quote(str(p)) for p in parts)


def build_values(ns: argparse.Namespace) -> Dict[str, str]:
    return {k: str(v) for k, v in vars(ns).items() if k not in {"family", "json"}}


def main() -> int:
    parser = argparse.ArgumentParser(description="Print safe GluonCV flag templates without executing anything.")
    parser.add_argument("family", choices=sorted(TEMPLATES), help="Workflow family to template.")
    parser.add_argument("--model", default="resnet", help="Model name or family for classification/action/segmentation templates.")
    parser.add_argument("--network", default="darknet53", help="Detection network/model family.")
    parser.add_argument("--backbone", default="resnet50", help="Segmentation backbone.")
    parser.add_argument("--dataset", default="voc", help="Dataset selector used by the target family.")
    parser.add_argument("--dataset-root", default="<dataset-root>", help="Dataset root placeholder.")
    parser.add_argument("--data-dir", default="<data-dir>", help="Data directory placeholder.")
    parser.add_argument("--data-shape", type=int, default=416, help="Input/data shape placeholder for detection templates.")
    parser.add_argument("--batch-size", type=int, default=2, help="Template batch size.")
    parser.add_argument("--gpus", default="", help="GPU list for MXNet-style workflows; empty string means CPU only when supported.")
    parser.add_argument("--num-gpus", type=int, default=0, help="Number of GPUs for workflows using --num-gpus/--ngpus.")
    parser.add_argument("--epochs", type=int, default=1, help="Small epoch count placeholder.")
    parser.add_argument("--num-workers", type=int, default=0, help="Small worker count for debugging.")
    parser.add_argument("--config-file", default="<config-file.yaml>", help="Torch config file placeholder.")
    parser.add_argument("--num-joints", type=int, default=17, help="Pose keypoint count placeholder.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    ns = parser.parse_args()

    tmpl = TEMPLATES[ns.family]
    values = build_values(ns)
    parts = [p.format(**values) for p in tmpl.flags]
    result = {
        "family": ns.family,
        "source_family": tmpl.source_family,
        "flag_template": shell_join(parts),
        "warnings": tmpl.warnings,
        "checklist": tmpl.checklist,
        "does_execute": False,
    }

    if ns.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Family: {result['family']}")
        print(f"Source family: {result['source_family']}")
        print("Flag template (not directly executable):")
        print(result["flag_template"])
        print("\nWarnings:")
        for item in result["warnings"]:
            print(f"- {item}")
        print("\nPrerequisite checklist:")
        for item in result["checklist"]:
            print(f"- {item}")
        print("\nThis helper only prints a non-executable flag template; it does not execute training or touch data/backends.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
