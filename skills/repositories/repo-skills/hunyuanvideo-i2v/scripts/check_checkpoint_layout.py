#!/usr/bin/env python3
"""Validate the HunyuanVideo-I2V checkpoint tree before a workflow run.

Safe by default: only checks for required files/directories and reports what is
missing. It does not download anything.

Example (run from the real checkout root):
  python "$SKILL_ROOT/scripts/check_checkpoint_layout.py" --ckpts-root "$CHECKOUT_ROOT/ckpts" --mode inference
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _required_paths(ckpts_root: Path, mode: str, model_resolution: str) -> list[Path]:
    base = ckpts_root
    i2v_root = base / f"hunyuan-video-i2v-{model_resolution}"
    checks: list[Path] = []
    if mode in {"inference", "train", "all"}:
        checks.extend(
            [
                i2v_root / "transformers" / "mp_rank_00_model_states.pt",
                i2v_root / "vae" / "pytorch_model.pt",
                base / "text_encoder_i2v",
                base / "text_encoder_2",
            ]
        )
    if mode in {"extraction", "all"}:
        checks.append(i2v_root / "vae" / "pytorch_model.pt")
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the HunyuanVideo-I2V checkpoint tree")
    parser.add_argument("--ckpts-root", default="./ckpts", help="Path to the checkpoint root")
    parser.add_argument("--mode", choices=["inference", "train", "extraction", "all"], default="inference")
    parser.add_argument("--model-resolution", choices=["540p", "720p"], default="720p")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    ckpts_root = Path(args.ckpts_root).expanduser().resolve()
    required = _required_paths(ckpts_root, args.mode, args.model_resolution)

    results: list[dict[str, Any]] = []
    missing: list[str] = []
    for path in required:
        ok = path.exists()
        results.append({"path": str(path), "ok": ok, "kind": "dir" if path.is_dir() else "file"})
        if not ok:
            missing.append(str(path))

    summary = {"ok": not missing, "ckpts_root": str(ckpts_root), "mode": args.mode, "results": results, "missing": missing}
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"Checkpoint root: {ckpts_root}")
        for item in results:
            status = "OK" if item["ok"] else "MISSING"
            print(f"{status} {item['kind']}: {item['path']}")
        if missing:
            print("Missing required paths:")
            for path in missing:
                print(f"- {path}")
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
