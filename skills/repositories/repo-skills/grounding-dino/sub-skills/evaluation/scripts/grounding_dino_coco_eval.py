#!/usr/bin/env python3
"""Run GroundingDINO zero-shot COCO bbox evaluation from an installed package.

This is a self-contained adaptation of the repository COCO evaluation demo.
It preserves the original CLI flags, validates inputs before expensive work,
and does not download checkpoints or datasets. Use ``--help`` safely without
COCO data or model weights.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser("Grounding DINO eval on COCO", add_help=True)
    parser.add_argument(
        "--config_file",
        "-c",
        type=str,
        required=True,
        help="path to GroundingDINO config file",
    )
    parser.add_argument(
        "--checkpoint_path",
        "-p",
        type=str,
        required=True,
        help="path to GroundingDINO checkpoint file",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cuda",
        help="running device (default: cuda)",
    )
    parser.add_argument(
        "--num_select",
        type=int,
        default=300,
        help="number of top-k query/category detections to evaluate",
    )
    parser.add_argument(
        "--anno_path",
        type=str,
        required=True,
        help="COCO annotation JSON, for example instances_val2017.json",
    )
    parser.add_argument(
        "--image_dir",
        type=str,
        required=True,
        help="directory containing images referenced by the COCO JSON",
    )
    parser.add_argument(
        "--num_workers",
        type=int,
        default=4,
        help="number of workers for dataloader",
    )
    return parser


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def validate_args(args: argparse.Namespace) -> tuple[Path, Path, Path, Path, dict[str, Any]]:
    config_file = Path(args.config_file).expanduser()
    checkpoint_path = Path(args.checkpoint_path).expanduser()
    anno_path = Path(args.anno_path).expanduser()
    image_dir = Path(args.image_dir).expanduser()

    if not config_file.is_file():
        fail(f"Missing config file: {config_file}")
    if not checkpoint_path.is_file():
        fail(f"Missing checkpoint file: {checkpoint_path}")
    if not anno_path.is_file():
        fail(f"Missing annotation JSON: {anno_path}")
    if not image_dir.is_dir():
        fail(f"Missing image directory: {image_dir}")
    if args.num_select <= 0:
        fail("--num_select must be a positive integer")
    if args.num_workers < 0:
        fail("--num_workers must be zero or a positive integer")

    try:
        with anno_path.open("r", encoding="utf-8") as handle:
            coco_json = json.load(handle)
    except json.JSONDecodeError as exc:
        fail(f"Annotation file is not valid JSON: {exc}")

    for key in ("images", "annotations", "categories"):
        if key not in coco_json:
            fail(f"COCO annotation JSON is missing required key: {key}")
    if not coco_json["images"]:
        fail("COCO annotation JSON contains no images")
    if not coco_json["categories"]:
        fail("COCO annotation JSON contains no categories")

    category_ids: list[int] = []
    category_names: list[str] = []
    for category in coco_json["categories"]:
        category_id = category.get("id")
        category_name = category.get("name")
        if not isinstance(category_id, int) or category_id < 0:
            fail("COCO categories must contain non-negative integer id values")
        if category_id in category_ids:
            fail(f"Duplicate COCO category id: {category_id}")
        if not isinstance(category_name, str) or not category_name.strip():
            fail(f"COCO category {category_id} has an empty or invalid name")
        category_ids.append(category_id)
        category_names.append(category_name)

    missing_sample: list[str] = []
    for image_info in coco_json["images"][:10]:
        file_name = image_info.get("file_name")
        if isinstance(file_name, str) and not (image_dir / file_name).is_file():
            missing_sample.append(file_name)
    if missing_sample:
        preview = ", ".join(missing_sample[:3])
        fail(
            "Image files referenced by COCO JSON were not found under "
            f"--image_dir; examples: {preview}"
        )

    return config_file, checkpoint_path, anno_path, image_dir, coco_json


def import_runtime_modules() -> dict[str, Any]:
    try:
        import torch
        import torch.nn as nn
        import torchvision
        from torch.utils.data import DataLoader

        import groundingdino.datasets.transforms as T
        from groundingdino.datasets.cocogrounding_eval import CocoGroundingEvaluator
        from groundingdino.models import build_model
        from groundingdino.util import box_ops, get_tokenlizer
        from groundingdino.util.misc import clean_state_dict, collate_fn
        from groundingdino.util.slconfig import SLConfig
        from groundingdino.util.vl_utils import (
            build_captions_and_token_span,
            create_positive_map_from_span,
        )
    except ImportError as exc:
        fail(
            "Missing runtime dependency while importing GroundingDINO evaluation modules. "
            "Install GroundingDINO with its base dependencies, including torch, "
            f"torchvision, transformers, and pycocotools. Original error: {exc}"
        )

    return {
        "torch": torch,
        "nn": nn,
        "torchvision": torchvision,
        "DataLoader": DataLoader,
        "T": T,
        "CocoGroundingEvaluator": CocoGroundingEvaluator,
        "build_model": build_model,
        "box_ops": box_ops,
        "get_tokenlizer": get_tokenlizer,
        "clean_state_dict": clean_state_dict,
        "collate_fn": collate_fn,
        "SLConfig": SLConfig,
        "build_captions_and_token_span": build_captions_and_token_span,
        "create_positive_map_from_span": create_positive_map_from_span,
    }


def check_device(torch: Any, device: str) -> None:
    if device.startswith("cuda") and not torch.cuda.is_available():
        fail(
            f"CUDA device requested ({device}) but torch.cuda.is_available() is False. "
            "Use --device cpu for a smoke test or run in a CUDA-enabled Torch environment."
        )
    try:
        torch.device(device)
    except Exception as exc:  # noqa: BLE001 - convert framework detail into CLI error.
        fail(f"Invalid torch device {device!r}: {exc}")


def run_evaluation(args: argparse.Namespace) -> None:
    config_file, checkpoint_path, anno_path, image_dir, _ = validate_args(args)
    modules = import_runtime_modules()
    torch = modules["torch"]
    nn = modules["nn"]
    torchvision = modules["torchvision"]
    DataLoader = modules["DataLoader"]
    T = modules["T"]
    CocoGroundingEvaluator = modules["CocoGroundingEvaluator"]
    build_model = modules["build_model"]
    box_ops = modules["box_ops"]
    get_tokenlizer = modules["get_tokenlizer"]
    clean_state_dict = modules["clean_state_dict"]
    collate_fn = modules["collate_fn"]
    SLConfig = modules["SLConfig"]
    build_captions_and_token_span = modules["build_captions_and_token_span"]
    create_positive_map_from_span = modules["create_positive_map_from_span"]

    check_device(torch, args.device)

    class CocoDetection(torchvision.datasets.CocoDetection):
        """COCO dataset wrapper returning fields required by GroundingDINO eval."""

        def __init__(self, img_folder: str, ann_file: str, transforms: Any) -> None:
            super().__init__(img_folder, ann_file)
            self._transforms = transforms

        def __getitem__(self, idx: int) -> tuple[Any, dict[str, Any]]:
            img, target = super().__getitem__(idx)
            width, height = img.size
            boxes = [obj["bbox"] for obj in target]
            boxes = torch.as_tensor(boxes, dtype=torch.float32).reshape(-1, 4)
            boxes[:, 2:] += boxes[:, :2]
            boxes[:, 0::2].clamp_(min=0, max=width)
            boxes[:, 1::2].clamp_(min=0, max=height)
            keep = (boxes[:, 3] > boxes[:, 1]) & (boxes[:, 2] > boxes[:, 0])
            boxes = boxes[keep]

            target_new = {
                "image_id": self.ids[idx],
                "boxes": boxes,
                "orig_size": torch.as_tensor([int(height), int(width)]),
            }
            if self._transforms is not None:
                img, target_new = self._transforms(img, target_new)
            return img, target_new

    class PostProcessCocoGrounding(nn.Module):
        """Convert GroundingDINO token logits and boxes into COCO detections."""

        def __init__(self, num_select: int, coco_api: Any, tokenlizer: Any) -> None:
            super().__init__()
            self.num_select = num_select
            category_dict = coco_api.dataset["categories"]
            cat_list = [str(item["name"]).lower() for item in category_dict]
            captions, cat2tokenspan = build_captions_and_token_span(cat_list, True)
            token_span_list = [cat2tokenspan[cat] for cat in cat_list]
            positive_map = create_positive_map_from_span(tokenlizer(captions), token_span_list)
            self.register_buffer("positive_map", positive_map)
            category_ids = torch.as_tensor([int(item["id"]) for item in category_dict], dtype=torch.long)
            self.register_buffer("category_ids", category_ids)

        @torch.no_grad()
        def forward(self, outputs: dict[str, Any], target_sizes: Any) -> list[dict[str, Any]]:
            out_logits = outputs["pred_logits"]
            out_bbox = outputs["pred_boxes"]
            if len(out_logits) != len(target_sizes):
                raise ValueError("outputs and target_sizes batch dimensions differ")
            if target_sizes.shape[1] != 2:
                raise ValueError("target_sizes must have shape [batch_size, 2]")

            prob_to_token = out_logits.sigmoid()
            pos_maps = self.positive_map.to(prob_to_token.device)
            prob_to_label = prob_to_token @ pos_maps.T
            num_select = min(self.num_select, prob_to_label.shape[1] * prob_to_label.shape[2])
            topk_values, topk_indexes = torch.topk(
                prob_to_label.view(out_logits.shape[0], -1), num_select, dim=1
            )
            topk_boxes = topk_indexes // prob_to_label.shape[2]
            label_indexes = topk_indexes % prob_to_label.shape[2]
            category_ids = self.category_ids.to(label_indexes.device)
            labels = category_ids[label_indexes]

            boxes = box_ops.box_cxcywh_to_xyxy(out_bbox)
            boxes = torch.gather(boxes, 1, topk_boxes.unsqueeze(-1).repeat(1, 1, 4))
            img_h, img_w = target_sizes.unbind(1)
            scale_fct = torch.stack([img_w, img_h, img_w, img_h], dim=1)
            boxes = boxes * scale_fct[:, None, :]

            return [
                {"scores": scores, "labels": label, "boxes": box}
                for scores, label, box in zip(topk_values, labels, boxes)
            ]

    def load_model(model_config_path: Path, model_checkpoint_path: Path, device: str) -> tuple[Any, Any]:
        cfg = SLConfig.fromfile(str(model_config_path))
        cfg.device = device
        model = build_model(cfg)
        try:
            checkpoint = torch.load(str(model_checkpoint_path), map_location="cpu")
        except Exception as exc:  # noqa: BLE001 - convert framework detail into CLI error.
            fail(f"Could not load checkpoint {model_checkpoint_path}: {exc}")
        state_dict = checkpoint.get("model", checkpoint) if isinstance(checkpoint, dict) else checkpoint
        if not isinstance(state_dict, dict):
            fail("Checkpoint must be a state dict or contain a 'model' state dict")
        model.load_state_dict(clean_state_dict(state_dict), strict=False)
        model.to(device)
        model.eval()
        return model, cfg

    model, cfg = load_model(config_file, checkpoint_path, args.device)

    transform = T.Compose(
        [
            T.RandomResize([800], max_size=1333),
            T.ToTensor(),
            T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )
    dataset = CocoDetection(str(image_dir), str(anno_path), transforms=transform)
    data_loader = DataLoader(
        dataset,
        batch_size=1,
        shuffle=False,
        num_workers=args.num_workers,
        collate_fn=collate_fn,
    )

    tokenlizer = get_tokenlizer.get_tokenlizer(cfg.text_encoder_type)
    postprocessor = PostProcessCocoGrounding(
        num_select=args.num_select,
        coco_api=dataset.coco,
        tokenlizer=tokenlizer,
    )
    evaluator = CocoGroundingEvaluator(dataset.coco, iou_types=("bbox",), useCats=True)

    category_dict = dataset.coco.dataset["categories"]
    cat_list = [str(item["name"]).lower() for item in category_dict]
    caption = " . ".join(cat_list) + " ."
    print("Input text prompt:", caption)

    start = time.time()
    with torch.no_grad():
        for index, (images, targets) in enumerate(data_loader):
            images = images.tensors.to(args.device)
            input_captions = [caption] * images.shape[0]
            outputs = model(images, captions=input_captions)
            orig_target_sizes = torch.stack([t["orig_size"] for t in targets], dim=0).to(images.device)
            results = postprocessor(outputs, orig_target_sizes)
            cocogrounding_res = {
                target["image_id"]: output for target, output in zip(targets, results)
            }
            evaluator.update(cocogrounding_res)

            if (index + 1) % 30 == 0:
                used_time = time.time() - start
                eta = len(data_loader) / (index + 1e-5) * used_time - used_time
                print(
                    f"processed {index}/{len(data_loader)} images. "
                    f"time: {used_time:.2f}s, ETA: {eta:.2f}s"
                )

    evaluator.synchronize_between_processes()
    evaluator.accumulate()
    evaluator.summarize()
    print("Final results:", evaluator.coco_eval["bbox"].stats.tolist())


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    run_evaluation(args)


if __name__ == "__main__":
    main()
