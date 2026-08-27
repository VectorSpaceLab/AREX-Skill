#!/usr/bin/env python3
"""Smoke safe interactive-deep-colorization core helpers.

The check imports source modules from a caller-supplied checkout and exercises
Lab/gamut helpers, image-prep helpers, and tiny PyTorch architecture forwards.
It deliberately avoids PyQt modules, Caffe prep_net calls, native notebooks,
repo GUI scripts, and downloaded model weights.
"""
from __future__ import annotations

import argparse
import contextlib
import importlib
import inspect
import io
import json
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List


def _shape(x: Any) -> List[int]:
    return [int(v) for v in getattr(x, "shape", ())]


def _sanitize(text: str, repo_root: Path | None = None) -> str:
    out = text or ""
    if repo_root is not None:
        try:
            out = out.replace(str(repo_root.resolve()), "<repo-root>")
        except Exception:
            pass
    return out


def _require_repo_root(repo_root: Path) -> None:
    required = [
        "data/colorize_image.py",
        "data/lab_gamut.py",
        "models/pytorch/model.py",
    ]
    missing = [rel for rel in required if not (repo_root / rel).is_file()]
    if missing:
        raise FileNotFoundError("missing expected file(s) under --repo-root: " + ", ".join(missing))


def _import_source(repo_root: Path) -> Dict[str, Any]:
    sys.path.insert(0, str(repo_root))
    imported = {}
    for mod_name in ("data.colorize_image", "data.lab_gamut", "models.pytorch.model"):
        imported[mod_name] = importlib.import_module(mod_name)
    return imported


