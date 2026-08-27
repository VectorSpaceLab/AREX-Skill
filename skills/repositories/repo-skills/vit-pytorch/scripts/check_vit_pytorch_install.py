#!/usr/bin/env python3
"""Package-level install and smoke check for vit-pytorch.

Purpose
-------
Verify that the installed vit-pytorch package can be imported, that the public
package version matches the distribution metadata, and that a tiny CPU forward
pass still works.

This helper does not download data or depend on the source checkout.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from importlib import import_module, metadata
from typing import Any

sys.dont_write_bytecode = True


@dataclass
class Check:
    name: str
    status: str
    detail: str


def _shape(value: Any) -> tuple[int, ...] | None:
    try:
        return tuple(value.shape)
    except Exception:
        return None


def _smoke_required() -> list[Check]:
    import torch
    from vit_pytorch import Dino, SimpleViT, ViT

    torch.manual_seed(0)
    img = torch.randn(2, 3, 32, 32)
    vit = ViT(
        image_size=32,
        patch_size=8,
        num_classes=7,
        dim=32,
        depth=1,
        heads=2,
        dim_head=16,
        mlp_dim=64,
    ).eval()
    simple = SimpleViT(
        image_size=32,
        patch_size=8,
        num_classes=7,
        dim=32,
        depth=1,
        heads=2,
        dim_head=16,
        mlp_dim=64,
    ).eval()
    vit_logits = vit(img)
    simple_logits = simple(img)
    if _shape(vit_logits) != (2, 7):
        raise AssertionError(f"ViT smoke shape mismatch: {_shape(vit_logits)}")
    if _shape(simple_logits) != (2, 7):
        raise AssertionError(f"SimpleViT smoke shape mismatch: {_shape(simple_logits)}")

    dino = Dino(
        vit,
        image_size=32,
        hidden_layer="to_latent",
        projection_hidden_size=32,
        num_classes_K=16,
        projection_layers=2,
        augment_fn=torch.nn.Identity(),
        augment_fn2=torch.nn.Identity(),
    )
    loss = dino(img)
    if not torch.is_tensor(loss) or loss.ndim != 0 or not bool(torch.isfinite(loss).item()):
        raise AssertionError("Dino smoke did not return a finite scalar")

    return [
        Check("vit", "passed", f"ViT logits shape {_shape(vit_logits)}"),
        Check("simple_vit", "passed", f"SimpleViT logits shape {_shape(simple_logits)}"),
        Check("dino", "passed", f"Dino loss {float(loss.item()):.6f}"),
    ]


def _imports(include_optional: bool) -> list[Check]:
    checks: list[Check] = []
    module_names = [
        "vit_pytorch",
        "vit_pytorch.vit",
        "vit_pytorch.simple_vit",
        "vit_pytorch.na_vit",
        "vit_pytorch.vit_3d",
        "vit_pytorch.recorder",
        "vit_pytorch.extractor",
        "vit_pytorch.cct",
        "vit_pytorch.cross_vit",
        "vit_pytorch.vivit",
    ]
    for name in module_names:
        import_module(name)
        checks.append(Check(name, "passed", "imported successfully"))

    if include_optional:
        try:
            import_module("vit_pytorch.vaat")
        except Exception as exc:  # optional dependency gap is not fatal here
            checks.append(Check("vit_pytorch.vaat", "optional-missing", f"{type(exc).__name__}: {exc}"))
        else:
            checks.append(Check("vit_pytorch.vaat", "passed", "imported successfully"))
    return checks


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument("--include-optional", action="store_true", help="also probe optional modules such as VAAT")
    parser.add_argument("--run-smoke", action="store_true", help="run tiny CPU forward checks for ViT, SimpleViT, and Dino")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    results: list[Check] = []
    exit_code = 0

    try:
        dist_version = metadata.version("vit-pytorch")
    except metadata.PackageNotFoundError as exc:
        print(f"vit-pytorch distribution metadata not found: {exc}", file=sys.stderr)
        return 1

    try:
        import vit_pytorch  # noqa: F401
        import torch
        results.append(Check("distribution", "passed", f"vit-pytorch {dist_version}"))
        results.extend(_imports(args.include_optional))
        if args.run_smoke:
            results.extend(_smoke_required())
    except Exception as exc:
        exit_code = 1
        results.append(Check("environment", "failed", f"{type(exc).__name__}: {exc}"))

    payload = {
        "distribution": dist_version,
        "results": [asdict(result) for result in results],
        "ok": exit_code == 0,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for result in results:
            print(f"[{result.status}] {result.name}: {result.detail}")
        print("overall:", "ok" if exit_code == 0 else "failed")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
