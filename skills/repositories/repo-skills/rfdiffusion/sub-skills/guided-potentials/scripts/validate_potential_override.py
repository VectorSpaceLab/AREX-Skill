#!/usr/bin/env python3
"""Validate RFdiffusion guiding-potential override strings.

This helper is intentionally lightweight: it checks syntax and source-derived
configuration rules without importing RFdiffusion or requiring model weights.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from typing import Iterable

IMPLEMENTED_POTENTIALS = {
    "monomer_ROG",
    "binder_ROG",
    "dimer_ROG",
    "binder_ncontacts",
    "interface_ncontacts",
    "monomer_contacts",
    "olig_contacts",
    "substrate_contacts",
}

REQUIRE_BINDERLEN = {
    "binder_ROG",
    "dimer_ROG",
    "binder_ncontacts",
    "interface_ncontacts",
}

DECAYS = {"constant", "linear", "quadratic", "cubic"}
CUSTOM_CONTACT_RE = re.compile(r"^[A-Z][&!][A-Z]$")


def parse_guiding_potentials(raw: str) -> list[str]:
    try:
        parsed = ast.literal_eval(raw)
    except (SyntaxError, ValueError) as exc:
        raise ValueError(
            "guiding potentials must be a Python/Hydra-like list of strings, "
            "for example '[\"type:monomer_ROG,weight:1\"]'"
        ) from exc

    if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
        raise ValueError("guiding potentials must parse to a list of strings")
    if not parsed:
        raise ValueError("guiding potentials list is empty")
    return parsed


def parse_potential_string(potential: str) -> dict[str, str]:
    settings: dict[str, str] = {}
    for entry in potential.split(","):
        if not entry:
            raise ValueError(f"empty entry in potential string {potential!r}")
        if ":" not in entry:
            raise ValueError(f"entry {entry!r} must use key:value syntax")
        key, value = entry.split(":", 1)
        if not key or not value:
            raise ValueError(f"entry {entry!r} must include both key and value")
        if key in settings:
            raise ValueError(f"duplicate key {key!r} in potential string {potential!r}")
        settings[key] = value

    potential_type = settings.get("type")
    if potential_type is None:
        raise ValueError(f"potential string {potential!r} is missing required type:<name>")
    if potential_type not in IMPLEMENTED_POTENTIALS:
        valid = ", ".join(sorted(IMPLEMENTED_POTENTIALS))
        raise ValueError(f"unknown potential {potential_type!r}; valid names are: {valid}")

    for key, value in settings.items():
        if key == "type":
            continue
        try:
            float(value)
        except ValueError as exc:
            raise ValueError(
                f"value for {key!r} in {potential_type!r} must be numeric because RFdiffusion parses it as float"
            ) from exc

    return settings


def validate_custom_contacts(contact_string: str, max_chain_letter: str | None) -> list[str]:
    warnings: list[str] = []
    tokens = [token.strip() for token in contact_string.split(",") if token.strip()]
    if not tokens:
        raise ValueError("olig custom contact string is empty")

    for token in tokens:
        if not CUSTOM_CONTACT_RE.match(token):
            raise ValueError(
                f"custom contact token {token!r} must be exactly like A&B for attraction or A!B for repulsion"
            )
        if max_chain_letter and (token[0] > max_chain_letter or token[2] > max_chain_letter):
            warnings.append(
                f"token {token!r} references a chain beyond expected A-{max_chain_letter} for the supplied symmetry"
            )
    return warnings


def chain_count_for_symmetry(symmetry: str | None) -> int | None:
    if not symmetry:
        return None
    symbol = symmetry.lower()
    if symbol.startswith("c") and symbol[1:].isdigit():
        return int(symbol[1:])
    if symbol.startswith("d") and symbol[1:].isdigit():
        return 2 * int(symbol[1:])
    if symbol.startswith("tetra") or symbol == "t":
        return 12
    return None


def max_chain_letter_for_count(count: int | None) -> str | None:
    if count is None or count < 1 or count > 26:
        return None
    return chr(ord("A") + count - 1)


def validate(args: argparse.Namespace) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if args.guide_decay not in DECAYS:
        errors.append(f"guide decay {args.guide_decay!r} is invalid; choose one of {', '.join(sorted(DECAYS))}")

    try:
        potential_strings = parse_guiding_potentials(args.guiding_potentials)
        settings_list = [parse_potential_string(item) for item in potential_strings]
    except ValueError as exc:
        errors.append(str(exc))
        return errors, warnings

    potential_types = {settings["type"] for settings in settings_list}
    symmetry_chain_count = chain_count_for_symmetry(args.symmetry)
    max_chain_letter = max_chain_letter_for_count(symmetry_chain_count)

    if "olig_contacts" in potential_types:
        if not args.symmetry:
            errors.append("olig_contacts requires --symmetry so RFdiffusion can build a contact matrix")
        if not (args.olig_intra_all or args.olig_inter_all or args.olig_custom_contact):
            warnings.append(
                "olig_contacts has no --olig-intra-all, --olig-inter-all, or --olig-custom-contact; contact matrix may be empty"
            )
        if args.olig_custom_contact:
            try:
                warnings.extend(validate_custom_contacts(args.olig_custom_contact, max_chain_letter))
            except ValueError as exc:
                errors.append(str(exc))

    if "substrate_contacts" in potential_types and not args.substrate:
        errors.append("substrate_contacts requires --substrate matching the substrate residue name in the input PDB")

    binder_potentials = sorted(potential_types & REQUIRE_BINDERLEN)
    if binder_potentials and not args.binderlen_available:
        warnings.append(
            "binder-specific potential(s) "
            + ", ".join(binder_potentials)
            + " require RFdiffusion to infer binderlen; use only with binder/PPI or dimer-style contigs"
        )

    if args.has_hotspots and potential_types:
        warnings.append(
            "PPI hotspot workflows should be baselined without potentials first; repository guidance notes odd interactions"
        )

    if args.guide_scale is not None and args.guide_scale <= 0:
        warnings.append("guide scale is non-positive; this is unusual for attractive guidance")

    return errors, warnings


def print_messages(label: str, messages: Iterable[str]) -> None:
    for message in messages:
        print(f"{label}: {message}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--guiding-potentials",
        required=True,
        help='List literal such as ["type:monomer_ROG,weight:1,min_dist:5"]',
    )
    parser.add_argument("--guide-decay", default="constant", help="constant, linear, quadratic, or cubic")
    parser.add_argument("--guide-scale", type=float, default=None, help="Optional global guide scale")
    parser.add_argument("--symmetry", default=None, help="Symmetry symbol such as C6, D2, or tetrahedral")
    parser.add_argument("--olig-intra-all", action="store_true", help="Set when potentials.olig_intra_all=True")
    parser.add_argument("--olig-inter-all", action="store_true", help="Set when potentials.olig_inter_all=True")
    parser.add_argument("--olig-custom-contact", default=None, help="Custom contact string such as A&B,A!C")
    parser.add_argument("--substrate", default=None, help="Substrate residue name for substrate_contacts")
    parser.add_argument("--binderlen-available", action="store_true", help="Set when using a binder/PPI or dimer-style contig")
    parser.add_argument("--has-hotspots", action="store_true", help="Set when the command also uses ppi.hotspot_res")
    args = parser.parse_args()

    errors, warnings = validate(args)
    print_messages("warning", warnings)
    if errors:
        print_messages("error", errors)
        return 1

    print("potential override validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
