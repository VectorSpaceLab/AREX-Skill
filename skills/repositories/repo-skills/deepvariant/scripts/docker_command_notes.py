#!/usr/bin/env python3
"""Print DeepVariant container command review notes.

This helper does not run containers. It summarizes safe review reminders for
DeepVariant workflow families so future agents can catch mount/runtime mistakes
before execution.
"""

from __future__ import annotations

import argparse
import json
import sys

WORKFLOW_INFO = {
    "germline": {
        "runner": "/opt/deepvariant/bin/run_deepvariant",
        "image": "google/deepvariant:1.10.0",
        "notes": [
            "Mount the reference/read parent directory and output directory at stable container paths such as /input and /output.",
            "Use exactly one model type and verify assay compatibility before running.",
            "Add --dry_run=true for command review when the user is not ready to execute.",
        ],
    },
    "trio": {
        "runner": "/opt/deepvariant/bin/deeptrio/run_deeptrio",
        "image": "google/deepvariant:1.10.0",
        "notes": [
            "Supply one VCF output for child and each supplied parent.",
            "In duo mode omit every parent2 flag instead of passing empty placeholders.",
            "Request a complete per-sample gVCF set before GLnexus merge planning.",
        ],
    },
    "pangenome": {
        "runner": "/opt/deepvariant/bin/run_pangenome_aware_deepvariant",
        "image": "google/deepvariant:1.10.0",
        "notes": [
            "Mount the GBZ pangenome and review shared-memory size before running.",
            "Confirm --ref_name_pangenome when the GBZ reference name differs from the FASTA label.",
            "Use WGS or WES model types for the documented pangenome-aware workflow.",
        ],
    },
    "analysis": {
        "runner": "vcf_stats_report, runtime_by_region_vis, or show_examples",
        "image": "google/deepvariant:1.10.0",
        "notes": [
            "Confirm the target report inputs already exist; do not create them from this helper.",
            "Bound show_examples scans with num-records, regions, or max-examples-to-scan.",
            "Keep report output directories explicit and mounted.",
        ],
    },
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Print DeepVariant container runtime review notes.")
    parser.add_argument("--workflow", choices=sorted(WORKFLOW_INFO), required=True)
    parser.add_argument("--engine", choices=["docker", "singularity"], default="docker")
    parser.add_argument("--gpu", action="store_true", help="Include GPU runtime reminders.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args()

    info = dict(WORKFLOW_INFO[args.workflow])
    notes = list(info["notes"])
    if args.engine == "docker":
        notes.extend([
            "Use -v host_dir:container_dir for every input, output, model, BED, logging, and intermediate directory.",
            "Do not mix host paths and container paths in DeepVariant flags.",
        ])
        if args.gpu:
            notes.append("Use GPU flags only after confirming NVIDIA container runtime and compatible image support.")
    else:
        notes.extend([
            "Use bind mounts that preserve the same container-visible paths as the planned command.",
            "Use --cleanenv when host environment variables risk changing tool behavior.",
        ])
        if args.gpu:
            notes.append("Confirm the HPC/Singularity installation exposes NVIDIA devices before adding GPU assumptions.")

    payload = {
        "workflow": args.workflow,
        "engine": args.engine,
        "runner": info["runner"],
        "suggested_image": info["image"],
        "notes": notes,
        "never_runs_commands": True,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Workflow: {payload['workflow']}")
        print(f"Engine: {payload['engine']}")
        print(f"Runner: {payload['runner']}")
        print(f"Suggested image: {payload['suggested_image']}")
        for note in notes:
            print(f"- {note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
