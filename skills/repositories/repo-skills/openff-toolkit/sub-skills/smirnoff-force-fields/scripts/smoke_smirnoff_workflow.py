#!/usr/bin/env python
"""Smoke-test a basic OpenFF Toolkit SMIRNOFF ForceField workflow."""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from typing import Any


def _error_summary(error: BaseException) -> dict[str, Any]:
    return {
        "ok": False,
        "error_type": type(error).__name__,
        "error": str(error),
        "traceback_tail": traceback.format_exception_only(type(error), error)[-1].strip(),
    }


def _summarize_labels(labels: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    for molecule_labels in labels:
        handler_summary: dict[str, Any] = {}
        for handler_name, assigned in molecule_labels.items():
            examples = []
            for match, parameter in list(assigned.items())[:3]:
                if isinstance(parameter, list):
                    parameter_ids = [getattr(item, "id", None) for item in parameter]
                    parameter_smirks = [getattr(item, "smirks", None) for item in parameter]
                else:
                    parameter_ids = getattr(parameter, "id", None)
                    parameter_smirks = getattr(parameter, "smirks", None)
                examples.append(
                    {
                        "match": str(match),
                        "parameter_id": parameter_ids,
                        "smirks": parameter_smirks,
                    }
                )
            handler_summary[handler_name] = {
                "assignment_count": len(assigned),
                "examples": examples,
            }
        summary.append(handler_summary)
    return summary


def run(args: argparse.Namespace) -> dict[str, Any]:
    try:
        from openff.toolkit import ForceField, Molecule, Topology
        from openff.toolkit.typing.engines.smirnoff import get_available_force_fields
    except Exception as error:  # pragma: no cover - actionability matters in smoke script
        summary = _error_summary(error)
        summary["action"] = "Install OpenFF Toolkit in the active Python environment before running this smoke test."
        return summary

    summary: dict[str, Any] = {
        "ok": True,
        "smiles": args.smiles,
        "force_field": args.force_field,
        "available_force_fields_count": None,
        "available_force_fields_sample": [],
        "molecule": {},
        "force_field_loaded": False,
        "registered_parameter_handlers": [],
        "labels": None,
        "interchange": None,
    }

    try:
        available = get_available_force_fields()
        summary["available_force_fields_count"] = len(available)
        summary["available_force_fields_sample"] = available[:10]
    except Exception as error:
        summary["available_force_fields_error"] = _error_summary(error)

    try:
        molecule = Molecule.from_smiles(args.smiles, allow_undefined_stereo=args.allow_undefined_stereo)
        topology = Topology.from_molecules([molecule])
        summary["molecule"] = {
            "n_atoms": molecule.n_atoms,
            "n_bonds": molecule.n_bonds,
            "topology_n_molecules": topology.n_molecules,
        }
    except Exception as error:
        summary.update(_error_summary(error))
        summary["action"] = "Check the SMILES, stereochemistry, and molecule construction workflow."
        return summary

    try:
        force_field = ForceField(args.force_field, load_plugins=args.load_plugins)
        summary["force_field_loaded"] = True
        summary["registered_parameter_handlers"] = list(force_field.registered_parameter_handlers)
    except Exception as error:
        summary.update(_error_summary(error))
        summary["action"] = (
            "Check get_available_force_fields(), install the package that supplies the requested OFFXML, "
            "or pass a local .offxml path. For custom handlers, install the plugin and use --load-plugins."
        )
        return summary

    if args.label:
        try:
            summary["labels"] = _summarize_labels(force_field.label_molecules(topology))
        except Exception as error:
            summary["labels"] = _error_summary(error)

    if not args.skip_interchange:
        try:
            interchange = force_field.create_interchange(topology)
            summary["interchange"] = {
                "ok": True,
                "type": type(interchange).__name__,
                "collections": sorted(getattr(interchange, "collections", {}).keys()),
            }
        except Exception as error:
            interchange_summary = _error_summary(error)
            interchange_summary["action"] = (
                "If this is a dependency error, install openff-interchange and required simulation backends. "
                "If this is an assignment error, inspect label_molecules() output for missing parameters."
            )
            summary["interchange"] = interchange_summary

    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smiles", default="CCO", help="SMILES string to build and parameter-label; default: CCO")
    parser.add_argument(
        "--force-field",
        default="openff-2.3.0.offxml",
        help="Installed OFFXML name or local .offxml path; default: openff-2.3.0.offxml",
    )
    parser.add_argument("--label", action="store_true", help="Run ForceField.label_molecules and include label summaries")
    parser.add_argument("--skip-interchange", action="store_true", help="Skip create_interchange even if available")
    parser.add_argument("--load-plugins", action="store_true", help="Load installed custom ParameterHandler plugins")
    parser.add_argument(
        "--allow-undefined-stereo",
        action="store_true",
        help="Allow undefined stereochemistry during Molecule.from_smiles",
    )
    args = parser.parse_args()

    summary = run(args)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary.get("ok") else 2


if __name__ == "__main__":
    sys.exit(main())
