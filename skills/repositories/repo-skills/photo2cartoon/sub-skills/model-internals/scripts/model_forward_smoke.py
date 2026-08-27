#!/usr/bin/env python3
"""Safe synthetic forward smoke for photo2cartoon model internals.

The script inspects source files from an explicit checkout root, runs synthetic
forward passes for the generator and discriminators, optionally validates a
checkpoint key map, and optionally checks the MobileFaceNet face-ID path.
It never downloads assets, trains, or writes outputs.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import types
from pathlib import Path
from typing import Any, Dict, Optional


MODULE_PREFIX = "_photo2cartoon_smoke"
FULL_CHECKPOINT_KEYS = {"genA2B", "genB2A", "disGA", "disGB", "disLA", "disLB"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a safe synthetic smoke for the photo2cartoon model stack: "
            "generator/discriminator tuples, checkpoint key maps, and optional "
            "face-ID embedding checks."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Checkout root that contains the source repo files to inspect.",
    )
    parser.add_argument(
        "--checkpoint",
        type=Path,
        help="Optional checkpoint file to inspect and load.",
    )
    parser.add_argument(
        "--checkpoint-mode",
        choices=("auto", "training", "generator"),
        default="auto",
        help="How to interpret the checkpoint key map.",
    )
    parser.add_argument(
        "--face-model",
        type=Path,
        help="Optional MobileFaceNet weight file used to verify the face-ID crop/112x112 embedding path.",
    )
    parser.add_argument(
        "--device",
        choices=("cpu", "cuda"),
        default="cpu",
        help="Device for the smoke run.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1,
        help="Synthetic batch size.",
    )
    parser.add_argument(
        "--input-size",
        type=int,
        default=32,
        help="Synthetic square generator input size. Use values divisible by 16.",
    )
    parser.add_argument(
        "--discriminator-input-size",
        type=int,
        default=256,
        help="Synthetic square discriminator input size. Use values divisible by 16.",
    )
    parser.add_argument(
        "--ngf",
        type=int,
        default=32,
        help="Generator base channels.",
    )
    parser.add_argument(
        "--ndf",
        type=int,
        default=32,
        help="Discriminator base channels.",
    )
    parser.add_argument(
        "--light",
        dest="light",
        action="store_true",
        default=True,
        help="Use the generator light path.",
    )
    parser.add_argument(
        "--full",
        dest="light",
        action="store_false",
        help="Use the generator full path.",
    )
    parser.add_argument(
        "--skip-utils",
        action="store_true",
        help="Skip optional utils smoke even if utils/utils.py is importable.",
    )
    return parser.parse_args()


def load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module {module_name} from {file_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def ensure_repo_layout(repo_root: Path) -> None:
    required = [
        repo_root / "models" / "networks.py",
        repo_root / "models" / "mobilefacenet.py",
        repo_root / "models" / "face_features.py",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit(
            "Missing expected source files under --repo-root: " + ", ".join(missing)
        )


def build_model_modules(repo_root: Path):
    models_dir = repo_root / "models"
    package_name = f"{MODULE_PREFIX}_models"
    package = types.ModuleType(package_name)
    package.__path__ = [str(models_dir)]
    sys.modules[package_name] = package

    mobilefacenet = load_module(f"{package_name}.mobilefacenet", models_dir / "mobilefacenet.py")
    networks = load_module(f"{package_name}.networks", models_dir / "networks.py")
    face_features = load_module(f"{package_name}.face_features", models_dir / "face_features.py")
    return networks, mobilefacenet, face_features


def load_optional_utils(repo_root: Path):
    utils_path = repo_root / "utils" / "utils.py"
    if not utils_path.exists():
        return None, "utils/utils.py is missing"
    try:
        utils_module = load_module(f"{MODULE_PREFIX}_utils", utils_path)
    except Exception as exc:  # pragma: no cover - exercised only when optional deps are present or absent
        return None, f"utils import skipped: {exc}"
    return utils_module, None


def build_models(torch, networks_module, args: argparse.Namespace, device):
    generator_img_size = args.input_size if not args.light else 256
    gen_a2b = networks_module.ResnetGenerator(
        ngf=args.ngf,
        img_size=generator_img_size,
        light=args.light,
    ).to(device)
    gen_b2a = networks_module.ResnetGenerator(
        ngf=args.ngf,
        img_size=generator_img_size,
        light=args.light,
    ).to(device)
    dis_ga = networks_module.Discriminator(input_nc=3, ndf=args.ndf, n_layers=7).to(device)
    dis_gb = networks_module.Discriminator(input_nc=3, ndf=args.ndf, n_layers=7).to(device)
    dis_la = networks_module.Discriminator(input_nc=3, ndf=args.ndf, n_layers=5).to(device)
    dis_lb = networks_module.Discriminator(input_nc=3, ndf=args.ndf, n_layers=5).to(device)

    for module in (gen_a2b, gen_b2a, dis_ga, dis_gb, dis_la, dis_lb):
        module.eval()

    return {
        "genA2B": gen_a2b,
        "genB2A": gen_b2a,
        "disGA": dis_ga,
        "disGB": dis_gb,
        "disLA": dis_la,
        "disLB": dis_lb,
    }


def apply_checkpoint(torch, checkpoint_path: Path, checkpoint_mode: str, models: Dict[str, Any], device):
    params = torch.load(str(checkpoint_path), map_location=device)
    if not isinstance(params, dict):
        raise SystemExit("Checkpoint must load as a dictionary of module state_dicts.")

    keys = set(params.keys())
    mode = checkpoint_mode

    if mode == "auto":
        if FULL_CHECKPOINT_KEYS.issubset(keys):
            mode = "training"
        elif keys == {"genA2B"}:
            mode = "generator"
        else:
            raise SystemExit(
                "Unrecognized checkpoint key map: " + ", ".join(sorted(keys))
            )

    if mode == "training":
        missing = FULL_CHECKPOINT_KEYS - keys
        if missing:
            raise SystemExit("Training checkpoint is missing keys: " + ", ".join(sorted(missing)))
        for key in sorted(FULL_CHECKPOINT_KEYS):
            models[key].load_state_dict(params[key])
    elif mode == "generator":
        if "genA2B" not in keys:
            raise SystemExit("Generator checkpoint is missing the 'genA2B' key.")
        models["genA2B"].load_state_dict(params["genA2B"])
    else:
        raise SystemExit(f"Unsupported checkpoint mode: {mode}")

    return {"mode": mode, "keys": sorted(keys)}


def crop_like_face_features(torch, batch_tensor):
    h, w = batch_tensor.shape[2:]
    top = int(h / 2.1 * (0.8 - 0.33))
    bottom = int(h - (h / 2.1 * 0.3))
    size = bottom - top
    left = int(w / 2 - size / 2)
    right = left + size
    return batch_tensor[:, :, top:bottom, left:right]


def run_model_smoke(torch, args: argparse.Namespace, device, models: Dict[str, Any]):
    if args.input_size % 16 != 0:
        raise SystemExit("--input-size must be divisible by 16 for the generator hourglass path.")
    if args.input_size < 32:
        raise SystemExit("--input-size must be at least 32 for the generator hourglass path.")
    if args.discriminator_input_size % 16 != 0:
        raise SystemExit("--discriminator-input-size must be divisible by 16 for the discriminator path.")
    if args.discriminator_input_size < 32:
        raise SystemExit("--discriminator-input-size must be at least 32 for the discriminator path.")

    x_gen = torch.randn(args.batch_size, 3, args.input_size, args.input_size, device=device)
    x_dis = torch.randn(
        args.batch_size,
        3,
        args.discriminator_input_size,
        args.discriminator_input_size,
        device=device,
    )

    with torch.no_grad():
        gen_out, gen_cam, gen_heat = models["genA2B"](x_gen)
        dis_g_out, dis_g_cam, dis_g_heat = models["disGA"](x_dis)
        dis_l_out, dis_l_cam, dis_l_heat = models["disLA"](x_dis)

    def tensor_stats(tensor):
        return {
            "shape": list(tensor.shape),
            "min": float(tensor.min().item()),
            "max": float(tensor.max().item()),
        }

    if list(gen_out.shape) != list(x_gen.shape):
        raise SystemExit(f"Generator output shape mismatch: {list(gen_out.shape)} != {list(x_gen.shape)}")
    if gen_cam.ndim != 2 or gen_cam.shape[1] != 2:
        raise SystemExit(f"Generator CAM logit shape mismatch: {list(gen_cam.shape)}")
    if gen_heat.ndim != 4 or gen_heat.shape[1] != 1:
        raise SystemExit(f"Generator heatmap shape mismatch: {list(gen_heat.shape)}")
    if not torch.isfinite(gen_out).all():
        raise SystemExit("Generator output contains non-finite values.")
    if gen_out.min().item() < -1.001 or gen_out.max().item() > 1.001:
        raise SystemExit("Generator output is outside the expected Tanh range.")

    for name, cam, heat, out in (
        ("disGA", dis_g_cam, dis_g_heat, dis_g_out),
        ("disLA", dis_l_cam, dis_l_heat, dis_l_out),
    ):
        if out.ndim != 4 or out.shape[1] != 1:
            raise SystemExit(f"{name} output shape mismatch: {list(out.shape)}")
        if cam.ndim != 2 or cam.shape[1] != 2:
            raise SystemExit(f"{name} CAM logit shape mismatch: {list(cam.shape)}")
        if heat.ndim != 4 or heat.shape[1] != 1:
            raise SystemExit(f"{name} heatmap shape mismatch: {list(heat.shape)}")
        if not torch.isfinite(out).all():
            raise SystemExit(f"{name} output contains non-finite values.")

    return {
        "generator_input": list(x_gen.shape),
        "discriminator_input": list(x_dis.shape),
        "generator": {
            "out": tensor_stats(gen_out),
            "cam_logit": tensor_stats(gen_cam),
            "heatmap": tensor_stats(gen_heat),
        },
        "disGA": {
            "out": tensor_stats(dis_g_out),
            "cam_logit": tensor_stats(dis_g_cam),
            "heatmap": tensor_stats(dis_g_heat),
        },
        "disLA": {
            "out": tensor_stats(dis_l_out),
            "cam_logit": tensor_stats(dis_l_cam),
            "heatmap": tensor_stats(dis_l_heat),
        },
    }


def run_face_id_smoke(torch, mobilefacenet_module, face_features_module, args: argparse.Namespace, device):
    if args.face_model is None:
        return {"status": "skipped", "reason": "no --face-model path was provided"}

    face_model_path = args.face_model
    if not face_model_path.exists():
        raise SystemExit(f"Face-ID model asset not found: {face_model_path}")

    # Try the source wrapper first so the smoke covers the repo's public API.
    wrapper_status = "source-wrapper"
    embedding = None
    source_input = torch.randn(1, 3, max(args.input_size, 256), max(args.input_size, 256), device=device)
    try:
        wrapper = face_features_module.FaceFeatures(str(face_model_path), device)
        with torch.no_grad():
            embedding = wrapper.infer(source_input)
    except Exception as exc:
        # Fall back to the underlying MobileFaceNet path with an explicit map_location.
        wrapper_status = f"fallback-manual-load ({exc})"
        state = torch.load(str(face_model_path), map_location=device)
        if isinstance(state, dict) and "state_dict" in state and isinstance(state["state_dict"], dict):
            state = state["state_dict"]
        model = mobilefacenet_module.MobileFaceNet(512).to(device)
        model.load_state_dict(state)
        model.eval()
        with torch.no_grad():
            cropped = crop_like_face_features(torch, source_input)
            cropped = torch.nn.functional.interpolate(
                cropped,
                size=[112, 112],
                mode="bilinear",
                align_corners=True,
            )
            embedding = model(cropped)

    norms = torch.norm(embedding, dim=1)
    cosine_self = 1 - torch.nn.functional.cosine_similarity(embedding, embedding)

    if embedding.ndim != 2 or embedding.shape[1] != 512:
        raise SystemExit(f"Face-ID embedding shape mismatch: {list(embedding.shape)}")

    return {
        "status": "passed",
        "path": str(face_model_path),
        "mode": wrapper_status,
        "input": list(source_input.shape),
        "embedding": {
            "shape": list(embedding.shape),
            "norms": [float(value) for value in norms.detach().cpu().tolist()],
            "self_cosine_distance": [float(value) for value in cosine_self.detach().cpu().tolist()],
        },
    }


def run_utils_smoke(torch, utils_module, args: argparse.Namespace):
    if utils_module is None:
        return {"status": "skipped", "reason": "optional utils module could not be imported"}

    import numpy as np

    values = np.array([0.0, 127.5, 255.0], dtype=np.float32)
    preprocessing = utils_module.preprocessing(values)
    denorm = utils_module.denorm(torch.tensor([-1.0, 0.0, 1.0], dtype=torch.float32).view(1, 3, 1, 1))
    tensor_np = utils_module.tensor2numpy(torch.zeros(3, 2, 2))
    cam_img = utils_module.cam(np.arange(16, dtype=np.float32).reshape(4, 4), size=8)
    rgb = np.array([[[10, 20, 30]]], dtype=np.uint8)
    rgb2bgr = utils_module.RGB2BGR(rgb)

    return {
        "status": "passed",
        "preprocessing": [float(value) for value in preprocessing.tolist()],
        "denorm": [float(value) for value in denorm.flatten().tolist()],
        "tensor2numpy_shape": list(tensor_np.shape),
        "cam": {
            "shape": list(cam_img.shape),
            "min": float(cam_img.min()),
            "max": float(cam_img.max()),
        },
        "rgb2bgr": rgb2bgr.reshape(-1).tolist(),
    }


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    ensure_repo_layout(repo_root)

    if args.device == "cuda":
        import torch
        if not torch.cuda.is_available():
            raise SystemExit("CUDA was requested but is not available in this environment.")
        device = torch.device("cuda")
    else:
        import torch
        device = torch.device("cpu")

    import torch.nn.functional as F  # noqa: F401 - used indirectly by imported modules

    torch.manual_seed(0)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(0)

    networks_module, mobilefacenet_module, face_features_module = build_model_modules(repo_root)
    utils_module, utils_skip_reason = load_optional_utils(repo_root)

    models = build_models(torch, networks_module, args, device)

    checkpoint_summary: Dict[str, Any] = {"status": "skipped"}
    if args.checkpoint is not None:
        if not args.checkpoint.exists():
            raise SystemExit(f"Checkpoint not found: {args.checkpoint}")
        checkpoint_summary = apply_checkpoint(
            torch,
            args.checkpoint,
            args.checkpoint_mode,
            models,
            device,
        )

    model_summary = run_model_smoke(torch, args, device, models)
    face_summary = run_face_id_smoke(torch, mobilefacenet_module, face_features_module, args, device)
    utils_summary = run_utils_smoke(torch, utils_module, args)
    if utils_summary.get("status") == "skipped" and utils_skip_reason:
        utils_summary["reason"] = utils_skip_reason

    summary = {
        "repo_root": str(repo_root),
        "device": str(device),
        "checkpoint": checkpoint_summary,
        "model_smoke": model_summary,
        "face_id_smoke": face_summary,
        "utils_smoke": utils_summary,
        "source_layout": {
            "models/networks.py": True,
            "models/mobilefacenet.py": True,
            "models/face_features.py": True,
            "utils/utils.py": (repo_root / "utils" / "utils.py").exists(),
        },
    }

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
