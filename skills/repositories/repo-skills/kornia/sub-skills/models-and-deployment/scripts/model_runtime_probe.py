#!/usr/bin/env python3
"""No-download Kornia model/deployment runtime probe.

The probe imports model/config/application classes, runs small tensor smokes for
safe raw models and wrappers, and reports optional deployment modules. It never
passes pretrained=True and never loads remote checkpoints by default.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from typing import Any, Callable


OPTIONAL_MODULES = (
    "PIL",
    "onnx",
    "onnxruntime",
    "onnxscript",
    "requests",
    "ivy",
    "jax",
    "tensorflow",
    "transformers",
    "diffusers",
    "huggingface_hub",
    "safetensors",
    "segmentation_models_pytorch",
    "basicsr",
    "boxmot",
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--device",
        choices=("auto", "cpu", "cuda"),
        default="auto",
        help="Device to use. 'auto' selects CUDA when available, otherwise CPU.",
    )
    parser.add_argument(
        "--dtype",
        choices=("float32", "float64"),
        default="float32",
        help="Floating dtype for small tensor smokes. Half precision is intentionally not a default probe path.",
    )
    parser.add_argument(
        "--include-sam-build",
        action="store_true",
        help="Also construct a non-pretrained MobileSAM model and inspect its encoder size; no forward pass is run.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")
    return parser.parse_args()


def _module_status() -> dict[str, bool]:
    return {name: importlib.util.find_spec(name) is not None for name in OPTIONAL_MODULES}


def _select_device(torch: Any, requested: str) -> Any:
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if requested == "cuda" and not torch.cuda.is_available():
        raise SystemExit("--device cuda requested, but torch.cuda.is_available() is False")
    return torch.device(requested)


def _shape(obj: Any) -> Any:
    if hasattr(obj, "shape"):
        return tuple(int(v) for v in obj.shape)
    if isinstance(obj, dict):
        return {key: _shape(value) for key, value in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_shape(value) for value in obj]
    return str(type(obj).__name__)


def _run_check(results: list[dict[str, Any]], name: str, fn: Callable[[], dict[str, Any]]) -> None:
    try:
        detail = fn()
    except Exception as exc:  # pragma: no cover - diagnostic path for broken runtimes
        results.append({"name": name, "status": "failed", "error": f"{type(exc).__name__}: {exc}"})
    else:
        results.append({"name": name, "status": "ok", "detail": detail})


def main() -> int:
    args = _parse_args()
    optional = _module_status()

    try:
        import torch
        import kornia
        from kornia.contrib.edge_detection import EdgeDetectorBuilder
        from kornia.contrib.object_detection import RTDETRDetectorBuilder
        from kornia.models.dexined import DexiNed
        from kornia.models.efficient_vit import EfficientViTConfig
        from kornia.models.efficient_vit import backbone as efficient_vit_backbone
        from kornia.models.kimi_vl import KimiVLBuilder, KimiVLConfig
        from kornia.models.kimi_vl.config import KimiVLProjectorConfig, MoonViTConfig
        from kornia.models.rt_detr import RTDETR, RTDETRConfig
        from kornia.models.sam import Sam, SamConfig
        from kornia.models.segmentation.segmentation_models import SegmentationModelsBuilder
        from kornia.models.tiny_vit import TinyViT
        from kornia.models.vit import VisionTransformer
        from kornia.models.vit_mobile import MobileViT
        from kornia.models.yunet import YuNet
        from kornia.onnx import ONNXModule, ONNXSequential
    except Exception as exc:  # pragma: no cover - diagnostic path for broken runtimes
        payload = {
            "status": "import-failed",
            "error": f"{type(exc).__name__}: {exc}",
            "optional_modules": optional,
        }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"model_runtime_probe import failed: {payload['error']}", file=sys.stderr)
            print("optional modules:")
            for name, present in optional.items():
                print(f"  {name}: {'present' if present else 'missing'}")
        return 2

    device = _select_device(torch, args.device)
    dtype = getattr(torch, args.dtype)
    torch.manual_seed(0)

    checks: list[dict[str, Any]] = []

    def config_only() -> dict[str, Any]:
        sam_cfg = SamConfig("vit_b")
        mobile_sam_cfg = SamConfig("mobile_sam")
        rtdetr_cfg = RTDETRConfig.from_name("rtdetr_r18vd", num_classes=3)
        eff_cfg = EfficientViTConfig.from_pretrained("b1", 224)
        return {
            "sam_model_types": [sam_cfg.model_type, mobile_sam_cfg.model_type],
            "rtdetr_model_type": str(rtdetr_cfg.model_type),
            "rtdetr_input_size": rtdetr_cfg.input_size,
            "efficientvit_checkpoint_configured": bool(eff_cfg.checkpoint),
            "kimi_vl_builder": KimiVLBuilder.__name__,
            "segmentation_builder_imported": SegmentationModelsBuilder.__name__,
            "onnx_classes_imported": [ONNXModule.__name__, ONNXSequential.__name__],
            "transpiler_functions": [hasattr(kornia, name) for name in ("to_numpy", "to_jax", "to_tensorflow")],
        }

    def vision_transformer_smoke() -> dict[str, Any]:
        model = VisionTransformer(image_size=32, patch_size=16, embed_dim=48, depth=1, num_heads=3)
        model = model.to(device=device, dtype=dtype).eval()
        x = torch.rand(1, 3, 32, 32, device=device, dtype=dtype)
        with torch.inference_mode():
            out = model(x)
        assert out.shape == (1, 5, 48)
        return {"output": _shape(out), "encoder_results": len(model.encoder_results)}

    def mobile_vit_smoke() -> dict[str, Any]:
        model = MobileViT(mode="xxs").to(device=device, dtype=dtype).eval()
        x = torch.rand(1, 3, 64, 64, device=device, dtype=dtype)
        with torch.inference_mode():
            out = model(x)
        return {"output": _shape(out)}

    def tiny_vit_smoke() -> dict[str, Any]:
        model = TinyViT(
            img_size=32,
            embed_dims=(16, 32, 64, 128),
            depths=(1, 1, 1, 1),
            num_heads=(1, 2, 4, 4),
            window_sizes=(4, 4, 4, 4),
            num_classes=7,
        )
        model = model.to(device=device, dtype=dtype).eval()
        x = torch.rand(1, 3, 32, 32, device=device, dtype=dtype)
        with torch.inference_mode():
            out = model(x)
        assert out.shape == (1, 7)
        return {"output": _shape(out)}

    def efficient_vit_smoke() -> dict[str, Any]:
        model = efficient_vit_backbone.efficientvit_backbone_b0().to(device=device, dtype=dtype).eval()
        x = torch.rand(1, 3, 32, 32, device=device, dtype=dtype)
        with torch.inference_mode():
            out = model(x)
        assert "input" in out and "stage_final" in out
        return {"input": _shape(out["input"]), "stage_final": _shape(out["stage_final"])}

    def kimi_vl_smoke() -> dict[str, Any]:
        vision_config = MoonViTConfig(
            image_size=32,
            patch_size=4,
            hidden_size=32,
            num_hidden_layers=1,
            num_attention_heads=4,
            intermediate_size=64,
        )
        projector_config = KimiVLProjectorConfig(input_dim=32, hidden_dim=64, output_dim=64)
        config = KimiVLConfig(vision_config=vision_config, projector_config=projector_config)
        model = KimiVLBuilder.from_config(config).to(device=device, dtype=dtype).eval()
        x = torch.rand(1, 3, 32, 32, device=device, dtype=dtype)
        with torch.inference_mode():
            out = model(x)
        assert out.shape == (1, 16, 64)
        return {"output": _shape(out)}

    def dexined_smoke() -> dict[str, Any]:
        model = DexiNed(pretrained=False).to(device=device, dtype=dtype).eval()
        x = torch.rand(1, 3, 32, 32, device=device, dtype=dtype)
        with torch.inference_mode():
            out = model(x)
        assert out.shape == (1, 1, 32, 32)
        return {"output": _shape(out)}

    def edge_detector_smoke() -> dict[str, Any]:
        model = EdgeDetectorBuilder.build(pretrained=False, image_size=32).to(device=device, dtype=dtype).eval()
        x = torch.rand(1, 3, 48, 40, device=device, dtype=dtype)
        with torch.inference_mode():
            out = model(x)
        return {"output": _shape(out)}

    def yunet_smoke() -> dict[str, Any]:
        model = YuNet("test", pretrained=False).to(device=device, dtype=dtype).eval()
        x = torch.rand(1, 3, 64, 64, device=device, dtype=dtype)
        with torch.inference_mode():
            out = model(x)
        return {"output": _shape(out)}

    def rtdetr_smoke() -> dict[str, Any]:
        model = RTDETR.from_config(RTDETRConfig("resnet18d", num_classes=3, head_num_queries=2))
        model = model.to(device=device, dtype=dtype).eval()
        x = torch.rand(1, 3, 32, 32, device=device, dtype=dtype)
        with torch.inference_mode():
            logits, boxes = model(x)
        assert logits.shape == (1, 2, 3)
        assert boxes.shape == (1, 2, 4)
        return {"logits": _shape(logits), "boxes": _shape(boxes)}

    def rtdetr_wrapper_smoke() -> dict[str, Any]:
        model = RTDETRDetectorBuilder.build(
            model_name="rtdetr_r18vd",
            pretrained=False,
            image_size=32,
        )
        model = model.to(device=device, dtype=dtype).eval()
        x = torch.rand(1, 3, 64, 64, device=device, dtype=dtype)
        with torch.inference_mode():
            out = model(x)
        return {"output": _shape(out)}

    def sam_build_inspection() -> dict[str, Any]:
        model = Sam.from_config(SamConfig("mobile_sam"))
        return {
            "model": type(model).__name__,
            "image_encoder_img_size": int(model.image_encoder.img_size),
            "forward_run": False,
        }

    for check_name, check_fn in (
        ("config-only imports", config_only),
        ("VisionTransformer small forward", vision_transformer_smoke),
        ("MobileViT small forward", mobile_vit_smoke),
        ("TinyViT small forward", tiny_vit_smoke),
        ("EfficientViT backbone small forward", efficient_vit_smoke),
        ("KimiVLBuilder small from_config forward", kimi_vl_smoke),
        ("DexiNed no-pretrained forward", dexined_smoke),
        ("EdgeDetectorBuilder no-pretrained wrapper", edge_detector_smoke),
        ("YuNet no-pretrained forward", yunet_smoke),
        ("RTDETR small raw forward", rtdetr_smoke),
        ("RTDETRDetectorBuilder no-pretrained wrapper", rtdetr_wrapper_smoke),
    ):
        _run_check(checks, check_name, check_fn)

    if args.include_sam_build:
        _run_check(checks, "Sam mobile_sam non-pretrained build", sam_build_inspection)

    failed = [item for item in checks if item["status"] != "ok"]
    payload = {
        "status": "failed" if failed else "ok",
        "kornia_version": getattr(kornia, "__version__", "unknown"),
        "torch_version": getattr(torch, "__version__", "unknown"),
        "device": str(device),
        "dtype": str(dtype),
        "optional_modules": optional,
        "checks": checks,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            "model_runtime_probe "
            f"{payload['status']}: kornia={payload['kornia_version']} "
            f"torch={payload['torch_version']} device={payload['device']} dtype={payload['dtype']}"
        )
        for item in checks:
            if item["status"] == "ok":
                print(f"  OK  {item['name']}: {item['detail']}")
            else:
                print(f"  ERR {item['name']}: {item['error']}")
        missing = [name for name, present in optional.items() if not present]
        print("optional modules missing: " + (", ".join(missing) if missing else "none"))

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
