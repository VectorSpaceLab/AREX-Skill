#!/usr/bin/env python3
"""Summarize a DreamCraft3D trial directory without importing ML libraries."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def rel_list(paths: List[Path], root: Path) -> List[str]:
    out = []
    for path in sorted(paths):
        try:
            out.append(str(path.relative_to(root)))
        except ValueError:
            out.append(str(path))
    return out


def summarize(trial_dir: Path, args: argparse.Namespace) -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "trial_dir": str(trial_dir),
        "exists": trial_dir.exists(),
        "is_dir": trial_dir.is_dir(),
        "status": "ok",
        "problems": [],
        "warnings": [],
        "paths": {},
    }
    if not trial_dir.exists() or not trial_dir.is_dir():
        report["status"] = "fail"
        report["problems"].append("trial directory is missing or is not a directory")
        return report

    ckpt = trial_dir / "ckpts" / "last.ckpt"
    parsed = trial_dir / "configs" / "parsed.yaml"
    save = trial_dir / "save"
    report["paths"].update(
        {
            "checkpoint": {"path": str(ckpt), "exists": ckpt.is_file()},
            "parsed_config": {"path": str(parsed), "exists": parsed.is_file()},
            "save_dir": {"path": str(save), "exists": save.is_dir()},
        }
    )
    if args.require_checkpoint and not ckpt.is_file():
        report["problems"].append("required checkpoint ckpts/last.ckpt is missing")
    if args.require_parsed_config and not parsed.is_file():
        report["problems"].append("required configs/parsed.yaml is missing")

    pngs = list(save.rglob("*.png")) if save.is_dir() else []
    mp4s = list(save.rglob("*.mp4")) if save.is_dir() else []
    objs = list(save.rglob("*.obj")) if save.is_dir() else []
    mtls = list(save.rglob("*.mtl")) if save.is_dir() else []
    textures = []
    if save.is_dir():
        for ext in ("*.jpg", "*.jpeg", "*.png", "*.exr"):
            textures.extend([p for p in save.rglob(ext) if "export" in p.as_posix()])
    export_dirs = [p for p in save.rglob("*export*") if p.is_dir()] if save.is_dir() else []

    report["artifacts"] = {
        "png_count": len(pngs),
        "mp4_count": len(mp4s),
        "obj_count": len(objs),
        "mtl_count": len(mtls),
        "texture_like_count": len(textures),
        "export_dirs": rel_list(export_dirs, trial_dir),
        "sample_pngs": rel_list(pngs[:20], trial_dir),
        "sample_mp4s": rel_list(mp4s[:20], trial_dir),
        "objs": rel_list(objs, trial_dir),
        "mtls": rel_list(mtls, trial_dir),
        "texture_like_files": rel_list(textures[:30], trial_dir),
    }

    if args.require_export and not objs:
        report["problems"].append("required export OBJ was not found under save/")
    if save.is_dir() is False:
        report["warnings"].append("save/ directory is absent; validation/test/export media may not have been produced")
    if not report["problems"] and not ckpt.is_file():
        report["warnings"].append("checkpoint ckpts/last.ckpt is absent; this trial may not be usable for downstream stages")
    if not report["problems"] and not parsed.is_file():
        report["warnings"].append("configs/parsed.yaml is absent; export may need reconstructed config overrides")

    report["status"] = "fail" if report["problems"] else "warn" if report["warnings"] else "ok"
    return report


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize DreamCraft3D output trial directories.")
    parser.add_argument("--trial-dir", required=True, help="Path to one DreamCraft3D trial directory.")
    parser.add_argument("--require-checkpoint", action="store_true", help="Fail if ckpts/last.ckpt is absent.")
    parser.add_argument("--require-parsed-config", action="store_true", help="Fail if configs/parsed.yaml is absent.")
    parser.add_argument("--require-export", action="store_true", help="Fail if no OBJ export is found under save/.")
    parser.add_argument("--json", action="store_true", help="Print JSON.")
    args = parser.parse_args(argv)

    report = summarize(Path(args.trial_dir), args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"status: {report['status']}")
        for problem in report["problems"]:
            print(f"problem: {problem}")
        for warning in report["warnings"]:
            print(f"warning: {warning}")
        if report.get("artifacts"):
            art = report["artifacts"]
            print(f"png={art['png_count']} mp4={art['mp4_count']} obj={art['obj_count']} mtl={art['mtl_count']} textures={art['texture_like_count']}")
            for obj in art["objs"]:
                print(f"obj: {obj}")
    return 0 if report["status"] in ("ok", "warn") else 2


if __name__ == "__main__":
    raise SystemExit(main())
