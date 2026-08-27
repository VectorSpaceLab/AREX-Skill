#!/usr/bin/env python3
"""Validate a HunyuanVideo checkpoint directory without loading weights.

The check is intentionally read-only: it verifies expected paths, derives the
FP8 map path, and reports actionable missing files before a long GPU job.

Examples:
  python validate_checkpoint_layout.py --model-base ckpts
  python validate_checkpoint_layout.py --model-base ckpts --require-fp8 --dit-weight ckpts/hunyuan-video-t2v-720p/transformers/mp_rank_00_model_states_fp8.pt
  python validate_checkpoint_layout.py --model-base ckpts --json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def check_path(path: Path, kind: str, required: bool = True) -> Dict[str, Any]:
    exists = path.is_dir() if kind == "dir" else path.is_file()
    return {
        "path": str(path),
        "kind": kind,
        "required": required,
        "exists": exists,
        "status": "ok" if exists else ("missing" if required else "optional-missing"),
    }


def has_any(path: Path, names: List[str]) -> bool:
    return any((path / name).exists() for name in names)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate HunyuanVideo checkpoint layout without loading model weights.")
    parser.add_argument("--model-base", default="ckpts", help="Model root used by --model-base / MODEL_BASE, default: ckpts.")
    parser.add_argument("--dit-weight", default=None, help="Optional explicit DIT .pt file or transformer directory to validate.")
    parser.add_argument("--require-fp8", action="store_true", help="Require an FP8 checkpoint and its derived *_map.pt file.")
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    args = parser.parse_args()

    model_base = Path(args.model_base).expanduser()
    t2v = model_base / "hunyuan-video-t2v-720p"
    transformers = t2v / "transformers"
    vae = t2v / "vae"
    text_encoder = model_base / "text_encoder"
    text_encoder_2 = model_base / "text_encoder_2"

    checks: List[Dict[str, Any]] = [
        check_path(model_base, "dir"),
        check_path(t2v, "dir"),
        check_path(transformers, "dir"),
        check_path(vae, "dir"),
        check_path(vae / "pytorch_model.pt", "file"),
        check_path(text_encoder, "dir"),
        check_path(text_encoder_2, "dir"),
    ]

    dit_weight = Path(args.dit_weight).expanduser() if args.dit_weight else transformers / "mp_rank_00_model_states.pt"
    if args.dit_weight and dit_weight.suffix != ".pt" and not dit_weight.is_dir():
        checks.append({"path": str(dit_weight), "kind": "file-or-dir", "required": True, "exists": False, "status": "invalid", "message": "--dit-weight should be a .pt file or a directory containing .pt weights."})
    elif dit_weight.is_dir():
        pt_files = sorted(dit_weight.glob("*.pt"))
        recognized = [p.name for p in pt_files if p.name.startswith("pytorch_model_") or p.name.endswith("_model_states.pt")]
        checks.append({"path": str(dit_weight), "kind": "dir", "required": True, "exists": bool(recognized), "status": "ok" if recognized else "missing", "recognized_weights": recognized})
    else:
        checks.append(check_path(dit_weight, "file"))

    fp8_map = None
    if args.require_fp8:
        if dit_weight.suffix == ".pt":
            fp8_map = dit_weight.with_name(dit_weight.name[:-3] + "_map.pt")
            checks.append(check_path(fp8_map, "file"))
        else:
            checks.append({"path": str(dit_weight), "kind": "file", "required": True, "exists": False, "status": "invalid", "message": "FP8 validation requires --dit-weight to name the *_fp8.pt file."})

    optional_notes = []
    if text_encoder.exists() and not has_any(text_encoder, ["config.json", "tokenizer.json", "tokenizer.model", "tokenizer_config.json"]):
        optional_notes.append("text_encoder exists but common config/tokenizer markers were not found; verify the LLaVA language-model extraction completed.")
    if text_encoder_2.exists() and not has_any(text_encoder_2, ["config.json", "pytorch_model.bin", "model.safetensors", "tokenizer.json"]):
        optional_notes.append("text_encoder_2 exists but common CLIP markers were not found; verify the CLIP download completed.")

    failures = [c for c in checks if c.get("required") and not c.get("exists")]
    report = {
        "schema": "hunyuan-video.checkpoint-layout.v1",
        "model_base": str(model_base),
        "dit_weight": str(dit_weight),
        "fp8_map": str(fp8_map) if fp8_map else None,
        "checks": checks,
        "notes": optional_notes,
        "ok": not failures,
        "failure_count": len(failures),
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for check in checks:
            marker = "OK" if check.get("exists") else ("MISS" if check.get("required") else "SKIP")
            extra = f" - {check.get('message')}" if check.get("message") else ""
            print(f"[{marker}] {check['path']}{extra}")
            if check.get("recognized_weights"):
                print("       recognized weights: " + ", ".join(check["recognized_weights"]))
        for note in optional_notes:
            print(f"[NOTE] {note}")
        print("Status: " + ("OK" if report["ok"] else "FAILED"))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
