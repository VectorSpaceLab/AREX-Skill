#!/usr/bin/env python3
"""Validate a Swin supervised main.py command without executing it."""
from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path

try:
    import yaml
except Exception:
    yaml = None


def parse_cmd(argv: list[str]):
    if argv and argv[0] in {"torchrun", "python", "python3"}:
        # Keep only the script and later flags.
        for i, tok in enumerate(argv):
            if tok.endswith("main.py"):
                argv = argv[i:]
                break
    if not argv or not argv[0].endswith("main.py"):
        raise SystemExit("command must target main.py")
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("script")
    p.add_argument("--cfg")
    p.add_argument("--data-path")
    p.add_argument("--zip", action="store_true")
    p.add_argument("--cache-mode", choices=["no", "full", "part"])
    p.add_argument("--pretrained")
    p.add_argument("--resume")
    p.add_argument("--eval", action="store_true")
    p.add_argument("--throughput", action="store_true")
    p.add_argument("--batch-size")
    p.add_argument("--accumulation-steps")
    p.add_argument("--use-checkpoint", action="store_true")
    p.add_argument("--disable_amp", action="store_true")
    p.add_argument("--fused_window_process", action="store_true")
    p.add_argument("--fused_layernorm", action="store_true")
    p.add_argument("--optim")
    p.add_argument("--opts", nargs="*")
    ns, unknown = p.parse_known_args(argv)
    return ns, unknown


def load_model_type(repo_root: Path | None, cfg: str | None):
    if not (repo_root and cfg and yaml):
        return None
    path = Path(cfg)
    if not path.is_absolute():
        path = repo_root / path
    if not path.exists():
        return "CONFIG_NOT_FOUND"
    data = yaml.safe_load(path.read_text()) or {}
    return (data.get("MODEL") or {}).get("TYPE")


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate a supervised Swin main.py command shape.")
    ap.add_argument("--repo-root", type=Path, help="Optional checkout root for config inspection.")
    ap.add_argument("command", nargs=argparse.REMAINDER, help="Use -- before the command to validate.")
    args = ap.parse_args()
    cmd = args.command
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    if len(cmd) == 1:
        cmd = shlex.split(cmd[0])
    ns, unknown = parse_cmd(cmd)
    errors = []
    warnings = []
    if not ns.cfg:
        errors.append("missing --cfg")
    if not ns.data_path:
        errors.append("missing --data-path")
    if ns.eval and not (ns.resume or ns.pretrained):
        warnings.append("--eval usually needs --resume or a pretrained checkpoint path")
    if ns.pretrained and ns.resume:
        warnings.append("both --pretrained and --resume were provided; verify this is intentional")
    if ns.throughput and not ns.disable_amp:
        warnings.append("throughput examples commonly use --disable_amp for stable measurement")
    if ns.fused_window_process:
        warnings.append("--fused_window_process requires the optional CUDA extension")
    if ns.optim and ns.optim.startswith("fused"):
        warnings.append("fused optimizers require Apex")
    mt = load_model_type(args.repo_root, ns.cfg)
    if mt == "CONFIG_NOT_FOUND":
        errors.append("config file not found relative to --repo-root")
    elif mt == "swin_moe":
        warnings.append("MODEL.TYPE is swin_moe; use moe-and-acceleration instead of baseline supervised guidance")
    elif mt and mt not in {"swin", "swinv2", "swin_mlp"}:
        warnings.append(f"unexpected MODEL.TYPE: {mt}")
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)
    for w in warnings:
        print(f"WARNING: {w}")
    if unknown:
        print("INFO: unparsed flags:", " ".join(unknown))
    if not errors:
        print("supervised command shape looks plausible; this did not run training")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
