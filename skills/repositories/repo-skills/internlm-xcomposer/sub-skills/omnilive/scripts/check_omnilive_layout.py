#!/usr/bin/env python3
"""Safely validate an InternLM-XComposer2.5-OmniLive model layout.

This helper is intentionally stdlib-only. It checks paths and marker files; it
never imports model libraries, downloads checkpoints, or starts services.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


WORKFLOW_COMPONENTS = {
    "all": ["audio", "base", "adapter", "memory", "merge_lora"],
    "audio": ["audio"],
    "base": ["base"],
    "memory": ["base", "memory", "merge_lora"],
    "service-srs": ["audio", "memory", "merge_lora"],
    "service-gradio": ["audio", "memory", "merge_lora"],
    "benchmark-audio": ["audio"],
    "benchmark-video": ["base"],
}

RECOMMENDED_COMPONENTS = {
    "memory": ["adapter"],
    "service-srs": ["base", "adapter"],
    "service-gradio": ["base", "adapter"],
}

COMPONENT_RULES = {
    "audio": {
        "purpose": "Swift/Qwen2-Audio ASR and audio classification checkpoint",
        "marker_any": [
            ["config.json", "preprocessor_config.json", "processor_config.json"],
            ["tokenizer.json", "tokenizer.model", "vocab.json", "merges.txt"],
        ],
        "weight_patterns": ["*.safetensors", "*.bin", "pytorch_model*.bin", "model*.safetensors"],
        "notes": "Required for audio quickstarts, ASR service, and ASR benchmarks.",
    },
    "base": {
        "purpose": "OmniLive base InternLM-XComposer2.5 VLM and LoRA merge base",
        "marker_any": [
            ["configuration_internlm_xcomposer2.py", "config.json"],
            ["modeling_internlm_xcomposer2.py", "model.safetensors.index.json", "pytorch_model.bin.index.json"],
            ["tokenizer.model", "tokenizer.json"],
        ],
        "weight_patterns": ["*.safetensors", "*.bin", "pytorch_model*.bin", "model*.safetensors"],
        "notes": "Required for base VLM checks and video benchmarks; also input to merge_lora.",
    },
    "adapter": {
        "purpose": "PEFT LoRA adapter to merge into the base model",
        "marker_any": [
            ["adapter_config.json", "README.md"],
            ["adapter_model.safetensors", "adapter_model.bin", "pytorch_model.bin", "zero_to_fp32.py", "tokenizer.model"],
        ],
        "weight_patterns": ["adapter_model*.safetensors", "adapter_model*.bin", "*.safetensors", "*.bin"],
        "notes": "Needed to recreate merge_lora; not enough by itself for memory QA.",
    },
    "memory": {
        "purpose": "Grounding/video-memory model for global and question-related memories",
        "marker_any": [
            ["grounding_qwen.py", "model_grounding_ego.py", "configuration_qwen.py", "config.json"],
            ["constants.py", "mm_utils.py", "llava_arch.py"],
            ["merges.txt", "tokenizer.json", "tokenizer.model"],
        ],
        "weight_patterns": ["*.safetensors", "*.bin", "pytorch_model*.bin", "model*.safetensors"],
        "notes": "Required for memory-backed video QA and online video memory service.",
    },
    "merge_lora": {
        "purpose": "Merged base+adapter MLLM used by memory QA and online services",
        "marker_any": [
            ["configuration_internlm_xcomposer2.py", "config.json"],
            ["modeling_internlm_xcomposer2.py", "model.safetensors.index.json", "pytorch_model.bin.index.json"],
            ["tokenizer.model", "tokenizer.json"],
        ],
        "weight_patterns": ["*.safetensors", "*.bin", "pytorch_model*.bin", "model*.safetensors"],
        "notes": "Must exist before memory video QA; produced by merging base/ and adapter/.",
    },
}

ROOT_RECOMMENDED_FILES = {
    "service-srs": ["SimHei.ttf"],
    "service-gradio": ["SimHei.ttf"],
}


@dataclass
class ComponentReport:
    name: str
    path: str
    purpose: str
    status: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    present_markers: List[str] = field(default_factory=list)
    present_weights: List[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class LayoutReport:
    root: str
    workflow: str
    ok: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    required_components: List[str] = field(default_factory=list)
    recommended_components: List[str] = field(default_factory=list)
    components: Dict[str, ComponentReport] = field(default_factory=dict)
    next_actions: List[str] = field(default_factory=list)


def _glob_names(path: Path, patterns: Iterable[str]) -> List[str]:
    names = []
    for pattern in patterns:
        for found in path.glob(pattern):
            if found.is_file():
                names.append(found.name)
    return sorted(set(names))


def _existing_from_group(path: Path, group: Sequence[str]) -> List[str]:
    return [name for name in group if (path / name).exists()]


def scan_component(
    root: Path,
    component: str,
    *,
    required: bool,
    require_weights: bool,
) -> ComponentReport:
    rule = COMPONENT_RULES[component]
    path = root / component
    report = ComponentReport(
        name=component,
        path=str(path),
        purpose=rule["purpose"],
        status="ok",
        notes=rule["notes"],
    )

    if not path.exists():
        msg = f"missing component directory: {component}/"
        if required:
            report.errors.append(msg)
            report.status = "error"
        else:
            report.warnings.append(msg)
            report.status = "warning"
        return report

    if path.is_symlink() and not path.resolve().exists():
        report.errors.append(f"broken symlink: {component}/ -> {path.resolve()}")
        report.status = "error"
        return report

    if not path.is_dir():
        report.errors.append(f"component path is not a directory: {component}/")
        report.status = "error"
        return report

    for group in rule["marker_any"]:
        present = _existing_from_group(path, group)
        report.present_markers.extend(present)
        if not present:
            msg = "missing any marker from group: " + ", ".join(group)
            if required:
                report.warnings.append(msg)
            else:
                report.warnings.append(msg)

    report.present_markers = sorted(set(report.present_markers))
    if required and not report.present_markers:
        report.errors.append("no recognized OmniLive marker files found in required component")

    report.present_weights = _glob_names(path, rule["weight_patterns"])
    if not report.present_weights:
        msg = "no obvious model weight files found (*.safetensors/*.bin); this may be a code stub or partial download"
        if require_weights and required:
            report.errors.append(msg)
        else:
            report.warnings.append(msg)

    if report.errors:
        report.status = "error"
    elif report.warnings:
        report.status = "warning"
    else:
        report.status = "ok"
    return report


def build_report(args: argparse.Namespace) -> LayoutReport:
    root = Path(args.model_root).expanduser().resolve()
    required_components = WORKFLOW_COMPONENTS[args.workflow]
    recommended_components = RECOMMENDED_COMPONENTS.get(args.workflow, [])

    report = LayoutReport(
        root=str(root),
        workflow=args.workflow,
        ok=False,
        required_components=required_components,
        recommended_components=recommended_components,
    )

    if not root.exists():
        report.errors.append(f"model root does not exist: {root}")
        report.next_actions.append("Download or mount the OmniLive model root before planning this workflow.")
        return report
    if not root.is_dir():
        report.errors.append(f"model root is not a directory: {root}")
        return report

    for component in required_components:
        comp_report = scan_component(
            root,
            component,
            required=True,
            require_weights=args.require_weights,
        )
        report.components[component] = comp_report
        report.errors.extend(f"{component}: {msg}" for msg in comp_report.errors)
        report.warnings.extend(f"{component}: {msg}" for msg in comp_report.warnings)

    for component in recommended_components:
        if component in report.components:
            continue
        comp_report = scan_component(
            root,
            component,
            required=False,
            require_weights=False,
        )
        report.components[component] = comp_report
        report.warnings.extend(f"{component}: {msg}" for msg in comp_report.warnings)

    for root_file in ROOT_RECOMMENDED_FILES.get(args.workflow, []):
        if not (root / root_file).exists():
            report.warnings.append(
                f"root file {root_file} not found; service code may need to use base/{root_file} or a patched font path"
            )

    if args.workflow in {"memory", "service-srs", "service-gradio"}:
        if "merge_lora" in report.components and report.components["merge_lora"].status == "error":
            report.next_actions.append("Create merge_lora/ by merging base/ and adapter/ before memory QA or services.")
        elif "merge_lora" in report.components and not report.components["merge_lora"].present_weights:
            report.next_actions.append("Confirm merge_lora/ contains saved model weights, not only code/tokenizer files.")

    if "audio" in required_components and "audio" in report.components:
        if report.components["audio"].status == "error":
            report.next_actions.append("Use the audio/ subdirectory as the Swift model path for audio workflows.")

    if "base" in required_components and "base" in report.components:
        if report.components["base"].status == "error":
            report.next_actions.append("Use the base/ subdirectory as the Transformers model path for video/base workflows.")

    report.ok = not report.errors
    if report.ok and report.warnings:
        report.next_actions.append("Layout has warnings; decide whether this is planning-only or requires real checkpoint weights.")
    if report.ok and not report.warnings:
        report.next_actions.append("Layout satisfies the selected workflow's structural checks.")
    return report


def report_to_dict(report: LayoutReport) -> dict:
    return {
        "root": report.root,
        "workflow": report.workflow,
        "ok": report.ok,
        "errors": report.errors,
        "warnings": report.warnings,
        "required_components": report.required_components,
        "recommended_components": report.recommended_components,
        "components": {
            name: {
                "path": comp.path,
                "purpose": comp.purpose,
                "status": comp.status,
                "errors": comp.errors,
                "warnings": comp.warnings,
                "present_markers": comp.present_markers,
                "present_weights": comp.present_weights,
                "notes": comp.notes,
            }
            for name, comp in report.components.items()
        },
        "next_actions": report.next_actions,
    }


def print_text(report: LayoutReport) -> None:
    status = "OK" if report.ok else "ERROR"
    print(f"OmniLive layout check: {status}")
    print(f"  root: {report.root}")
    print(f"  workflow: {report.workflow}")
    print(f"  required: {', '.join(report.required_components) or '(none)'}")
    if report.recommended_components:
        print(f"  recommended: {', '.join(report.recommended_components)}")
    print()

    for name, comp in report.components.items():
        print(f"[{comp.status.upper()}] {name}/ - {comp.purpose}")
        print(f"  path: {comp.path}")
        if comp.present_markers:
            print(f"  markers: {', '.join(comp.present_markers)}")
        if comp.present_weights:
            print(f"  weights: {', '.join(comp.present_weights[:8])}" + (" ..." if len(comp.present_weights) > 8 else ""))
        for msg in comp.errors:
            print(f"  error: {msg}")
        for msg in comp.warnings:
            print(f"  warning: {msg}")
        print(f"  note: {comp.notes}")
        print()

    if report.errors:
        print("Errors:")
        for msg in report.errors:
            print(f"  - {msg}")
    if report.warnings:
        print("Warnings:")
        for msg in report.warnings:
            print(f"  - {msg}")
    if report.next_actions:
        print("Next actions:")
        for msg in report.next_actions:
            print(f"  - {msg}")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate an OmniLive model directory layout without importing ML libraries.",
    )
    parser.add_argument("model_root", help="Path to the local internlm-xcomposer2d5-ol-7b model root.")
    parser.add_argument(
        "--workflow",
        choices=sorted(WORKFLOW_COMPONENTS),
        default="all",
        help="Workflow to validate. Default: all components.",
    )
    parser.add_argument(
        "--require-weights",
        action="store_true",
        help="Treat missing *.safetensors/*.bin files in required components as errors.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format. Default: text.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    report = build_report(args)
    if args.format == "json":
        print(json.dumps(report_to_dict(report), indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0 if report.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
