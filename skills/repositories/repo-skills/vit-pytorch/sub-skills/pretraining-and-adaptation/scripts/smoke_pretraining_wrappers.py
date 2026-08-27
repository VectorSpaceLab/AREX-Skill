#!/usr/bin/env python3
"""
Tiny CPU smoke checks for vit-pytorch pretraining and adaptation wrappers.

The checks use random tensors only: no downloads, datasets, credentials, W&B,
Accelerate, or pretrained checkpoints. They are intended to answer two questions:

1. Which wrappers produce a finite one-step loss/logit result in this runtime?
2. Do known version-fragile wrappers (MAE, SimMIM, MPP) still fail with current
   ViT token / positional-embedding assumptions, or has the installed package
   fixed them?

Examples:
    python smoke_pretraining_wrappers.py
    python smoke_pretraining_wrappers.py --json
    python smoke_pretraining_wrappers.py --case distill --case dino
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Result:
    case: str
    status: str
    summary: str
    details: dict[str, Any] = field(default_factory=dict)


CASE_ORDER = [
    "distill",
    "mp3",
    "dino",
    "esvit",
    "learnable-memory",
    "lejepa",
    "vat",
    "vat-siglip",
    "wwt",
    "vit-with-decorr",
    "mae",
    "simmim",
    "mpp",
    "vaat-import",
]

VERSION_FRAGILE = {"mae", "simmim", "mpp"}
OPTIONAL_DEPENDENCIES = {
    "dino": ("torchvision",),
    "esvit": ("torchvision",),
    "lejepa": ("torchvision",),
    "vaat-import": ("torchaudio",),
}


def _jsonable(value: Any) -> Any:
    try:
        import torch

        if torch.is_tensor(value):
            if value.ndim == 0:
                return float(value.detach().cpu())
            return list(value.shape)
    except Exception:
        pass
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, tuple):
        return [_jsonable(v) for v in value]
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    return repr(value)


def _finite_scalar(t: Any) -> bool:
    import torch

    return torch.is_tensor(t) and t.ndim == 0 and bool(torch.isfinite(t).item())


def _finite_tensor(t: Any) -> bool:
    import torch

    return torch.is_tensor(t) and bool(torch.isfinite(t).all().item())


def _base_vit(image_size: int = 16, patch_size: int = 8, dim: int = 32, depth: int = 1, num_classes: int = 5):
    from vit_pytorch import ViT

    return ViT(
        image_size=image_size,
        patch_size=patch_size,
        num_classes=num_classes,
        dim=dim,
        depth=depth,
        heads=2,
        dim_head=16,
        mlp_dim=64,
    )


def _distill() -> dict[str, Any]:
    import torch
    from torch import nn
    from vit_pytorch.distill import DistillableViT, DistillWrapper

    class TinyTeacher(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.net = nn.Sequential(nn.Flatten(), nn.Linear(3 * 16 * 16, 5))

        def forward(self, x):
            return self.net(x)

    student = DistillableViT(
        image_size=16,
        patch_size=8,
        num_classes=5,
        dim=32,
        depth=1,
        heads=2,
        dim_head=16,
        mlp_dim=64,
    )
    teacher = TinyTeacher()
    wrapper = DistillWrapper(student=student, teacher=teacher, temperature=2.0, alpha=0.5)
    images = torch.randn(2, 3, 16, 16)
    labels = torch.randint(0, 5, (2,))
    loss = wrapper(images, labels)
    loss.backward()
    logits = student.to_vit()(images)
    assert _finite_scalar(loss), "distillation loss is not a finite scalar"
    assert tuple(logits.shape) == (2, 5), f"unexpected converted ViT logits shape {tuple(logits.shape)}"
    return {"loss": loss, "logits_shape": tuple(logits.shape)}


def _mae() -> dict[str, Any]:
    import torch
    from vit_pytorch import MAE

    encoder = _base_vit()
    learner = MAE(encoder=encoder, decoder_dim=16, masking_ratio=0.5, decoder_depth=1, decoder_heads=2, decoder_dim_head=8)
    loss = learner(torch.randn(2, 3, 16, 16))
    loss.backward()
    assert _finite_scalar(loss), "MAE loss is not a finite scalar"
    return {"loss": loss}


def _simmim() -> dict[str, Any]:
    import torch
    from vit_pytorch.simmim import SimMIM

    learner = SimMIM(encoder=_base_vit(), masking_ratio=0.5)
    loss = learner(torch.randn(2, 3, 16, 16))
    loss.backward()
    assert _finite_scalar(loss), "SimMIM loss is not a finite scalar"
    return {"loss": loss}


def _mpp() -> dict[str, Any]:
    import torch
    from vit_pytorch.mpp import MPP

    encoder = _base_vit(dim=32)
    learner = MPP(transformer=encoder, patch_size=8, dim=32, mask_prob=0.5, replace_prob=0.5, random_patch_prob=0.25)
    loss = learner(torch.rand(2, 3, 16, 16))
    loss.backward()
    assert _finite_scalar(loss), "MPP loss is not a finite scalar"
    return {"loss": loss}


def _mp3() -> dict[str, Any]:
    import torch
    from vit_pytorch.mp3 import ViT, MP3

    vit = ViT(image_size=16, patch_size=8, num_classes=5, dim=32, depth=1, heads=2, dim_head=16, mlp_dim=64)
    learner = MP3(vit=vit, masking_ratio=0.5)
    loss = learner(torch.randn(2, 3, 16, 16))
    loss.backward()
    assert _finite_scalar(loss), "MP3 loss is not a finite scalar"
    return {"loss": loss}


def _dino() -> dict[str, Any]:
    import torch
    from torch import nn
    from vit_pytorch import Dino

    model = _base_vit()
    learner = Dino(
        model,
        image_size=16,
        hidden_layer="to_latent",
        projection_hidden_size=32,
        num_classes_K=16,
        projection_layers=2,
        augment_fn=nn.Identity(),
        augment_fn2=nn.Identity(),
    )
    loss = learner(torch.randn(2, 3, 16, 16))
    loss.backward()
    learner.update_moving_average()
    embedding = learner(torch.randn(2, 3, 16, 16), return_embedding=True, return_projection=False)
    assert _finite_scalar(loss), "DINO loss is not a finite scalar"
    assert tuple(embedding.shape) == (2, 32), f"unexpected DINO embedding shape {tuple(embedding.shape)}"
    return {"loss": loss, "embedding_shape": tuple(embedding.shape)}


def _esvit() -> dict[str, Any]:
    import torch
    from torch import nn
    from vit_pytorch.cvt import CvT
    from vit_pytorch.es_vit import EsViTTrainer

    cvt = CvT(
        num_classes=5,
        s1_emb_dim=16,
        s1_emb_kernel=3,
        s1_emb_stride=2,
        s1_proj_kernel=3,
        s1_kv_proj_stride=1,
        s1_heads=1,
        s1_depth=1,
        s1_mlp_mult=2,
        s2_emb_dim=24,
        s2_emb_kernel=3,
        s2_emb_stride=2,
        s2_proj_kernel=3,
        s2_kv_proj_stride=1,
        s2_heads=1,
        s2_depth=1,
        s2_mlp_mult=2,
        s3_emb_dim=32,
        s3_emb_kernel=3,
        s3_emb_stride=2,
        s3_proj_kernel=3,
        s3_kv_proj_stride=1,
        s3_heads=1,
        s3_depth=1,
        s3_mlp_mult=2,
        dropout=0.0,
    )
    learner = EsViTTrainer(
        cvt,
        image_size=32,
        hidden_layer="layers",
        projection_hidden_size=32,
        num_classes_K=16,
        projection_layers=2,
        augment_fn=nn.Identity(),
        augment_fn2=nn.Identity(),
    )
    loss = learner(torch.randn(2, 3, 32, 32))
    loss.backward()
    learner.update_moving_average()
    assert _finite_scalar(loss), "EsViT loss is not a finite scalar"
    return {"loss": loss}


def _learnable_memory() -> dict[str, Any]:
    import torch
    from vit_pytorch.learnable_memory_vit import ViT, Adapter

    vit = ViT(image_size=16, patch_size=8, num_classes=5, dim=32, depth=1, heads=2, dim_head=16, mlp_dim=64)
    adapter = Adapter(vit=vit, num_classes=3, num_memories_per_layer=2)
    logits = adapter(torch.randn(2, 3, 16, 16))
    logits.mean().backward()
    assert tuple(logits.shape) == (2, 3), f"unexpected adapter logits shape {tuple(logits.shape)}"
    assert _finite_tensor(logits), "adapter logits contain non-finite values"
    return {"logits_shape": tuple(logits.shape)}


def _lejepa() -> dict[str, Any]:
    import torch
    from torch import nn
    from vit_pytorch.lejepa import LeJEPA

    learner = LeJEPA(
        _base_vit(),
        image_size=16,
        hidden_layer="to_latent",
        projection_hidden_size=32,
        num_classes_K=16,
        projection_layers=2,
        sigreg_loss_kwargs={"num_slices": 16, "domain": (-2, 2), "num_knots": 5},
        augment_fn=nn.Identity(),
        augment_fn2=nn.Identity(),
    )
    loss = learner(torch.randn(2, 3, 16, 16))
    loss.backward()
    assert _finite_scalar(loss), "LeJEPA loss is not a finite scalar"
    return {"loss": loss}


def _vat() -> dict[str, Any]:
    import torch
    from vit_pytorch.vat import ViT, VAT

    vit = ViT(image_size=16, patch_size=8, num_classes=5, dim=32, depth=1, heads=2, dim_head=16, mlp_dim=64)
    model = VAT(vit, dim=32, depth=1, heads=2, dim_head=16, dim_action=4, mlp_dim=64, action_chunk_len=3)
    images = torch.randn(2, 1, 3, 16, 16)  # explicit singleton view dimension
    actions = torch.randn(2, 3, 4)
    loss = model(images, actions=actions, freeze_vit=True)
    loss.backward()
    pred = model(images, freeze_vit=True)
    assert _finite_scalar(loss), "VAT action loss is not a finite scalar"
    assert tuple(pred.shape) == (2, 3, 4), f"unexpected VAT prediction shape {tuple(pred.shape)}"
    return {"loss": loss, "prediction_shape": tuple(pred.shape)}


def _vat_siglip() -> dict[str, Any]:
    import torch
    from vit_pytorch.vat_siglip import SigLIPVAT

    model = SigLIPVAT(
        dim=32,
        depth=1,
        heads=2,
        dim_head=16,
        dim_action=4,
        mlp_dim=64,
        action_chunk_len=3,
        siglip_image_size=14,
        siglip_patch_size=7,
        siglip_dim=32,
        siglip_depth=2,
        siglip_heads=2,
        siglip_mlp_dim=64,
        vit_layer_indices=(1,),
    )
    images = torch.randn(2, 1, 3, 14, 14)
    actions = torch.randn(2, 3, 4)
    loss = model(images, actions=actions, freeze_vit=True)
    loss.backward()
    pred = model(images, freeze_vit=True)
    assert _finite_scalar(loss), "SigLIP-VAT action loss is not a finite scalar"
    assert tuple(pred.shape) == (2, 3, 4), f"unexpected SigLIP-VAT prediction shape {tuple(pred.shape)}"
    return {"loss": loss, "prediction_shape": tuple(pred.shape), "checkpoint_loaded": False}


def _wwt() -> dict[str, Any]:
    import torch
    from vit_pytorch.wwt import WWT

    model = WWT(
        image_size=16,
        patch_size=8,
        num_classes=5,
        dim=32,
        depth=1,
        num_slots=(4, 2),
        sigreg_slots=(True, False),
        heads=2,
        dim_head=16,
        mlp_dim=64,
    )
    out = model(torch.randn(2, 3, 16, 16))
    if isinstance(out, tuple):
        logits, sigreg_loss = out
    else:
        logits, sigreg_loss = out, None
    total = logits.mean() + (sigreg_loss if sigreg_loss is not None else 0)
    total.backward()
    assert tuple(logits.shape) == (2, 5), f"unexpected WWT logits shape {tuple(logits.shape)}"
    if sigreg_loss is not None:
        assert _finite_scalar(sigreg_loss), "WWT SigReg loss is not finite"
    return {"logits_shape": tuple(logits.shape), "sigreg_loss": sigreg_loss}


def _vit_with_decorr() -> dict[str, Any]:
    import torch
    import torch.nn.functional as F
    from vit_pytorch.vit_with_decorr import ViT

    model = ViT(
        image_size=16,
        patch_size=8,
        num_classes=5,
        dim=32,
        depth=1,
        heads=2,
        dim_head=16,
        mlp_dim=64,
        decorr_sample_frac=1.0,
    )
    model.train()
    logits, aux_loss = model(torch.randn(2, 3, 16, 16))
    labels = torch.randint(0, 5, (2,))
    loss = F.cross_entropy(logits, labels) + 0.1 * aux_loss
    loss.backward()
    assert tuple(logits.shape) == (2, 5), f"unexpected decorrelation ViT logits shape {tuple(logits.shape)}"
    assert _finite_scalar(aux_loss), "decorrelation auxiliary loss is not finite"
    return {"logits_shape": tuple(logits.shape), "aux_loss": aux_loss}


def _vaat_import() -> dict[str, Any]:
    import importlib

    module = importlib.import_module("vit_pytorch.vaat")
    names = [name for name in ("AST", "ViT", "VAAT") if hasattr(module, name)]
    assert names == ["AST", "ViT", "VAAT"], f"unexpected VAAT exports {names}"
    return {"exports": names, "coverage": "import-only; construct an audio smoke only after torchaudio and audio layout are selected"}


CASES: dict[str, Callable[[], dict[str, Any]]] = {
    "distill": _distill,
    "mae": _mae,
    "simmim": _simmim,
    "mpp": _mpp,
    "mp3": _mp3,
    "dino": _dino,
    "esvit": _esvit,
    "learnable-memory": _learnable_memory,
    "lejepa": _lejepa,
    "vat": _vat,
    "vat-siglip": _vat_siglip,
    "wwt": _wwt,
    "vit-with-decorr": _vit_with_decorr,
    "vaat-import": _vaat_import,
}


def _looks_like_dependency_gap(case: str, exc: BaseException) -> bool:
    text = f"{type(exc).__name__}: {exc}"
    if isinstance(exc, (ImportError, ModuleNotFoundError)):
        return True
    return any(dep in text for dep in OPTIONAL_DEPENDENCIES.get(case, ()))


def run_case(case: str) -> Result:
    try:
        details = CASES[case]()
    except Exception as exc:  # noqa: BLE001 - this is a diagnostic runner
        err = {"error_type": type(exc).__name__, "error": str(exc).splitlines()[0] if str(exc) else repr(exc)}
        if _looks_like_dependency_gap(case, exc):
            deps = OPTIONAL_DEPENDENCIES.get(case, ())
            dep_text = ", ".join(deps) if deps else "runtime dependency"
            return Result(case, "dependency_gap", f"missing or incompatible optional dependency: {dep_text}", err)
        if case in VERSION_FRAGILE:
            return Result(case, "version_fragile", "known current-version token/positional-embedding compatibility pitfall reproduced", err)
        return Result(case, "unexpected_failure", "expected tiny smoke to pass but it failed", err)

    details = _jsonable(details)
    if case in VERSION_FRAGILE:
        return Result(case, "verified", "previously version-fragile wrapper passed in this runtime", details)
    return Result(case, "verified", "tiny CPU smoke passed", details)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tiny CPU smoke checks for vit-pytorch pretraining/adaptation wrappers.")
    parser.add_argument("--case", action="append", choices=[*CASE_ORDER, "all"], help="Run only selected case(s). May be repeated. Default: all cases.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of a text summary.")
    parser.add_argument("--fail-on-unexpected", action="store_true", help="Exit non-zero for unexpected failures. Known version-fragile and dependency-gap results do not fail.")
    parser.add_argument("--threads", type=int, default=1, help="torch.set_num_threads value for deterministic small CPU checks. Default: 1.")
    parser.add_argument("--seed", type=int, default=7, help="Random seed. Default: 7.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    try:
        import torch

        torch.manual_seed(args.seed)
        torch.set_num_threads(args.threads)
        torch.set_grad_enabled(True)
    except Exception as exc:  # noqa: BLE001
        result = Result("environment", "dependency_gap", "PyTorch is required for all vit-pytorch smoke checks", {"error_type": type(exc).__name__, "error": str(exc)})
        payload = {"results": [result.__dict__], "summary": {"dependency_gap": 1}}
        print(json.dumps(payload, indent=2) if args.json else f"[dependency_gap] environment: {result.summary}: {result.details['error']}")
        return 1

    selected = args.case or ["all"]
    if "all" in selected:
        cases = CASE_ORDER
    else:
        # Preserve canonical order while honoring repeated --case values only once.
        requested = set(selected)
        cases = [case for case in CASE_ORDER if case in requested]

    results = [run_case(case) for case in cases]
    summary: dict[str, int] = {}
    for result in results:
        summary[result.status] = summary.get(result.status, 0) + 1

    if args.json:
        print(json.dumps({"results": [result.__dict__ for result in results], "summary": summary}, indent=2, sort_keys=True))
    else:
        for result in results:
            details = ""
            if result.details:
                if "error" in result.details:
                    details = f" ({result.details.get('error_type')}: {result.details.get('error')})"
                else:
                    details = f" {json.dumps(result.details, sort_keys=True)}"
            print(f"[{result.status}] {result.case}: {result.summary}{details}")
        print("summary: " + ", ".join(f"{key}={value}" for key, value in sorted(summary.items())))

    if args.fail_on_unexpected and summary.get("unexpected_failure", 0):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
