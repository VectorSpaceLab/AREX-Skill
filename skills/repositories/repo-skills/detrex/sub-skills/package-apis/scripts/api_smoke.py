#!/usr/bin/env python3
"""Safe detrex package API smoke/introspection helper.

This script imports and inspects selected public detrex APIs. It performs no
training, evaluation, dataset registration, checkpoint download, or pretrained
weight download. Optional flags can load a packaged config, run tiny CPU tensor
checks, instantiate a torchvision backbone with pretrained=False, or check CUDA
extension symbol availability.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
import traceback
from typing import Any, Dict, Iterable, List, Tuple


API_GROUPS: Dict[str, List[str]] = {
    "detrex": ["layers", "modeling", "utils", "data", "config"],
    "detrex.layers": [
        "MultiScaleDeformableAttention",
        "multi_scale_deformable_attn_pytorch",
        "DCNv3",
        "dcnv3_core_pytorch",
        "LayerNorm",
        "box_cxcywh_to_xyxy",
        "box_xyxy_to_cxcywh",
        "box_iou",
        "generalized_box_iou",
        "masks_to_boxes",
        "BaseTransformerLayer",
        "TransformerLayerSequence",
        "PositionEmbeddingLearned",
        "PositionEmbeddingSine",
        "get_sine_pos_embed",
        "MLP",
        "FFN",
        "MultiheadAttention",
        "ConditionalSelfAttention",
        "ConditionalCrossAttention",
        "ConvNormAct",
        "ConvNorm",
        "apply_box_noise",
        "apply_label_noise",
        "GenerateDNQueries",
        "ShapeSpec",
    ],
    "detrex.modeling": [
        "SetCriterion",
        "BaseCriterion",
        "HungarianMatcher",
        "CrossEntropyLoss",
        "FocalLoss",
        "DiceLoss",
        "L1Loss",
        "GIoULoss",
        "ChannelMapper",
        "BasicStem",
        "ResNet",
        "make_stage",
        "ConvNeXt",
        "FocalNet",
        "TimmBackbone",
    ],
    "detrex.modeling.backbone": [
        "TimmBackbone",
        "TorchvisionBackbone",
        "BasicStem",
        "ResNet",
        "make_stage",
        "ConvNeXt",
        "FocalNet",
        "InternImage",
        "EVAViT",
        "EVA02_ViT",
        "SimpleFeaturePyramid",
        "get_vit_lr_decay_rate",
    ],
    "detrex.modeling.matcher": [
        "HungarianMatcher",
        "ModifedMatcher",
        "FocalLossCost",
        "CrossEntropyCost",
        "L1Cost",
        "GIoUCost",
    ],
    "detrex.config": ["get_config", "try_get_key"],
    "detrex.data": [
        "DetrDatasetMapper",
        "COCOInstanceNewBaselineDatasetMapper",
        "COCOPanopticNewBaselineDatasetMapper",
        "MaskFormerSemanticDatasetMapper",
        "MaskFormerInstanceDatasetMapper",
        "MaskFormerPanopticDatasetMapper",
        "ColorAugSSDTransform",
    ],
    "detrex.checkpoint": ["DetectionCheckpointer"],
    "detrex.modeling.ema": [
        "EMAState",
        "EMAUpdater",
        "EMAHook",
        "may_build_model_ema",
        "may_get_ema_checkpointer",
        "get_model_ema_state",
        "apply_model_ema",
        "apply_model_ema_and_restore",
    ],
    "detrex.utils": [
        "interpolate",
        "inverse_sigmoid",
        "is_dist_avail_and_initialized",
        "get_world_size",
        "get_rank",
        "WandbWriter",
    ],
}


class Recorder:
    def __init__(self) -> None:
        self.result: Dict[str, Any] = {
            "imports": {},
            "objects": {},
            "checks": {},
            "errors": [],
        }

    def add_error(self, where: str, exc: BaseException, include_trace: bool = False) -> None:
        entry = {"where": where, "type": type(exc).__name__, "message": str(exc)}
        if include_trace:
            entry["traceback"] = traceback.format_exc()
        self.result["errors"].append(entry)

    def import_module(self, module_name: str):
        try:
            module = importlib.import_module(module_name)
        except BaseException as exc:  # import can raise more than ImportError
            self.result["imports"][module_name] = {
                "ok": False,
                "error": f"{type(exc).__name__}: {exc}",
            }
            self.add_error(f"import {module_name}", exc)
            return None
        self.result["imports"][module_name] = {"ok": True}
        return module

    def inspect_object(self, module_name: str, module: Any, attr: str) -> None:
        key = f"{module_name}.{attr}"
        try:
            obj = getattr(module, attr)
        except BaseException as exc:
            self.result["objects"][key] = {
                "ok": False,
                "error": f"{type(exc).__name__}: {exc}",
            }
            self.add_error(f"getattr {key}", exc)
            return

        item: Dict[str, Any] = {
            "ok": True,
            "type": type(obj).__name__,
            "module": getattr(obj, "__module__", None),
        }
        try:
            item["signature"] = str(inspect.signature(obj))
        except (TypeError, ValueError):
            item["signature"] = None
        self.result["objects"][key] = item


def inspect_public_apis(rec: Recorder) -> None:
    for module_name, attrs in API_GROUPS.items():
        module = rec.import_module(module_name)
        if module is None:
            continue
        for attr in attrs:
            rec.inspect_object(module_name, module, attr)


def check_cuda_extension(rec: Recorder) -> None:
    check: Dict[str, Any] = {"requested": True}
    try:
        ext = importlib.import_module("detrex._C")
        symbols = ["ms_deform_attn_forward", "ms_deform_attn_backward"]
        check["import_ok"] = True
        check["symbols"] = {name: hasattr(ext, name) for name in symbols}
        check["all_symbols_present"] = all(check["symbols"].values())
    except BaseException as exc:
        check["import_ok"] = False
        check["error"] = f"{type(exc).__name__}: {exc}"
        rec.add_error("import detrex._C", exc)

    try:
        torch = importlib.import_module("torch")
        check["torch_cuda_available"] = bool(torch.cuda.is_available())
        check["torch_cuda_device_count"] = int(torch.cuda.device_count()) if torch.cuda.is_available() else 0
    except BaseException as exc:
        check["torch_error"] = f"{type(exc).__name__}: {exc}"
        rec.add_error("inspect torch.cuda", exc)

    rec.result["checks"]["cuda_extension"] = check


def check_config(rec: Recorder, config_name: str) -> None:
    check: Dict[str, Any] = {"requested": config_name}
    try:
        config_mod = importlib.import_module("detrex.config")
        cfg = config_mod.get_config(config_name)
        keys = list(cfg.keys()) if hasattr(cfg, "keys") else []
        check.update({"ok": True, "type": type(cfg).__name__, "top_level_keys": keys})
    except BaseException as exc:
        check.update({"ok": False, "error": f"{type(exc).__name__}: {exc}"})
        rec.add_error(f"get_config {config_name}", exc)
    rec.result["checks"]["config"] = check


def tiny_cpu_checks(rec: Recorder) -> None:
    check: Dict[str, Any] = {"requested": True, "steps": {}}
    try:
        torch = importlib.import_module("torch")
        layers = importlib.import_module("detrex.layers")
        losses = importlib.import_module("detrex.modeling.losses")

        boxes = torch.tensor([[0.5, 0.5, 0.2, 0.4], [0.4, 0.4, 0.2, 0.2]], dtype=torch.float32)
        xyxy = layers.box_cxcywh_to_xyxy(boxes)
        giou = layers.generalized_box_iou(xyxy, xyxy)
        check["steps"]["box_ops"] = {"xyxy_shape": list(xyxy.shape), "giou_shape": list(giou.shape)}

        mask = torch.zeros(1, 4, 5, dtype=torch.bool)
        pos = layers.PositionEmbeddingSine(num_pos_feats=8, normalize=True)(mask)
        check["steps"]["position_embedding"] = {"shape": list(pos.shape)}

        ffn = layers.FFN(embed_dim=16, feedforward_dim=32, output_dim=16, num_fcs=2)
        ffn_out = ffn(torch.randn(2, 3, 16))
        check["steps"]["ffn"] = {"shape": list(ffn_out.shape)}

        focal = losses.FocalLoss(alpha=0.25, gamma=2.0, reduction="mean", loss_weight=1.0, activated=False)
        logits = torch.randn(6, 4)
        labels = torch.randint(0, 4, (6,), dtype=torch.long)
        loss_value = focal(logits, labels, avg_factor=3)
        check["steps"]["focal_loss"] = {"scalar": float(loss_value.detach().cpu())}

        check["ok"] = True
    except BaseException as exc:
        check["ok"] = False
        check["error"] = f"{type(exc).__name__}: {exc}"
        rec.add_error("tiny CPU checks", exc, include_trace=True)
    rec.result["checks"]["tiny_cpu"] = check


def check_torchvision_backbone(rec: Recorder, model_name: str) -> None:
    check: Dict[str, Any] = {"requested": True, "model_name": model_name, "pretrained": False}
    try:
        torch = importlib.import_module("torch")
        backbone_mod = importlib.import_module("detrex.modeling.backbone")
        TorchvisionBackbone = getattr(backbone_mod, "TorchvisionBackbone")
        model = TorchvisionBackbone(
            model_name=model_name,
            pretrained=False,
            return_nodes={"layer1": "res2", "layer2": "res3"},
        )
        model.eval()
        with torch.no_grad():
            outs = model(torch.randn(1, 3, 64, 64))
        check["ok"] = True
        check["out_shapes"] = {name: list(tensor.shape) for name, tensor in outs.items()}
    except BaseException as exc:
        check["ok"] = False
        check["error"] = f"{type(exc).__name__}: {exc}"
        rec.add_error("torchvision backbone check", exc, include_trace=True)
    rec.result["checks"]["torchvision_backbone"] = check


def summarize(result: Dict[str, Any]) -> str:
    lines: List[str] = []
    ok_imports = sum(1 for value in result["imports"].values() if value.get("ok"))
    total_imports = len(result["imports"])
    ok_objects = sum(1 for value in result["objects"].values() if value.get("ok"))
    total_objects = len(result["objects"])
    lines.append(f"imports: {ok_imports}/{total_imports} ok")
    lines.append(f"objects: {ok_objects}/{total_objects} ok")
    for name, check in result["checks"].items():
        if isinstance(check, dict) and "ok" in check:
            lines.append(f"check {name}: {'ok' if check['ok'] else 'failed'}")
        elif name == "cuda_extension":
            ok = check.get("import_ok") and check.get("all_symbols_present")
            lines.append(f"check {name}: {'ok' if ok else 'failed'}")
    if result["errors"]:
        lines.append("errors:")
        for err in result["errors"]:
            lines.append(f"- {err['where']}: {err['type']}: {err['message']}")
    else:
        lines.append("errors: none")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safely import and inspect selected detrex package APIs.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--json", action="store_true", help="emit full JSON report")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit non-zero if any requested import/object/check fails",
    )
    parser.add_argument(
        "--check-cuda-extension",
        action="store_true",
        help="also import detrex._C and check ms_deform_attn symbols; does not run kernels",
    )
    parser.add_argument(
        "--check-config",
        metavar="CONFIG",
        default="",
        help="load a packaged detrex config resource such as common/train.py",
    )
    parser.add_argument(
        "--tiny-cpu",
        action="store_true",
        help="run tiny CPU checks for box ops, position embedding, FFN, and focal loss",
    )
    parser.add_argument(
        "--check-torchvision-backbone",
        action="store_true",
        help="instantiate TorchvisionBackbone with pretrained=False and run a tiny CPU forward",
    )
    parser.add_argument(
        "--torchvision-model",
        default="resnet18",
        help="torchvision model name for --check-torchvision-backbone",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rec = Recorder()

    inspect_public_apis(rec)
    if args.check_cuda_extension:
        check_cuda_extension(rec)
    if args.check_config:
        check_config(rec, args.check_config)
    if args.tiny_cpu:
        tiny_cpu_checks(rec)
    if args.check_torchvision_backbone:
        check_torchvision_backbone(rec, args.torchvision_model)

    if args.json:
        print(json.dumps(rec.result, indent=2, sort_keys=True))
    else:
        print(summarize(rec.result))

    if args.strict and rec.result["errors"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
