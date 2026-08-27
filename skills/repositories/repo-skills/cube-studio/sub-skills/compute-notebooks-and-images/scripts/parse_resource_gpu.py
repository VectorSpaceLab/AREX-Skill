#!/usr/bin/env python3
"""Parse CubeStudio GPU resource strings and show selector implications.

This helper is standalone and does not import CubeStudio modules.
It mirrors the platform rules for notebook / debug GPU parsing:
- quantity is a non-negative integer
- an optional model name may appear in ASCII or Chinese parentheses
- the model name is uppercased
- commas inside the model name are rejected

Examples
--------
  python parse_resource_gpu.py 0
  python parse_resource_gpu.py 1 2(V100) 2（V100） --base-node-selector 'cpu=true;notebook=true;org=public'
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from typing import Iterable, List, Optional

GPU_VALUE_RE = re.compile(r"^\s*(\d+)\s*(?:[\(（]\s*(.+?)\s*[\)）])?\s*$")


@dataclass
class ParseResult:
    raw: str
    gpu_num: int
    gpu_type: Optional[str]
    resource_name: str
    base_node_selector: str
    notebook_node_selector: str
    pod_node_selector: str
    pod_labels: dict
    pod_env: dict
    note: str


def parse_gpu_value(raw: str, resource_name: str) -> tuple[int, Optional[str], str]:
    text = "" if raw is None else str(raw).strip()
    if not text:
        return 0, None, resource_name

    match = GPU_VALUE_RE.match(text)
    if not match:
        raise ValueError(
            "GPU resource only supports non-negative integer quantities, optionally followed by a model in parentheses, e.g. 2(V100) or 2（V100）"
        )

    gpu_num = int(match.group(1))
    gpu_type = match.group(2)
    if gpu_type is not None:
        gpu_type = gpu_type.strip().upper()
        if "," in gpu_type:
            raise ValueError("GPU type only supports a single model name without commas")
        if not gpu_type:
            gpu_type = None
    return gpu_num, gpu_type, resource_name


def normalize_selector(selector: str) -> str:
    parts: List[str] = []
    for part in re.split(r";|\n|\t", selector or ""):
        part = part.strip()
        if part and part not in parts:
            parts.append(part)
    return ";".join(parts)


def compute_default_node_selector(base_selector: str, gpu_num: int, model_type: str) -> str:
    selector = base_selector or ""
    if gpu_num >= 1:
        selector = selector.replace("cpu=true", "gpu=true") + f";gpu=true;{model_type}=true"
    else:
        selector = selector.replace("gpu=true", "cpu=true") + f";cpu=true;{model_type}=true"
    if "org" not in selector:
        selector += ";org=public"
    return normalize_selector(selector)


def build_result(raw: str, args: argparse.Namespace) -> ParseResult:
    gpu_num, gpu_type, resource_name = parse_gpu_value(raw, args.resource_name)
    base_selector = args.base_node_selector or ""
    notebook_selector = compute_default_node_selector(base_selector, gpu_num, args.model_type)

    pod_labels = {}
    pod_env = {}
    pod_notes: List[str] = []
    if gpu_num >= 1:
        pod_labels["gpu"] = "true"
        pod_notes.append(f"request/limit {resource_name}={gpu_num}")
        if gpu_type:
            pod_notes.append(f"nodeSelector[gpu-type]={gpu_type}")
    else:
        pod_env["NVIDIA_VISIBLE_DEVICES"] = "none"
        pod_notes.append("CPU path only; GPU visibility disabled")

    if "org" not in notebook_selector:
        pod_notes.append("org fallback should have been appended, but check selector input")

    note = "; ".join(pod_notes) if pod_notes else "CPU path with no extra GPU selector"
    pod_node_selector = notebook_selector
    if gpu_type:
        pod_node_selector = f"{pod_node_selector};gpu-type={gpu_type}"

    return ParseResult(
        raw=raw,
        gpu_num=gpu_num,
        gpu_type=gpu_type,
        resource_name=resource_name,
        base_node_selector=normalize_selector(base_selector),
        notebook_node_selector=notebook_selector,
        pod_node_selector=pod_node_selector,
        pod_labels=pod_labels,
        pod_env=pod_env,
        note=note,
    )


def format_human(result: ParseResult) -> str:
    lines = [
        f"input: {result.raw}",
        f"parsed: gpu_num={result.gpu_num} gpu_type={result.gpu_type or '-'} resource_name={result.resource_name}",
        f"base_selector: {result.base_node_selector or '(empty)'}",
        f"notebook_selector: {result.notebook_node_selector}",
        f"pod_selector: {result.pod_node_selector}",
    ]
    if result.pod_labels:
        lines.append(f"pod_labels: {json.dumps(result.pod_labels, ensure_ascii=False, sort_keys=True)}")
    if result.pod_env:
        lines.append(f"pod_env: {json.dumps(result.pod_env, ensure_ascii=False, sort_keys=True)}")
    lines.append(f"note: {result.note}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Parse CubeStudio GPU resource strings and show node-selector implications.",
        epilog=(
            "Examples:\n"
            "  python parse_resource_gpu.py 0\n"
            "  python parse_resource_gpu.py 1 2(V100) 2（V100） --base-node-selector 'cpu=true;notebook=true'\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "resource_gpu",
        nargs="+",
        help="One or more CubeStudio GPU strings such as 0, 1, 2(V100), or 2（V100）.",
    )
    parser.add_argument(
        "--base-node-selector",
        default="cpu=true;notebook=true",
        help="Base selector to normalize before CubeStudio adds GPU / org labels.",
    )
    parser.add_argument(
        "--model-type",
        default="notebook",
        help="Model-type label appended by CubeStudio (for example: notebook or train).",
    )
    parser.add_argument(
        "--resource-name",
        default="nvidia.com/gpu",
        help="Kubernetes GPU resource key used for requests and limits.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of human-readable text.",
    )
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    results: List[ParseResult] = []
    for raw in args.resource_gpu:
        results.append(build_result(raw, args))

    if args.json:
        payload = [asdict(item) for item in results]
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        for idx, result in enumerate(results):
            if idx:
                print()
            print(format_human(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
