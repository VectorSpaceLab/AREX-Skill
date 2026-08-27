#!/usr/bin/env python3
"""Patch AnyDoor placeholder checkpoint paths in a controlled way.

This helper performs exact string replacements for the known placeholder values
used by the repo configs. Use --dry-run first when you only want to inspect the
planned changes.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

PLACEHOLDER_MAP = {
    "configs/inference.yaml": {
        "path/epoch=1-step=8687.ckpt": "{inference_ckpt}",
    },
    "configs/demo.yaml": {
        "path/epoch=1-step=8687.ckpt": "{demo_ckpt}",
    },
    "configs/anydoor.yaml": {
        "path/dinov2_vitg14_pretrain.pth": "{dinov2_weight}",
    },
}


def replace_exact(text: str, old: str, new: str) -> tuple[str, bool]:
    if old not in text:
        return text, False
    return text.replace(old, new), True


def patch_file(path: Path, replacements: dict[str, str], apply: bool) -> list[str]:
    text = path.read_text(encoding="utf-8")
    changes: list[str] = []
    updated = text
    for old, new in replacements.items():
        updated, changed = replace_exact(updated, old, new)
        if changed:
            changes.append(f"{old} -> {new}")
    if apply and updated != text:
        path.write_text(updated, encoding="utf-8")
    return changes


def main() -> int:
    parser = argparse.ArgumentParser(description="Patch AnyDoor placeholder checkpoint paths.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="AnyDoor repository root.")
    parser.add_argument("--inference-ckpt", required=True, help="Replacement for configs/inference.yaml pretrained_model.")
    parser.add_argument("--demo-ckpt", required=True, help="Replacement for configs/demo.yaml pretrained_model.")
    parser.add_argument("--dinov2-weight", required=True, help="Replacement for configs/anydoor.yaml DINOv2 weight.")
    parser.add_argument("--apply", action="store_true", help="Write changes to disk.")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    substitutions = {
        "configs/inference.yaml": {"path/epoch=1-step=8687.ckpt": args.inference_ckpt},
        "configs/demo.yaml": {"path/epoch=1-step=8687.ckpt": args.demo_ckpt},
        "configs/anydoor.yaml": {"path/dinov2_vitg14_pretrain.pth": args.dinov2_weight},
    }

    any_changes = False
    for rel, repls in substitutions.items():
        path = repo_root / rel
        if not path.exists():
            print(f"missing: {rel}")
            continue
        changes = patch_file(path, repls, args.apply)
        if changes:
            any_changes = True
            print(rel)
            for item in changes:
                print(f"  {item}")
        else:
            print(f"{rel}: no placeholder replacements needed")

    if not args.apply:
        print("dry-run only; rerun with --apply to write files")
    elif not any_changes:
        print("nothing changed")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