def run_smoke(repo_root: Path, size: int, skip_torch_forward: bool = False) -> Dict[str, Any]:
    if size < 8 or size % 8 != 0:
        raise ValueError("--size must be a multiple of 8 and at least 8 for the PyTorch downsample/upsample smoke")

    _require_repo_root(repo_root)
    modules = _import_source(repo_root)
    CI = modules["data.colorize_image"]
    lab_gamut = modules["data.lab_gamut"]
    torch_model = modules["models.pytorch.model"]

    import numpy as np

    report: Dict[str, Any] = {
        "status": "ok",
        "repo_root_supplied": True,
        "size": size,
        "avoided": ["PyQt imports", "Caffe prep_net", "model weight loading", "native notebooks/examples"],
        "imports": sorted(modules.keys()),
        "signatures": {},
        "lab_gamut": {},
        "image_helpers": {},
        "pytorch_forward": {},
        "distribution_helpers": {},
        "captured_source_stdout_lines": 0,
    }

    signature_targets = [
        ("ColorizeImageBase", CI.ColorizeImageBase),
        ("ColorizeImageTorch", CI.ColorizeImageTorch),
        ("ColorizeImageTorchDist", CI.ColorizeImageTorchDist),
        ("ColorizeImageCaffe", CI.ColorizeImageCaffe),
        ("ColorizeImageCaffeDist", CI.ColorizeImageCaffeDist),
        ("ColorizeImageCaffeGlobDist", CI.ColorizeImageCaffeGlobDist),
        ("ColorizeImageTorch.prep_net", CI.ColorizeImageTorch.prep_net),
        ("SIGGRAPHGenerator", torch_model.SIGGRAPHGenerator),
        ("SIGGRAPHGenerator.forward", torch_model.SIGGRAPHGenerator.forward),
    ]
    report["signatures"] = {name: str(inspect.signature(obj)) for name, obj in signature_targets}

    rgb = np.array([128, 64, 32], dtype=np.uint8)
    lab = lab_gamut.rgb2lab_1d(rgb)
    rgb_back = lab_gamut.lab2rgb_1d(lab)
    snapped_rgb = lab_gamut.snap_ab(50, rgb, return_type="rgb")
    snapped_lab = lab_gamut.snap_ab(50, rgb, return_type="lab")
    grid = lab_gamut.abGrid(gamut_size=10, D=10)
    ab_map, mask = grid.update_gamut(l_in=50)
    xy = grid.ab2xy(0, 0)
    ab = grid.xy2ab(*xy)
    report["lab_gamut"] = {
        "rgb2lab_shape": _shape(lab),
        "lab2rgb_shape": _shape(rgb_back),
        "snap_rgb_shape": _shape(snapped_rgb),
        "snap_lab_shape": _shape(snapped_lab),
        "snap_lab_L_approx": float(snapped_lab[0]),
        "ab_grid_map_shape": _shape(ab_map),
        "ab_grid_mask_shape": _shape(mask),
        "ab_xy_roundtrip": {"xy_for_0_0": [int(xy[0]), int(xy[1])], "ab_back": [int(ab[0]), int(ab[1])]},
        "finite": bool(np.isfinite(lab).all() and np.isfinite(snapped_lab).all()),
    }

    # Build a deterministic synthetic RGB image. This tests source image/Lab
    # helpers without reading fixture bytes.
    ramp = np.linspace(0, 255, size, dtype=np.uint8)
    synthetic_rgb = np.stack(
        [
            np.tile(ramp[None, :], (size, 1)),
            np.tile(ramp[:, None], (1, size)),
            np.full((size, size), 127, dtype=np.uint8),
        ],
        axis=2,
    )

    source_stdout = io.StringIO()
    with contextlib.redirect_stdout(source_stdout):
        color_wrapper = CI.ColorizeImageTorch(Xd=size, maskcent=False)
        color_wrapper.set_image(synthetic_rgb)
    report["image_helpers"] = {
        "img_rgb_shape": _shape(color_wrapper.img_rgb),
        "img_l_shape": _shape(color_wrapper.img_l),
        "img_ab_shape": _shape(color_wrapper.img_ab),
        "img_gray_shape": _shape(color_wrapper.get_img_gray()),
        "img_gray_fullres_shape": _shape(color_wrapper.get_img_gray_fullres()),
        "mask_mult": float(color_wrapper.mask_mult),
        "mask_cent": float(color_wrapper.mask_cent),
    }

    if skip_torch_forward:
        report["pytorch_forward"] = {"skipped": True}
        report["distribution_helpers"] = {"skipped": True}
    else:
        import torch

        input_ab = np.zeros((2, size, size), dtype=np.float32)
        input_mask = np.zeros((1, size, size), dtype=np.float32)
        with torch.no_grad(), contextlib.redirect_stdout(source_stdout):
            net = torch_model.SIGGRAPHGenerator(dist=False).eval()
            raw_out = net.forward(color_wrapper.img_l_mc, input_ab, input_mask, maskcent=0)
            color_wrapper.net = net
            color_wrapper.net_set = True
            wrapper_out = color_wrapper.net_forward(input_ab, input_mask)
        report["pytorch_forward"] = {
            "siggraph_dist_false_shape": _shape(raw_out),
            "wrapper_output_rgb_shape": _shape(wrapper_out),
            "wrapper_output_ab_shape": _shape(color_wrapper.output_ab),
            "wrapper_output_rgb_dtype": str(wrapper_out.dtype),
        }

        with torch.no_grad(), contextlib.redirect_stdout(source_stdout):
            dist_wrapper = CI.ColorizeImageTorchDist(Xd=size, maskcent=False)
            dist_wrapper.set_image(synthetic_rgb)
            dist_wrapper.net = torch_model.SIGGRAPHGenerator(dist=True).eval()
            dist_wrapper.net_set = True
            dist_return = dist_wrapper.net_forward(input_ab, input_mask)
        np.random.seed(7)
        with contextlib.redirect_stdout(source_stdout):
            rec_ab, rec_conf = dist_wrapper.get_ab_reccs(
                h=size // 2,
                w=size // 2,
                K=2,
                N=200,
                return_conf=True,
            )
        report["distribution_helpers"] = {
            "dist_return_shape": _shape(dist_return),
            "dist_ab_shape": _shape(dist_wrapper.dist_ab),
            "dist_ab_full_shape": _shape(dist_wrapper.dist_ab_full),
            "dist_ab_grid_shape": _shape(dist_wrapper.dist_ab_grid),
            "get_ab_reccs_shape": _shape(rec_ab),
            "get_ab_reccs_conf_shape": _shape(rec_conf),
            "get_ab_reccs_conf_sum": float(np.sum(rec_conf)),
            "dist_ab_set": bool(dist_wrapper.dist_ab_set),
        }

    captured = source_stdout.getvalue().splitlines()
    report["captured_source_stdout_lines"] = len(captured)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run safe source-level smoke checks for interactive-deep-colorization core helpers."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="repository checkout root containing data/ and models/pytorch/ modules",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=8,
        help="tiny square working size for helper and PyTorch architecture checks; must be a multiple of 8",
    )
    parser.add_argument(
        "--skip-torch-forward",
        action="store_true",
        help="skip random-weight SIGGRAPHGenerator forward checks",
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    try:
        report = run_smoke(repo_root=repo_root, size=args.size, skip_torch_forward=args.skip_torch_forward)
    except Exception as exc:  # keep errors concise and avoid absolute path leakage
        error = {
            "status": "error",
            "error_type": exc.__class__.__name__,
            "error": _sanitize(str(exc), repo_root),
            "traceback_tail": _sanitize("\n".join(traceback.format_exc().splitlines()[-5:]), repo_root),
        }
        if args.json:
            print(json.dumps(error, indent=2, sort_keys=True))
        else:
            print(f"ERROR [{error['error_type']}]: {error['error']}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("safe core helper smoke: ok")
        print(f"imports: {', '.join(report['imports'])}")
        print(f"size: {report['size']}")
        print(f"ColorizeImageTorch image L shape: {report['image_helpers']['img_l_shape']}")
        if report["pytorch_forward"].get("skipped"):
            print("PyTorch forward: skipped")
        else:
            print(f"SIGGRAPHGenerator(dist=False): {report['pytorch_forward']['siggraph_dist_false_shape']}")
            print(f"ColorizeImageTorch output RGB: {report['pytorch_forward']['wrapper_output_rgb_shape']}")
            print(f"distribution branch: {report['distribution_helpers']['dist_ab_shape']}")
            print(f"recommendations: {report['distribution_helpers']['get_ab_reccs_shape']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
