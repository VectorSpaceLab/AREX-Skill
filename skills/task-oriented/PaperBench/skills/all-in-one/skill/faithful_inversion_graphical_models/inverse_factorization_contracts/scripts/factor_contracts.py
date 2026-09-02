#!/usr/bin/env python3
"""Build ordered inverse factor contracts from inverse BN parent sets."""

from __future__ import annotations

import argparse
import json


def build_contracts(inverse_parents, latents, observed, elimination_order, families=None):
    latents = set(latents)
    observed = set(observed)
    families = families or {}
    sampling_order = list(reversed(elimination_order))
    contracts = []
    for variable in sampling_order:
        parents = sorted(inverse_parents.get(variable, []))
        contract = {
            "variable": variable,
            "parents": parents,
            "latent_parents": [item for item in parents if item in latents],
            "observed_parents": [item for item in parents if item in observed],
            "family": families.get(variable, "gaussian"),
            "feature_order": parents,
            "factor": "q({} | {})".format(variable, ", ".join(parents) if parents else "empty"),
        }
        contracts.append(contract)
    return contracts


def validate_contracts(contracts, latents, observed):
    latents = set(latents)
    observed = set(observed)
    known = latents | observed
    issues = []
    seen = set()
    for contract in contracts:
        variable = contract.get("variable")
        if variable not in latents:
            issues.append({"check": "factor_variable_not_latent", "variable": variable})
        if variable in observed:
            issues.append({"check": "observed_variable_sampled", "variable": variable})
        if variable in seen:
            issues.append({"check": "duplicate_factor", "variable": variable})
        seen.add(variable)
        parents = contract.get("parents", [])
        for parent in parents:
            if parent not in known:
                issues.append({"check": "unknown_parent", "variable": variable, "parent": parent})
        if sorted(contract.get("latent_parents", [])) != sorted(parent for parent in parents if parent in latents):
            issues.append({"check": "latent_parent_split_mismatch", "variable": variable})
        if sorted(contract.get("observed_parents", [])) != sorted(parent for parent in parents if parent in observed):
            issues.append({"check": "observed_parent_split_mismatch", "variable": variable})
    missing = latents - seen
    for variable in sorted(missing):
        issues.append({"check": "missing_factor", "variable": variable})
    return {"ok": not issues, "issues": issues, "factor_count": len(contracts)}


def feature_vector(contract, values):
    missing = [name for name in contract["feature_order"] if name not in values]
    if missing:
        raise KeyError("missing feature values: " + ", ".join(missing))
    return [float(values[name]) for name in contract["feature_order"]]


def build_and_validate(inverse_parents, latents, observed, elimination_order, families=None):
    contracts = build_contracts(inverse_parents, latents, observed, elimination_order, families=families)
    validation = validate_contracts(contracts, latents, observed)
    return {"schema_version": 1, "contracts": contracts, "validation": validation}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="JSON input with inverse_parents, latents, observed, elimination_order, and optional families.")
    parser.add_argument("--output", default="")
    args = parser.parse_args(argv)
    with open(args.input, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    result = build_and_validate(
        data["inverse_parents"],
        data["latents"],
        data.get("observed", []),
        data["elimination_order"],
        data.get("families", {}),
    )
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2, sort_keys=True)
            handle.write("\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["validation"]["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
