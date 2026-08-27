#!/usr/bin/env python3
"""Build a quoted RFdiffusion binder-design command.

This helper validates lightweight formatting and prints a command. It does not
import RFdiffusion, read model weights, or run inference.
"""

from __future__ import annotations

import argparse
import re
import shlex

HOTSPOT_RE = re.compile(r"^[A-Za-z][0-9]+[A-Za-z]?$")
SPAN_RE = re.compile(r"^[A-Za-z][0-9]+[A-Za-z]?(?:-[0-9]+[A-Za-z]?)?(?:/[A-Za-z][0-9]+[A-Za-z]?(?:-[0-9]+[A-Za-z]?)*?)*$|^[A-Za-z][0-9]+-[0-9]+$")
LENGTH_RE = re.compile(r"^[0-9]+-[0-9]+$")


def validate_hotspots(raw: str) -> list[str]:
    hotspots = [item.strip().strip("'\"") for item in raw.split(",") if item.strip()]
    if not hotspots:
        raise SystemExit("at least one hotspot is required")
    bad = [item for item in hotspots if not HOTSPOT_RE.match(item)]
    if bad:
        raise SystemExit(f"invalid hotspot(s): {', '.join(bad)}; expected chain-qualified values like A59")
    return hotspots


def validate_length(raw: str) -> str:
    if not LENGTH_RE.match(raw):
        raise SystemExit("--binder-length must look like 70-100 or 100-100")
    lo, hi = [int(x) for x in raw.split("-")]
    if lo <= 0 or hi < lo:
        raise SystemExit("--binder-length must be positive and ordered")
    return raw


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-inference", default="run_inference.py")
    parser.add_argument("--input-pdb", required=True)
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--target-contig", required=True, help="Target span such as A1-150")
    parser.add_argument("--binder-length", required=True, help="Binder range such as 70-100")
    parser.add_argument("--hotspots", required=True, help="Comma-separated chain-qualified residues such as A59,A83,A91")
    parser.add_argument("--num-designs", type=int, default=10)
    parser.add_argument("--model-directory")
    parser.add_argument("--checkpoint")
    parser.add_argument("--noise-scale", type=float, help="Set both denoiser.noise_scale_ca and denoiser.noise_scale_frame")
    parser.add_argument("--flexible-target", help="Residue span for contigmap.inpaint_str, such as B10-35")
    args = parser.parse_args()

    target = args.target_contig.strip()
    binder_length = validate_length(args.binder_length.strip())
    hotspots = validate_hotspots(args.hotspots)
    if args.num_designs < 1:
        raise SystemExit("--num-designs must be >= 1")

    contig = f"contigmap.contigs=[{target}/0 {binder_length}]"
    parts = [shlex.quote(args.run_inference)]
    parts.append(f"inference.output_prefix={shlex.quote(args.output_prefix)}")
    parts.append(f"inference.input_pdb={shlex.quote(args.input_pdb)}")
    parts.append(shlex.quote(contig))
    parts.append(shlex.quote(f"ppi.hotspot_res=[{','.join(hotspots)}]"))
    parts.append(f"inference.num_designs={args.num_designs}")
    if args.model_directory:
        parts.append(f"inference.model_directory_path={shlex.quote(args.model_directory)}")
    if args.checkpoint:
        parts.append(f"inference.ckpt_override_path={shlex.quote(args.checkpoint)}")
    if args.noise_scale is not None:
        parts.append(f"denoiser.noise_scale_ca={args.noise_scale:g}")
        parts.append(f"denoiser.noise_scale_frame={args.noise_scale:g}")
    if args.flexible_target:
        parts.append(shlex.quote(f"contigmap.inpaint_str=[{args.flexible_target}]"))

    print(" ".join(parts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
