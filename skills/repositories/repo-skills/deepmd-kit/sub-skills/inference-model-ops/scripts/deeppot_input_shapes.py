#!/usr/bin/env python3
"""Print DeePMD-kit DeepPot input shapes and a minimal NumPy skeleton."""

from __future__ import annotations

import argparse
import textwrap


def positive_int(value: str) -> int:
    """Parse a positive integer for argparse."""
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected an integer, got {value!r}") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compute expected DeepPot coord/cell/atype shapes and print a minimal "
            "NumPy skeleton. This helper does not import DeePMD-kit or load a model."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--natoms", type=positive_int, required=True, help="Number of atoms per frame")
    parser.add_argument("--nframes", type=positive_int, default=1, help="Number of frames")
    parser.add_argument(
        "--nopbc",
        action="store_true",
        help="Use cell=None for non-periodic systems instead of a periodic cell array",
    )
    parser.add_argument(
        "--mixed-type",
        action="store_true",
        help="Print atom_types as (nframes, natoms) for mixed_type=True",
    )
    parser.add_argument(
        "--atomic",
        action="store_true",
        help="Include expected additional DeepPot.eval outputs when atomic=True",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    coord_flat = (args.nframes, args.natoms * 3)
    coord_structured = (args.nframes, args.natoms, 3)
    cell_flat = None if args.nopbc else (args.nframes, 9)
    cell_structured = None if args.nopbc else (args.nframes, 3, 3)
    atype = (args.nframes, args.natoms) if args.mixed_type else (args.natoms,)

    print("DeepPot input shapes")
    print(f"  coords flattened:  {coord_flat}")
    print(f"  coords structured: {coord_structured}")
    if args.nopbc:
        print("  cells:             None  # non-periodic")
    else:
        print(f"  cells flattened:   {cell_flat}")
        print(f"  cells structured:  {cell_structured}")
    print(f"  atom_types:        {atype}")
    print(f"  mixed_type:        {args.mixed_type}")
    print()

    print("Expected DeepPot.eval outputs")
    print(f"  energy:            {(args.nframes, 1)}")
    print(f"  force:             {(args.nframes, args.natoms, 3)}")
    print(f"  virial:            {(args.nframes, 9)}")
    if args.atomic:
        print(f"  atomic_energy:     {(args.nframes, args.natoms, 1)}")
        print(f"  atomic_virial:     {(args.nframes, args.natoms, 9)}")
    print()

    cell_line = "cell = None" if args.nopbc else (
        f"cell = np.tile(np.eye(3).reshape(1, 9), ({args.nframes}, 1))"
    )
    if args.mixed_type:
        atype_line = (
            f"atype = np.zeros(({args.nframes}, {args.natoms}), dtype=np.int32)  "
            "# per-frame type indices"
        )
    else:
        atype_line = f"atype = np.zeros(({args.natoms},), dtype=np.int32)  # model type_map indices"
    atomic_arg = ", atomic=True" if args.atomic else ""
    mixed_arg = ", mixed_type=True" if args.mixed_type else ""

    skeleton = f"""
    import numpy as np
    from deepmd.infer import DeepPot

    nframes = {args.nframes}
    natoms = {args.natoms}

    pot = DeepPot("model.pth", auto_batch_size=True)
    coord = np.zeros((nframes, natoms * 3), dtype=float)
    {cell_line}
    {atype_line}

    result = pot.eval(coord, cell, atype{atomic_arg}{mixed_arg})
    energy, force, virial = result[:3]
    """
    print("Minimal NumPy skeleton")
    print(textwrap.dedent(skeleton).strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
