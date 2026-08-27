#!/usr/bin/env python3
"""Suggest a PhysicsNeMo route from coarse task signals.

This helper is intentionally dependency-free. It does not import PhysicsNeMo
and it never reads the source checkout beyond its own arguments.
"""

from __future__ import annotations

import argparse
import json
import sys

SHAPE_FAMILIES = {
    "grid": ["FNO", "AFNO", "Pix2Pix", "UNet", "SRResNet", "DiT"],
    "weather": ["DLWP", "GraphCastNet", "Pangu", "Fengwu", "SwinRNN", "AFNO"],
    "mesh": ["MeshGraphNet", "Transolver", "GeoTransolver", "FIGConvUNet", "DoMINO", "VFGN"],
    "point-cloud": ["DoMINO", "FIGConvUNet", "GeoTransolver"],
    "sequence": ["One2ManyRNN", "Seq2SeqRNN", "SwinRNN"],
    "diffusion": ["SongUNet", "DhariwalUNet", "StormCastUNet", "TopoDiff", "DPOTNet"],
    "tabular": ["FullyConnected"],
}

DOMAIN_EXAMPLES = {
    "cfd": ["Darcy FNO tutorial", "Vortex Shedding MeshGraphNet tutorial", "External aerodynamics recipes"],
    "weather": ["FCN-AFNO tutorial", "GraphCast weather recipe", "StormCast diffusion recipe"],
    "structural": ["Deforming Plate tutorial", "Crash surrogate recipes"],
    "geophysics": ["Diffusion FWI recipe"],
    "active-learning": ["Two-moons active learning tutorial"],
    "generative": ["TopoDiff tutorial"],
}

SIBLING_ROUTES = {
    "datapipes": "datapipes",
    "distributed": "distributed-and-domain-parallel",
    "mesh": "mesh-and-geometry",
    "diffusion": "diffusion-and-generative",
    "active": "active-learning-and-deployment",
}


def suggest(shape: str | None, domain: str | None, task: str | None) -> dict[str, object]:
    families = SHAPE_FAMILIES.get((shape or "").lower(), [])
    examples = DOMAIN_EXAMPLES.get((domain or "").lower(), [])
    sibling_routes = []
    text = " ".join([shape or "", domain or "", task or ""]).lower()
    for token, route in SIBLING_ROUTES.items():
        if token in text:
            sibling_routes.append(route)
    if "mesh" in text and "mesh-and-geometry" not in sibling_routes:
        sibling_routes.append("mesh-and-geometry")
    if any(k in text for k in ["ddp", "fsdp", "shardtensor", "distributed", "torchrun"]):
        sibling_routes.append("distributed-and-domain-parallel")
    if any(k in text for k in ["diffusion", "generative", "downscaling", "inverse"]):
        sibling_routes.append("diffusion-and-generative")
    if any(k in text for k in ["active learning", "onnx", "deploy", "export"]):
        sibling_routes.append("active-learning-and-deployment")
    return {
        "data_shape": shape,
        "domain": domain,
        "task": task,
        "candidate_families": families,
        "example_starting_points": examples,
        "sibling_routes": list(dict.fromkeys(sibling_routes)),
        "note": "Confirm exact class existence in the installed package when a family is optional-backend dependent or low-stability.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-shape", help="Coarse data-shape signal such as grid, weather, mesh, sequence, diffusion, tabular.")
    parser.add_argument("--domain", help="Domain signal such as cfd, weather, structural, geophysics, active-learning, generative.")
    parser.add_argument("--task", help="Short task description.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a text menu.")
    args = parser.parse_args(argv)

    payload = suggest(args.data_shape, args.domain, args.task)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    print(f"Shape: {payload['data_shape'] or 'unknown'}")
    print(f"Domain: {payload['domain'] or 'unknown'}")
    print(f"Task: {payload['task'] or 'unknown'}")
    print("Candidate families:")
    for family in payload["candidate_families"]:
        print(f"- {family}")
    print("Example starting points:")
    for example in payload["example_starting_points"]:
        print(f"- {example}")
    if payload["sibling_routes"]:
        print("Sibling routes:")
        for route in payload["sibling_routes"]:
            print(f"- {route}")
    print(payload["note"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
