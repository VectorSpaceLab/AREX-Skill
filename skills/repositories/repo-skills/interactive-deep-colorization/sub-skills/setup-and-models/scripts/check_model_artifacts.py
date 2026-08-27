#!/usr/bin/env python3
"""Check Interactive Deep Colorization model artifact presence without downloading.

The repository's historical fetch scripts download several model files. This
helper records the expected relative paths and validates whether they are
present under a caller-supplied checkout or artifact root. It never contacts the
network and never modifies files.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List

ARTIFACTS: Dict[str, Dict[str, object]] = {
    "reference-caffe": {
        "relative_path": "models/reference_model/model.caffemodel",
        "workflows": ["caffe-local"],
        "role": "Official Caffe local-hints colorization and distribution model weights.",
        "source_url_hint": "http://colorization.eecs.berkeley.edu/siggraph/models/model.caffemodel",
    },
    "global-caffe": {
        "relative_path": "models/global_model/global_model.caffemodel",
        "workflows": ["global-histogram"],
        "role": "Caffe colorization weights for global histogram transfer.",
        "source_url_hint": "http://colorization.eecs.berkeley.edu/siggraph/models/global_model.caffemodel",
    },
    "global-dummy": {
        "relative_path": "models/global_model/dummy.caffemodel",
        "workflows": ["global-histogram"],
        "role": "Dummy Caffe weights for the global statistics network.",
        "source_url_hint": "http://colorization.eecs.berkeley.edu/siggraph/models/dummy.caffemodel",
    },
    "pytorch-trained": {
        "relative_path": "models/pytorch/pytorch_trained.pth",
        "workflows": ["pytorch-local"],
        "role": "PyTorch-trained local-hints weights listed by the repository fetch script.",
        "source_url_hint": "http://colorization.eecs.berkeley.edu/siggraph/models/pytorch.pth",
    },
    "pytorch-converted-caffe": {
        "relative_path": "models/pytorch/caffemodel.pth",
        "workflows": ["pytorch-local", "docker-pytorch"],
        "role": "Converted Caffe weights used by the PyTorch GUI/Docker default path.",
        "source_url_hint": "http://colorization.eecs.berkeley.edu/siggraph/models/caffemodel.pth",
    },
}

PROTOTXTS = {
    "reference-deploy-nodist": "models/reference_model/deploy_nodist.prototxt",
    "reference-deploy-nopred": "models/reference_model/deploy_nopred.prototxt",
    "global-deploy-nodist": "models/global_model/deploy_nodist.prototxt",
    "global-stats": "models/global_model/global_stats.prototxt",
}


def selected_artifacts(workflow: str) -> Iterable[tuple[str, Dict[str, object]]]:
    for key, meta in ARTIFACTS.items():
        if workflow == "all" or workflow in meta["workflows"]:
            yield key, meta


def file_status(root: Path, rel: str) -> Dict[str, object]:
    path = root / rel
    exists = path.is_file()
    return {
        "relative_path": rel,
        "exists": exists,
        "size_bytes": path.stat().st_size if exists else None,
    }


def build_report(root: Path, workflow: str, include_prototxts: bool) -> Dict[str, object]:
    artifacts: Dict[str, object] = {}
    missing: List[str] = []
    for key, meta in selected_artifacts(workflow):
        status = file_status(root, str(meta["relative_path"]))
        item = dict(meta)
        item.update(status)
        artifacts[key] = item
        if not status["exists"]:
            missing.append(str(meta["relative_path"]))

    prototxt_report = {}
    if include_prototxts:
        for key, rel in PROTOTXTS.items():
            prototxt_report[key] = file_status(root, rel)

    return {
        "status": "ok" if not missing else "missing-artifacts",
        "workflow": workflow,
        "root_checked": str(root),
        "network_performed": False,
        "artifacts": artifacts,
        "prototxts": prototxt_report,
        "missing_required_for_workflow": missing,
        "notes": [
            "This helper does not download model files.",
            "Prototxt presence is useful but does not replace required model weights.",
        ],
    }


def print_human(report: Dict[str, object]) -> None:
    print(f"model artifact check: {report['status']}")
    print(f"workflow: {report['workflow']}")
    print("network performed: no")
    print()
    for key, meta in report["artifacts"].items():
        marker = "OK" if meta["exists"] else "MISSING"
        size = meta["size_bytes"] if meta["size_bytes"] is not None else "-"
        print(f"[{marker}] {meta['relative_path']} ({key}, size={size})")
        print(f"       role: {meta['role']}")
    if report.get("prototxts"):
        print("\nprototxt/config files:")
        for key, meta in report["prototxts"].items():
            marker = "OK" if meta["exists"] else "MISSING"
            print(f"[{marker}] {meta['relative_path']} ({key})")
    missing = report["missing_required_for_workflow"]
    if missing:
        print("\nmissing required artifact(s):")
        for rel in missing:
            print(f"  - {rel}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate expected iDeepColor model artifact files without downloading.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="checkout or artifact root containing models/")
    parser.add_argument(
        "--workflow",
        choices=("all", "pytorch-local", "docker-pytorch", "caffe-local", "global-histogram"),
        default="all",
        help="restrict expected model files to one workflow",
    )
    parser.add_argument("--no-prototxts", action="store_true", help="skip checking bundled prototxt/config files")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args()

    root = args.repo_root.resolve()
    report = build_report(root=root, workflow=args.workflow, include_prototxts=not args.no_prototxts)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)
    return 0 if report["status"] == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
