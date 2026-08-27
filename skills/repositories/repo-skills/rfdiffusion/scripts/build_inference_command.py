#!/usr/bin/env python3
"""Build quoted RFdiffusion run_inference.py commands for common workflows.

The helper prints a shell command; it does not run RFdiffusion.
"""

from __future__ import annotations

import argparse
import shlex


def quote_override(value: str) -> str:
    return shlex.quote(value)


def base_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--run-inference", default="run_inference.py", help="RFdiffusion launcher command")
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--num-designs", type=int, default=10)
    parser.add_argument("--model-directory")
    parser.add_argument("--checkpoint")
    parser.add_argument("--deterministic", action="store_true")
    parser.add_argument("--no-trajectory", action="store_true")
    parser.add_argument("--final-step", type=int)


def add_shared(parts: list[str], args: argparse.Namespace) -> None:
    parts.append(f"inference.output_prefix={shlex.quote(args.output_prefix)}")
    parts.append(f"inference.num_designs={args.num_designs}")
    if args.model_directory:
        parts.append(f"inference.model_directory_path={shlex.quote(args.model_directory)}")
    if args.checkpoint:
        parts.append(f"inference.ckpt_override_path={shlex.quote(args.checkpoint)}")
    if args.deterministic:
        parts.append("inference.deterministic=True")
    if args.no_trajectory:
        parts.append("inference.write_trajectory=False")
    if args.final_step is not None:
        parts.append(f"inference.final_step={args.final_step}")


def require_contig(contig: str) -> str:
    if not contig:
        raise SystemExit("contig is required")
    if contig.startswith("[") and contig.endswith("]"):
        return f"contigmap.contigs={contig}"
    return f"contigmap.contigs=[{contig}]"


def build_unconditional(args: argparse.Namespace) -> list[str]:
    parts = [shlex.quote(args.run_inference)]
    add_shared(parts, args)
    parts.append(quote_override(require_contig(args.contig)))
    return parts


def build_motif(args: argparse.Namespace) -> list[str]:
    parts = [shlex.quote(args.run_inference)]
    add_shared(parts, args)
    parts.append(f"inference.input_pdb={shlex.quote(args.input_pdb)}")
    parts.append(quote_override(require_contig(args.contig)))
    if args.length:
        parts.append(f"contigmap.length={args.length}")
    return parts


def build_partial(args: argparse.Namespace) -> list[str]:
    parts = [shlex.quote(args.run_inference)]
    add_shared(parts, args)
    parts.append(f"inference.input_pdb={shlex.quote(args.input_pdb)}")
    parts.append(quote_override(require_contig(args.contig)))
    parts.append(f"diffuser.partial_T={args.partial_t}")
    if args.provide_seq:
        parts.append(quote_override(f"contigmap.provide_seq=[{args.provide_seq}]"))
    return parts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="workflow", required=True)

    uncond = subparsers.add_parser("unconditional")
    base_args(uncond)
    uncond.add_argument("--contig", required=True, help="Length/range such as 150-150 or [100-200]")
    uncond.set_defaults(builder=build_unconditional)

    motif = subparsers.add_parser("motif")
    base_args(motif)
    motif.add_argument("--input-pdb", required=True)
    motif.add_argument("--contig", required=True)
    motif.add_argument("--length")
    motif.set_defaults(builder=build_motif)

    partial = subparsers.add_parser("partial")
    base_args(partial)
    partial.add_argument("--input-pdb", required=True)
    partial.add_argument("--contig", required=True)
    partial.add_argument("--partial-t", type=int, required=True)
    partial.add_argument("--provide-seq")
    partial.set_defaults(builder=build_partial)

    args = parser.parse_args()
    print(" ".join(args.builder(args)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
