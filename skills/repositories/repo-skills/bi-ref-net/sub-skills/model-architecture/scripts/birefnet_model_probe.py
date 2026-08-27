#!/usr/bin/env python3
"""Safe BiRefNet model/helper probe.

This script is intentionally safe from arbitrary current working directories:
- it never adds the current working directory to sys.path;
- it imports BiRefNet source code only from an explicit --repo-root;
- the default run performs no model or backbone weight downloads;
- --construct-model instantiates BiRefNet(bb_pretrained=False) only.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Iterator, Optional, Tuple


def clean_state_dict_keys(
    state_dict: Dict[str, Any],
    unwanted_prefixes: Iterable[str] = ("module.", "_orig_mod."),
) -> Dict[str, Any]:
    """Local mirror of BiRefNet's prefix cleanup for default offline probing."""
    for key in list(state_dict.keys()):
        prefix_length = 0
        for unwanted_prefix in unwanted_prefixes:
            if key[prefix_length:].startswith(unwanted_prefix):
                prefix_length += len(unwanted_prefix)
        state_dict[key[prefix_length:]] = state_dict.pop(key)
    return state_dict


@contextlib.contextmanager
def explicit_repo_context(repo_root_arg: str) -> Iterator[Path]:
    """Temporarily import from an explicit BiRefNet repository root only."""
    repo_root = Path(repo_root_arg).expanduser().resolve()
    if not (repo_root / "models" / "birefnet.py").is_file():
        raise FileNotFoundError(
            f"--repo-root must point to a BiRefNet checkout containing models/birefnet.py: {repo_root}"
        )

    old_sys_path = list(sys.path)
    old_cwd = os.getcwd()
    try:
        sys.path.insert(0, str(repo_root))
        os.chdir(str(repo_root))
        yield repo_root
    finally:
        sys.path[:] = old_sys_path
        os.chdir(old_cwd)


def local_image2patches(image: Any, grid_h: int = 2, grid_w: int = 2, patch_ref: Optional[Any] = None) -> Any:
    """Default image2patches behavior implemented with torch tensor ops."""
    if patch_ref is not None:
        grid_h = image.shape[-2] // patch_ref.shape[-2]
        grid_w = image.shape[-1] // patch_ref.shape[-1]
    b, c, height, width = image.shape
    if height % grid_h or width % grid_w:
        raise ValueError(f"image shape {(height, width)} is not divisible by grid {(grid_h, grid_w)}")
    patch_h = height // grid_h
    patch_w = width // grid_w
    return (
        image.reshape(b, c, grid_h, patch_h, grid_w, patch_w)
        .permute(0, 2, 4, 1, 3, 5)
        .reshape(b * grid_h * grid_w, c, patch_h, patch_w)
    )


def local_patches2image(patches: Any, grid_h: int = 2, grid_w: int = 2, patch_ref: Optional[Any] = None) -> Any:
    """Default patches2image behavior implemented with torch tensor ops."""
    if patch_ref is not None:
        grid_h = patch_ref.shape[-2] // patches[0].shape[-2]
        grid_w = patch_ref.shape[-1] // patches[0].shape[-1]
    patch_batch, c, patch_h, patch_w = patches.shape
    if patch_batch % (grid_h * grid_w):
        raise ValueError(f"patch batch {patch_batch} is not divisible by grid_h*grid_w={grid_h * grid_w}")
    b = patch_batch // (grid_h * grid_w)
    return (
        patches.reshape(b, grid_h, grid_w, c, patch_h, patch_w)
        .permute(0, 3, 1, 4, 2, 5)
        .reshape(b, c, grid_h * patch_h, grid_w * patch_w)
    )


def prefix_probe(check_state_dict_func: Callable[[Dict[str, Any]], Dict[str, Any]]) -> Dict[str, Any]:
    sample = {
        "module._orig_mod.bb.weight": 1,
        "_orig_mod.decoder.bias": 2,
        "plain.weight": 3,
    }
    cleaned = check_state_dict_func(dict(sample))
    return {
        "input_keys": list(sample.keys()),
        "cleaned_keys": sorted(cleaned.keys()),
        "passed": sorted(cleaned.keys()) == ["bb.weight", "decoder.bias", "plain.weight"],
    }


def patch_roundtrip_probe(
    image2patches_func: Callable[..., Any],
    patches2image_func: Callable[..., Any],
) -> Dict[str, Any]:
    try:
        import torch
    except Exception as exc:  # pragma: no cover - environment dependent
        return {
            "passed": False,
            "skipped": True,
            "reason": "torch is not importable; install torch to run patch-helper tensor checks",
            "error": repr(exc),
        }

    image = torch.arange(1 * 3 * 8 * 12, dtype=torch.float32).reshape(1, 3, 8, 12)
    patches = image2patches_func(image, grid_h=2, grid_w=3)
    reconstructed = patches2image_func(patches, grid_h=2, grid_w=3)
    ref = torch.zeros(1, 3, 4, 4)
    patches_from_ref = image2patches_func(image, patch_ref=ref)
    return {
        "passed": bool(torch.equal(image, reconstructed)),
        "image_shape": list(image.shape),
        "patches_shape": list(patches.shape),
        "reconstructed_shape": list(reconstructed.shape),
        "patch_ref_shape": list(ref.shape),
        "patches_from_ref_shape": list(patches_from_ref.shape),
    }


