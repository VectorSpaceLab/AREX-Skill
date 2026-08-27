#!/usr/bin/env python3
"""Generate a conservative LAMMPS input for DeePMD-kit models.

The script prints to stdout only. It does not execute LAMMPS, inspect models,
or modify files.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable


ELEMENT_MASSES = {
    "H": 1.008,
    "He": 4.002602,
    "Li": 6.94,
    "Be": 9.0121831,
    "B": 10.81,
    "C": 12.011,
    "N": 14.007,
    "O": 15.999,
    "F": 18.998403163,
    "Ne": 20.1797,
    "Na": 22.98976928,
    "Mg": 24.305,
    "Al": 26.9815385,
    "Si": 28.085,
    "P": 30.973761998,
    "S": 32.06,
    "Cl": 35.45,
    "Ar": 39.948,
    "K": 39.0983,
    "Ca": 40.078,
    "Sc": 44.955908,
    "Ti": 47.867,
    "V": 50.9415,
    "Cr": 51.9961,
    "Mn": 54.938044,
    "Fe": 55.845,
    "Co": 58.933194,
    "Ni": 58.6934,
    "Cu": 63.546,
    "Zn": 65.38,
}


def positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def non_negative_float(value: str) -> float:
    parsed = float(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return parsed


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def parse_mass_overrides(values: Iterable[str]) -> dict[str, float]:
    masses: dict[str, float] = {}
    for item in values:
        if ":" not in item:
            raise argparse.ArgumentTypeError(
                f"mass override {item!r} must use ELEMENT:MASS syntax"
            )
        element, raw_mass = item.split(":", 1)
        element = element.strip()
        if not element:
            raise argparse.ArgumentTypeError("mass override element cannot be empty")
        try:
            mass = positive_float(raw_mass)
        except argparse.ArgumentTypeError as exc:
            raise argparse.ArgumentTypeError(
                f"mass for {element!r} must be positive"
            ) from exc
        masses[element] = mass
    return masses


def format_float(value: float) -> str:
    return f"{value:g}"


def build_pair_style(args: argparse.Namespace) -> str:
    keywords: list[str] = []
    if len(args.model) > 1:
        keywords.extend(
            [
                "out_file",
                args.model_deviation_file,
                "out_freq",
                str(args.model_deviation_freq),
            ]
        )
        if args.atomic_deviation:
            keywords.append("atomic")
        if args.relative is not None:
            keywords.extend(["relative", format_float(args.relative)])
        if args.relative_v is not None:
            keywords.extend(["relative_v", format_float(args.relative_v)])
    elif any(
        value is not None
        for value in (args.relative, args.relative_v)
    ) or args.atomic_deviation:
        raise SystemExit(
            "model-deviation options require at least two --model values"
        )

    for value in args.fparam:
        keywords.extend(["fparam", value])
    for value in args.aparam:
        keywords.extend(["aparam", value])
    for value in args.charge_spin:
        keywords.extend(["charge_spin", value])

    pieces = ["pair_style", args.pair_style, *args.model, *keywords]
    return " ".join(str(piece) for piece in pieces)


def ensemble_lines(args: argparse.Namespace) -> list[str]:
    temp = format_float(args.temp)
    tdamp = format_float(args.tdamp)
    if args.ensemble == "nve":
        return ["fix             1 all nve"]
    if args.ensemble == "nvt":
        return [f"velocity        all create {temp} {args.seed}", f"fix             1 all nvt temp {temp} {temp} {tdamp}"]
    pressure = format_float(args.pressure)
    pdamp = format_float(args.pdamp)
    return [
        f"velocity        all create {temp} {args.seed}",
        f"fix             1 all npt temp {temp} {temp} {tdamp} iso {pressure} {pressure} {pdamp}",
    ]


def render_input(args: argparse.Namespace) -> str:
    if args.units == "lj":
        raise SystemExit("DeePMD-kit LAMMPS integration does not support units lj")
    if args.pair_style == "deepspin" and args.atom_style == "atomic":
        raise SystemExit("pair_style deepspin usually requires a spin-capable --atom-style")
    if len(args.model) > 1 and args.model_deviation_freq > args.steps:
        print(
            "warning: --model-deviation-freq is greater than --steps; no deviation output will be written",
            file=sys.stderr,
        )

    mass_overrides = parse_mass_overrides(args.masses)
    missing_masses = [
        element
        for element in args.elements
        if element not in mass_overrides and element not in ELEMENT_MASSES
    ]
    if missing_masses and not args.omit_masses:
        missing = ", ".join(missing_masses)
        raise SystemExit(
            f"missing masses for {missing}; pass --masses ELEMENT:MASS or --omit-masses"
        )

    lines: list[str] = [
        "# Conservative DeePMD-kit LAMMPS input generated by write_lammps_deepmd_input.py",
        "# Review model type_map, atom types, masses, and ensemble settings before production runs.",
    ]
    if args.plugin:
        lines.extend(
            [
                "# Plugin mode: omit this line if your LAMMPS binary has USER-DEEPMD built in.",
                "plugin          load libdeepmd_lmp.so",
            ]
        )
    lines.extend(
        [
            f"units           {args.units}",
            "boundary        p p p",
            f"atom_style      {args.atom_style}",
        ]
    )
    if args.atom_style == "spin":
        lines.append("atom_modify     map array")
    lines.extend(
        [
            "neighbor        2.0 bin",
            "neigh_modify    every 10 delay 0 check yes",
            f"read_data       {args.data}",
        ]
    )

    if not args.omit_masses:
        for index, element in enumerate(args.elements, start=1):
            mass = mass_overrides.get(element, ELEMENT_MASSES[element])
            lines.append(f"mass            {index} {format_float(mass)}  # {element}")

    lines.extend(
        [
            build_pair_style(args),
            "pair_coeff      * * " + " ".join(args.elements),
            "thermo_style    custom step temp pe ke etotal press vol lx ly lz",
            f"thermo          {args.thermo_freq}",
            f"dump            1 all custom {args.dump_freq} {args.dump_file} id type x y z",
        ]
    )
    lines.extend(ensemble_lines(args))
    lines.extend(
        [
            f"timestep        {format_float(args.timestep)}",
            f"run             {args.steps}",
            "",
        ]
    )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Print a conservative LAMMPS input using DeePMD-kit pair_style "
            "deepmd or deepspin. The script does not run LAMMPS."
        )
    )
    parser.add_argument(
        "--model",
        nargs="+",
        required=True,
        help="DeePMD model file(s); first drives dynamics, later models enable deviation output.",
    )
    parser.add_argument("--data", required=True, help="LAMMPS data file path.")
    parser.add_argument(
        "--elements",
        nargs="+",
        required=True,
        help="LAMMPS atom type to model element mapping, in type order.",
    )
    parser.add_argument(
        "--masses",
        nargs="*",
        default=[],
        metavar="ELEMENT:MASS",
        help="Per-element mass overrides, for example O:15.999 H:1.008.",
    )
    parser.add_argument(
        "--omit-masses",
        action="store_true",
        help="Do not emit mass commands; use only if the data file already defines Masses.",
    )
    parser.add_argument(
        "--pair-style",
        choices=["deepmd", "deepspin"],
        default="deepmd",
        help="DeePMD LAMMPS pair style to use.",
    )
    parser.add_argument(
        "--atom-style",
        default="atomic",
        help="LAMMPS atom_style. Use a spin-capable style for deepspin models.",
    )
    parser.add_argument(
        "--plugin",
        action="store_true",
        help="Include plugin load line for libdeepmd_lmp.so.",
    )
    parser.add_argument(
        "--units",
        default="metal",
        help="LAMMPS units style. DeePMD-kit does not support lj.",
    )
    parser.add_argument(
        "--ensemble",
        choices=["nve", "nvt", "npt"],
        default="nvt",
        help="Integrator/thermostat/barostat ensemble.",
    )
    parser.add_argument("--temp", type=positive_float, default=300.0, help="Target temperature.")
    parser.add_argument("--pressure", type=float, default=1.0, help="Target isotropic pressure for NPT.")
    parser.add_argument("--tdamp", type=positive_float, default=0.1, help="Thermostat damping time.")
    parser.add_argument("--pdamp", type=positive_float, default=1.0, help="Barostat damping time.")
    parser.add_argument("--timestep", type=positive_float, default=0.0005, help="LAMMPS timestep.")
    parser.add_argument("--steps", type=positive_int, default=1000, help="Number of MD steps.")
    parser.add_argument("--seed", type=positive_int, default=743574, help="Velocity random seed.")
    parser.add_argument("--thermo-freq", type=positive_int, default=100, help="Thermo output frequency.")
    parser.add_argument("--dump-freq", type=positive_int, default=100, help="Trajectory dump frequency.")
    parser.add_argument("--dump-file", default="traj.lammpstrj", help="Trajectory dump filename.")
    parser.add_argument(
        "--model-deviation-file",
        default="model_devi.out",
        help="Deviation output file when multiple models are provided.",
    )
    parser.add_argument(
        "--model-deviation-freq",
        type=positive_int,
        default=100,
        help="Deviation output frequency when multiple models are provided.",
    )
    parser.add_argument(
        "--atomic-deviation",
        action="store_true",
        help="Emit atomic model deviation when multiple models are provided.",
    )
    parser.add_argument(
        "--relative",
        type=non_negative_float,
        help="Relative force deviation level when multiple models are provided.",
    )
    parser.add_argument(
        "--relative-v",
        type=non_negative_float,
        help="Relative virial deviation level when multiple models are provided.",
    )
    parser.add_argument(
        "--fparam",
        action="append",
        default=[],
        help="Append a frame parameter value to pair_style.",
    )
    parser.add_argument(
        "--aparam",
        action="append",
        default=[],
        help="Append an atomic parameter value to pair_style.",
    )
    parser.add_argument(
        "--charge-spin",
        action="append",
        default=[],
        help="Append a charge/spin value to pair_style.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    print(render_input(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