def import_source_helpers(repo_root: str) -> Tuple[Dict[str, Any], Optional[Callable[..., Any]], Optional[Callable[..., Any]], Optional[Callable[..., Any]]]:
    info: Dict[str, Any] = {"repo_import": "requested"}
    check_state_dict_func: Optional[Callable[..., Any]] = None
    image2patches_func: Optional[Callable[..., Any]] = None
    patches2image_func: Optional[Callable[..., Any]] = None

    try:
        with explicit_repo_context(repo_root):
            try:
                from utils import check_state_dict  # type: ignore

                check_state_dict_func = check_state_dict
                info["utils.check_state_dict"] = "imported"
            except Exception as exc:
                info["utils.check_state_dict"] = {
                    "status": "failed",
                    "error": repr(exc),
                    "hint": "Install BiRefNet's Python dependencies if source helper imports are required.",
                }

            try:
                from models.birefnet import image2patches, patches2image  # type: ignore

                image2patches_func = image2patches
                patches2image_func = patches2image
                info["models.birefnet.patch_helpers"] = "imported"
            except Exception as exc:
                info["models.birefnet.patch_helpers"] = {
                    "status": "failed",
                    "error": repr(exc),
                    "hint": "Missing dependencies commonly include torch, torchvision, einops, kornia, timm, or huggingface_hub.",
                }
    except Exception as exc:
        info["repo_import"] = {"status": "failed", "error": repr(exc)}

    return info, check_state_dict_func, image2patches_func, patches2image_func


def construct_model_probe(repo_root: str) -> Dict[str, Any]:
    try:
        with explicit_repo_context(repo_root):
            from models.birefnet import BiRefNet  # type: ignore

            model = BiRefNet(bb_pretrained=False)
            config = getattr(model, "config", None)
            total_params = sum(parameter.numel() for parameter in model.parameters())
            return {
                "requested": True,
                "passed": True,
                "class": type(model).__name__,
                "bb_pretrained": False,
                "training_mode_initial": bool(model.training),
                "parameter_count": int(total_params),
                "config": {
                    "bb": getattr(config, "bb", None),
                    "model": getattr(config, "model", None),
                    "size": list(getattr(config, "size", [])) if getattr(config, "size", None) else None,
                    "dec_att": getattr(config, "dec_att", None),
                    "mul_scl_ipt": getattr(config, "mul_scl_ipt", None),
                    "dec_ipt": getattr(config, "dec_ipt", None),
                    "ms_supervision": getattr(config, "ms_supervision", None),
                    "out_ref": getattr(config, "out_ref", None),
                },
            }
    except Exception as exc:  # pragma: no cover - environment dependent
        return {
            "requested": True,
            "passed": False,
            "error": repr(exc),
            "traceback_tail": traceback.format_exc(limit=5).splitlines()[-12:],
            "hint": "This optional construction uses BiRefNet(bb_pretrained=False), so failures usually indicate missing Python dependencies or architecture source import errors rather than missing backbone weights.",
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Safely probe BiRefNet state-dict prefix cleanup, patch helpers, and optional model construction.",
    )
    parser.add_argument(
        "--repo-root",
        type=str,
        default=None,
        help="Explicit BiRefNet repository root to import source helpers from. The current working directory is never used implicitly.",
    )
    parser.add_argument(
        "--construct-model",
        action="store_true",
        help="Optionally instantiate BiRefNet(bb_pretrained=False). This does not download backbone weights but can use significant CPU memory.",
    )
    parser.add_argument(
        "--skip-model",
        action="store_true",
        help="Force skipping model construction even if --construct-model is present.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON only.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result: Dict[str, Any] = {
        "script": "birefnet_model_probe.py",
        "repo_root_supplied": bool(args.repo_root),
        "downloads": "none; default checks do not construct models or request pretrained backbones",
    }

    check_state_dict_func: Callable[[Dict[str, Any]], Dict[str, Any]] = clean_state_dict_keys
    image2patches_func: Callable[..., Any] = local_image2patches
    patches2image_func: Callable[..., Any] = local_patches2image

    if args.repo_root:
        source_info, source_check, source_i2p, source_p2i = import_source_helpers(args.repo_root)
        result["source_import"] = source_info
        if source_check is not None:
            check_state_dict_func = source_check
        if source_i2p is not None and source_p2i is not None:
            image2patches_func = source_i2p
            patches2image_func = source_p2i
    else:
        result["source_import"] = "skipped; pass --repo-root to import BiRefNet source helpers"

    result["prefix_cleanup_probe"] = prefix_probe(check_state_dict_func)
    result["patch_roundtrip_probe"] = patch_roundtrip_probe(image2patches_func, patches2image_func)

    if args.construct_model and not args.skip_model:
        if not args.repo_root:
            result["model_construction"] = {
                "requested": True,
                "passed": False,
                "error": "--construct-model requires --repo-root so imports are explicit",
            }
        else:
            result["model_construction"] = construct_model_probe(args.repo_root)
    else:
        result["model_construction"] = "skipped; pass --construct-model with --repo-root to instantiate BiRefNet(bb_pretrained=False)"

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("BiRefNet model probe")
        print(json.dumps(result, indent=2, sort_keys=True))
        if not args.repo_root:
            print("\nHint: pass --repo-root to import source helpers. Without it, this script uses local mirrored logic only.")
        if args.construct_model and args.skip_model:
            print("Hint: --skip-model took precedence over --construct-model.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
